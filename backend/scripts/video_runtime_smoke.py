"""Production-container smoke test for the real ffmpeg/ffprobe boundary."""

from __future__ import annotations

import io
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from sidebyside.attachments import videos
from sidebyside.attachments.limits import rule_for

LOCATION = "+49.1234+007.1234/"
CREATED_AT = "2026-01-02T03:04:05Z"


def _generate(path: Path, container: str) -> None:
    """Create a tiny deterministic fixture using the production binary itself."""
    subprocess.run(
        [
            videos.FFMPEG,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=64x48:r=10:d=1",
            "-metadata",
            f"location={LOCATION}",
            "-metadata",
            f"com.apple.quicktime.location.ISO6709={LOCATION}",
            "-metadata",
            f"creation_time={CREATED_AT}",
            "-c:v",
            "mpeg4",
            "-an",
            "-threads",
            "1",
            "-f",
            container,
            str(path),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=True,
    )


def _check(mime_type: str, container: str, directory: Path) -> None:
    rule = rule_for(mime_type)
    if rule is None:
        raise AssertionError(f"missing media rule for {mime_type}")

    source = directory / f"source-{container}.bin"
    target = directory / f"clean-{container}.bin"
    _generate(source, container)

    source_bytes = source.read_bytes()
    if LOCATION.encode() not in source_bytes:
        raise AssertionError(f"fixture did not contain location metadata for {mime_type}")

    processed = videos.process(source, target, rule)
    if processed.mime_type != mime_type:
        raise AssertionError(f"wrong detected MIME: {processed.mime_type}")
    if (processed.width, processed.height) != (64, 48):
        raise AssertionError("server-derived dimensions are wrong")
    if processed.duration_seconds != 1:
        raise AssertionError("server-derived duration is wrong")
    if processed.captured_at is None:
        raise AssertionError("captured timestamp was not retained in allowlist payload")
    if processed.poster is None:
        raise AssertionError("poster frame was not generated")

    clean_bytes = target.read_bytes()
    if LOCATION.encode() in clean_bytes:
        raise AssertionError("location metadata survived sanitized video")

    with Image.open(io.BytesIO(processed.poster)) as poster:
        poster.load()
        if max(poster.size) > videos.POSTER_EDGE:
            raise AssertionError("poster exceeds edge limit")
        if len(poster.getexif()) != 0:
            raise AssertionError("poster contains EXIF metadata")

    truncated = directory / f"truncated-{container}.bin"
    truncated.write_bytes(source_bytes[:64])
    rejected = directory / f"rejected-{container}.bin"
    try:
        videos.process(truncated, rejected, rule)
    except videos.VideoRejectedError:
        pass
    else:
        raise AssertionError("truncated video was not rejected")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="sidebyside-video-smoke-") as temp:
        directory = Path(temp)
        _check("video/mp4", "mp4", directory)
        _check("video/quicktime", "mov", directory)
    print("production ffmpeg video smoke: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
