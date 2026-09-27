#!/usr/bin/env python3
"""
TetoDL - Main Entry Point
by rannd1nt
"""

import sys


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ('-v', '--version'):
        from tetodl.constants import APP_VERSION
        print(f"TetoDL v{APP_VERSION}")
        sys.exit(0)

    from tetodl.ui.app import app
    app.launch()


if __name__ == "__main__":
    main()