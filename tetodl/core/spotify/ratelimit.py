from __future__ import annotations

import time


class SpotifyRateLimiter:
    def __init__(
        self,
        max_per_minute: int = 30,
        base_delay: float = 1.0,
        backoff: float = 2.0,
        max_retries: int = 3,
    ) -> None:
        self._max_per_minute = max_per_minute
        self._base_delay = base_delay
        self._backoff = backoff
        self._max_retries = max_retries

        self._request_times: list[float] = []
        self._consecutive_429 = 0

    def _enforce_minute_window(self) -> None:
        now = time.monotonic()
        cutoff = now - 60.0
        self._request_times = [t for t in self._request_times if t > cutoff]
        if len(self._request_times) >= self._max_per_minute:
            sleep_for = self._request_times[0] + 60.0 - now
            if sleep_for > 0:
                time.sleep(sleep_for)
        self._request_times.append(time.monotonic())

    def wait(self) -> None:
        self._enforce_minute_window()

        if self._consecutive_429 > 0:
            delay = self._base_delay * (self._backoff ** (self._consecutive_429 - 1))
            time.sleep(min(delay, 30.0))

    def report_success(self) -> None:
        self._consecutive_429 = 0

    def report_429(self) -> bool:
        self._consecutive_429 += 1
        return self._consecutive_429 <= self._max_retries
