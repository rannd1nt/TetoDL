"""
Extractor plugins — each submodule auto-registers on import.
"""

from .youtube import YouTubeExtractor  # noqa: F401
from .search import SearchExtractor  # noqa: F401
from .spotify import SpotifyExtractor  # noqa: F401
