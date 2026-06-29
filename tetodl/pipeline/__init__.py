"""
TetoDL download pipeline.

Orchestrates extraction, classification, download, cover-art processing,
lyrics embedding, and finalization for YouTube media.
Steps live under ``.steps`` and are composed by ``Pipeline``.
"""

from . import steps
