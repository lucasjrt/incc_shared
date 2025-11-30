from typing import Any, Optional


class AppError(Exception):
    def __init__(self, code="unexpected_error", message="An unexpected error happened"):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class Conflict(AppError):
    def __init__(self, message="Conflict"):
        super().__init__(code="conflict", message=message)


class InvalidData(AppError):
    def __init__(self, message="Value error"):
        super().__init__(code="value_error", message=message)


class InvalidState(AppError):
    def __init__(self, message="Invalid state"):
        super().__init__(code="invalid_state", message=message)


class NotFound(AppError):
    def __init__(self, message="Not found"):
        super().__init__(code="not_found", message=message)


class PermissionDenied(AppError):
    def __init__(self, message="Permission denied"):
        super().__init__(code="permission_denied", message=message)


class IdempotencyError(AppError):
    metadata: Optional[dict[str, Any]]

    def __init__(self, message="Idempotency error", metadata=None):
        super().__init__(code="idempotency_error", message=message)
        self.metadata = metadata
