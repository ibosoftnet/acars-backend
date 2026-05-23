"""
ACARS Application API Module
HTTP API exposing ATS application messages to external (server-to-server)
callers. Designed to be extensible: each ATS application is registered as a
handler and reached at `/acars-app/<application>` with its own query schema.

Currently registered applications:
- `datis` — recent DEP/ARR D-ATIS messages for a given ICAO.

Future applications (e.g. dcl, pdc, aoc) can be added by writing a new
`_handle_<name>` method and registering it in `self._handlers`.

Authentication: this module only accepts the static `X-API-Key` HTTP header
(via the shared `auth_helper`). The browser-facing JWT cookie flow used by the
SSE stream is deliberately **not** accepted here; browsers do not call this
module.
"""

import logging
import re
import time
from threading import Event, Thread

from flask import Flask, jsonify, request
from flask_cors import CORS

logger = logging.getLogger(__name__)


# ACARS-network app.name values, mirroring how the frontend classifies traffic
# (see acars-viewing-software/page-data-link.php). Any other network (e.g.
# ATN/VDL2 via 'dumpvdl2') is excluded from results.
ACARS_APP_NAMES = ('acarsdec', 'vdlm2dec', 'jaero', 'dumphfdl')

# D-ATIS uplink label.
DATIS_LABEL = 'B9'

# Accepted ATIS direction tokens (D-ATIS).
VALID_DATIS_TYPES = ('dep', 'arr')

# ICAO must be exactly four ASCII letters.
_ICAO_PATTERN = re.compile(r'^[A-Z]{4}$')


class AcarsAppApi:
    """HTTP API dispatching ATS-application queries by sub-path."""

    def __init__(self, db_handler, host, port, max_count_per_type,
                 api_keys=None):
        """
        Args:
            db_handler: Shared DatabaseHandler instance.
            host (str): IP address to bind to.
            port (int): Port to listen on.
            max_count_per_type (int): Hard cap on `count` per type (per
                request). Each handler applies this cap to its own count
                parameter.
            api_keys (iterable[str] | None): Static keys accepted via the
                X-API-Key HTTP header. JWT cookies are intentionally NOT
                accepted by this module.
        """
        self.db_handler = db_handler
        self.host = host
        self.port = port
        self.max_count_per_type = max_count_per_type
        self.app = Flask(__name__)
        CORS(self.app)
        self.thread = None
        self.running = Event()

        # Registry of <application> -> handler. New ATS applications go here.
        self._handlers = {
            'datis': self._handle_datis,
        }

        self._setup_routes()

        if api_keys:
            from auth_helper import make_auth_validator
            self.app.before_request(make_auth_validator(
                api_keys=api_keys,
                jwt_secret=None,        # JWT cookie path closed for this module
                exempt_paths=set(),
            ))

    # ------------------------------------------------------------------ routes
    def _setup_routes(self):
        @self.app.route('/acars-app/<application>', methods=['GET'])
        def dispatch(application):
            handler = self._handlers.get(application)
            if not handler:
                return jsonify({
                    "error": f"unsupported application: {application}",
                    "supported": list(self._handlers.keys()),
                }), 400
            return handler()

    # ------------------------------------------------------------ application
    # handlers — each handler validates its own query parameters and returns a
    # Flask response.
    # --------------------------------------------------------------------------

    def _handle_datis(self):
        """`/acars-app/datis?icao=<ICAO>&type=<dep|arr|dep,arr>&count=<N>&days=<N>`"""
        # ICAO -------------------------------------------------------------
        icao_raw = request.args.get('icao', default='').strip().upper()
        if not _ICAO_PATTERN.match(icao_raw):
            return jsonify({"error": "icao must be 4 letters"}), 400
        icao = icao_raw

        # type -------------------------------------------------------------
        type_raw = request.args.get('type', default='').strip().lower()
        if not type_raw:
            requested_types = list(VALID_DATIS_TYPES)
        else:
            tokens = [t.strip() for t in type_raw.split(',') if t.strip()]
            if not tokens or any(t not in VALID_DATIS_TYPES for t in tokens):
                return jsonify({
                    "error": "type must contain dep and/or arr"
                }), 400
            # Preserve canonical order (dep, arr); drop duplicates.
            requested_types = [t for t in VALID_DATIS_TYPES if t in tokens]

        # count ------------------------------------------------------------
        count_raw = request.args.get('count', default='1')
        try:
            count = int(count_raw)
        except (TypeError, ValueError):
            return jsonify({"error": "count must be an integer"}), 400
        if count < 1:
            return jsonify({"error": "count must be >= 1"}), 400
        if count > self.max_count_per_type:
            count = self.max_count_per_type

        # days (optional) --------------------------------------------------
        days_raw = request.args.get('days', default=None)
        days = None
        if days_raw is not None:
            try:
                days = int(days_raw)
            except (TypeError, ValueError):
                return jsonify({"error": "days must be an integer"}), 400
            if days < 1:
                return jsonify({"error": "days must be >= 1"}), 400

        # Query ------------------------------------------------------------
        result = {"icao": icao, "count": count}
        try:
            for atis_type in requested_types:
                result[atis_type] = self._query_datis(icao, atis_type, count, days)
        except Exception as e:
            logger.error(f"D-ATIS query failed for icao={icao}: {e}")
            return jsonify({"error": "internal server error"}), 500

        return jsonify(result)

    def _query_datis(self, icao, atis_type, count, days=None):
        """Return [{timestamp, text}, ...] for the requested ICAO/type.

        The regex tolerates either a space or a hyphen between the ICAO,
        the direction (DEP/ARR), and the literal 'ATIS' — so '/LTAI DEP ATIS',
        '/LTAI-DEP-ATIS' and '/LTAI DEP-ATIS' all match. ICAO is already
        validated as [A-Z]{4} and direction is hardcoded, so no regex special
        characters can be injected by callers.
        """
        direction = atis_type.upper()  # 'DEP' or 'ARR'
        regex = f"/{icao}[ -]{direction}[ -]ATIS[ -]"
        params = [DATIS_LABEL, *ACARS_APP_NAMES, regex]
        time_clause = ""
        if days is not None:
            cutoff = time.time() - days * 86400
            time_clause = "  AND timestamp_msg >= %s "
            params.append(cutoff)
        params.append(int(count))
        sql = (
            "SELECT timestamp_msg, text "
            "FROM messages_json_raw "
            "WHERE label = %s "
            "  AND app_name IN (%s, %s, %s, %s) "
            "  AND text REGEXP %s "
            f"{time_clause}"
            "ORDER BY timestamp_msg DESC "
            "LIMIT %s"
        )

        cursor = None
        try:
            cursor = self.db_handler._get_cursor()
            cursor.execute(sql, params)
            return [
                {"timestamp": row[0], "text": row[1]}
                for row in cursor.fetchall()
            ]
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass

    # ---------------------------------------------------------------- lifecycle
    def start(self):
        if self.thread and self.thread.is_alive():
            logger.warning("ACARS Application API is already running")
            return False
        try:
            self.running.set()
            self.thread = Thread(target=self._run_server, daemon=True)
            self.thread.start()
            time.sleep(1)
            logger.info(
                f"ACARS Application API started on http://{self.host}:{self.port}/acars-app"
            )
            return True
        except Exception as e:
            logger.error(f"Error starting ACARS Application API: {e}")
            return False

    def _run_server(self):
        try:
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.WARNING)
            logger.info("ACARS Application API is running and accepting connections")
            self.app.run(host=self.host, port=self.port, threaded=True)
        except Exception as e:
            logger.error(f"ACARS Application API server error: {e}")

    def stop(self):
        logger.info("Stopping ACARS Application API...")
        self.running.clear()
