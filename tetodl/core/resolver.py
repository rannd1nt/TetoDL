"""
ConfigResolver — merge base AppConfig with session overrides.

This is the **only** place that knows how session CLI flags translate
into AppConfig field overrides.  Every other part of the codebase simply
reads the resolved ``AppConfig`` without touching ``RuntimeConfig``.

See Also
--------
:class:`AppConfig` : The resolved configuration model.
:class:`DownloadSession` : Per-request session overrides.
"""

from typing import Any

from .models import AppConfig, DownloadSession


class ConfigResolver:
    """
    Merge a base ``AppConfig`` with per-request ``SessionOverrides``.

    Parameters
    ----------
    base : AppConfig | None
        Base configuration loaded from ``config.json``.
        If ``None`` a default ``AppConfig`` is used.

    Examples
    --------
    >>> from tetodl.core.models import AppConfig
    >>> from tetodl.core.resolver import ConfigResolver
    >>> base = AppConfig()
    >>> resolver = ConfigResolver(base)
    >>> isinstance(resolver, ConfigResolver)
    True

    See Also
    --------
    :meth:`resolve` : Apply session overrides to produce final config.
    :class:`AppConfig` : Target configuration model.
    :class:`DownloadSession` : Source of per-request overrides.
    """

    def __init__(self, base: AppConfig | None = None) -> None:
        """Initialise with an optional base AppConfig."""
        self._base = base or AppConfig()

    def resolve(self, session: DownloadSession) -> AppConfig:
        """
        Produce a new ``AppConfig`` with all session overrides applied.

        Maps CLI flags from a :class:`DownloadSession` onto
        :class:`AppConfig` fields such as output paths, media format,
        cover-art behaviour and feature toggles.

        Parameters
        ----------
        session : DownloadSession
            Parsed CLI or daemon request.

        Returns
        -------
        AppConfig
            Merged configuration — never mutates the base.

        Examples
        --------
        >>> from tetodl.core.models import AppConfig, DownloadSession
        >>> from tetodl.core.resolver import ConfigResolver
        >>> base = AppConfig()
        >>> resolver = ConfigResolver(base)
        >>> session = DownloadSession()
        >>> cfg = resolver.resolve(session)
        >>> isinstance(cfg, AppConfig)
        True

        See Also
        --------
        :class:`DownloadSession` : Source of per-request overrides.
        :class:`AppConfig` : Target model with all resolved fields.
        :meth:`ConfigResolver.__init__` : Construct the resolver.
        """
        o = session.merged_overrides
        updates: dict[str, Any] = {'simple_mode': True}

        # --- library paths ---
        if o.output_path:
            updates['music_root'] = o.output_path
            updates['video_root'] = o.output_path
            updates['thumbnail_root'] = o.output_path
        if o.group_folder:
            updates['group_mode'] = o.group_folder

        # --- media format ---
        if o.format:
            target = 'video_container' if session.media_type == 'video' else 'audio_quality'
            updates[target] = o.format
        if o.codec:
            updates['video_codec'] = o.codec
        if o.resolution:
            updates['max_video_resolution'] = o.resolution

        # --- cover art ---
        if o.no_cover:
            updates['no_cover_mode'] = True
            updates['smart_cover_mode'] = False
        elif o.smart_cover:
            updates['smart_cover_mode'] = True
            updates['no_cover_mode'] = False
        if o.force_crop:
            updates['force_crop'] = True

        # --- feature toggles ---
        if o.lyrics:
            updates['lyrics_mode'] = True
        if o.romaji:
            updates['romaji_mode'] = True
        if o.zip:
            updates['zip_mode'] = True
        if o.m3u:
            updates['create_m3u'] = True
            if not self._base.group_mode and not o.group_folder:
                updates['group_mode'] = True
        if o.quiet:
            updates['quiet'] = True
        if o.async_mode:
            updates['async_mode'] = True

        return self._base.model_copy(update=updates)
