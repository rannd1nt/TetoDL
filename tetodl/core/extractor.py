"""
Extractor protocol + registry — plugin per platform.

Each extractor implements :class:`Extractor` and uses ``handles(url)``
to declare which URLs it can process.  At import time every extractor
calls :func:`register_extractor` to add itself to the global registry.

Usage::

    from tetodl.core.extractor import resolve_extractor

    extractor = resolve_extractor("https://youtu.be/...")
    info = extractor.extract(url)
"""

from abc import ABC, abstractmethod

from .models import MediaInfo
from .step import PipelineError


class Extractor(ABC):
    """Base class for URL extractors.

    Subclasses must override :meth:`handles` and :meth:`extract`.
    """

    @staticmethod
    @abstractmethod
    def handles(url: str) -> bool:
        """Return ``True`` if this extractor can handle the given URL."""

    @abstractmethod
    def extract(self, url: str) -> MediaInfo:
        """Extract metadata from the URL.

        Parameters
        ----------
        url : str
            The URL to extract metadata from.

        Returns
        -------
        MediaInfo
            Structured metadata.

        Raises
        ------
        PipelineError
            If extraction fails.
        """


_registry: list[type[Extractor]] = []


def register_extractor(cls: type[Extractor]) -> None:
    """Register an extractor class in the global registry.

    Parameters
    ----------
    cls : type[Extractor]
        Extractor class to register.
    """
    if cls not in _registry:
        _registry.append(cls)


def resolve_extractor(url: str) -> Extractor:
    """Find the first registered extractor that handles the URL.

    Parameters
    ----------
    url : str
        The URL to find an extractor for.

    Returns
    -------
    Extractor
        An instance of the matching extractor.

    Raises
    ------
    PipelineError
        If no registered extractor handles the URL.
    """
    for cls in _registry:
        if cls.handles(url):
            return cls()
    raise PipelineError(f"No extractor found for URL: {url}", "extract")
