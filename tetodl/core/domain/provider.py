"""UI provider protocol — domain-level abstraction for UI rendering."""

from typing import Protocol


class UIProvider(Protocol):
    """Interface for all UI rendering strategies."""

    def header(self) -> None: ...

    def clear(self) -> None: ...

    def wait_and_clear_prompt(self, msg: str | None = None) -> None: ...


class NullUI:
    """Silent provider — no output, no interaction."""

    @staticmethod
    def header() -> None: pass

    @staticmethod
    def clear() -> None: pass

    @staticmethod
    def wait_and_clear_prompt(msg: str | None = None) -> None: pass
