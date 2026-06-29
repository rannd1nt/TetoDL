"""
Pipeline step abstraction — template for all pipeline steps.

Each step is a stateless transformation:
    Input T → Output R

Steps are composed by the Pipeline orchestrator.
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
    """

    def __init__(
        self,
        message: str,
        step_name: str = "",
        recoverable: bool = False,
    ) -> None:
        self.step_name = step_name
        self.recoverable = recoverable
        super().__init__(f"[{step_name}] {message}")


class PipelineStep(ABC, Generic[T, R]):
    """
    A single step in the download pipeline.

    Each step transforms input *T* into output *R*.
    Steps are stateless — all dependencies are passed via ``__call__``.

    Type Parameters
    ----------
    T : TypeVar
        Input type consumed by this step.
    R : TypeVar
        Output type produced by this step.
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
        """
        ...
