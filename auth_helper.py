"""
Authentication Helper
Provides a Flask before_request validator that gates connection establishment for
protected endpoints. Accepts two credential channels:

1. X-API-Key HTTP header — static keys for server-to-server (external app) callers.
2. JWT cookie (default name 'datalink_session') — short-lived HS256 token issued by
   atcweb (signed with the shared secret). Used by browser clients; the static key
   itself never reaches the browser.

Auth runs only at connection establishment; once the SSE stream is open, no
per-message check is performed.
"""

import logging
import jwt
from flask import request, jsonify

logger = logging.getLogger(__name__)


def parse_api_keys(raw):
    """Parse a comma-separated api_keys config value into a set."""
    if not raw:
        return set()
    return {part.strip() for part in raw.split(',') if part.strip()}


def make_auth_validator(api_keys=None, jwt_secret=None,
                        jwt_cookie_name='datalink_session', exempt_paths=None):
    """
    Build a Flask before_request handler that enforces connection-level auth.

    Args:
        api_keys (iterable[str] | None): Accepted static keys (X-API-Key header).
        jwt_secret (str | None): Shared HS256 secret for verifying JWT cookies.
        jwt_cookie_name (str): Name of the cookie carrying the JWT.
        exempt_paths (iterable[str] | None): Request paths that bypass auth
                                             (typically health endpoints).

    Returns:
        callable: Function suitable for `app.before_request(...)`. If neither
                  api_keys nor jwt_secret is configured, auth is disabled and
                  the validator returns None for every request.
    """
    api_keys_set = set(api_keys) if api_keys else set()
    secret = jwt_secret or None
    exempt = set(exempt_paths or [])

    if not api_keys_set and not secret:
        def noop():
            return None
        return noop

    def validator():
        path = request.path or ''
        if path in exempt:
            return None
        if request.method == 'OPTIONS':
            return None

        # Channel 1: static key via X-API-Key header
        provided_key = request.headers.get('X-API-Key')
        if provided_key and provided_key in api_keys_set:
            return None

        # Channel 2: JWT cookie
        if secret:
            token = request.cookies.get(jwt_cookie_name)
            if token:
                try:
                    jwt.decode(token, secret, algorithms=['HS256'])
                    return None
                except jwt.ExpiredSignatureError:
                    logger.warning(
                        f"Expired JWT on {path} from {request.remote_addr}"
                    )
                except jwt.InvalidTokenError as e:
                    logger.warning(
                        f"Invalid JWT on {path} from {request.remote_addr}: {e}"
                    )

        logger.warning(
            f"Unauthorized request to {path} from {request.remote_addr}"
        )
        return jsonify({"error": "unauthorized"}), 401

    return validator
