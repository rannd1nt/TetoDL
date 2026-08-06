from __future__ import annotations

import requests

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


class SpotifyAuth:
    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": _USER_AGENT,
        })

    @property
    def session(self) -> requests.Session:
        return self._session
