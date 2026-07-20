"""
Pipeline step abstraction — template for all pipeline steps.

Each step is a stateless transformation::

    Input T → Output R

Steps are composed by the :class:`MediaPipeline` orchestrator.

See Also
--------
:class:`PipelineStep` : Base class that all steps must subclass.
:class:`PipelineError` : Exception raised when a step fails.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class PipelineError(Exception):
    """
    Exception raised when a pipeline step fails.

    Attributes
    ----------
    message : str
        Human-readable error description.
    step_name : str
        Name of the step that raised the error.
    recoverable : bool
        If True, the pipeline may continue to the next step.

    See Also
    --------
    :class:`PipelineStep` : Steps raise this on failure.
    :func:`MediaPipeline.run` : Catches and handles the exception.

    Examples
    --------
    >>> from tetodl.core.step import PipelineError
    >>> raise PipelineError("yt-dlp not found", "extract", recoverable=False)
    Traceback (most recent call last):
        ...
    tetodl.core.step.PipelineError: [extract] yt-dlp not found

    >>> err = PipelineError("timeout", "download", recoverable=True)
    >>> err.recoverable
    True
    >>> str(err)
    '[download] timeout'
    """

    def __init__(
        self,
        message: str,
        step_name: str = "",
        recoverable: bool = False,
    ) -> None:
        """
        Parameters
        ----------
        message : str
            Human-readable error description.
        step_name : str, optional
            Name of the step that raised the error (default ``""``).
        recoverable : bool, optional
            If True, the pipeline may continue to the next step
            (default ``False``).
        """
        self.step_name = step_name
        self.recoverable = recoverable
        super().__init__(f"[{step_name}] {message}")


class PipelineStep(ABC, Generic[T, R]):
    """
    A single step in the download pipeline.

    Each step transforms input *T* into output *R*.
    Steps are stateless — all dependencies are passed via ``__call__``.

    Subclasses must override :meth:`__call__` with the concrete
    transformation logic.

    Type Parameters
    ----------
    T : TypeVar
        Input type consumed by this step.
    R : TypeVar
        Output type produced by this step.

    See Also
    --------
    :class:`ExtractStep` : Concrete step that extracts metadata.
    :class:`DownloadStep` : Concrete step that downloads media.
    :class:`CoverStep` : Concrete step that processes cover art.
    :class:`ClassifyStep` : Concrete step that classifies content.
    :class:`LyricsStep` : Concrete step that embeds lyrics.
    :class:`FinalizeStep` : Concrete step that finalises output.
    :class:`PipelineError` : Exception that steps raise on failure.
    :func:`MediaPipeline.run` : Orchestrates the sequence of steps.

    Examples
    --------
    A concrete step that uppercases text::

        from tetodl.core.step import PipelineStep

        class UpperStep(PipelineStep[str, str]):
            def __call__(self, data: str) -> str:
                return data.upper()

        step = UpperStep()
        result = step("hello")   # "HELLO"

    Concrete step that operates on :class:`PipelineContext`::

        from tetodl.core.models import PipelineContext
        from tetodl.core.step import PipelineStep

        class MyStep(PipelineStep[PipelineContext, PipelineContext]):
            def __call__(self, ctx: PipelineContext) -> PipelineContext:
                ctx.error = None
                return ctx
    """

    @abstractmethod
    def __call__(self, data: T) -> R:
        """
        Execute the pipeline step.

        Parameters
        ----------
        data : T
            Input data for this step.

        Returns
        -------
        R
            Output data for the next step.

        Raises
        ------
        PipelineError
            If the step fails and the pipeline should stop.

        See Also
        --------
        :meth:`ExtractStep.__call__` : Concrete implementation example.

        Examples
        --------
        Subclasses are called by the pipeline orchestrator::

            from tetodl.core.models import PipelineContext
            from tetodl.pipeline.steps.extract import ExtractStep

            ctx = PipelineContext(config=..., url="https://youtu.be/...")
            step = ExtractStep()
            result = step(ctx)
            # result.media_info is now populated
        """
        ...
