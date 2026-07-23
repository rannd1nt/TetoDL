"""
Dispatch: Handles CLI Execution Logic (Headless Mode).
"""
import os
from tetodl.utils.console import console
from tetodl.utils.i18n_keys import Keys
from tetodl.utils.tracer import trace, traced
from tetodl.utils.files import TempManager, move_contents_and_cleanup
from tetodl.utils.network import start_share_server
from tetodl.core.models import DownloadSession, DownloadResult
from tetodl.core.config import load_app_config
from tetodl.core.resolver import ConfigResolver

from tetodl.pipeline.handlers import download_audio_youtube, download_spotify, download_spotify_thumbnail, download_video_youtube
from tetodl.utils.thumbnail import download_thumbnail_task

@trace
def execute_download(session: DownloadSession):
    """Main entry for headless download. Accepts typed DownloadSession."""
    base_config = load_app_config()
    app_config = ConfigResolver(base=base_config).resolve(session)
    if session.m3u and app_config.group_mode and not base_config.group_mode:
        console.warn(Keys.dispatch.m3u_auto_group)

    with console.context(is_quiet=app_config.quiet):
        try:
            url = session.url.strip()
            if not url:
                console.err(Keys.dispatch.no_url_provided)
                return DownloadResult(success=False, file_path=None)

            # Thumbnail Only
            if session.media_type == 'thumbnail':
                fmt = session.format or 'jpg'
                with traced(f'thumbnail-only mode, format={fmt}'):
                    if session.is_spotify:
                        result = download_spotify_thumbnail(url, target_format=fmt)
                    else:
                        result = download_thumbnail_task(url, target_format=fmt)
                return result

            with traced(f'dispatching to {"video" if session.media_type == "video" else "audio"} handler'):
                if session.is_spotify:
                    result = download_spotify(url, session=session, config=app_config)
                elif session.media_type == 'video':
                    result = download_video_youtube(
                        url, session=session, config=app_config,
                    )
                else:
                    result = download_audio_youtube(
                        url, session=session, config=app_config,
                    )

            # Share Logic (Temporary or Normal)
            if session.share_after_download:
                with traced(f'share mode, path={result.file_path}, staging={result.is_staging}'):
                    path_to_share = result.file_path
                    is_existing = result.skipped and path_to_share and os.path.exists(path_to_share)
                    if result.success or is_existing:
                        if path_to_share:
                            path_to_share = os.path.abspath(path_to_share)
                            if os.path.exists(path_to_share):
                                try:
                                    start_share_server(path_to_share)
                                except KeyboardInterrupt:
                                    print()
                                    pass

                                if result.is_staging and not session.is_temp_session:
                                    with traced('moving files from staging'):
                                        console.warn(Keys.dispatch.moving_files_back)
                                        moved_files = move_contents_and_cleanup(path_to_share, result.parent_dir)

                                        if moved_files:
                                            from tetodl.core.registry import registry
                                            for new_path in moved_files:
                                                filename = os.path.basename(new_path)
                                                old_path = os.path.join(path_to_share, filename)
                                                registry.update_path(old_path, new_path)
                                            console.ok(Keys.dispatch.moved_files_and_updated(count=len(moved_files)))
                                        else:
                                            console.neutral(Keys.dispatch.no_files_moved)
                            else:
                                console.err(Keys.dispatch.cannot_share_path_not_found)
                    else:
                        if not result.suppress_error:
                            if not result.success and not is_existing:
                                console.err(Keys.dispatch.nothing_to_share)

            return result

        except KeyboardInterrupt:
            console.warn(Keys.dispatch.operation_cancelled)
            return DownloadResult(success=False, file_path=None, cancelled=True)

        finally:
            if session.is_temp_session:
                with traced('cleaning temp files'):
                    console.warn(Keys.dispatch.cleaning_temp_files)
                    TempManager.cleanup()
                    console.ok(Keys.dispatch.cleanup_complete)
