"""
ACARS D-ATIS API Module
Provides a focused HTTP API for external applications to fetch the most recent
DEP and/or ARR D-ATIS messages for a given airport ICAO code, searched within
ACARS-network traffic (label B9).

Unlike the SSE stream (which is push-style for the frontend), this endpoint is
pull-style: a single request returns up to N DEP and/or N ARR messages, ordered
newest first. Static API keys and JWT cookies issued by atcweb are accepted via
the shared auth_helper module.
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

# Accepted ATIS direction tokens.
VALID_TYPES = ('dep', 'arr')

# ICAO must be exactly four ASCII letters.
_ICAO_PATTERN = re.compile(r'^[A-Z]{4}$')


class AcarsDatisAPI:
    """HTTP API exposing recent D-ATIS messages for a given airport ICAO."""

    def __init__(self, db_handler, host, port, max_count_per_type,
                 api_keys=None, jwt_secret=None,
                 jwt_cookie_name='datalink_session'):
        """
        Args:
            db_handler: Shared DatabaseHandler instance.
            host (str): IP address to bind to.
            port (int): Port to listen on.
            max_count_per_type (int): Hard cap on `count` per DEP/ARR type.
            api_keys (iterable[str] | None): Static keys accepted via X-API-Key header.
            jwt_secret (str | None): HS256 secret for verifying browser JWT cookies.
            jwt_cookie_name (str): Cookie name carrying the JWT.
        """
        self.db_handler = db_handler
        self.host = host
        self.port = port
        self.max_count_per_type = max_count_per_type
        self.app = Flask(__name__)
        CORS(self.app, supports_credentials=True)
        self.thread = None
        self.running = Event()
        self._setup_routes()

        if api_keys or jwt_secret:
            from auth_helper import make_auth_validator
            self.app.before_request(make_auth_validator(
                api_keys=api_keys,
                jwt_secret=jwt_secret,
                jwt_cookie_name=jwt_cookie_name,
                exempt_paths={'/acars-datis/health'},
            ))

    def _setup_routes(self):
        @self.app.route('/acars-datis', methods=['GET'])
        def get_datis():
            # ICAO ---------------------------------------------------------
            icao_raw = request.args.get('icao', default='').strip().upper()
            if not _ICAO_PATTERN.match(icao_raw):
                return jsonify({"error": "icao must be 4 letters"}), 400
            icao = icao_raw

            # type ---------------------------------------------------------
            type_raw = request.args.get('type', default='').strip().lower()
            if not type_raw:
                requested_types = list(VALID_TYPES)
            else:
                tokens = [t.strip() for t in type_raw.split(',') if t.strip()]
                if not tokens or any(t not in VALID_TYPES for t in tokens):
                    return jsonify({
                        "error": "type must contain dep and/or arr"
                    }), 400
                # Preserve canonical order (dep, arr) while removing duplicates.
                requested_types = [t for t in VALID_TYPES if t in tokens]

            # count --------------------------------------------------------
            count_raw = request.args.get('count', default='1')
            try:
                count = int(count_raw)
            except (TypeError, ValueError):
                return jsonify({"error": "count must be an integer"}), 400
            if count < 1:
                return jsonify({"error": "count must be >= 1"}), 400
            if count > self.max_count_per_type:
                count = self.max_count_per_type

            # Query --------------------------------------------------------
            result = {"icao": icao, "count": count}
            try:
                for atis_type in requested_types:
                    result[atis_type] = self._query_datis(icao, atis_type, count)
            except Exception as e:
                logger.error(f"D-ATIS query failed for icao={icao}: {e}")
                return jsonify({"error": "internal server error"}), 500

            return jsonify(result)

        @self.app.route('/acars-datis/health', methods=['GET'])
        def health():
            return jsonify({
                "status": "ok",
                "max_count_per_type": self.max_count_per_type,
                "acars_app_names": list(ACARS_APP_NAMES),
            })

    def _query_datis(self, icao, atis_type, count):
        """Return [{timestamp, text}, ...] for the requested ICAO/type.

        The regex tolerates either a space or a hyphen between the ICAO,
        the direction (DEP/ARR), and the literal 'ATIS' — so '/LTAI DEP ATIS',
        '/LTAI-DEP-ATIS' and '/LTAI DEP-ATIS' all match. ICAO is already
        validated as [A-Z]{4} and direction is hardcoded, so no regex special
        characters can be injected by callers.
        """
        direction = atis_type.upper()  # 'DEP' or 'ARR'
        regex = f"/{icao}[ -]{direction}[ -]ATIS[ -]"
        sql = (
            "SELECT timestamp_msg, text "
            "FROM messages_json_raw "
            "WHERE label = %s "
            "  AND app_name IN (%s, %s, %s, %s) "
            "  AND text REGEXP %s "
            "ORDER BY timestamp_msg DESC "
            "LIMIT %s"
        )
        params = (DATIS_LABEL, *ACARS_APP_NAMES, regex, int(count))

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

    def start(self):
        if self.thread and self.thread.is_alive():
            logger.warning("ACARS D-ATIS API is already running")
            return False
        try:
            self.running.set()
            self.thread = Thread(target=self._run_server, daemon=True)
            self.thread.start()
            time.sleep(1)
            logger.info(
                f"ACARS D-ATIS API started on http://{self.host}:{self.port}/acars-datis"
            )
            return True
        except Exception as e:
            logger.error(f"Error starting ACARS D-ATIS API: {e}")
            return False

    def _run_server(self):
        try:
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.WARNING)
            logger.info("ACARS D-ATIS API is running and accepting connections")
            self.app.run(host=self.host, port=self.port, threaded=True)
        except Exception as e:
            logger.error(f"ACARS D-ATIS API server error: {e}")

    def stop(self):
        logger.info("Stopping ACARS D-ATIS API...")
        self.running.clear()
