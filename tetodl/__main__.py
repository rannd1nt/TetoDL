import os
import sys

IS_BINARY = getattr(sys, 'frozen', False)

if IS_BINARY:
    sys.path.insert(0, os.path.dirname(sys.executable))

def main():
    # Fast-path for version check without loading app/pydantic/yt_dlp/fastapi
    if len(sys.argv) == 2 and sys.argv[1] in ('-v', '--version'):
        from tetodl.constants import APP_VERSION
        print(f"TetoDL v{APP_VERSION}")
        sys.exit(0)

    if IS_BINARY:
        os.environ["TETODL_BINARY"] = sys.executable
    from tetodl.ui.app import app
    app.launch()


if __name__ == "__main__":
    main()

