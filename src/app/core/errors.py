from __future__ import annotations


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 500, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class DependencyUnavailableError(AppError):
    pass


class UpstreamRequestError(AppError):
    pass
