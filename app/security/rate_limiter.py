"""Sliding-window rate limit per user (L2). Use Redis instead when running several replicas."""
import threading
import time
from collections import defaultdict, deque

from app.config import get_settings


class RateLimiter:
    def __init__(self, limit: int, window: int = 60):
        self.limit = limit
        self.window = window
        self.hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, user_id: str) -> bool:
        now = time.time()
        with self._lock:
            q = self.hits[user_id]
            while q and now - q[0] > self.window:
                q.popleft()

            if len(q) >= self.limit:
                return False

            q.append(now)
            return True


limiter = RateLimiter(get_settings().rate_limit_per_min)