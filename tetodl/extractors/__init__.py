"""
Extractor plugins — each submodule auto-registers on import.
"""

from .search import SearchExtractor  # noqa: F401
from .spotify import SpotifyExtractor  # noqa: F401
from .youtube import YouTubeExtractor  # noqa: F401
