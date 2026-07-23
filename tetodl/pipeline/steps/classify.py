"""
ClassifyStep — determine whether extracted media is a playlist,
and optionally check the file registry for existing downloads.
"""


from tetodl.utils.tracer import trace, traced

from ...core.models import Classification, DownloadResult, MediaInfo, PipelineContext
from ...core.registry import registry
from ...core.step import PipelineStep
from ...utils.console import console
from ...utils.i18n_keys import Keys


class ClassifyStep(PipelineStep[PipelineContext, PipelineContext]):
    """Check whether the extracted :class:`MediaInfo` represents a playlist,
    and optionally short-circuit when an existing download is found in the
    registry.

    When ``ctx.media_info`` indicates a playlist (``is_playlist`` or
    ``entries``) the step sets ``classification.is_playlist`` and returns
    immediately without checking the registry.

    See Also
    --------
    :class:`PipelineContext` : Context carrying media info and config.
    :class:`Classification` : Result model for this step.
    :class:`DownloadStep` : Next step in the pipeline.

    Example
    -------
    >>> step = ClassifyStep(skip_existing=True)
    >>> ctx = PipelineContext(media_info=some_media_info)
    >>> result = step(ctx)
    >>> result.classification is not None
    True
    """

    def __init__(self, skip_existing: bool = True) -> None:
        """Configure the classify step.

        Parameters
        ----------
        skip_existing : bool
            When ``True``, check the file registry for existing downloads
            and short-circuit if a match is found.

        Returns
        -------
        None

        Example
        -------
        >>> step = ClassifyStep(skip_existing=True)
        """
        self._skip_existing = skip_existing

    @trace
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        """Classify the media info in the pipeline context.

        If ``ctx.media_info`` is ``None`` the context is returned
        unchanged.  For playlists a simple :class:`Classification` with
        ``is_playlist=True`` is set.  For single items, when
        ``skip_existing`` is enabled, the registry is checked for
        previously downloaded files.

        Parameters
        ----------
        ctx : PipelineContext
            Pipeline context with ``media_info`` populated by
            :class:`ExtractStep`.

        Returns
        -------
        PipelineContext
            Context with ``classification`` populated.

        Raises
        ------
        None
            This step does not raise exceptions; all outcomes are
            communicated via the pipeline context.

        See Also
        --------
        :class:`Classification` : Result model with optional short-circuit.
        :meth:`_check_registry` : Registry lookup logic.

        Example
        -------
        >>> step = ClassifyStep()
        >>> ctx = PipelineContext(media_info=MediaInfo(id="abc123"))
        >>> result = step(ctx)
        >>> result.classification.is_playlist
        False
        """
        if not ctx.media_info:
            return ctx

        info = ctx.media_info
        is_playlist = info.is_playlist or bool(info.entries)

        if is_playlist:
            ctx.classification = Classification(is_playlist=True)
            return ctx

        # Audio always skips existing; video only when skip_existing_files is set
        should_skip = ctx.media_type == "audio" or ctx.config.skip_existing_files
        if self._skip_existing and should_skip:
            existing = self._check_registry(info, ctx)
            if existing is not None:
                ctx.classification = Classification(existing_result=existing)
                return ctx

        ctx.classification = Classification()
        return ctx

    def _check_registry(
        self,
        info: MediaInfo,
        ctx: PipelineContext,
    ) -> DownloadResult | None:
        """Check the file registry for an existing download by video ID."""
        video_id = info.id
        if not video_id:
            return None

        exists, metadata = registry.check_existing(
            video_id,
            ctx.media_type,
            ctx.target_dir,
        )
        if not exists:
            return None

        with traced('found in registry'):
            console.ok(Keys.download.youtube.file_exists)
            if metadata:
                console.warn(Keys.download.youtube.exists_title(
                    title=metadata.get("title", ""),
                ))
                console.warn(Keys.download.youtube.exists_path(
                    path=metadata.get("file_path", ""),
                ))
            return DownloadResult(
                success=True,
                file_path=metadata.get("file_path") if metadata else None,
                skipped=True,
            )
