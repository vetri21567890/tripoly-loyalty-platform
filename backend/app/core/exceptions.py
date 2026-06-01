from typing import Any


class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", details: dict | None = None):
        super().__init__("NOT_FOUND", message, 404, details)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Unauthorized", details: dict | None = None):
        super().__init__("AUTH_REQUIRED", message, 401, details)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden", details: dict | None = None):
        super().__init__("FORBIDDEN", message, 403, details)


class ConflictError(AppException):
    def __init__(self, message: str = "Conflict", code: str = "CONFLICT", details: dict | None = None):
        super().__init__(code, message, 409, details)


class ValidationError(AppException):
    def __init__(self, message: str = "Validation error", details: dict | None = None):
        super().__init__("VALIDATION_ERROR", message, 400, details)


class InsufficientCoinsError(AppException):
    def __init__(self, message: str = "Insufficient Tripoly Coins"):
        super().__init__("INSUFFICIENT_COINS", message, 409)


class RewardUnavailableError(AppException):
    def __init__(self, message: str = "Reward is unavailable"):
        super().__init__("REWARD_UNAVAILABLE", message, 409)


class RateLimitedError(AppException):
    def __init__(self, message: str = "Too many requests"):
        super().__init__("RATE_LIMITED", message, 429)
