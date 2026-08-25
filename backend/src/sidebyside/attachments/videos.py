"""Video validation helpers for M2 attachments.

The module deliberately keeps ffmpeg/ffprobe behind a small boundary. It does
not decide attachment state; the lifecycle service remains authoritative.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


FFPROBE_TIMEOUT_SECONDS = 10
FFMPEG_TIMEOUT_SECONDS = 45
MAX_POSTER_BYTES = 4 * 1024 * 1024


class VideoRejectedError(Exception):
    """Stable validation failure without leaking parser output."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ProcessedVideo:
    mime_type: str
    width: int
    height: int
    duration_seconds: int
    content: bytes
    poster: bytes | None


def _run(args: list[str], *, timeout: int) -> subprocess.CompletedProcess[bytes]:
    """Run an external parser without shell interpolation."""
    try:
        return subprocess.run(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=timeout,
            shell=False,
        )
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as exc:
        raise VideoRejectedError("VIDEO_PROCESSING_FAILED") from exc


def process(path: Path) -> ProcessedVideo:
    """Validate and sanitize a video file.

    Runtime implementation is intentionally completed in the attachment
    validation slice. This boundary documents the security contract before
    the lifecycle calls it.
    """
    del path
    raise VideoRejectedError("VIDEO_PROCESSING_NOT_IMPLEMENTED")
