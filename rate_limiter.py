"""
Rate Limiter Module

A tiny, dependency-free per-IP sliding-window rate limiter used by the ACARS
Application API to shield the database from request floods (e.g. the D-ATIS
Search site hammering `/acars-app/datis`).

Design goals:
- SHORT window: throttle instantaneous bursts, but never lock a client out for
  long — as soon as the window rolls over the client may retry.
- In-memory, thread-safe, no external dependency (single-process backend).
"""

import time
from collections import deque
from threading import Lock

from flask import jsonify, request


class SlidingWindowRateLimiter:
    """Per-IP sliding-window limiter: at most `max_requests` per `window_sec`."""

    def __init__(self, max_requests, window_sec):
        """
        Args:
            max_requests (int): Allowed requests per window per IP. A value <= 0
                disables limiting entirely.
            window_sec (float): Window length in seconds (kept intentionally
                short, e.g. 1s).
        """
        self.max_requests = int(max_requests)
        self.window_sec = float(window_sec)
        self._hits = {}          # ip -> deque[timestamps]
        self._lock = Lock()

    @property
    def enabled(self):
        return self.max_requests > 0 and self.window_sec > 0

    def check(self, ip):
        """Record a hit for `ip`. Return True if allowed, False if over limit."""
        if not self.enabled:
            return True

        now = time.time()
        cutoff = now - self.window_sec
        with self._lock:
            dq = self._hits.get(ip)
            if dq is None:
                dq = deque()
                self._hits[ip] = dq
            # Drop timestamps outside the current window.
            while dq and dq[0] <= cutoff:
                dq.popleft()
            if len(dq) >= self.max_requests:
                return False
            dq.append(now)
            return True


def client_ip(trust_proxy):
    """Resolve the client IP, honouring X-Forwarded-For when behind a proxy."""
    if trust_proxy:
        xff = request.headers.get('X-Forwarded-For', '')
        if xff:
            # First hop is the original client.
            return xff.split(',')[0].strip()
    return request.remote_addr or 'unknown'


def make_rate_limit_validator(limiter, trust_proxy):
    """Build a Flask `before_request` callback enforcing `limiter`.

    Returns None (allow) or a Flask (response, status) tuple (reject).
    """
    def _validate():
        if not limiter.enabled:
            return None
        ip = client_ip(trust_proxy)
        if limiter.check(ip):
            return None
        retry_after = max(1, int(round(limiter.window_sec)))
        resp = jsonify({"error": "rate limit exceeded"})
        resp.headers['Retry-After'] = str(retry_after)
        return resp, 429

    return _validate
