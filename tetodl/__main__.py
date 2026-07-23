import os
import sys

IS_BINARY = getattr(sys, 'frozen', False)

if IS_BINARY:
    sys.path.insert(0, os.path.dirname(sys.executable))

from tetodl.ui.entry.app import app  # noqa: E402


def main():
    if IS_BINARY:
        os.environ["TETODL_BINARY"] = sys.executable
    app.launch()


if __name__ == "__main__":
    main()
