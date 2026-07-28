"""
TetoDL download pipeline.

Orchestrates extraction, classification, download, cover-art processing,
lyrics embedding, and finalization for YouTube media.
Steps live under ``.stages`` and are composed by ``MediaPipeline``.
"""

from tetodl.core.pipeline.runner import MediaPipeline

__all__ = ["MediaPipeline"]
