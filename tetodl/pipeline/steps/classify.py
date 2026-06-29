"""
ClassifyStep — determine whether the URL is a single video or a playlist,
and optionally check the file registry for existing downloads.
"""

from dataclasses import dataclass
from typing import Optional

from ...core.models import MediaInfo, DownloadResult
from ...core.step import PipelineStep


@dataclass
class Classification:
    """Result of classifying a :class:`MediaInfo`.

    Attributes
    ----------
    is_playlist : bool
        True if the resolved content is a playlist.
    existing_result : DownloadResult | None
        If a matching file was found in the registry, a ``DownloadResult``
        with ``skipped=True`` is returned so the pipeline can short-circuit.
    """

    is_playlist: bool = False
    existing_result: Optional[DownloadResult] = None


class ClassifyStep(PipelineStep[MediaInfo, Classification]):
    """Determine whether the extracted ``MediaInfo`` represents a single
    video or a playlist, and optionally short-circuit when an existing
    download is found in the registry.

    The registry check mirrors the logic in the original ``handlers.py``:
    only single videos are checked (playlists are always processed).
    """

    def __init__(self, skip_existing: bool = True) -> None:
        """Configure the classify step.

        Parameters
        ----------
        skip_existing : bool
            When ``True``, check the file registry for existing downloads
            and short-circuit if a match is found.
        """
        self._skip_existing = skip_existing

    def __call__(self, info: MediaInfo) -> Classification:
        """Classify the media info.

        Parameters
        ----------
        info : MediaInfo
            Extracted media metadata.

        Returns
        -------
        Classification
            Classification result.
        """
        if info.is_playlist or bool(info.entries):
            return Classification(is_playlist=True)

        if self._skip_existing:
            result = self._check_registry(info)
            if result is not None:
                return Classification(existing_result=result)

        return Classification()

    def _check_registry(self, info: MediaInfo) -> Optional[DownloadResult]:
        """Check the file registry for an existing download.

        This is a stub — the full implementation will integrate with
        ``core.registry`` once the old code path is retired.
        """
        # TODO: wire up core.registry.check_existing()
        return None
