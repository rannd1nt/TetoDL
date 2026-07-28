from tetodl.constants import APP_NAME, APP_VERSION


def get_headers() -> dict[str, str]:
    return {
        "User-Agent": f"{APP_NAME}/{APP_VERSION} (+https://github.com/rannd1nt/TetoDL)"
    }
