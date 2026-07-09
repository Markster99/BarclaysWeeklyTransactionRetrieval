class BarclaysRetrievalError(RuntimeError):
    """Base exception for retrieval workflow errors."""


class ConfigurationError(BarclaysRetrievalError):
    """Raised when runtime configuration is incomplete or invalid."""


class AuthenticationError(BarclaysRetrievalError):
    """Raised when a token cannot be obtained or used."""


class BarclaysApiError(BarclaysRetrievalError):
    """Raised when the Barclays API returns an error or malformed response."""
