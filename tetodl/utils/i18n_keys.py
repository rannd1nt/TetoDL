"""AUTO-GENERATED FILE. DO NOT EDIT."""
from typing import TypeAlias, Tuple, Dict, Any, Union

I18nKey: TypeAlias = Union[str, Tuple[str, Dict[str, Any]]]

class _UiCoreEngineUpdatedToCallable:
    """
    [Callable Props Type] CoreEngineUpdatedTo
    
    Original template: "Core Engine updated to: {version}"
    """
    def __call__(self, *, version: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            version (str | int): Dynamic value for {version}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("ui.core_engine_updated_to", {"version": version})

class _UiCoreEngineUpToDateCallable:
    """
    [Callable Props Type] CoreEngineUpToDate
    
    Original template: "Core Engine is up to date: {version}"
    """
    def __call__(self, *, version: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            version (str | int): Dynamic value for {version}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("ui.core_engine_up_to_date", {"version": version})

class _UiCoreEngineInstalledCallable:
    """
    [Callable Props Type] CoreEngineInstalled
    
    Original template: "Core Engine installed: {version} (Network check skipped)"
    """
    def __call__(self, *, version: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            version (str | int): Dynamic value for {version}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("ui.core_engine_installed", {"version": version})

class _UiFailedCheckEngineVersionCallable:
    """
    [Callable Props Type] FailedCheckEngineVersion
    
    Original template: "Failed to check engine version: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("ui.failed_check_engine_version", {"error": error})

class _UiDetectedSystemLanguageCallable:
    """
    [Callable Props Type] DetectedSystemLanguage
    
    Original template: "Detected System Language: {language} | ({code})"
    """
    def __call__(self, *, language: str | int, code: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            language (str | int): Dynamic value for {language}.
            code (str | int): Dynamic value for {code}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("ui.detected_system_language", {"language": language, "code": code})

class _UiLanguageSetToCallable:
    """
    [Callable Props Type] LanguageSetTo
    
    Original template: "Language set to: {name}"
    """
    def __call__(self, *, name: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            name (str | int): Dynamic value for {name}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("ui.language_set_to", {"name": name})

class _UiSelectionCancelledDefaultingCallable:
    """
    [Callable Props Type] SelectionCancelledDefaulting
    
    Original template: "Selection cancelled. Defaulting to use detected system language: {name}."
    """
    def __call__(self, *, name: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            name (str | int): Dynamic value for {name}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("ui.selection_cancelled_defaulting", {"name": name})

class _UiEnvironmentDetectedCallable:
    """
    [Callable Props Type] EnvironmentDetected
    
    Original template: "Environment Detected: {env}"
    """
    def __call__(self, *, env: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            env (str | int): Dynamic value for {env}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("ui.environment_detected", {"env": env})

class _UiMusicPathSetToCallable:
    """
    [Callable Props Type] MusicPathSetTo
    
    Original template: "Music Path set to: {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("ui.music_path_set_to", {"path": path})

class _UiVideoPathSetToCallable:
    """
    [Callable Props Type] VideoPathSetTo
    
    Original template: "Video Path set to: {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("ui.video_path_set_to", {"path": path})

class _UiAccessDeniedToCallable:
    """
    [Callable Props Type] AccessDeniedTo
    
    Original template: "Access denied to: {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("ui.access_denied_to", {"path": path})

class _UiErrorReadingFolderCallable:
    """
    [Callable Props Type] ErrorReadingFolder
    
    Original template: "Error reading folder: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("ui.error_reading_folder", {"error": error})

class _UiUnexpectedErrorCallable:
    """
    [Callable Props Type] UnexpectedError
    
    Original template: "Unexpected error: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("ui.unexpected_error", {"error": error})

class _UiFailedLoadContentCallable:
    """
    [Callable Props Type] FailedLoadContent
    
    Original template: "Failed to Load Content. Visit: {url}"
    """
    def __call__(self, *, url: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            url (str | int): Dynamic value for {url}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("ui.failed_load_content", {"url": url})

class _UiHeaderNotFoundCallable:
    """
    [Callable Props Type] HeaderNotFound
    
    Original template: "Header '{file}' not found. Falling back."
    """
    def __call__(self, *, file: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            file (str | int): Dynamic value for {file}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("ui.header_not_found", {"file": file})

class _UiK:
    """
    [Key Type] Ui
    """
    dependency_update_available: str = "ui.dependency_update_available"
    """[Props Type] DependencyUpdateAvailable"""
    updating_ytdlp: str = "ui.updating_ytdlp"
    """[Props Type] UpdatingYtdlp"""
    update_complete: str = "ui.update_complete"
    """[Props Type] UpdateComplete"""
    update_failed_check_connection: str = "ui.update_failed_check_connection"
    """[Props Type] UpdateFailedCheckConnection"""
    fatal_error_unsupported_platform: str = "ui.fatal_error_unsupported_platform"
    """[Props Type] FatalErrorUnsupportedPlatform"""
    no_windows_support: str = "ui.no_windows_support"
    """[Props Type] NoWindowsSupport"""
    use_wsl_or_linux: str = "ui.use_wsl_or_linux"
    """[Props Type] UseWslOrLinux"""
    checking_core_engine: str = "ui.checking_core_engine"
    """[Props Type] CheckingCoreEngine"""
    core_engine_updated_to: _UiCoreEngineUpdatedToCallable = _UiCoreEngineUpdatedToCallable()
    """
    [Callable Props Type] CoreEngineUpdatedTo
    
    Original template: "Core Engine updated to: {version}"
    """
    core_engine_up_to_date: _UiCoreEngineUpToDateCallable = _UiCoreEngineUpToDateCallable()
    """
    [Callable Props Type] CoreEngineUpToDate
    
    Original template: "Core Engine is up to date: {version}"
    """
    core_engine_installed: _UiCoreEngineInstalledCallable = _UiCoreEngineInstalledCallable()
    """
    [Callable Props Type] CoreEngineInstalled
    
    Original template: "Core Engine installed: {version} (Network check skipped)"
    """
    failed_check_engine_version: _UiFailedCheckEngineVersionCallable = _UiFailedCheckEngineVersionCallable()
    """
    [Callable Props Type] FailedCheckEngineVersion
    
    Original template: "Failed to check engine version: {error}"
    """
    initializing_language_setup: str = "ui.initializing_language_setup"
    """[Props Type] InitializingLanguageSetup"""
    detected_system_language: _UiDetectedSystemLanguageCallable = _UiDetectedSystemLanguageCallable()
    """
    [Callable Props Type] DetectedSystemLanguage
    
    Original template: "Detected System Language: {language} | ({code})"
    """
    language_set_to: _UiLanguageSetToCallable = _UiLanguageSetToCallable()
    """
    [Callable Props Type] LanguageSetTo
    
    Original template: "Language set to: {name}"
    """
    selection_cancelled_defaulting: _UiSelectionCancelledDefaultingCallable = _UiSelectionCancelledDefaultingCallable()
    """
    [Callable Props Type] SelectionCancelledDefaulting
    
    Original template: "Selection cancelled. Defaulting to use detected system language: {name}."
    """
    environment_detected: _UiEnvironmentDetectedCallable = _UiEnvironmentDetectedCallable()
    """
    [Callable Props Type] EnvironmentDetected
    
    Original template: "Environment Detected: {env}"
    """
    wsl_detected: str = "ui.wsl_detected"
    """[Props Type] WslDetected"""
    wsl_file_explorer_access: str = "ui.wsl_file_explorer_access"
    """[Props Type] WslFileExplorerAccess"""
    default_download_locations: str = "ui.default_download_locations"
    """[Props Type] DefaultDownloadLocations"""
    default_paths_applied: str = "ui.default_paths_applied"
    """[Props Type] DefaultPathsApplied"""
    select_custom_music_folder: str = "ui.select_custom_music_folder"
    """[Props Type] SelectCustomMusicFolder"""
    music_path_set_to: _UiMusicPathSetToCallable = _UiMusicPathSetToCallable()
    """
    [Callable Props Type] MusicPathSetTo
    
    Original template: "Music Path set to: {path}"
    """
    cancelled_default_music_path: str = "ui.cancelled_default_music_path"
    """[Props Type] CancelledDefaultMusicPath"""
    select_custom_video_folder: str = "ui.select_custom_video_folder"
    """[Props Type] SelectCustomVideoFolder"""
    video_path_set_to: _UiVideoPathSetToCallable = _UiVideoPathSetToCallable()
    """
    [Callable Props Type] VideoPathSetTo
    
    Original template: "Video Path set to: {path}"
    """
    cancelled_default_video_path: str = "ui.cancelled_default_video_path"
    """[Props Type] CancelledDefaultVideoPath"""
    verification_completed: str = "ui.verification_completed"
    """[Props Type] VerificationCompleted"""
    access_denied_to: _UiAccessDeniedToCallable = _UiAccessDeniedToCallable()
    """
    [Callable Props Type] AccessDeniedTo
    
    Original template: "Access denied to: {path}"
    """
    error_reading_folder: _UiErrorReadingFolderCallable = _UiErrorReadingFolderCallable()
    """
    [Callable Props Type] ErrorReadingFolder
    
    Original template: "Error reading folder: {error}"
    """
    unexpected_error: _UiUnexpectedErrorCallable = _UiUnexpectedErrorCallable()
    """
    [Callable Props Type] UnexpectedError
    
    Original template: "Unexpected error: {error}"
    """
    failed_load_content: _UiFailedLoadContentCallable = _UiFailedLoadContentCallable()
    """
    [Callable Props Type] FailedLoadContent
    
    Original template: "Failed to Load Content. Visit: {url}"
    """
    header_not_found: _UiHeaderNotFoundCallable = _UiHeaderNotFoundCallable()
    """
    [Callable Props Type] HeaderNotFound
    
    Original template: "Header '{file}' not found. Falling back."
    """

class _DaemonDaemonUrlCallable:
    """
    [Callable Props Type] DaemonUrl
    
    Original template: "TetoDL Daemon URL: {url}"
    """
    def __call__(self, *, url: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            url (str | int): Dynamic value for {url}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("daemon.daemon_url", {"url": url})

class _DaemonDaemonPortCallable:
    """
    [Callable Props Type] DaemonPort
    
    Original template: "Port: {port}"
    """
    def __call__(self, *, port: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            port (str | int): Dynamic value for {port}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("daemon.daemon_port", {"port": port})

class _DaemonOpenBrowserCallable:
    """
    [Callable Props Type] OpenBrowser
    
    Original template: "Open {url} in your browser."
    """
    def __call__(self, *, url: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            url (str | int): Dynamic value for {url}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("daemon.open_browser", {"url": url})

class _DaemonServiceFileCreatedCallable:
    """
    [Callable Props Type] ServiceFileCreated
    
    Original template: "Systemd service file created at: {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("daemon.service_file_created", {"path": path})

class _DaemonFailedSetupSystemdCallable:
    """
    [Callable Props Type] FailedSetupSystemd
    
    Original template: "Failed to setup systemd service: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("daemon.failed_setup_systemd", {"error": error})

class _DaemonFailedRemoveSystemdCallable:
    """
    [Callable Props Type] FailedRemoveSystemd
    
    Original template: "Failed to remove systemd service: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("daemon.failed_remove_systemd", {"error": error})

class _DaemonMdnsBroadcastActiveCallable:
    """
    [Callable Props Type] MdnsBroadcastActive
    
    Original template: "mDNS Broadcast active. You can access via: http://{hostname}:{port}"
    """
    def __call__(self, *, hostname: str | int, port: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            hostname (str | int): Dynamic value for {hostname}.
            port (str | int): Dynamic value for {port}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("daemon.mdns_broadcast_active", {"hostname": hostname, "port": port})

class _DaemonMdnsBroadcastFailedCallable:
    """
    [Callable Props Type] MdnsBroadcastFailed
    
    Original template: "mDNS Broadcast failed (Zeroconf might not be supported on this network): {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("daemon.mdns_broadcast_failed", {"error": error})

class _DaemonK:
    """
    [Key Type] Daemon
    """
    not_configured: str = "daemon.not_configured"
    """[Props Type] NotConfigured"""
    run_setup: str = "daemon.run_setup"
    """[Props Type] RunSetup"""
    or_run_manually: str = "daemon.or_run_manually"
    """[Props Type] OrRunManually"""
    registered_not_running: str = "daemon.registered_not_running"
    """[Props Type] RegisteredNotRunning"""
    start_with_systemctl: str = "daemon.start_with_systemctl"
    """[Props Type] StartWithSystemctl"""
    service_unavailable: str = "daemon.service_unavailable"
    """[Props Type] ServiceUnavailable"""
    could_not_detect_lan_ip: str = "daemon.could_not_detect_lan_ip"
    """[Props Type] CouldNotDetectLanIp"""
    daemon_url: _DaemonDaemonUrlCallable = _DaemonDaemonUrlCallable()
    """
    [Callable Props Type] DaemonUrl
    
    Original template: "TetoDL Daemon URL: {url}"
    """
    daemon_port: _DaemonDaemonPortCallable = _DaemonDaemonPortCallable()
    """
    [Callable Props Type] DaemonPort
    
    Original template: "Port: {port}"
    """
    scan_qr: str = "daemon.scan_qr"
    """[Props Type] ScanQr"""
    open_browser: _DaemonOpenBrowserCallable = _DaemonOpenBrowserCallable()
    """
    [Callable Props Type] OpenBrowser
    
    Original template: "Open {url} in your browser."
    """
    configuring_systemd: str = "daemon.configuring_systemd"
    """[Props Type] ConfiguringSystemd"""
    service_file_created: _DaemonServiceFileCreatedCallable = _DaemonServiceFileCreatedCallable()
    """
    [Callable Props Type] ServiceFileCreated
    
    Original template: "Systemd service file created at: {path}"
    """
    failed_setup_systemd: _DaemonFailedSetupSystemdCallable = _DaemonFailedSetupSystemdCallable()
    """
    [Callable Props Type] FailedSetupSystemd
    
    Original template: "Failed to setup systemd service: {error}"
    """
    removing_systemd: str = "daemon.removing_systemd"
    """[Props Type] RemovingSystemd"""
    daemon_not_installed: str = "daemon.daemon_not_installed"
    """[Props Type] DaemonNotInstalled"""
    daemon_removed: str = "daemon.daemon_removed"
    """[Props Type] DaemonRemoved"""
    failed_remove_systemd: _DaemonFailedRemoveSystemdCallable = _DaemonFailedRemoveSystemdCallable()
    """
    [Callable Props Type] FailedRemoveSystemd
    
    Original template: "Failed to remove systemd service: {error}"
    """
    mdns_broadcast_active: _DaemonMdnsBroadcastActiveCallable = _DaemonMdnsBroadcastActiveCallable()
    """
    [Callable Props Type] MdnsBroadcastActive
    
    Original template: "mDNS Broadcast active. You can access via: http://{hostname}:{port}"
    """
    mdns_broadcast_failed: _DaemonMdnsBroadcastFailedCallable = _DaemonMdnsBroadcastFailedCallable()
    """
    [Callable Props Type] MdnsBroadcastFailed
    
    Original template: "mDNS Broadcast failed (Zeroconf might not be supported on this network): {error}"
    """

class _FilesFailedToMoveCallable:
    """
    [Callable Props Type] FailedToMove
    
    Original template: "Failed to move {item}: {error}"
    """
    def __call__(self, *, item: str | int, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            item (str | int): Dynamic value for {item}.
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("files.failed_to_move", {"item": item, "error": error})

class _FilesFailedCreateZipCallable:
    """
    [Callable Props Type] FailedCreateZip
    
    Original template: "Failed to create zip: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("files.failed_create_zip", {"error": error})

class _FilesZipSourceNotFoundCallable:
    """
    [Callable Props Type] ZipSourceNotFound
    
    Original template: "Zip source not found: {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("files.zip_source_not_found", {"path": path})

class _FilesArchivingToCallable:
    """
    [Callable Props Type] ArchivingTo
    
    Original template: "Archiving to {name}.zip ..."
    """
    def __call__(self, *, name: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            name (str | int): Dynamic value for {name}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("files.archiving_to", {"name": name})

class _FilesArchiveCreatedAtCallable:
    """
    [Callable Props Type] ArchiveCreatedAt
    
    Original template: "Archive created at: {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("files.archive_created_at", {"path": path})

class _FilesArchiveCreatedCallable:
    """
    [Callable Props Type] ArchiveCreated
    
    Original template: "Archive created: {name}"
    """
    def __call__(self, *, name: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            name (str | int): Dynamic value for {name}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("files.archive_created", {"name": name})

class _FilesZipSuccessButFileMissingCallable:
    """
    [Callable Props Type] ZipSuccessButFileMissing
    
    Original template: "Zip reported success but file missing at: {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("files.zip_success_but_file_missing", {"path": path})

class _FilesPlaylistGeneratedCallable:
    """
    [Callable Props Type] PlaylistGenerated
    
    Original template: "Playlist generated: {name}"
    """
    def __call__(self, *, name: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            name (str | int): Dynamic value for {name}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("files.playlist_generated", {"name": name})

class _FilesFailedCreatePlaylistCallable:
    """
    [Callable Props Type] FailedCreatePlaylist
    
    Original template: "Failed to create playlist: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("files.failed_create_playlist", {"error": error})

class _FilesFailedDeleteNomediaCallable:
    """
    [Callable Props Type] FailedDeleteNomedia
    
    Original template: "Failed to delete .nomedia: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("files.failed_delete_nomedia", {"error": error})

class _FilesCleanedTempFilesCallable:
    """
    [Callable Props Type] CleanedTempFiles
    
    Original template: "Cleaned {count} temporary files"
    """
    def __call__(self, *, count: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            count (str | int): Dynamic value for {count}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("files.cleaned_temp_files", {"count": count})

class _FilesK:
    """
    [Key Type] Files
    """
    failed_to_move: _FilesFailedToMoveCallable = _FilesFailedToMoveCallable()
    """
    [Callable Props Type] FailedToMove
    
    Original template: "Failed to move {item}: {error}"
    """
    failed_create_zip: _FilesFailedCreateZipCallable = _FilesFailedCreateZipCallable()
    """
    [Callable Props Type] FailedCreateZip
    
    Original template: "Failed to create zip: {error}"
    """
    zip_source_not_found: _FilesZipSourceNotFoundCallable = _FilesZipSourceNotFoundCallable()
    """
    [Callable Props Type] ZipSourceNotFound
    
    Original template: "Zip source not found: {path}"
    """
    archiving_to: _FilesArchivingToCallable = _FilesArchivingToCallable()
    """
    [Callable Props Type] ArchivingTo
    
    Original template: "Archiving to {name}.zip ..."
    """
    archive_created_at: _FilesArchiveCreatedAtCallable = _FilesArchiveCreatedAtCallable()
    """
    [Callable Props Type] ArchiveCreatedAt
    
    Original template: "Archive created at: {path}"
    """
    archive_created: _FilesArchiveCreatedCallable = _FilesArchiveCreatedCallable()
    """
    [Callable Props Type] ArchiveCreated
    
    Original template: "Archive created: {name}"
    """
    zip_success_but_file_missing: _FilesZipSuccessButFileMissingCallable = _FilesZipSuccessButFileMissingCallable()
    """
    [Callable Props Type] ZipSuccessButFileMissing
    
    Original template: "Zip reported success but file missing at: {path}"
    """
    playlist_generated: _FilesPlaylistGeneratedCallable = _FilesPlaylistGeneratedCallable()
    """
    [Callable Props Type] PlaylistGenerated
    
    Original template: "Playlist generated: {name}"
    """
    failed_create_playlist: _FilesFailedCreatePlaylistCallable = _FilesFailedCreatePlaylistCallable()
    """
    [Callable Props Type] FailedCreatePlaylist
    
    Original template: "Failed to create playlist: {error}"
    """
    failed_delete_nomedia: _FilesFailedDeleteNomediaCallable = _FilesFailedDeleteNomediaCallable()
    """
    [Callable Props Type] FailedDeleteNomedia
    
    Original template: "Failed to delete .nomedia: {error}"
    """
    cleaned_temp_files: _FilesCleanedTempFilesCallable = _FilesCleanedTempFilesCallable()
    """
    [Callable Props Type] CleanedTempFiles
    
    Original template: "Cleaned {count} temporary files"
    """

class _SpotSimpleModeDownloadCallable:
    """
    [Callable Props Type] SimpleModeDownload
    
    Original template: "Simple Mode: Downloading directly to {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("spot.simple_mode_download", {"path": path})

class _SpotTypeDetectedCallable:
    """
    [Callable Props Type] TypeDetected
    
    Original template: "Spotify {type} detected"
    """
    def __call__(self, *, type: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            type (str | int): Dynamic value for {type}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("spot.type_detected", {"type": type})

class _SpotCommandDebugCallable:
    """
    [Callable Props Type] CommandDebug
    
    Original template: "Running command: {command}"
    """
    def __call__(self, *, command: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            command (str | int): Dynamic value for {command}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("spot.command_debug", {"command": command})

class _SpotSpotdlBinaryPathCallable:
    """
    [Callable Props Type] SpotdlBinaryPath
    
    Original template: "Path Binary: {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("spot.spotdl_binary_path", {"path": path})

class _SpotPythonInterpreterCallable:
    """
    [Callable Props Type] PythonInterpreter
    
    Original template: "Python Interpreter: {interpreter}"
    """
    def __call__(self, *, interpreter: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            interpreter (str | int): Dynamic value for {interpreter}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("spot.python_interpreter", {"interpreter": interpreter})

class _SpotK:
    """
    [Key Type] Spot
    """
    invalid_url: str = "spot.invalid_url"
    """[Props Type] InvalidUrl"""
    no_internet: str = "spot.no_internet"
    """[Props Type] NoInternet"""
    simple_mode_download: _SpotSimpleModeDownloadCallable = _SpotSimpleModeDownloadCallable()
    """
    [Callable Props Type] SimpleModeDownload
    
    Original template: "Simple Mode: Downloading directly to {path}"
    """
    cancelled: str = "spot.cancelled"
    """[Props Type] Cancelled"""
    type_detected: _SpotTypeDetectedCallable = _SpotTypeDetectedCallable()
    """
    [Callable Props Type] TypeDetected
    
    Original template: "Spotify {type} detected"
    """
    classification_failed: str = "spot.classification_failed"
    """[Props Type] ClassificationFailed"""
    downloading: str = "spot.downloading"
    """[Props Type] Downloading"""
    command_debug: _SpotCommandDebugCallable = _SpotCommandDebugCallable()
    """
    [Callable Props Type] CommandDebug
    
    Original template: "Running command: {command}"
    """
    download_complete: str = "spot.download_complete"
    """[Props Type] DownloadComplete"""
    download_failed: str = "spot.download_failed"
    """[Props Type] DownloadFailed"""
    error_details: str = "spot.error_details"
    """[Props Type] ErrorDetails"""
    no_valid_spotdl_method: str = "spot.no_valid_spotdl_method"
    """[Props Type] NoValidSpotdlMethod"""
    spotdl_binary_path: _SpotSpotdlBinaryPathCallable = _SpotSpotdlBinaryPathCallable()
    """
    [Callable Props Type] SpotdlBinaryPath
    
    Original template: "Path Binary: {path}"
    """
    python_interpreter: _SpotPythonInterpreterCallable = _SpotPythonInterpreterCallable()
    """
    [Callable Props Type] PythonInterpreter
    
    Original template: "Python Interpreter: {interpreter}"
    """

class _NetFileDirNotFoundCallable:
    """
    [Callable Props Type] FileDirNotFound
    
    Original template: "File/Directory not found: {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("net.file_dir_not_found", {"path": path})

class _NetPortsBusyCallable:
    """
    [Callable Props Type] PortsBusy
    
    Original template: "All ports from {start} to {end} are busy."
    """
    def __call__(self, *, start: str | int, end: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            start (str | int): Dynamic value for {start}.
            end (str | int): Dynamic value for {end}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("net.ports_busy", {"start": start, "end": end})

class _NetK:
    """
    [Key Type] Net
    """
    file_dir_not_found: _NetFileDirNotFoundCallable = _NetFileDirNotFoundCallable()
    """
    [Callable Props Type] FileDirNotFound
    
    Original template: "File/Directory not found: {path}"
    """
    ports_busy: _NetPortsBusyCallable = _NetPortsBusyCallable()
    """
    [Callable Props Type] PortsBusy
    
    Original template: "All ports from {start} to {end} are busy."
    """
    wsl_nat_warning: str = "net.wsl_nat_warning"
    """[Props Type] WslNatWarning"""
    wsl_share_tip: str = "net.wsl_share_tip"
    """[Props Type] WslShareTip"""
    no_lan_ip: str = "net.no_lan_ip"
    """[Props Type] NoLanIp"""
    localhost_only: str = "net.localhost_only"
    """[Props Type] LocalhostOnly"""
    sharing_started: str = "net.sharing_started"
    """[Props Type] SharingStarted"""
    not_git_repo: str = "net.not_git_repo"
    """[Props Type] NotGitRepo"""
    pulling_latest: str = "net.pulling_latest"
    """[Props Type] PullingLatest"""
    update_successful: str = "net.update_successful"
    """[Props Type] UpdateSuccessful"""
    git_pull_failed: str = "net.git_pull_failed"
    """[Props Type] GitPullFailed"""
    git_command_not_found: str = "net.git_command_not_found"
    """[Props Type] GitCommandNotFound"""

class _TaggerFileNotFoundCallable:
    """
    [Callable Props Type] FileNotFound
    
    Original template: "File does not exist: {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("tagger.file_not_found", {"path": path})

class _TaggerFailedEmbedLyricsCallable:
    """
    [Callable Props Type] FailedEmbedLyrics
    
    Original template: "Failed to embed lyrics: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("tagger.failed_embed_lyrics", {"error": error})

class _TaggerMetadataEmbeddingErrorCallable:
    """
    [Callable Props Type] MetadataEmbeddingError
    
    Original template: "Metadata embedding error: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("tagger.metadata_embedding_error", {"error": error})

class _TaggerK:
    """
    [Key Type] Tagger
    """
    mutagen_not_found_lyrics: str = "tagger.mutagen_not_found_lyrics"
    """[Props Type] MutagenNotFoundLyrics"""
    file_not_found: _TaggerFileNotFoundCallable = _TaggerFileNotFoundCallable()
    """
    [Callable Props Type] FileNotFound
    
    Original template: "File does not exist: {path}"
    """
    failed_embed_lyrics: _TaggerFailedEmbedLyricsCallable = _TaggerFailedEmbedLyricsCallable()
    """
    [Callable Props Type] FailedEmbedLyrics
    
    Original template: "Failed to embed lyrics: {error}"
    """
    mutagen_not_found_metadata: str = "tagger.mutagen_not_found_metadata"
    """[Props Type] MutagenNotFoundMetadata"""
    metadata_embedding_error: _TaggerMetadataEmbeddingErrorCallable = _TaggerMetadataEmbeddingErrorCallable()
    """
    [Callable Props Type] MetadataEmbeddingError
    
    Original template: "Metadata embedding error: {error}"
    """

class _DispatchMovedFilesAndUpdatedCallable:
    """
    [Callable Props Type] MovedFilesAndUpdated
    
    Original template: "Moved {count} files and updated registry."
    """
    def __call__(self, *, count: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            count (str | int): Dynamic value for {count}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("dispatch.moved_files_and_updated", {"count": count})

class _DispatchK:
    """
    [Key Type] Dispatch
    """
    m3u_auto_group: str = "dispatch.m3u_auto_group"
    """[Props Type] M3uAutoGroup"""
    no_url_provided: str = "dispatch.no_url_provided"
    """[Props Type] NoUrlProvided"""
    moving_files_back: str = "dispatch.moving_files_back"
    """[Props Type] MovingFilesBack"""
    moved_files_and_updated: _DispatchMovedFilesAndUpdatedCallable = _DispatchMovedFilesAndUpdatedCallable()
    """
    [Callable Props Type] MovedFilesAndUpdated
    
    Original template: "Moved {count} files and updated registry."
    """
    no_files_moved: str = "dispatch.no_files_moved"
    """[Props Type] NoFilesMoved"""
    cannot_share_path_not_found: str = "dispatch.cannot_share_path_not_found"
    """[Props Type] CannotSharePathNotFound"""
    nothing_to_share: str = "dispatch.nothing_to_share"
    """[Props Type] NothingToShare"""
    operation_cancelled: str = "dispatch.operation_cancelled"
    """[Props Type] OperationCancelled"""
    cleaning_temp_files: str = "dispatch.cleaning_temp_files"
    """[Props Type] CleaningTempFiles"""
    cleanup_complete: str = "dispatch.cleanup_complete"
    """[Props Type] CleanupComplete"""

class _CoreFailedDeleteCacheCallable:
    """
    [Callable Props Type] FailedDeleteCache
    
    Original template: "Failed to delete cache: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("core.failed_delete_cache", {"error": error})

class _CoreFailedSaveHistoryCallable:
    """
    [Callable Props Type] FailedSaveHistory
    
    Original template: "Failed to save history: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("core.failed_save_history", {"error": error})

class _CoreFailedDeleteHistoryCallable:
    """
    [Callable Props Type] FailedDeleteHistory
    
    Original template: "Failed to delete history: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("core.failed_delete_history", {"error": error})

class _CoreK:
    """
    [Key Type] Core
    """
    failed_save_cache: str = "core.failed_save_cache"
    """[Props Type] FailedSaveCache"""
    failed_delete_cache: _CoreFailedDeleteCacheCallable = _CoreFailedDeleteCacheCallable()
    """
    [Callable Props Type] FailedDeleteCache
    
    Original template: "Failed to delete cache: {error}"
    """
    failed_save_config: str = "core.failed_save_config"
    """[Props Type] FailedSaveConfig"""
    failed_save_history: _CoreFailedSaveHistoryCallable = _CoreFailedSaveHistoryCallable()
    """
    [Callable Props Type] FailedSaveHistory
    
    Original template: "Failed to save history: {error}"
    """
    failed_delete_history: _CoreFailedDeleteHistoryCallable = _CoreFailedDeleteHistoryCallable()
    """
    [Callable Props Type] FailedDeleteHistory
    
    Original template: "Failed to delete history: {error}"
    """

class _SearchSearchResultsCallable:
    """
    [Callable Props Type] SearchResults
    
    Original template: "Search Results for '{query}':"
    """
    def __call__(self, *, query: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            query (str | int): Dynamic value for {query}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("search.search_results", {"query": query})

class _SearchSearchErrorCallable:
    """
    [Callable Props Type] SearchError
    
    Original template: "Search error: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("search.search_error", {"error": error})

class _SearchK:
    """
    [Key Type] Search
    """
    ytdlp_not_found: str = "search.ytdlp_not_found"
    """[Props Type] YtdlpNotFound"""
    search_failed: str = "search.search_failed"
    """[Props Type] SearchFailed"""
    no_results_found: str = "search.no_results_found"
    """[Props Type] NoResultsFound"""
    search_results: _SearchSearchResultsCallable = _SearchSearchResultsCallable()
    """
    [Callable Props Type] SearchResults
    
    Original template: "Search Results for '{query}':"
    """
    search_error: _SearchSearchErrorCallable = _SearchSearchErrorCallable()
    """
    [Callable Props Type] SearchError
    
    Original template: "Search error: {error}"
    """

class _MaintFoundNewCommitsCallable:
    """
    [Callable Props Type] FoundNewCommits
    
    Original template: "Found {count} new commit(s)! Updating..."
    """
    def __call__(self, *, count: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            count (str | int): Dynamic value for {count}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("maint.found_new_commits", {"count": count})

class _MaintUpdateFailedCallable:
    """
    [Callable Props Type] UpdateFailed
    
    Original template: "Update failed: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("maint.update_failed", {"error": error})

class _MaintUninstallerScriptNotFoundCallable:
    """
    [Callable Props Type] UninstallerScriptNotFound
    
    Original template: "Uninstaller script not found at: {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("maint.uninstaller_script_not_found", {"path": path})

class _MaintFailedCleanDataCallable:
    """
    [Callable Props Type] FailedCleanData
    
    Original template: "Failed to clean some data: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("maint.failed_clean_data", {"error": error})

class _MaintErrorExecutingUninstallerCallable:
    """
    [Callable Props Type] ErrorExecutingUninstaller
    
    Original template: "Error executing uninstaller: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("maint.error_executing_uninstaller", {"error": error})

class _MaintNothingToCleanCallable:
    """
    [Callable Props Type] NothingToClean
    
    Original template: "{target}: Nothing to clean"
    """
    def __call__(self, *, target: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            target (str | int): Dynamic value for {target}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("maint.nothing_to_clean", {"target": target})

class _MaintWipeRegistryWarningCallable:
    """
    [Callable Props Type] WipeRegistryWarning
    
    Original template: "{warning} You are about to wipe the DOWNLOAD REGISTRY."
    """
    def __call__(self, *, warning: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            warning (str | int): Dynamic value for {warning}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("maint.wipe_registry_warning", {"warning": warning})

class _MaintWillAlsoResetCallable:
    """
    [Callable Props Type] WillAlsoReset
    
    Original template: "This will also reset: {items}"
    """
    def __call__(self, *, items: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            items (str | int): Dynamic value for {items}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("maint.will_also_reset", {"items": items})

class _MaintAboutToResetCallable:
    """
    [Callable Props Type] AboutToReset
    
    Original template: "You are about to reset: {items}"
    """
    def __call__(self, *, items: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            items (str | int): Dynamic value for {items}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("maint.about_to_reset", {"items": items})

class _MaintK:
    """
    [Key Type] Maint
    """
    not_git_repo: str = "maint.not_git_repo"
    """[Props Type] NotGitRepo"""
    manual_update_required: str = "maint.manual_update_required"
    """[Props Type] ManualUpdateRequired"""
    already_up_to_date: str = "maint.already_up_to_date"
    """[Props Type] AlreadyUpToDate"""
    found_new_commits: _MaintFoundNewCommitsCallable = _MaintFoundNewCommitsCallable()
    """
    [Callable Props Type] FoundNewCommits
    
    Original template: "Found {count} new commit(s)! Updating..."
    """
    update_successful: str = "maint.update_successful"
    """[Props Type] UpdateSuccessful"""
    update_failed: _MaintUpdateFailedCallable = _MaintUpdateFailedCallable()
    """
    [Callable Props Type] UpdateFailed
    
    Original template: "Update failed: {error}"
    """
    repo_broken: str = "maint.repo_broken"
    """[Props Type] RepoBroken"""
    try_reinstall: str = "maint.try_reinstall"
    """[Props Type] TryReinstall"""
    git_not_found: str = "maint.git_not_found"
    """[Props Type] GitNotFound"""
    uninstaller_script_not_found: _MaintUninstallerScriptNotFoundCallable = _MaintUninstallerScriptNotFoundCallable()
    """
    [Callable Props Type] UninstallerScriptNotFound
    
    Original template: "Uninstaller script not found at: {path}"
    """
    uninstall_warning: str = "maint.uninstall_warning"
    """[Props Type] UninstallWarning"""
    uninstall_details: str = "maint.uninstall_details"
    """[Props Type] UninstallDetails"""
    invalid_choice_aborting: str = "maint.invalid_choice_aborting"
    """[Props Type] InvalidChoiceAborting"""
    alert_permanent_delete: str = "maint.alert_permanent_delete"
    """[Props Type] AlertPermanentDelete"""
    uninstall_cancelled: str = "maint.uninstall_cancelled"
    """[Props Type] UninstallCancelled"""
    cleaning_user_data: str = "maint.cleaning_user_data"
    """[Props Type] CleaningUserData"""
    cache_dir_removed: str = "maint.cache_dir_removed"
    """[Props Type] CacheDirRemoved"""
    config_dir_removed: str = "maint.config_dir_removed"
    """[Props Type] ConfigDirRemoved"""
    data_dir_removed: str = "maint.data_dir_removed"
    """[Props Type] DataDirRemoved"""
    history_file_removed: str = "maint.history_file_removed"
    """[Props Type] HistoryFileRemoved"""
    registry_kept_safe: str = "maint.registry_kept_safe"
    """[Props Type] RegistryKeptSafe"""
    failed_clean_data: _MaintFailedCleanDataCallable = _MaintFailedCleanDataCallable()
    """
    [Callable Props Type] FailedCleanData
    
    Original template: "Failed to clean some data: {error}"
    """
    launching_uninstaller: str = "maint.launching_uninstaller"
    """[Props Type] LaunchingUninstaller"""
    error_executing_uninstaller: _MaintErrorExecutingUninstallerCallable = _MaintErrorExecutingUninstallerCallable()
    """
    [Callable Props Type] ErrorExecutingUninstaller
    
    Original template: "Error executing uninstaller: {error}"
    """
    cache_nothing_to_clean: str = "maint.cache_nothing_to_clean"
    """[Props Type] CacheNothingToClean"""
    cache_cleared: str = "maint.cache_cleared"
    """[Props Type] CacheCleared"""
    nothing_to_clean: _MaintNothingToCleanCallable = _MaintNothingToCleanCallable()
    """
    [Callable Props Type] NothingToClean
    
    Original template: "{target}: Nothing to clean"
    """
    wipe_registry_warning: _MaintWipeRegistryWarningCallable = _MaintWipeRegistryWarningCallable()
    """
    [Callable Props Type] WipeRegistryWarning
    
    Original template: "{warning} You are about to wipe the DOWNLOAD REGISTRY."
    """
    will_lose_track: str = "maint.will_lose_track"
    """[Props Type] WillLoseTrack"""
    will_also_reset: _MaintWillAlsoResetCallable = _MaintWillAlsoResetCallable()
    """
    [Callable Props Type] WillAlsoReset
    
    Original template: "This will also reset: {items}"
    """
    reset_cancelled: str = "maint.reset_cancelled"
    """[Props Type] ResetCancelled"""
    download_history_cleared: str = "maint.download_history_cleared"
    """[Props Type] DownloadHistoryCleared"""
    config_reset_to_defaults: str = "maint.config_reset_to_defaults"
    """[Props Type] ConfigResetToDefaults"""
    registry_nuked: str = "maint.registry_nuked"
    """[Props Type] RegistryNuked"""
    about_to_reset: _MaintAboutToResetCallable = _MaintAboutToResetCallable()
    """
    [Callable Props Type] AboutToReset
    
    Original template: "You are about to reset: {items}"
    """

class _CliStartingApiServerCallable:
    """
    [Callable Props Type] StartingApiServer
    
    Original template: "Starting TetoDL API Server on {host}:{port}..."
    """
    def __call__(self, *, host: str | int, port: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            host (str | int): Dynamic value for {host}.
            port (str | int): Dynamic value for {port}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("cli.starting_api_server", {"host": host, "port": port})

class _CliHeaderStyleCallable:
    """
    [Callable Props Type] HeaderStyle
    
    Original template: "Header style: {style}"
    """
    def __call__(self, *, style: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            style (str | int): Dynamic value for {style}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("cli.header_style", {"style": style})

class _CliProgressStyleCallable:
    """
    [Callable Props Type] ProgressStyle
    
    Original template: "Progress style: {style}"
    """
    def __call__(self, *, style: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            style (str | int): Dynamic value for {style}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("cli.progress_style", {"style": style})

class _CliLanguageSetCallable:
    """
    [Callable Props Type] LanguageSet
    
    Original template: "Language: {name}"
    """
    def __call__(self, *, name: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            name (str | int): Dynamic value for {name}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("cli.language_set", {"name": name})

class _CliDelaySetCallable:
    """
    [Callable Props Type] DelaySet
    
    Original template: "Delay: {delay}s"
    """
    def __call__(self, *, delay: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            delay (str | int): Dynamic value for {delay}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("cli.delay_set", {"delay": delay})

class _CliRetriesSetCallable:
    """
    [Callable Props Type] RetriesSet
    
    Original template: "Retries: {retries}"
    """
    def __call__(self, *, retries: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            retries (str | int): Dynamic value for {retries}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("cli.retries_set", {"retries": retries})

class _CliMediaScannerStatusCallable:
    """
    [Callable Props Type] MediaScannerStatus
    
    Original template: "Media Scanner {status}."
    """
    def __call__(self, *, status: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            status (str | int): Dynamic value for {status}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("cli.media_scanner_status", {"status": status})

class _CliGroupFolderNotFoundCallable:
    """
    [Callable Props Type] GroupFolderNotFound
    
    Original template: "Group folder not found: '{name}'"
    """
    def __call__(self, *, name: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            name (str | int): Dynamic value for {name}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("cli.group_folder_not_found", {"name": name})

class _CliSearchedInCallable:
    """
    [Callable Props Type] SearchedIn
    
    Original template: "Searched in: {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("cli.searched_in", {"path": path})

class _CliArchivingFolderCallable:
    """
    [Callable Props Type] ArchivingFolder
    
    Original template: "Archiving folder for temporary share: {name}..."
    """
    def __call__(self, *, name: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            name (str | int): Dynamic value for {name}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("cli.archiving_folder", {"name": name})

class _CliServingTempArchiveCallable:
    """
    [Callable Props Type] ServingTempArchive
    
    Original template: "Serving Temporary Archive: {name}"
    """
    def __call__(self, *, name: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            name (str | int): Dynamic value for {name}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("cli.serving_temp_archive", {"name": name})

class _CliFailedRemoveTempZipCallable:
    """
    [Callable Props Type] FailedRemoveTempZip
    
    Original template: "Failed to remove temp zip: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("cli.failed_remove_temp_zip", {"error": error})

class _CliSharingGroupCallable:
    """
    [Callable Props Type] SharingGroup
    
    Original template: "Sharing Group: {name}"
    """
    def __call__(self, *, name: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            name (str | int): Dynamic value for {name}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("cli.sharing_group", {"name": name})

class _CliSharePathCallable:
    """
    [Callable Props Type] SharePath
    
    Original template: "Path: {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("cli.share_path", {"path": path})

class _CliK:
    """
    [Key Type] Cli
    """
    starting_api_server: _CliStartingApiServerCallable = _CliStartingApiServerCallable()
    """
    [Callable Props Type] StartingApiServer
    
    Original template: "Starting TetoDL API Server on {host}:{port}..."
    """
    checking_for_updates: str = "cli.checking_for_updates"
    """[Props Type] CheckingForUpdates"""
    header_style: _CliHeaderStyleCallable = _CliHeaderStyleCallable()
    """
    [Callable Props Type] HeaderStyle
    
    Original template: "Header style: {style}"
    """
    progress_style: _CliProgressStyleCallable = _CliProgressStyleCallable()
    """
    [Callable Props Type] ProgressStyle
    
    Original template: "Progress style: {style}"
    """
    language_set: _CliLanguageSetCallable = _CliLanguageSetCallable()
    """
    [Callable Props Type] LanguageSet
    
    Original template: "Language: {name}"
    """
    delay_set: _CliDelaySetCallable = _CliDelaySetCallable()
    """
    [Callable Props Type] DelaySet
    
    Original template: "Delay: {delay}s"
    """
    retries_set: _CliRetriesSetCallable = _CliRetriesSetCallable()
    """
    [Callable Props Type] RetriesSet
    
    Original template: "Retries: {retries}"
    """
    media_scanner_status: _CliMediaScannerStatusCallable = _CliMediaScannerStatusCallable()
    """
    [Callable Props Type] MediaScannerStatus
    
    Original template: "Media Scanner {status}."
    """
    media_scanner_note: str = "cli.media_scanner_note"
    """[Props Type] MediaScannerNote"""
    share_specify_mode: str = "cli.share_specify_mode"
    """[Props Type] ShareSpecifyMode"""
    share_example: str = "cli.share_example"
    """[Props Type] ShareExample"""
    group_folder_not_found: _CliGroupFolderNotFoundCallable = _CliGroupFolderNotFoundCallable()
    """
    [Callable Props Type] GroupFolderNotFound
    
    Original template: "Group folder not found: '{name}'"
    """
    searched_in: _CliSearchedInCallable = _CliSearchedInCallable()
    """
    [Callable Props Type] SearchedIn
    
    Original template: "Searched in: {path}"
    """
    specify_folder_name: str = "cli.specify_folder_name"
    """[Props Type] SpecifyFolderName"""
    no_download_history: str = "cli.no_download_history"
    """[Props Type] NoDownloadHistory"""
    last_download_missing: str = "cli.last_download_missing"
    """[Props Type] LastDownloadMissing"""
    archiving_folder: _CliArchivingFolderCallable = _CliArchivingFolderCallable()
    """
    [Callable Props Type] ArchivingFolder
    
    Original template: "Archiving folder for temporary share: {name}..."
    """
    serving_temp_archive: _CliServingTempArchiveCallable = _CliServingTempArchiveCallable()
    """
    [Callable Props Type] ServingTempArchive
    
    Original template: "Serving Temporary Archive: {name}"
    """
    cleaning_temp_archive: str = "cli.cleaning_temp_archive"
    """[Props Type] CleaningTempArchive"""
    cleanup_complete: str = "cli.cleanup_complete"
    """[Props Type] CleanupComplete"""
    failed_remove_temp_zip: _CliFailedRemoveTempZipCallable = _CliFailedRemoveTempZipCallable()
    """
    [Callable Props Type] FailedRemoveTempZip
    
    Original template: "Failed to remove temp zip: {error}"
    """
    failed_to_create_zip: str = "cli.failed_to_create_zip"
    """[Props Type] FailedToCreateZip"""
    skipping_zip_creation: str = "cli.skipping_zip_creation"
    """[Props Type] SkippingZipCreation"""
    sharing_group: _CliSharingGroupCallable = _CliSharingGroupCallable()
    """
    [Callable Props Type] SharingGroup
    
    Original template: "Sharing Group: {name}"
    """
    cannot_share_path_not_found: str = "cli.cannot_share_path_not_found"
    """[Props Type] CannotSharePathNotFound"""
    share_path: _CliSharePathCallable = _CliSharePathCallable()
    """
    [Callable Props Type] SharePath
    
    Original template: "Path: {path}"
    """
    share_usage: str = "cli.share_usage"
    """[Props Type] ShareUsage"""
    audio_mode_note: str = "cli.audio_mode_note"
    """[Props Type] AudioModeNote"""
    share_group_folder_error: str = "cli.share_group_folder_error"
    """[Props Type] ShareGroupFolderError"""

class _ErrorFileCheckFailedCallable:
    """
    [Callable Props Type] FileCheckFailed
    
    Original template: "Error checking existing files: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("error.file_check_failed", {"error": error})

class _ErrorK:
    """
    [Key Type] Error
    """
    invalid_input: str = "error.invalid_input"
    """[Props Type] InvalidInput"""
    file_check_failed: _ErrorFileCheckFailedCallable = _ErrorFileCheckFailedCallable()
    """
    [Callable Props Type] FileCheckFailed
    
    Original template: "Error checking existing files: {error}"
    """
    documentation_unavailable: str = "error.documentation_unavailable"
    """[Props Type] DocumentationUnavailable"""

class _MediaScanFailedCallable:
    """
    [Callable Props Type] ScanFailed
    
    Original template: "Failed to scan media: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.scan_failed", {"error": error})

class _MediaCropFailedCallable:
    """
    [Callable Props Type] CropFailed
    
    Original template: "FFmpeg crop failed: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.crop_failed", {"error": error})

class _MediaCropErrorCallable:
    """
    [Callable Props Type] CropError
    
    Original template: "Error cropping thumbnail: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.crop_error", {"error": error})

class _MediaThumbnailErrorCallable:
    """
    [Callable Props Type] ThumbnailError
    
    Original template: "Error processing thumbnail: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.thumbnail_error", {"error": error})

class _MediaEmbedErrorCallable:
    """
    [Callable Props Type] EmbedError
    
    Original template: "Error embedding thumbnail: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.embed_error", {"error": error})

class _MediaTempCleanErrorCallable:
    """
    [Callable Props Type] TempCleanError
    
    Original template: "Error cleaning temp files: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.temp_clean_error", {"error": error})

class _MediaEncodingCallable:
    """
    [Callable Props Type] Encoding
    
    Original template: "Re-encoding video to {codec} (this might take a while)..."
    """
    def __call__(self, *, codec: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            codec (str | int): Dynamic value for {codec}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.encoding", {"codec": codec})

class _MediaTrimmingAudioCallable:
    """
    [Callable Props Type] TrimmingAudio
    
    Original template: "Trimming audio: {start}s to {end}s"
    """
    def __call__(self, *, start: str | int, end: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            start (str | int): Dynamic value for {start}.
            end (str | int): Dynamic value for {end}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.trimming_audio", {"start": start, "end": end})

class _MediaTrimmingVideoCallable:
    """
    [Callable Props Type] TrimmingVideo
    
    Original template: "Trimming video: {start}s to {end}s (This may take longer)"
    """
    def __call__(self, *, start: str | int, end: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            start (str | int): Dynamic value for {start}.
            end (str | int): Dynamic value for {end}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.trimming_video", {"start": start, "end": end})

class _MediaSearchingLyricsForCallable:
    """
    [Callable Props Type] SearchingLyricsFor
    
    Original template: "Searching lyrics for: {artist} - {title}"
    """
    def __call__(self, *, artist: str | int, title: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            artist (str | int): Dynamic value for {artist}.
            title (str | int): Dynamic value for {title}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.searching_lyrics_for", {"artist": artist, "title": title})

class _MediaCoverArtFoundViaCallable:
    """
    [Callable Props Type] CoverArtFoundVia
    
    Original template: "Cover art found via {source}!"
    """
    def __call__(self, *, source: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            source (str | int): Dynamic value for {source}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.cover_art_found_via", {"source": source})

class _MediaFoundRomanizedLyricsCallable:
    """
    [Callable Props Type] FoundRomanizedLyrics
    
    Original template: "Found Romanized lyrics: {title}"
    """
    def __call__(self, *, title: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            title (str | int): Dynamic value for {title}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.found_romanized_lyrics", {"title": title})

class _MediaFetchingLyricsFromCallable:
    """
    [Callable Props Type] FetchingLyricsFrom
    
    Original template: "Fetching lyrics from: {title}"
    """
    def __call__(self, *, title: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            title (str | int): Dynamic value for {title}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.fetching_lyrics_from", {"title": title})

class _MediaHighConcurrencyWarningCallable:
    """
    [Callable Props Type] HighConcurrencyWarning
    
    Original template: "Warning: High concurrency {n} increases risk of IP Ban."
    """
    def __call__(self, *, n: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            n (str | int): Dynamic value for {n}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.high_concurrency_warning", {"n": n})

class _MediaAsyncModeCallable:
    """
    [Callable Props Type] AsyncMode
    
    Original template: "Async Mode: {count} threads active. Press Ctrl+C to stop."
    """
    def __call__(self, *, count: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            count (str | int): Dynamic value for {count}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.async_mode", {"count": count})

class _MediaScanErrorCallable:
    """
    [Callable Props Type] ScanError
    
    Original template: "Scan error: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.scan_error", {"error": error})

class _MediaCannotCreateThumbDirCallable:
    """
    [Callable Props Type] CannotCreateThumbDir
    
    Original template: "Cannot create thumbnail directory: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.cannot_create_thumb_dir", {"error": error})

class _MediaExtractionFailedCallable:
    """
    [Callable Props Type] ExtractionFailed
    
    Original template: "Extraction failed: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.extraction_failed", {"error": error})

class _MediaPlaylistDetectedCallable:
    """
    [Callable Props Type] PlaylistDetected
    
    Original template: "Playlist detected: {title}"
    """
    def __call__(self, *, title: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            title (str | int): Dynamic value for {title}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.playlist_detected", {"title": title})

class _MediaFoundItemsProcessingCallable:
    """
    [Callable Props Type] FoundItemsProcessing
    
    Original template: "Found {count} items. Processing thumbnails..."
    """
    def __call__(self, *, count: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            count (str | int): Dynamic value for {count}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.found_items_processing", {"count": count})

class _MediaProcessingEntryCallable:
    """
    [Callable Props Type] ProcessingEntry
    
    Original template: "[{current}/{total}] Processing: {title}"
    """
    def __call__(self, *, current: str | int, total: str | int, title: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            current (str | int): Dynamic value for {current}.
            total (str | int): Dynamic value for {total}.
            title (str | int): Dynamic value for {title}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.processing_entry", {"current": current, "total": total, "title": title})

class _MediaProcessedThumbnailsCallable:
    """
    [Callable Props Type] ProcessedThumbnails
    
    Original template: "Processed {success}/{total} thumbnails."
    """
    def __call__(self, *, success: str | int, total: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            success (str | int): Dynamic value for {success}.
            total (str | int): Dynamic value for {total}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.processed_thumbnails", {"success": success, "total": total})

class _MediaProcessingCoverForCallable:
    """
    [Callable Props Type] ProcessingCoverFor
    
    Original template: "Processing cover for: {title}"
    """
    def __call__(self, *, title: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            title (str | int): Dynamic value for {title}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.processing_cover_for", {"title": title})

class _MediaThumbnailSavedCallable:
    """
    [Callable Props Type] ThumbnailSaved
    
    Original template: "Saved: {name}"
    """
    def __call__(self, *, name: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            name (str | int): Dynamic value for {name}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.thumbnail_saved", {"name": name})

class _MediaThumbnailSavedAsCallable:
    """
    [Callable Props Type] ThumbnailSavedAs
    
    Original template: "Saved as: {name}"
    """
    def __call__(self, *, name: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            name (str | int): Dynamic value for {name}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.thumbnail_saved_as", {"name": name})

class _MediaSkippingItemCallable:
    """
    [Callable Props Type] SkippingItem
    
    Original template: "Skipping item {index} (Not selected)"
    """
    def __call__(self, *, index: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            index (str | int): Dynamic value for {index}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("media.skipping_item", {"index": index})

class _MediaK:
    """
    [Key Type] Media
    """
    scanning: str = "media.scanning"
    """[Props Type] Scanning"""
    scan_complete: str = "media.scan_complete"
    """[Props Type] ScanComplete"""
    scan_failed: _MediaScanFailedCallable = _MediaScanFailedCallable()
    """
    [Callable Props Type] ScanFailed
    
    Original template: "Failed to scan media: {error}"
    """
    convert_error: str = "media.convert_error"
    """[Props Type] ConvertError"""
    crop_failed: _MediaCropFailedCallable = _MediaCropFailedCallable()
    """
    [Callable Props Type] CropFailed
    
    Original template: "FFmpeg crop failed: {error}"
    """
    crop_error: _MediaCropErrorCallable = _MediaCropErrorCallable()
    """
    [Callable Props Type] CropError
    
    Original template: "Error cropping thumbnail: {error}"
    """
    thumbnail_error: _MediaThumbnailErrorCallable = _MediaThumbnailErrorCallable()
    """
    [Callable Props Type] ThumbnailError
    
    Original template: "Error processing thumbnail: {error}"
    """
    embed_error: _MediaEmbedErrorCallable = _MediaEmbedErrorCallable()
    """
    [Callable Props Type] EmbedError
    
    Original template: "Error embedding thumbnail: {error}"
    """
    temp_clean_error: _MediaTempCleanErrorCallable = _MediaTempCleanErrorCallable()
    """
    [Callable Props Type] TempCleanError
    
    Original template: "Error cleaning temp files: {error}"
    """
    encoding: _MediaEncodingCallable = _MediaEncodingCallable()
    """
    [Callable Props Type] Encoding
    
    Original template: "Re-encoding video to {codec} (this might take a while)..."
    """
    download_cancelled: str = "media.download_cancelled"
    """[Props Type] DownloadCancelled"""
    cleaning_partial_files: str = "media.cleaning_partial_files"
    """[Props Type] CleaningPartialFiles"""
    lyrics_embedded_success: str = "media.lyrics_embedded_success"
    """[Props Type] LyricsEmbeddedSuccess"""
    failed_to_embed_lyrics: str = "media.failed_to_embed_lyrics"
    """[Props Type] FailedToEmbedLyrics"""
    lyrics_not_found_genius: str = "media.lyrics_not_found_genius"
    """[Props Type] LyricsNotFoundGenius"""
    trimming_audio: _MediaTrimmingAudioCallable = _MediaTrimmingAudioCallable()
    """
    [Callable Props Type] TrimmingAudio
    
    Original template: "Trimming audio: {start}s to {end}s"
    """
    trimming_video: _MediaTrimmingVideoCallable = _MediaTrimmingVideoCallable()
    """
    [Callable Props Type] TrimmingVideo
    
    Original template: "Trimming video: {start}s to {end}s (This may take longer)"
    """
    searching_lyrics_for: _MediaSearchingLyricsForCallable = _MediaSearchingLyricsForCallable()
    """
    [Callable Props Type] SearchingLyricsFor
    
    Original template: "Searching lyrics for: {artist} - {title}"
    """
    cover_art_found_via: _MediaCoverArtFoundViaCallable = _MediaCoverArtFoundViaCallable()
    """
    [Callable Props Type] CoverArtFoundVia
    
    Original template: "Cover art found via {source}!"
    """
    found_romanized_lyrics: _MediaFoundRomanizedLyricsCallable = _MediaFoundRomanizedLyricsCallable()
    """
    [Callable Props Type] FoundRomanizedLyrics
    
    Original template: "Found Romanized lyrics: {title}"
    """
    fetching_lyrics_from: _MediaFetchingLyricsFromCallable = _MediaFetchingLyricsFromCallable()
    """
    [Callable Props Type] FetchingLyricsFrom
    
    Original template: "Fetching lyrics from: {title}"
    """
    stopping_threads: str = "media.stopping_threads"
    """[Props Type] StoppingThreads"""
    high_concurrency_warning: _MediaHighConcurrencyWarningCallable = _MediaHighConcurrencyWarningCallable()
    """
    [Callable Props Type] HighConcurrencyWarning
    
    Original template: "Warning: High concurrency {n} increases risk of IP Ban."
    """
    async_mode: _MediaAsyncModeCallable = _MediaAsyncModeCallable()
    """
    [Callable Props Type] AsyncMode
    
    Original template: "Async Mode: {count} threads active. Press Ctrl+C to stop."
    """
    all_items_exist: str = "media.all_items_exist"
    """[Props Type] AllItemsExist"""
    scan_skipped: str = "media.scan_skipped"
    """[Props Type] ScanSkipped"""
    termux_tools_missing: str = "media.termux_tools_missing"
    """[Props Type] TermuxToolsMissing"""
    scan_error: _MediaScanErrorCallable = _MediaScanErrorCallable()
    """
    [Callable Props Type] ScanError
    
    Original template: "Scan error: {error}"
    """
    cannot_create_thumb_dir: _MediaCannotCreateThumbDirCallable = _MediaCannotCreateThumbDirCallable()
    """
    [Callable Props Type] CannotCreateThumbDir
    
    Original template: "Cannot create thumbnail directory: {error}"
    """
    extraction_failed: _MediaExtractionFailedCallable = _MediaExtractionFailedCallable()
    """
    [Callable Props Type] ExtractionFailed
    
    Original template: "Extraction failed: {error}"
    """
    playlist_detected: _MediaPlaylistDetectedCallable = _MediaPlaylistDetectedCallable()
    """
    [Callable Props Type] PlaylistDetected
    
    Original template: "Playlist detected: {title}"
    """
    found_items_processing: _MediaFoundItemsProcessingCallable = _MediaFoundItemsProcessingCallable()
    """
    [Callable Props Type] FoundItemsProcessing
    
    Original template: "Found {count} items. Processing thumbnails..."
    """
    processing_entry: _MediaProcessingEntryCallable = _MediaProcessingEntryCallable()
    """
    [Callable Props Type] ProcessingEntry
    
    Original template: "[{current}/{total}] Processing: {title}"
    """
    processed_thumbnails: _MediaProcessedThumbnailsCallable = _MediaProcessedThumbnailsCallable()
    """
    [Callable Props Type] ProcessedThumbnails
    
    Original template: "Processed {success}/{total} thumbnails."
    """
    processing_cover_for: _MediaProcessingCoverForCallable = _MediaProcessingCoverForCallable()
    """
    [Callable Props Type] ProcessingCoverFor
    
    Original template: "Processing cover for: {title}"
    """
    thumbnail_saved: _MediaThumbnailSavedCallable = _MediaThumbnailSavedCallable()
    """
    [Callable Props Type] ThumbnailSaved
    
    Original template: "Saved: {name}"
    """
    thumbnail_saved_as: _MediaThumbnailSavedAsCallable = _MediaThumbnailSavedAsCallable()
    """
    [Callable Props Type] ThumbnailSavedAs
    
    Original template: "Saved as: {name}"
    """
    failed_to_download_thumbnail: str = "media.failed_to_download_thumbnail"
    """[Props Type] FailedToDownloadThumbnail"""
    skipping_item: _MediaSkippingItemCallable = _MediaSkippingItemCallable()
    """
    [Callable Props Type] SkippingItem
    
    Original template: "Skipping item {index} (Not selected)"
    """
    cut_flag_ignored_playlist: str = "media.cut_flag_ignored_playlist"
    """[Props Type] CutFlagIgnoredPlaylist"""

class _ConfigResolutionChangedCallable:
    """
    [Callable Props Type] ResolutionChanged
    
    Original template: "Max Video Resolution changed to: {resolution}"
    """
    def __call__(self, *, resolution: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            resolution (str | int): Dynamic value for {resolution}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("config.resolution_changed", {"resolution": resolution})

class _ConfigContainerChangedCallable:
    """
    [Callable Props Type] ContainerChanged
    
    Original template: "Default video container changed to {container}"
    """
    def __call__(self, *, container: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            container (str | int): Dynamic value for {container}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("config.container_changed", {"container": container})

class _ConfigCodecChangedCallable:
    """
    [Callable Props Type] CodecChanged
    
    Original template: "Video codec changed to: {codec}"
    """
    def __call__(self, *, codec: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            codec (str | int): Dynamic value for {codec}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("config.codec_changed", {"codec": codec})

class _ConfigMusicRootSetCallable:
    """
    [Callable Props Type] MusicRootSet
    
    Original template: "Music root set to: {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("config.music_root_set", {"path": path})

class _ConfigVideoRootSetCallable:
    """
    [Callable Props Type] VideoRootSet
    
    Original template: "Video root set to: {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("config.video_root_set", {"path": path})

class _ConfigGhostFolderRemovedCallable:
    """
    [Callable Props Type] GhostFolderRemoved
    
    Original template: "Removing ghost subfolder '{type}/{name}' from config"
    """
    def __call__(self, *, type: str | int, name: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            type (str | int): Dynamic value for {type}.
            name (str | int): Dynamic value for {name}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("config.ghost_folder_removed", {"type": type, "name": name})

class _ConfigLanguageChangedCallable:
    """
    [Callable Props Type] LanguageChanged
    
    Original template: "Language changed to: {lang}."
    """
    def __call__(self, *, lang: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            lang (str | int): Dynamic value for {lang}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("config.language_changed", {"lang": lang})

class _ConfigK:
    """
    [Key Type] Config
    """
    simple_mode_enabled: str = "config.simple_mode_enabled"
    """[Props Type] SimpleModeEnabled"""
    simple_mode_disabled: str = "config.simple_mode_disabled"
    """[Props Type] SimpleModeDisabled"""
    smart_cover_enabled: str = "config.smart_cover_enabled"
    """[Props Type] SmartCoverEnabled"""
    smart_cover_disabled: str = "config.smart_cover_disabled"
    """[Props Type] SmartCoverDisabled"""
    skip_existing_enabled: str = "config.skip_existing_enabled"
    """[Props Type] SkipExistingEnabled"""
    skip_existing_disabled: str = "config.skip_existing_disabled"
    """[Props Type] SkipExistingDisabled"""
    media_scanner_enabled: str = "config.media_scanner_enabled"
    """[Props Type] MediaScannerEnabled"""
    media_scanner_disabled: str = "config.media_scanner_disabled"
    """[Props Type] MediaScannerDisabled"""
    resolution_changed: _ConfigResolutionChangedCallable = _ConfigResolutionChangedCallable()
    """
    [Callable Props Type] ResolutionChanged
    
    Original template: "Max Video Resolution changed to: {resolution}"
    """
    container_changed: _ConfigContainerChangedCallable = _ConfigContainerChangedCallable()
    """
    [Callable Props Type] ContainerChanged
    
    Original template: "Default video container changed to {container}"
    """
    codec_changed: _ConfigCodecChangedCallable = _ConfigCodecChangedCallable()
    """
    [Callable Props Type] CodecChanged
    
    Original template: "Video codec changed to: {codec}"
    """
    music_root_set: _ConfigMusicRootSetCallable = _ConfigMusicRootSetCallable()
    """
    [Callable Props Type] MusicRootSet
    
    Original template: "Music root set to: {path}"
    """
    video_root_set: _ConfigVideoRootSetCallable = _ConfigVideoRootSetCallable()
    """
    [Callable Props Type] VideoRootSet
    
    Original template: "Video root set to: {path}"
    """
    reset_default: str = "config.reset_default"
    """[Props Type] ResetDefault"""
    cache_deleted: str = "config.cache_deleted"
    """[Props Type] CacheDeleted"""
    cache_empty: str = "config.cache_empty"
    """[Props Type] CacheEmpty"""
    history_deleted: str = "config.history_deleted"
    """[Props Type] HistoryDeleted"""
    history_empty: str = "config.history_empty"
    """[Props Type] HistoryEmpty"""
    confirm_clear_cache: str = "config.confirm_clear_cache"
    """[Props Type] ConfirmClearCache"""
    confirm_clear_history: str = "config.confirm_clear_history"
    """[Props Type] ConfirmClearHistory"""
    ghost_folder_removed: _ConfigGhostFolderRemovedCallable = _ConfigGhostFolderRemovedCallable()
    """
    [Callable Props Type] GhostFolderRemoved
    
    Original template: "Removing ghost subfolder '{type}/{name}' from config"
    """
    save_failed: str = "config.save_failed"
    """[Props Type] SaveFailed"""
    language_changed: _ConfigLanguageChangedCallable = _ConfigLanguageChangedCallable()
    """
    [Callable Props Type] LanguageChanged
    
    Original template: "Language changed to: {lang}."
    """

class _DependencyPythonVersionCallable:
    """
    [Callable Props Type] PythonVersion
    
    Original template: "Python {version}"
    """
    def __call__(self, *, version: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            version (str | int): Dynamic value for {version}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("dependency.python_version", {"version": version})

class _DependencyPythonOldCallable:
    """
    [Callable Props Type] PythonOld
    
    Original template: "Python {version} - Required: 3.8+"
    """
    def __call__(self, *, version: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            version (str | int): Dynamic value for {version}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("dependency.python_old", {"version": version})

class _DependencyFfmpegVersionCallable:
    """
    [Callable Props Type] FfmpegVersion
    
    Original template: "FFmpeg {version}"
    """
    def __call__(self, *, version: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            version (str | int): Dynamic value for {version}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("dependency.ffmpeg_version", {"version": version})

class _DependencyPackageInstalledCallable:
    """
    [Callable Props Type] PackageInstalled
    
    Original template: "{package} {version}"
    """
    def __call__(self, *, package: str | int, version: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            package (str | int): Dynamic value for {package}.
            version (str | int): Dynamic value for {version}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("dependency.package_installed", {"package": package, "version": version})

class _DependencyPackageSimpleCallable:
    """
    [Callable Props Type] PackageSimple
    
    Original template: "{package} (installed)"
    """
    def __call__(self, *, package: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            package (str | int): Dynamic value for {package}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("dependency.package_simple", {"package": package})

class _DependencyPackageNotFoundCallable:
    """
    [Callable Props Type] PackageNotFound
    
    Original template: "{package} not found"
    """
    def __call__(self, *, package: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            package (str | int): Dynamic value for {package}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("dependency.package_not_found", {"package": package})

class _DependencyK:
    """
    [Key Type] Dependency
    """
    title: str = "dependency.title"
    """[Props Type] Title"""
    verifying: str = "dependency.verifying"
    """[Props Type] Verifying"""
    once_only: str = "dependency.once_only"
    """[Props Type] OnceOnly"""
    core_verifying: str = "dependency.core_verifying"
    """[Props Type] CoreVerifying"""
    python_version: _DependencyPythonVersionCallable = _DependencyPythonVersionCallable()
    """
    [Callable Props Type] PythonVersion
    
    Original template: "Python {version}"
    """
    python_old: _DependencyPythonOldCallable = _DependencyPythonOldCallable()
    """
    [Callable Props Type] PythonOld
    
    Original template: "Python {version} - Required: 3.8+"
    """
    ffmpeg_version: _DependencyFfmpegVersionCallable = _DependencyFfmpegVersionCallable()
    """
    [Callable Props Type] FfmpegVersion
    
    Original template: "FFmpeg {version}"
    """
    ffmpeg_not_found: str = "dependency.ffmpeg_not_found"
    """[Props Type] FfmpegNotFound"""
    package_installed: _DependencyPackageInstalledCallable = _DependencyPackageInstalledCallable()
    """
    [Callable Props Type] PackageInstalled
    
    Original template: "{package} {version}"
    """
    package_simple: _DependencyPackageSimpleCallable = _DependencyPackageSimpleCallable()
    """
    [Callable Props Type] PackageSimple
    
    Original template: "{package} (installed)"
    """
    package_not_found: _DependencyPackageNotFoundCallable = _DependencyPackageNotFoundCallable()
    """
    [Callable Props Type] PackageNotFound
    
    Original template: "{package} not found"
    """
    core_success: str = "dependency.core_success"
    """[Props Type] CoreSuccess"""
    core_failed: str = "dependency.core_failed"
    """[Props Type] CoreFailed"""
    install_missing: str = "dependency.install_missing"
    """[Props Type] InstallMissing"""
    install_ffmpeg: str = "dependency.install_ffmpeg"
    """[Props Type] InstallFfmpeg"""
    install_ytdlp: str = "dependency.install_ytdlp"
    """[Props Type] InstallYtdlp"""
    install_requests: str = "dependency.install_requests"
    """[Props Type] InstallRequests"""
    checking_spotify: str = "dependency.checking_spotify"
    """[Props Type] CheckingSpotify"""
    spotify_available: str = "dependency.spotify_available"
    """[Props Type] SpotifyAvailable"""
    spotify_unavailable: str = "dependency.spotify_unavailable"
    """[Props Type] SpotifyUnavailable"""
    spotify_install: str = "dependency.spotify_install"
    """[Props Type] SpotifyInstall"""
    spotify_warning: str = "dependency.spotify_warning"
    """[Props Type] SpotifyWarning"""
    verification_complete: str = "dependency.verification_complete"
    """[Props Type] VerificationComplete"""
    spotify_hidden: str = "dependency.spotify_hidden"
    """[Props Type] SpotifyHidden"""
    verification_failed: str = "dependency.verification_failed"
    """[Props Type] VerificationFailed"""
    install_and_retry: str = "dependency.install_and_retry"
    """[Props Type] InstallAndRetry"""
    verification_reset: str = "dependency.verification_reset"
    """[Props Type] VerificationReset"""
    verify_next_run: str = "dependency.verify_next_run"
    """[Props Type] VerifyNextRun"""

class _HistoryTotalDurationCallable:
    """
    [Callable Props Type] TotalDuration
    
    Original template: "Total Duration: {duration}"
    """
    def __call__(self, *, duration: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            duration (str | int): Dynamic value for {duration}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("history.total_duration", {"duration": duration})

class _HistoryK:
    """
    [Key Type] History
    """
    title: str = "history.title"
    """[Props Type] Title"""
    empty: str = "history.empty"
    """[Props Type] Empty"""
    total_duration: _HistoryTotalDurationCallable = _HistoryTotalDurationCallable()
    """
    [Callable Props Type] TotalDuration
    
    Original template: "Total Duration: {duration}"
    """
    entries: str = "history.entries"
    """[Props Type] Entries"""

class _DownloadNavigationCannotReadCallable:
    """
    [Callable Props Type] CannotRead
    
    Original template: "Cannot read folder: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.navigation.cannot_read", {"error": error})

class _DownloadNavigationSettedMusicCallable:
    """
    [Callable Props Type] SettedMusic
    
    Original template: "Music root setted to: {music_root}"
    """
    def __call__(self, *, music_root: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            music_root (str | int): Dynamic value for {music_root}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.navigation.setted_music", {"music_root": music_root})

class _DownloadNavigationSettedVideoCallable:
    """
    [Callable Props Type] SettedVideo
    
    Original template: "Video root setted to: {video_root}"
    """
    def __call__(self, *, video_root: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            video_root (str | int): Dynamic value for {video_root}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.navigation.setted_video", {"video_root": video_root})

class _DownloadNavigationK:
    """
    [Key Type] Navigation
    """
    title: str = "download.navigation.title"
    """[Props Type] Title"""
    current_location: str = "download.navigation.current_location"
    """[Props Type] CurrentLocation"""
    go_up: str = "download.navigation.go_up"
    """[Props Type] GoUp"""
    select_this: str = "download.navigation.select_this"
    """[Props Type] SelectThis"""
    cannot_read: _DownloadNavigationCannotReadCallable = _DownloadNavigationCannotReadCallable()
    """
    [Callable Props Type] CannotRead
    
    Original template: "Cannot read folder: {error}"
    """
    cannot_go_up_root: str = "download.navigation.cannot_go_up_root"
    """[Props Type] CannotGoUpRoot"""
    cannot_go_up: str = "download.navigation.cannot_go_up"
    """[Props Type] CannotGoUp"""
    setted_music: _DownloadNavigationSettedMusicCallable = _DownloadNavigationSettedMusicCallable()
    """
    [Callable Props Type] SettedMusic
    
    Original template: "Music root setted to: {music_root}"
    """
    setted_video: _DownloadNavigationSettedVideoCallable = _DownloadNavigationSettedVideoCallable()
    """
    [Callable Props Type] SettedVideo
    
    Original template: "Video root setted to: {video_root}"
    """

class _DownloadFolderSelectLocationCallable:
    """
    [Callable Props Type] SelectLocation
    
    Original template: "Select Save Location ({type})"
    """
    def __call__(self, *, type: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            type (str | int): Dynamic value for {type}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.folder.select_location", {"type": type})

class _DownloadFolderRootCallable:
    """
    [Callable Props Type] Root
    
    Original template: "Target: {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.folder.root", {"path": path})

class _DownloadFolderCreateFailedCallable:
    """
    [Callable Props Type] CreateFailed
    
    Original template: "Failed to create folder: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.folder.create_failed", {"error": error})

class _DownloadFolderNotFoundCallable:
    """
    [Callable Props Type] NotFound
    
    Original template: "Subfolder '{name}' not found, removing from config..."
    """
    def __call__(self, *, name: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            name (str | int): Dynamic value for {name}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.folder.not_found", {"name": name})

class _DownloadFolderK:
    """
    [Key Type] Folder
    """
    select_location: _DownloadFolderSelectLocationCallable = _DownloadFolderSelectLocationCallable()
    """
    [Callable Props Type] SelectLocation
    
    Original template: "Select Save Location ({type})"
    """
    root: _DownloadFolderRootCallable = _DownloadFolderRootCallable()
    """
    [Callable Props Type] Root
    
    Original template: "Target: {path}"
    """
    create_new: str = "download.folder.create_new"
    """[Props Type] CreateNew"""
    no_subfolder: str = "download.folder.no_subfolder"
    """[Props Type] NoSubfolder"""
    browse_title: str = "download.folder.browse_title"
    """[Props Type] BrowseTitle"""
    browse_system: str = "download.folder.browse_system"
    """[Props Type] BrowseSystem"""
    save_to_root: str = "download.folder.save_to_root"
    """[Props Type] SaveToRoot"""
    enter_name: str = "download.folder.enter_name"
    """[Props Type] EnterName"""
    create_failed: _DownloadFolderCreateFailedCallable = _DownloadFolderCreateFailedCallable()
    """
    [Callable Props Type] CreateFailed
    
    Original template: "Failed to create folder: {error}"
    """
    not_found: _DownloadFolderNotFoundCallable = _DownloadFolderNotFoundCallable()
    """
    [Callable Props Type] NotFound
    
    Original template: "Subfolder '{name}' not found, removing from config..."
    """
    choose_again: str = "download.folder.choose_again"
    """[Props Type] ChooseAgain"""

class _DownloadSpotifyDetectedCallable:
    """
    [Callable Props Type] Detected
    
    Original template: "Spotify {type} detected"
    """
    def __call__(self, *, type: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            type (str | int): Dynamic value for {type}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.spotify.detected", {"type": type})

class _DownloadSpotifySpotdlErrorCallable:
    """
    [Callable Props Type] SpotdlError
    
    Original template: "Failed to run spotdl: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.spotify.spotdl_error", {"error": error})

class _DownloadSpotifyK:
    """
    [Key Type] Spotify
    """
    url_input: str = "download.spotify.url_input"
    """[Props Type] UrlInput"""
    invalid_url: str = "download.spotify.invalid_url"
    """[Props Type] InvalidUrl"""
    no_internet: str = "download.spotify.no_internet"
    """[Props Type] NoInternet"""
    detected: _DownloadSpotifyDetectedCallable = _DownloadSpotifyDetectedCallable()
    """
    [Callable Props Type] Detected
    
    Original template: "Spotify {type} detected"
    """
    classification_failed: str = "download.spotify.classification_failed"
    """[Props Type] ClassificationFailed"""
    downloading: str = "download.spotify.downloading"
    """[Props Type] Downloading"""
    success: str = "download.spotify.success"
    """[Props Type] Success"""
    failed: str = "download.spotify.failed"
    """[Props Type] Failed"""
    spotdl_error: _DownloadSpotifySpotdlErrorCallable = _DownloadSpotifySpotdlErrorCallable()
    """
    [Callable Props Type] SpotdlError
    
    Original template: "Failed to run spotdl: {error}"
    """
    not_available: str = "download.spotify.not_available"
    """[Props Type] NotAvailable"""
    install_instruction: str = "download.spotify.install_instruction"
    """[Props Type] InstallInstruction"""
    reset_verification_hint: str = "download.spotify.reset_verification_hint"
    """[Props Type] ResetVerificationHint"""

class _DownloadYoutubeDetectedCallable:
    """
    [Callable Props Type] Detected
    
    Original template: "{type} detected"
    """
    def __call__(self, *, type: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            type (str | int): Dynamic value for {type}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.detected", {"type": type})

class _DownloadYoutubeExtractedCallable:
    """
    [Callable Props Type] Extracted
    
    Original template: "Successfully extracted {count} {type}"
    """
    def __call__(self, *, count: str | int, type: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            count (str | int): Dynamic value for {count}.
            type (str | int): Dynamic value for {type}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.extracted", {"count": count, "type": type})

class _DownloadYoutubeFoundPlaylistCallable:
    """
    [Callable Props Type] FoundPlaylist
    
    Original template: "Found {count} {type} in playlist/album: {title}"
    """
    def __call__(self, *, count: str | int, type: str | int, title: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            count (str | int): Dynamic value for {count}.
            type (str | int): Dynamic value for {type}.
            title (str | int): Dynamic value for {title}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.found_playlist", {"count": count, "type": type, "title": title})

class _DownloadYoutubeSimpleModeStartCallable:
    """
    [Callable Props Type] SimpleModeStart
    
    Original template: "Simple Mode: Starting {type} download → {path}"
    """
    def __call__(self, *, type: str | int, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            type (str | int): Dynamic value for {type}.
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.simple_mode_start", {"type": type, "path": path})

class _DownloadYoutubeStartDownloadCallable:
    """
    [Callable Props Type] StartDownload
    
    Original template: "Starting {type} download → {path}"
    """
    def __call__(self, *, type: str | int, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            type (str | int): Dynamic value for {type}.
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.start_download", {"type": type, "path": path})

class _DownloadYoutubeFileExistsPlaylistCallable:
    """
    [Callable Props Type] FileExistsPlaylist
    
    Original template: "{title} already exists, skipping..."
    """
    def __call__(self, *, title: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            title (str | int): Dynamic value for {title}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.file_exists_playlist", {"title": title})

class _DownloadYoutubeExistsTitleCallable:
    """
    [Callable Props Type] ExistsTitle
    
    Original template: "Title: {title}"
    """
    def __call__(self, *, title: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            title (str | int): Dynamic value for {title}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.exists_title", {"title": title})

class _DownloadYoutubeExistsPathCallable:
    """
    [Callable Props Type] ExistsPath
    
    Original template: "Path: {path}"
    """
    def __call__(self, *, path: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            path (str | int): Dynamic value for {path}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.exists_path", {"path": path})

class _DownloadYoutubeUsingCacheCallable:
    """
    [Callable Props Type] UsingCache
    
    Original template: "Using cache for: {title}"
    """
    def __call__(self, *, title: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            title (str | int): Dynamic value for {title}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.using_cache", {"title": title})

class _DownloadYoutubeDownloadingItemCallable:
    """
    [Callable Props Type] DownloadingItem
    
    Original template: "Downloading: {title}"
    """
    def __call__(self, *, title: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            title (str | int): Dynamic value for {title}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.downloading_item", {"title": title})

class _DownloadYoutubeFileNotFoundCallable:
    """
    [Callable Props Type] FileNotFound
    
    Original template: "Audio file not found: {filename}"
    """
    def __call__(self, *, filename: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            filename (str | int): Dynamic value for {filename}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.file_not_found", {"filename": filename})

class _DownloadYoutubeMaxResolutionCallable:
    """
    [Callable Props Type] MaxResolution
    
    Original template: "Max video resolution: {resolution}"
    """
    def __call__(self, *, resolution: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            resolution (str | int): Dynamic value for {resolution}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.max_resolution", {"resolution": resolution})

class _DownloadYoutubeProgressCallable:
    """
    [Callable Props Type] Progress
    
    Original template: "Progress: {current}/{total}"
    """
    def __call__(self, *, current: str | int, total: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            current (str | int): Dynamic value for {current}.
            total (str | int): Dynamic value for {total}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.progress", {"current": current, "total": total})

class _DownloadYoutubeDownloadingUrlCallable:
    """
    [Callable Props Type] DownloadingUrl
    
    Original template: "Downloading URL: {url} as {type}."
    """
    def __call__(self, *, url: str | int, type: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            url (str | int): Dynamic value for {url}.
            type (str | int): Dynamic value for {type}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.downloading_url", {"url": url, "type": type})

class _DownloadYoutubeSuccessCallable:
    """
    [Callable Props Type] Success
    
    Original template: "Success: {title}"
    """
    def __call__(self, *, title: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            title (str | int): Dynamic value for {title}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.success", {"title": title})

class _DownloadYoutubeFailedCallable:
    """
    [Callable Props Type] Failed
    
    Original template: "Failed: {title}"
    """
    def __call__(self, *, title: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            title (str | int): Dynamic value for {title}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.failed", {"title": title})

class _DownloadYoutubeWaitDelayCallable:
    """
    [Callable Props Type] WaitDelay
    
    Original template: "Waiting {delay} seconds before next download..."
    """
    def __call__(self, *, delay: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            delay (str | int): Dynamic value for {delay}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.wait_delay", {"delay": delay})

class _DownloadYoutubeSummaryCallable:
    """
    [Callable Props Type] Summary
    
    Original template: "Summary: {success} successful, {skipped} skipped, {failed} failed out of {total} {type}"
    """
    def __call__(self, *, success: str | int, skipped: str | int, failed: str | int, total: str | int, type: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            success (str | int): Dynamic value for {success}.
            skipped (str | int): Dynamic value for {skipped}.
            failed (str | int): Dynamic value for {failed}.
            total (str | int): Dynamic value for {total}.
            type (str | int): Dynamic value for {type}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.summary", {"success": success, "skipped": skipped, "failed": failed, "total": total, "type": type})

class _DownloadYoutubeFailedItemsCallable:
    """
    [Callable Props Type] FailedItems
    
    Original template: "{count} {type} failed to download"
    """
    def __call__(self, *, count: str | int, type: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            count (str | int): Dynamic value for {count}.
            type (str | int): Dynamic value for {type}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.failed_items", {"count": count, "type": type})

class _DownloadYoutubeExtractFailedCallable:
    """
    [Callable Props Type] ExtractFailed
    
    Original template: "Failed to extract content: {error}"
    """
    def __call__(self, *, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.extract_failed", {"error": error})

class _DownloadYoutubeErrorDownloadingCallable:
    """
    [Callable Props Type] ErrorDownloading
    
    Original template: "Error downloading {type}: {error}"
    """
    def __call__(self, *, type: str | int, error: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            type (str | int): Dynamic value for {type}.
            error (str | int): Dynamic value for {error}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.error_downloading", {"type": type, "error": error})

class _DownloadYoutubeCompleteCallable:
    """
    [Callable Props Type] Complete
    
    Original template: "Download successful: {title}"
    """
    def __call__(self, *, title: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            title (str | int): Dynamic value for {title}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.complete", {"title": title})

class _DownloadYoutubeCompleteMetadataCallable:
    """
    [Callable Props Type] CompleteMetadata
    
    Original template: "Download successful with metadata: {title}"
    """
    def __call__(self, *, title: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            title (str | int): Dynamic value for {title}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("download.youtube.complete_metadata", {"title": title})

class _DownloadYoutubeK:
    """
    [Key Type] Youtube
    """
    url_input_ytm: str = "download.youtube.url_input_ytm"
    """[Props Type] UrlInputYtm"""
    url_input_ytv: str = "download.youtube.url_input_ytv"
    """[Props Type] UrlInputYtv"""
    invalid_url: str = "download.youtube.invalid_url"
    """[Props Type] InvalidUrl"""
    checking_internet: str = "download.youtube.checking_internet"
    """[Props Type] CheckingInternet"""
    no_internet: str = "download.youtube.no_internet"
    """[Props Type] NoInternet"""
    detected: _DownloadYoutubeDetectedCallable = _DownloadYoutubeDetectedCallable()
    """
    [Callable Props Type] Detected
    
    Original template: "{type} detected"
    """
    yt_music_detected: str = "download.youtube.yt_music_detected"
    """[Props Type] YtMusicDetected"""
    yt_audio_plain: str = "download.youtube.yt_audio_plain"
    """[Props Type] YtAudioPlain"""
    smart_cover_info: str = "download.youtube.smart_cover_info"
    """[Props Type] SmartCoverInfo"""
    extracting: str = "download.youtube.extracting"
    """[Props Type] Extracting"""
    extracted: _DownloadYoutubeExtractedCallable = _DownloadYoutubeExtractedCallable()
    """
    [Callable Props Type] Extracted
    
    Original template: "Successfully extracted {count} {type}"
    """
    found_playlist: _DownloadYoutubeFoundPlaylistCallable = _DownloadYoutubeFoundPlaylistCallable()
    """
    [Callable Props Type] FoundPlaylist
    
    Original template: "Found {count} {type} in playlist/album: {title}"
    """
    simple_mode_start: _DownloadYoutubeSimpleModeStartCallable = _DownloadYoutubeSimpleModeStartCallable()
    """
    [Callable Props Type] SimpleModeStart
    
    Original template: "Simple Mode: Starting {type} download → {path}"
    """
    start_download: _DownloadYoutubeStartDownloadCallable = _DownloadYoutubeStartDownloadCallable()
    """
    [Callable Props Type] StartDownload
    
    Original template: "Starting {type} download → {path}"
    """
    checking_existing: str = "download.youtube.checking_existing"
    """[Props Type] CheckingExisting"""
    file_exists: str = "download.youtube.file_exists"
    """[Props Type] FileExists"""
    file_exists_playlist: _DownloadYoutubeFileExistsPlaylistCallable = _DownloadYoutubeFileExistsPlaylistCallable()
    """
    [Callable Props Type] FileExistsPlaylist
    
    Original template: "{title} already exists, skipping..."
    """
    exists_title: _DownloadYoutubeExistsTitleCallable = _DownloadYoutubeExistsTitleCallable()
    """
    [Callable Props Type] ExistsTitle
    
    Original template: "Title: {title}"
    """
    exists_path: _DownloadYoutubeExistsPathCallable = _DownloadYoutubeExistsPathCallable()
    """
    [Callable Props Type] ExistsPath
    
    Original template: "Path: {path}"
    """
    using_cache: _DownloadYoutubeUsingCacheCallable = _DownloadYoutubeUsingCacheCallable()
    """
    [Callable Props Type] UsingCache
    
    Original template: "Using cache for: {title}"
    """
    downloading_item: _DownloadYoutubeDownloadingItemCallable = _DownloadYoutubeDownloadingItemCallable()
    """
    [Callable Props Type] DownloadingItem
    
    Original template: "Downloading: {title}"
    """
    processing_cover: str = "download.youtube.processing_cover"
    """[Props Type] ProcessingCover"""
    fetch_success: str = "download.youtube.fetch_success"
    """[Props Type] FetchSuccess"""
    processing_art_track: str = "download.youtube.processing_art_track"
    """[Props Type] ProcessingArtTrack"""
    embedding_cover: str = "download.youtube.embedding_cover"
    """[Props Type] EmbeddingCover"""
    cover_success: str = "download.youtube.cover_success"
    """[Props Type] CoverSuccess"""
    cover_failed: str = "download.youtube.cover_failed"
    """[Props Type] CoverFailed"""
    file_not_found: _DownloadYoutubeFileNotFoundCallable = _DownloadYoutubeFileNotFoundCallable()
    """
    [Callable Props Type] FileNotFound
    
    Original template: "Audio file not found: {filename}"
    """
    cover_process_failed: str = "download.youtube.cover_process_failed"
    """[Props Type] CoverProcessFailed"""
    skip_cover: str = "download.youtube.skip_cover"
    """[Props Type] SkipCover"""
    skip_cover_opus: str = "download.youtube.skip_cover_opus"
    """[Props Type] SkipCoverOpus"""
    max_resolution: _DownloadYoutubeMaxResolutionCallable = _DownloadYoutubeMaxResolutionCallable()
    """
    [Callable Props Type] MaxResolution
    
    Original template: "Max video resolution: {resolution}"
    """
    progress: _DownloadYoutubeProgressCallable = _DownloadYoutubeProgressCallable()
    """
    [Callable Props Type] Progress
    
    Original template: "Progress: {current}/{total}"
    """
    downloading_url: _DownloadYoutubeDownloadingUrlCallable = _DownloadYoutubeDownloadingUrlCallable()
    """
    [Callable Props Type] DownloadingUrl
    
    Original template: "Downloading URL: {url} as {type}."
    """
    success: _DownloadYoutubeSuccessCallable = _DownloadYoutubeSuccessCallable()
    """
    [Callable Props Type] Success
    
    Original template: "Success: {title}"
    """
    failed: _DownloadYoutubeFailedCallable = _DownloadYoutubeFailedCallable()
    """
    [Callable Props Type] Failed
    
    Original template: "Failed: {title}"
    """
    wait_delay: _DownloadYoutubeWaitDelayCallable = _DownloadYoutubeWaitDelayCallable()
    """
    [Callable Props Type] WaitDelay
    
    Original template: "Waiting {delay} seconds before next download..."
    """
    summary: _DownloadYoutubeSummaryCallable = _DownloadYoutubeSummaryCallable()
    """
    [Callable Props Type] Summary
    
    Original template: "Summary: {success} successful, {skipped} skipped, {failed} failed out of {total} {type}"
    """
    failed_items: _DownloadYoutubeFailedItemsCallable = _DownloadYoutubeFailedItemsCallable()
    """
    [Callable Props Type] FailedItems
    
    Original template: "{count} {type} failed to download"
    """
    extract_failed: _DownloadYoutubeExtractFailedCallable = _DownloadYoutubeExtractFailedCallable()
    """
    [Callable Props Type] ExtractFailed
    
    Original template: "Failed to extract content: {error}"
    """
    error_downloading: _DownloadYoutubeErrorDownloadingCallable = _DownloadYoutubeErrorDownloadingCallable()
    """
    [Callable Props Type] ErrorDownloading
    
    Original template: "Error downloading {type}: {error}"
    """
    complete: _DownloadYoutubeCompleteCallable = _DownloadYoutubeCompleteCallable()
    """
    [Callable Props Type] Complete
    
    Original template: "Download successful: {title}"
    """
    complete_metadata: _DownloadYoutubeCompleteMetadataCallable = _DownloadYoutubeCompleteMetadataCallable()
    """
    [Callable Props Type] CompleteMetadata
    
    Original template: "Download successful with metadata: {title}"
    """
    cancelled: str = "download.youtube.cancelled"
    """[Props Type] Cancelled"""

class _DownloadK:
    """
    [Key Type] Download
    """
    youtube: _DownloadYoutubeK = _DownloadYoutubeK()
    """[Key Type] Youtube"""
    spotify: _DownloadSpotifyK = _DownloadSpotifyK()
    """[Key Type] Spotify"""
    folder: _DownloadFolderK = _DownloadFolderK()
    """[Key Type] Folder"""
    navigation: _DownloadNavigationK = _DownloadNavigationK()
    """[Key Type] Navigation"""

class _MenuAboutTitleCallable:
    """
    [Callable Props Type] Title
    
    Original template: "TetoDL v{version}, by rannd1nt"
    """
    def __call__(self, *, version: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            version (str | int): Dynamic value for {version}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("menu.about.title", {"version": version})

class _MenuAboutK:
    """
    [Key Type] About
    """
    title: _MenuAboutTitleCallable = _MenuAboutTitleCallable()
    """
    [Callable Props Type] Title
    
    Original template: "TetoDL v{version}, by rannd1nt"
    """
    subtitle: str = "menu.about.subtitle"
    """[Props Type] Subtitle"""
    description: str = "menu.about.description"
    """[Props Type] Description"""
    documentation: str = "menu.about.documentation"
    """[Props Type] Documentation"""
    github: str = "menu.about.github"
    """[Props Type] Github"""
    instagram: str = "menu.about.instagram"
    """[Props Type] Instagram"""

class _MenuRootFolderK:
    """
    [Key Type] RootFolder
    """
    title: str = "menu.root_folder.title"
    """[Props Type] Title"""
    change_music: str = "menu.root_folder.change_music"
    """[Props Type] ChangeMusic"""
    change_video: str = "menu.root_folder.change_video"
    """[Props Type] ChangeVideo"""
    reset: str = "menu.root_folder.reset"
    """[Props Type] Reset"""
    nav_folder_title: str = "menu.root_folder.nav_folder_title"
    """[Props Type] NavFolderTitle"""

class _MenuLanguageCurrentCallable:
    """
    [Callable Props Type] Current
    
    Original template: "Current language: {lang}"
    """
    def __call__(self, *, lang: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            lang (str | int): Dynamic value for {lang}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("menu.language.current", {"lang": lang})

class _MenuLanguageK:
    """
    [Key Type] Language
    """
    title: str = "menu.language.title"
    """[Props Type] Title"""
    current: _MenuLanguageCurrentCallable = _MenuLanguageCurrentCallable()
    """
    [Callable Props Type] Current
    
    Original template: "Current language: {lang}"
    """
    choose: str = "menu.language.choose"
    """[Props Type] Choose"""

class _MenuVideoCodecK:
    """
    [Key Type] VideoCodec
    """
    title: str = "menu.video_codec.title"
    """[Props Type] Title"""
    select: str = "menu.video_codec.select"
    """[Props Type] Select"""
    default_title: str = "menu.video_codec.default_title"
    """[Props Type] DefaultTitle"""
    default_desc: str = "menu.video_codec.default_desc"
    """[Props Type] DefaultDesc"""
    h264_title: str = "menu.video_codec.h264_title"
    """[Props Type] H264Title"""
    h264_desc: str = "menu.video_codec.h264_desc"
    """[Props Type] H264Desc"""
    h265_title: str = "menu.video_codec.h265_title"
    """[Props Type] H265Title"""
    h265_desc: str = "menu.video_codec.h265_desc"
    """[Props Type] H265Desc"""

class _MenuVideoResolutionCurrentCallable:
    """
    [Callable Props Type] Current
    
    Original template: "Current Resolution: {resolution}"
    """
    def __call__(self, *, resolution: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            resolution (str | int): Dynamic value for {resolution}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("menu.video_resolution.current", {"resolution": resolution})

class _MenuVideoResolutionK:
    """
    [Key Type] VideoResolution
    """
    title: str = "menu.video_resolution.title"
    """[Props Type] Title"""
    current: _MenuVideoResolutionCurrentCallable = _MenuVideoResolutionCurrentCallable()
    """
    [Callable Props Type] Current
    
    Original template: "Current Resolution: {resolution}"
    """
    select: str = "menu.video_resolution.select"
    """[Props Type] Select"""
    _4320p_desc: str = "menu.video_resolution.4320p_desc"
    """[Props Type] 4320pDesc"""
    _2160p_desc: str = "menu.video_resolution.2160p_desc"
    """[Props Type] 2160pDesc"""
    _1440p_desc: str = "menu.video_resolution.1440p_desc"
    """[Props Type] 1440pDesc"""
    _1080p_desc: str = "menu.video_resolution.1080p_desc"
    """[Props Type] 1080pDesc"""
    _720p_desc: str = "menu.video_resolution.720p_desc"
    """[Props Type] 720pDesc"""
    _480p_desc: str = "menu.video_resolution.480p_desc"
    """[Props Type] 480pDesc"""
    very_high_storage: str = "menu.video_resolution.very_high_storage"
    """[Props Type] VeryHighStorage"""
    high_quality: str = "menu.video_resolution.high_quality"
    """[Props Type] HighQuality"""
    standard: str = "menu.video_resolution.standard"
    """[Props Type] Standard"""
    save_storage: str = "menu.video_resolution.save_storage"
    """[Props Type] SaveStorage"""
    slow_connection: str = "menu.video_resolution.slow_connection"
    """[Props Type] SlowConnection"""

class _MenuAudioQualityCurrentCallable:
    """
    [Callable Props Type] Current
    
    Original template: "Current: {format} {bitrate}"
    """
    def __call__(self, *, format: str | int, bitrate: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            format (str | int): Dynamic value for {format}.
            bitrate (str | int): Dynamic value for {bitrate}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("menu.audio_quality.current", {"format": format, "bitrate": bitrate})

class _MenuAudioQualityChangedCallable:
    """
    [Callable Props Type] Changed
    
    Original template: "Audio quality changed to: {format}"
    """
    def __call__(self, *, format: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            format (str | int): Dynamic value for {format}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("menu.audio_quality.changed", {"format": format})

class _MenuAudioQualityK:
    """
    [Key Type] AudioQuality
    """
    title: str = "menu.audio_quality.title"
    """[Props Type] Title"""
    current: _MenuAudioQualityCurrentCallable = _MenuAudioQualityCurrentCallable()
    """
    [Callable Props Type] Current
    
    Original template: "Current: {format} {bitrate}"
    """
    select: str = "menu.audio_quality.select"
    """[Props Type] Select"""
    mp3_title: str = "menu.audio_quality.mp3_title"
    """[Props Type] Mp3Title"""
    mp3_desc_1: str = "menu.audio_quality.mp3_desc_1"
    """[Props Type] Mp3Desc1"""
    mp3_desc_2: str = "menu.audio_quality.mp3_desc_2"
    """[Props Type] Mp3Desc2"""
    mp3_desc_3: str = "menu.audio_quality.mp3_desc_3"
    """[Props Type] Mp3Desc3"""
    m4a_title: str = "menu.audio_quality.m4a_title"
    """[Props Type] M4aTitle"""
    m4a_desc_1: str = "menu.audio_quality.m4a_desc_1"
    """[Props Type] M4aDesc1"""
    m4a_desc_2: str = "menu.audio_quality.m4a_desc_2"
    """[Props Type] M4aDesc2"""
    m4a_desc_3: str = "menu.audio_quality.m4a_desc_3"
    """[Props Type] M4aDesc3"""
    opus_title: str = "menu.audio_quality.opus_title"
    """[Props Type] OpusTitle"""
    opus_desc_1: str = "menu.audio_quality.opus_desc_1"
    """[Props Type] OpusDesc1"""
    opus_desc_2: str = "menu.audio_quality.opus_desc_2"
    """[Props Type] OpusDesc2"""
    opus_desc_3: str = "menu.audio_quality.opus_desc_3"
    """[Props Type] OpusDesc3"""
    changed: _MenuAudioQualityChangedCallable = _MenuAudioQualityChangedCallable()
    """
    [Callable Props Type] Changed
    
    Original template: "Audio quality changed to: {format}"
    """

class _MenuSettingsSimpleModeCallable:
    """
    [Callable Props Type] SimpleMode
    
    Original template: "Simple Mode: {status}"
    """
    def __call__(self, *, status: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            status (str | int): Dynamic value for {status}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("menu.settings.simple_mode", {"status": status})

class _MenuSettingsSmartCoverCallable:
    """
    [Callable Props Type] SmartCover
    
    Original template: "Smart Cover Mode: {status}"
    """
    def __call__(self, *, status: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            status (str | int): Dynamic value for {status}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("menu.settings.smart_cover", {"status": status})

class _MenuSettingsSkipExistingCallable:
    """
    [Callable Props Type] SkipExisting
    
    Original template: "Skip Existing Files: {status}"
    """
    def __call__(self, *, status: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            status (str | int): Dynamic value for {status}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("menu.settings.skip_existing", {"status": status})

class _MenuSettingsMaxResolutionCallable:
    """
    [Callable Props Type] MaxResolution
    
    Original template: "Video Resolution Limit: {resolution}"
    """
    def __call__(self, *, resolution: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            resolution (str | int): Dynamic value for {resolution}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("menu.settings.max_resolution", {"resolution": resolution})

class _MenuSettingsVideoContainerCallable:
    """
    [Callable Props Type] VideoContainer
    
    Original template: "Video Container Output: {container}"
    """
    def __call__(self, *, container: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            container (str | int): Dynamic value for {container}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("menu.settings.video_container", {"container": container})

class _MenuSettingsVideoCodecCallable:
    """
    [Callable Props Type] VideoCodec
    
    Original template: "Video Codec Settings: {codec}"
    """
    def __call__(self, *, codec: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            codec (str | int): Dynamic value for {codec}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("menu.settings.video_codec", {"codec": codec})

class _MenuSettingsAudioQualityCallable:
    """
    [Callable Props Type] AudioQuality
    
    Original template: "Audio Quality Settings: {format}"
    """
    def __call__(self, *, format: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            format (str | int): Dynamic value for {format}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("menu.settings.audio_quality", {"format": format})

class _MenuSettingsMediaScannerCallable:
    """
    [Callable Props Type] MediaScanner
    
    Original template: "Automatic Media Scanner (Android 9 >): {status}"
    """
    def __call__(self, *, status: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            status (str | int): Dynamic value for {status}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("menu.settings.media_scanner", {"status": status})

class _MenuSettingsLanguageCallable:
    """
    [Callable Props Type] Language
    
    Original template: "Current language: {lang}"
    """
    def __call__(self, *, lang: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            lang (str | int): Dynamic value for {lang}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("menu.settings.language", {"lang": lang})

class _MenuSettingsK:
    """
    [Key Type] Settings
    """
    title: str = "menu.settings.title"
    """[Props Type] Title"""
    simple_mode: _MenuSettingsSimpleModeCallable = _MenuSettingsSimpleModeCallable()
    """
    [Callable Props Type] SimpleMode
    
    Original template: "Simple Mode: {status}"
    """
    simple_mode_desc: str = "menu.settings.simple_mode_desc"
    """[Props Type] SimpleModeDesc"""
    smart_cover: _MenuSettingsSmartCoverCallable = _MenuSettingsSmartCoverCallable()
    """
    [Callable Props Type] SmartCover
    
    Original template: "Smart Cover Mode: {status}"
    """
    smart_cover_desc_1: str = "menu.settings.smart_cover_desc_1"
    """[Props Type] SmartCoverDesc1"""
    smart_cover_desc_2: str = "menu.settings.smart_cover_desc_2"
    """[Props Type] SmartCoverDesc2"""
    smart_cover_desc_3: str = "menu.settings.smart_cover_desc_3"
    """[Props Type] SmartCoverDesc3"""
    skip_existing: _MenuSettingsSkipExistingCallable = _MenuSettingsSkipExistingCallable()
    """
    [Callable Props Type] SkipExisting
    
    Original template: "Skip Existing Files: {status}"
    """
    skip_existing_desc: str = "menu.settings.skip_existing_desc"
    """[Props Type] SkipExistingDesc"""
    max_resolution: _MenuSettingsMaxResolutionCallable = _MenuSettingsMaxResolutionCallable()
    """
    [Callable Props Type] MaxResolution
    
    Original template: "Video Resolution Limit: {resolution}"
    """
    max_resolution_desc_1: str = "menu.settings.max_resolution_desc_1"
    """[Props Type] MaxResolutionDesc1"""
    max_resolution_desc_2: str = "menu.settings.max_resolution_desc_2"
    """[Props Type] MaxResolutionDesc2"""
    video_container: _MenuSettingsVideoContainerCallable = _MenuSettingsVideoContainerCallable()
    """
    [Callable Props Type] VideoContainer
    
    Original template: "Video Container Output: {container}"
    """
    video_container_desc: str = "menu.settings.video_container_desc"
    """[Props Type] VideoContainerDesc"""
    video_codec: _MenuSettingsVideoCodecCallable = _MenuSettingsVideoCodecCallable()
    """
    [Callable Props Type] VideoCodec
    
    Original template: "Video Codec Settings: {codec}"
    """
    video_codec_desc: str = "menu.settings.video_codec_desc"
    """[Props Type] VideoCodecDesc"""
    audio_quality: _MenuSettingsAudioQualityCallable = _MenuSettingsAudioQualityCallable()
    """
    [Callable Props Type] AudioQuality
    
    Original template: "Audio Quality Settings: {format}"
    """
    audio_quality_desc: str = "menu.settings.audio_quality_desc"
    """[Props Type] AudioQualityDesc"""
    history: str = "menu.settings.history"
    """[Props Type] History"""
    history_desc: str = "menu.settings.history_desc"
    """[Props Type] HistoryDesc"""
    clear_cache: str = "menu.settings.clear_cache"
    """[Props Type] ClearCache"""
    clear_cache_desc: str = "menu.settings.clear_cache_desc"
    """[Props Type] ClearCacheDesc"""
    clear_history: str = "menu.settings.clear_history"
    """[Props Type] ClearHistory"""
    clear_history_desc: str = "menu.settings.clear_history_desc"
    """[Props Type] ClearHistoryDesc"""
    reset_verification: str = "menu.settings.reset_verification"
    """[Props Type] ResetVerification"""
    reset_verification_desc: str = "menu.settings.reset_verification_desc"
    """[Props Type] ResetVerificationDesc"""
    media_scanner: _MenuSettingsMediaScannerCallable = _MenuSettingsMediaScannerCallable()
    """
    [Callable Props Type] MediaScanner
    
    Original template: "Automatic Media Scanner (Android 9 >): {status}"
    """
    media_scanner_desc: str = "menu.settings.media_scanner_desc"
    """[Props Type] MediaScannerDesc"""
    language: _MenuSettingsLanguageCallable = _MenuSettingsLanguageCallable()
    """
    [Callable Props Type] Language
    
    Original template: "Current language: {lang}"
    """
    language_desc: str = "menu.settings.language_desc"
    """[Props Type] LanguageDesc"""

class _MenuMainYoutubeAudioCallable:
    """
    [Callable Props Type] YoutubeAudio
    
    Original template: "YouTube Audio/YouTube Music → {format} {bitrate}"
    """
    def __call__(self, *, format: str | int, bitrate: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            format (str | int): Dynamic value for {format}.
            bitrate (str | int): Dynamic value for {bitrate}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("menu.main.youtube_audio", {"format": format, "bitrate": bitrate})

class _MenuMainYoutubeVideoCallable:
    """
    [Callable Props Type] YoutubeVideo
    
    Original template: "YouTube Video → {container} (Max: {resolution})"
    """
    def __call__(self, *, container: str | int, resolution: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            container (str | int): Dynamic value for {container}.
            resolution (str | int): Dynamic value for {resolution}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("menu.main.youtube_video", {"container": container, "resolution": resolution})

class _MenuMainK:
    """
    [Key Type] Main
    """
    title: str = "menu.main.title"
    """[Props Type] Title"""
    subtitle: str = "menu.main.subtitle"
    """[Props Type] Subtitle"""
    choose: str = "menu.main.choose"
    """[Props Type] Choose"""
    youtube_audio: _MenuMainYoutubeAudioCallable = _MenuMainYoutubeAudioCallable()
    """
    [Callable Props Type] YoutubeAudio
    
    Original template: "YouTube Audio/YouTube Music → {format} {bitrate}"
    """
    youtube_video: _MenuMainYoutubeVideoCallable = _MenuMainYoutubeVideoCallable()
    """
    [Callable Props Type] YoutubeVideo
    
    Original template: "YouTube Video → {container} (Max: {resolution})"
    """
    spotify: str = "menu.main.spotify"
    """[Props Type] Spotify"""
    spotify_unavailable: str = "menu.main.spotify_unavailable"
    """[Props Type] SpotifyUnavailable"""
    root_folder: str = "menu.main.root_folder"
    """[Props Type] RootFolder"""
    settings: str = "menu.main.settings"
    """[Props Type] Settings"""
    about: str = "menu.main.about"
    """[Props Type] About"""
    exit: str = "menu.main.exit"
    """[Props Type] Exit"""

class _MenuK:
    """
    [Key Type] Menu
    """
    main: _MenuMainK = _MenuMainK()
    """[Key Type] Main"""
    settings: _MenuSettingsK = _MenuSettingsK()
    """[Key Type] Settings"""
    audio_quality: _MenuAudioQualityK = _MenuAudioQualityK()
    """[Key Type] AudioQuality"""
    video_resolution: _MenuVideoResolutionK = _MenuVideoResolutionK()
    """[Key Type] VideoResolution"""
    video_codec: _MenuVideoCodecK = _MenuVideoCodecK()
    """[Key Type] VideoCodec"""
    language: _MenuLanguageK = _MenuLanguageK()
    """[Key Type] Language"""
    root_folder: _MenuRootFolderK = _MenuRootFolderK()
    """[Key Type] RootFolder"""
    about: _MenuAboutK = _MenuAboutK()
    """[Key Type] About"""

class _CommonChooseInfoCallable:
    """
    [Callable Props Type] ChooseInfo
    
    Original template: "Choose ({info}) > "
    """
    def __call__(self, *, info: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            info (str | int): Dynamic value for {info}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("common.choose_info", {"info": info})

class _CommonConfirmCallable:
    """
    [Callable Props Type] Confirm
    
    Original template: "Are you sure you want to {action}?"
    """
    def __call__(self, *, action: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            action (str | int): Dynamic value for {action}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("common.confirm", {"action": action})

class _CommonSuccessCallable:
    """
    [Callable Props Type] Success
    
    Original template: "{item} successfully {action}"
    """
    def __call__(self, *, item: str | int, action: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            item (str | int): Dynamic value for {item}.
            action (str | int): Dynamic value for {action}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("common.success", {"item": item, "action": action})

class _CommonFailedCallable:
    """
    [Callable Props Type] Failed
    
    Original template: "{item} failed to {action}"
    """
    def __call__(self, *, item: str | int, action: str | int) -> tuple[str, dict]:
        """
        Formats the translation string.
        
        Args:
            item (str | int): Dynamic value for {item}.
            action (str | int): Dynamic value for {action}.
        
        Returns:
            tuple[str, dict]: Key path and formatting dictionary.
        """
        return ("common.failed", {"item": item, "action": action})

class _CommonK:
    """
    [Key Type] Common
    """
    yes: str = "common.yes"
    """[Props Type] Yes"""
    no: str = "common.no"
    """[Props Type] No"""
    back: str = "common.back"
    """[Props Type] Back"""
    choose: str = "common.choose"
    """[Props Type] Choose"""
    choose_info: _CommonChooseInfoCallable = _CommonChooseInfoCallable()
    """
    [Callable Props Type] ChooseInfo
    
    Original template: "Choose ({info}) > "
    """
    zero_enter: str = "common.zero_enter"
    """[Props Type] ZeroEnter"""
    cancel: str = "common.cancel"
    """[Props Type] Cancel"""
    confirm: _CommonConfirmCallable = _CommonConfirmCallable()
    """
    [Callable Props Type] Confirm
    
    Original template: "Are you sure you want to {action}?"
    """
    success: _CommonSuccessCallable = _CommonSuccessCallable()
    """
    [Callable Props Type] Success
    
    Original template: "{item} successfully {action}"
    """
    failed: _CommonFailedCallable = _CommonFailedCallable()
    """
    [Callable Props Type] Failed
    
    Original template: "{item} failed to {action}"
    """
    active: str = "common.active"
    """[Props Type] Active"""
    inactive: str = "common.inactive"
    """[Props Type] Inactive"""
    available: str = "common.available"
    """[Props Type] Available"""
    not_available: str = "common.not_available"
    """[Props Type] NotAvailable"""
    press_enter: str = "common.press_enter"
    """[Props Type] PressEnter"""
    loading: str = "common.loading"
    """[Props Type] Loading"""
    processing: str = "common.processing"
    """[Props Type] Processing"""
    downloading: str = "common.downloading"
    """[Props Type] Downloading"""
    skipped: str = "common.skipped"
    """[Props Type] Skipped"""
    error: str = "common.error"
    """[Props Type] Error"""
    unknown: str = "common.unknown"
    """[Props Type] Unknown"""
    total: str = "common.total"
    """[Props Type] Total"""

class I18nKeysMap:
    """
    [Root Object] I18n Keys Mapping
    
    Provides strongly-typed, auto-completed access to all translation keys.
    - Navigate nested keys using dot notation.
    - If a key requires formatting (e.g., {item}), call it as a function.
    """
    common: _CommonK = _CommonK()
    """[Key Type] Common"""
    menu: _MenuK = _MenuK()
    """[Key Type] Menu"""
    download: _DownloadK = _DownloadK()
    """[Key Type] Download"""
    history: _HistoryK = _HistoryK()
    """[Key Type] History"""
    dependency: _DependencyK = _DependencyK()
    """[Key Type] Dependency"""
    config: _ConfigK = _ConfigK()
    """[Key Type] Config"""
    media: _MediaK = _MediaK()
    """[Key Type] Media"""
    error: _ErrorK = _ErrorK()
    """[Key Type] Error"""
    cli: _CliK = _CliK()
    """[Key Type] Cli"""
    maint: _MaintK = _MaintK()
    """[Key Type] Maint"""
    search: _SearchK = _SearchK()
    """[Key Type] Search"""
    core: _CoreK = _CoreK()
    """[Key Type] Core"""
    dispatch: _DispatchK = _DispatchK()
    """[Key Type] Dispatch"""
    tagger: _TaggerK = _TaggerK()
    """[Key Type] Tagger"""
    net: _NetK = _NetK()
    """[Key Type] Net"""
    spot: _SpotK = _SpotK()
    """[Key Type] Spot"""
    files: _FilesK = _FilesK()
    """[Key Type] Files"""
    daemon: _DaemonK = _DaemonK()
    """[Key Type] Daemon"""
    ui: _UiK = _UiK()
    """[Key Type] Ui"""

Keys = I18nKeysMap()
"""
[Root Object] I18n Keys Mapping

Provides strongly-typed, auto-completed access to all translation keys.
- Navigate nested keys using dot notation.
- If a key requires formatting (e.g., {item}), call it as a function.
"""
