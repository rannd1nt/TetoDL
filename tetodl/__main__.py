import sys
import os

IS_BINARY = getattr(sys, 'frozen', False)

if IS_BINARY:
    sys.path.insert(0, os.path.dirname(sys.executable))


def main():
    if IS_BINARY:
        os.environ["TETODL_BINARY"] = sys.executable
    try:
        from tetodl.ui.entry.app import app
    except ImportError:
        from tetodl.cli.parser import cli
        from tetodl.cli.dispatch import execute_download
        from tetodl.core.models import CliDownload, CliSearch
        from tetodl.core.search import perform_youtube_search
        handled, result = cli.parse()
        if handled:
            return
        if isinstance(result, CliSearch):
            url = perform_youtube_search(result.query, result.limit)
            if url:
                session = result.session.model_copy(update={'url': url})
                execute_download(session, result.force_recheck)
        elif isinstance(result, CliDownload):
            execute_download(result.session, result.force_recheck)
        return
    app.run()


if __name__ == "__main__":
    main()
