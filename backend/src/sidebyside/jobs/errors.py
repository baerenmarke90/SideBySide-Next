"""Controlled background-job outcomes that may safely retain state."""

from __future__ import annotations


class RetryableJobError(Exception):
    """Request queue backoff without rolling back safe handler metadata."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code
