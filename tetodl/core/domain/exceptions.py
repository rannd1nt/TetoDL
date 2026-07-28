"""Application exception hierarchy."""


class TetodlError(Exception):
    """Base exception for all TetoDL errors."""


class ConfigError(TetodlError):
    """Configuration-related errors."""


class CacheError(TetodlError):
    """Cache-related errors."""


class HistoryError(TetodlError):
    """History-related errors."""


class RegistryError(TetodlError):
    """Registry-related errors."""


class DependencyError(TetodlError):
    """Dependency verification errors."""
