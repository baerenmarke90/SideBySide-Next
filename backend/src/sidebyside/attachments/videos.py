"""Video validation and sanitization for M2 attachments.

The lifecycle service remains authoritative. This module only converts an
untrusted MP4/QuickTime object into a validated, sanitized representation.
All client-controlled bytes are treated as hostile.
"""

from __future__ import annotations

import contextlib
import io
import json
import math
import os
import resource
import signal
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from sidebyside.attachments.limits import MediaRule

FFPROBE = "/usr/bin/ffprobe"
FFMPEG = "/usr/bin/ffmpeg"
FFPROBE_TIMEOUT_SECONDS = 10
FFMPEG_TIMEOUT_SECONDS = 45
POSTER_TIMEOUT_SECONDS = 20
PROCESS_ADDRESS_SPACE_BYTES = 768 * 1024 * 1024
MAX_PROBE_OUTPUT_BYTES = 1024 * 1024
MAX_POSTER_BYTES = 4 * 1024 * 1024
POSTER_EDGE = 512

_MP4_BRANDS = {
    b"isom",
    b"iso2",
    b"iso4",
    b"iso5",
    b"iso6",
    b"mp41",
    b"mp42",
    b"avc1",
    b"hvc1",
    b"hev1",
    b"M4V ",
}
_QUICKTIME_BRAND = b"qt  "
_SAFE_FORMAT_TAGS = {"major_brand", "minor_version", "compatible_brands", "encoder"}
_SAFE_STREAM_TAGS = {"language", "handler_name", "vendor_id"}
_SAFE_DISPLAY_MATRIX_KEYS = {"side_data_type", "displaymatrix", "rotation"}


class VideoRejectedError(Exception):
    """Stable failure code without ffmpeg/ffprobe output."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ProcessedVideo:
    mime_type: str
    width: int
    height: int
    duration_seconds: int
    captured_at: datetime | None
    orientation: int | None
    size: int
    poster: bytes | None


@dataclass(frozen=True)
class _Probe:
    mime_type: str
    width: int
    height: int
    duration: float
    captured_at: datetime | None
    orientation: int | None
    document: dict[str, Any]


def _resource_limiter(cpu_seconds: int, max_file_size: int | None) -> Callable[[], None]:
    """Apply hard Linux limits in the child immediately before exec."""

    def apply() -> None:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 1))
        resource.setrlimit(
            resource.RLIMIT_AS,
            (PROCESS_ADDRESS_SPACE_BYTES, PROCESS_ADDRESS_SPACE_BYTES),
        )
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
        if hasattr(resource, "RLIMIT_NPROC"):
            resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
        if max_file_size is not None:
            resource.setrlimit(resource.RLIMIT_FSIZE, (max_file_size, max_file_size))

    return apply


def _run(
    args: list[str],
    *,
    timeout: int,
    cpu_seconds: int,
    max_file_size: int | None = None,
    capture_stdout: bool = False,
    failure_code: str = "VIDEO_PROCESSING_FAILED",
) -> bytes:
    """Run one parser step without a shell and kill its whole group on timeout."""
    try:
        process = subprocess.Popen(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE if capture_stdout else subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={
                "PATH": "/usr/bin:/bin",
                "LANG": "C",
                "LC_ALL": "C",
                "HOME": "/nonexistent",
            },
            shell=False,
            start_new_session=True,
            preexec_fn=_resource_limiter(cpu_seconds, max_file_size),
        )
    except OSError as error:
        raise VideoRejectedError(failure_code) from error

    try:
        stdout, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise VideoRejectedError("VIDEO_PROCESSING_TIMEOUT") from error

    if process.returncode != 0:
        raise VideoRejectedError(failure_code)

    data = stdout or b""
    if len(data) > MAX_PROBE_OUTPUT_BYTES:
        raise VideoRejectedError("VIDEO_PROBE_OUTPUT_TOO_LARGE")
    return data


def _detect_container(path: Path) -> str:
    """Recognize only the two ISO-BMFF families allowed by M2-D04."""
    try:
        size = path.stat().st_size
        with path.open("rb") as file:
            head = file.read(4096)
    except OSError as error:
        raise VideoRejectedError("VIDEO_UNREADABLE") from error

    if size < 16 or len(head) < 16 or head[4:8] != b"ftyp":
        raise VideoRejectedError("VIDEO_TYPE_NOT_ALLOWED")

    box_size = int.from_bytes(head[:4], "big")
    if box_size < 16 or box_size > 4096 or box_size > size or box_size > len(head):
        raise VideoRejectedError("VIDEO_TYPE_NOT_ALLOWED")
    if (box_size - 16) % 4:
        raise VideoRejectedError("VIDEO_TYPE_NOT_ALLOWED")

    major = head[8:12]
    compatibles = {head[index : index + 4] for index in range(16, box_size, 4)}
    if major == _QUICKTIME_BRAND or _QUICKTIME_BRAND in compatibles:
        return "video/quicktime"
    if major in _MP4_BRANDS or compatibles & _MP4_BRANDS:
        return "video/mp4"
    raise VideoRejectedError("VIDEO_TYPE_NOT_ALLOWED")


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def _orientation_from_rotation(value: object) -> int | None:
    if value is None:
        return None
    try:
        rotation = float(value)
    except (TypeError, ValueError):
        raise VideoRejectedError("VIDEO_ORIENTATION_INVALID") from None
    if not math.isfinite(rotation):
        raise VideoRejectedError("VIDEO_ORIENTATION_INVALID")
    rounded = round(rotation)
    if abs(rotation - rounded) > 0.01:
        raise VideoRejectedError("VIDEO_ORIENTATION_INVALID")
    normalized = int(rounded) % 360
    # ffprobe reports positive display rotation counter-clockwise. EXIF 8 is
    # 90 degrees CCW, EXIF 6 is 90 degrees CW.
    mapping = {0: 1, 90: 8, 180: 3, 270: 6}
    orientation = mapping.get(normalized)
    if orientation is None:
        raise VideoRejectedError("VIDEO_ORIENTATION_INVALID")
    return orientation


def _probe_document(path: Path, *, include_metadata: bool) -> dict[str, Any]:
    entries = (
        "format=format_name,duration:format_tags:"
        "stream=index,codec_type,width,height,duration:stream_tags:stream_side_data"
        if include_metadata
        else (
            "format=format_name,duration:format_tags=creation_time:"
            "stream=index,codec_type,width,height,duration:"
            "stream_tags=rotate,creation_time:stream_side_data=rotation"
        )
    )
    output = _run(
        [
            FFPROBE,
            "-v",
            "error",
            "-protocol_whitelist",
            "file",
            "-of",
            "json",
            "-show_entries",
            entries,
            str(path),
        ],
        timeout=FFPROBE_TIMEOUT_SECONDS,
        cpu_seconds=8,
        capture_stdout=True,
        failure_code="VIDEO_UNREADABLE",
    )
    try:
        parsed = json.loads(output)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise VideoRejectedError("VIDEO_UNREADABLE") from error
    if not isinstance(parsed, dict):
        raise VideoRejectedError("VIDEO_UNREADABLE")
    return parsed


def _probe(path: Path, expected_mime: str, *, include_metadata: bool = False) -> _Probe:
    document = _probe_document(path, include_metadata=include_metadata)

    if _detect_container(path) != expected_mime:
        raise VideoRejectedError("VIDEO_TYPE_MISMATCH")

    streams = document.get("streams")
    fmt = document.get("format")
    if not isinstance(streams, list) or not isinstance(fmt, dict):
        raise VideoRejectedError("VIDEO_UNREADABLE")

    format_name = fmt.get("format_name")
    if (
        not isinstance(format_name, str)
        or "mp4" not in format_name
        or "mov" not in format_name
    ):
        raise VideoRejectedError("VIDEO_TYPE_NOT_ALLOWED")

    video_streams = [
        stream
        for stream in streams
        if isinstance(stream, dict) and stream.get("codec_type") == "video"
    ]
    if len(video_streams) != 1:
        raise VideoRejectedError("VIDEO_STREAMS_NOT_ALLOWED")

    stream = video_streams[0]
    width = stream.get("width")
    height = stream.get("height")
    if (
        not isinstance(width, int)
        or not isinstance(height, int)
        or width <= 0
        or height <= 0
    ):
        raise VideoRejectedError("VIDEO_DIMENSIONS_INVALID")

    raw_duration = fmt.get("duration") or stream.get("duration") or 0
    try:
        duration = float(raw_duration)
    except (TypeError, ValueError) as error:
        raise VideoRejectedError("VIDEO_DURATION_INVALID") from error
    if not math.isfinite(duration) or duration <= 0:
        raise VideoRejectedError("VIDEO_DURATION_INVALID")

    format_tags = fmt.get("tags") if isinstance(fmt.get("tags"), dict) else {}
    stream_tags = stream.get("tags") if isinstance(stream.get("tags"), dict) else {}
    captured_at = _parse_datetime(format_tags.get("creation_time")) or _parse_datetime(
        stream_tags.get("creation_time")
    )

    rotation: object = stream_tags.get("rotate")
    side_data = stream.get("side_data_list")
    if isinstance(side_data, list):
        for item in side_data:
            if isinstance(item, dict) and item.get("rotation") is not None:
                rotation = item.get("rotation")
                break

    return _Probe(
        mime_type=expected_mime,
        width=width,
        height=height,
        duration=duration,
        captured_at=captured_at,
        orientation=_orientation_from_rotation(rotation),
        document=document,
    )


def _enforce(probe: _Probe, rule: MediaRule) -> None:
    if (
        rule.max_duration_seconds is None
        or rule.max_edge is None
        or rule.max_short_edge is None
    ):
        raise VideoRejectedError("VIDEO_RULE_INVALID")
    if probe.duration > rule.max_duration_seconds:
        raise VideoRejectedError("VIDEO_TOO_LONG")
    long_edge, short_edge = sorted((probe.width, probe.height), reverse=True)
    if long_edge > rule.max_edge or short_edge > rule.max_short_edge:
        raise VideoRejectedError("VIDEO_RESOLUTION_TOO_LARGE")


def _remux(source: Path, target: Path, rule: MediaRule) -> None:
    mux = "mov" if rule.mime_type == "video/quicktime" else "mp4"
    args = [
        FFMPEG,
        "-nostdin",
        "-hide_banner",
        "-v",
        "error",
        "-xerror",
        "-y",
        "-protocol_whitelist",
        "file",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-map",
        "0:a:0?",
        "-c",
        "copy",
        "-map_metadata",
        "-1",
        "-map_chapters",
        "-1",
        "-threads",
        "1",
    ]
    if mux == "mp4":
        args.extend(["-movflags", "+faststart"])
    args.extend(["-f", mux, str(target)])
    _run(
        args,
        timeout=FFMPEG_TIMEOUT_SECONDS,
        cpu_seconds=30,
        max_file_size=rule.max_size,
        failure_code="VIDEO_NOT_SANITIZABLE",
    )


def _validate_sanitized_metadata(probe: _Probe) -> None:
    """Allow only muxer/stream bookkeeping generated by the clean container."""
    fmt = probe.document.get("format")
    streams = probe.document.get("streams")
    if not isinstance(fmt, dict) or not isinstance(streams, list):
        raise VideoRejectedError("VIDEO_METADATA_UNSAFE")

    tags = fmt.get("tags")
    if tags is not None and (
        not isinstance(tags, dict)
        or any(str(key).lower() not in _SAFE_FORMAT_TAGS for key in tags)
    ):
        raise VideoRejectedError("VIDEO_METADATA_UNSAFE")

    video_count = 0
    audio_count = 0
    for stream in streams:
        if not isinstance(stream, dict):
            raise VideoRejectedError("VIDEO_METADATA_UNSAFE")
        codec_type = stream.get("codec_type")
        if codec_type == "video":
            video_count += 1
        elif codec_type == "audio":
            audio_count += 1
        else:
            raise VideoRejectedError("VIDEO_METADATA_UNSAFE")

        stream_tags = stream.get("tags")
        if stream_tags is not None and (
            not isinstance(stream_tags, dict)
            or any(str(key).lower() not in _SAFE_STREAM_TAGS for key in stream_tags)
        ):
            raise VideoRejectedError("VIDEO_METADATA_UNSAFE")

        side_data = stream.get("side_data_list")
        if side_data is not None:
            if codec_type != "video" or not isinstance(side_data, list):
                raise VideoRejectedError("VIDEO_METADATA_UNSAFE")
            for item in side_data:
                if (
                    not isinstance(item, dict)
                    or item.get("side_data_type") != "Display Matrix"
                    or any(str(key) not in _SAFE_DISPLAY_MATRIX_KEYS for key in item)
                ):
                    raise VideoRejectedError("VIDEO_METADATA_UNSAFE")
                _orientation_from_rotation(item.get("rotation"))

    if video_count != 1 or audio_count > 1:
        raise VideoRejectedError("VIDEO_STREAMS_NOT_ALLOWED")


def _poster(path: Path) -> bytes | None:
    """Create one metadata-free JPEG. Failure is deliberately non-fatal."""
    raw = path.with_name("poster-frame.raw.jpg")
    try:
        raw.unlink(missing_ok=True)
        _run(
            [
                FFMPEG,
                "-nostdin",
                "-hide_banner",
                "-v",
                "error",
                "-xerror",
                "-y",
                "-protocol_whitelist",
                "file",
                "-i",
                str(path),
                "-frames:v",
                "1",
                "-vf",
                f"scale={POSTER_EDGE}:{POSTER_EDGE}:force_original_aspect_ratio=decrease",
                "-threads",
                "1",
                "-filter_threads",
                "1",
                "-q:v",
                "3",
                "-f",
                "image2",
                str(raw),
            ],
            timeout=POSTER_TIMEOUT_SECONDS,
            cpu_seconds=12,
            max_file_size=MAX_POSTER_BYTES,
            failure_code="VIDEO_POSTER_FAILED",
        )
        if (
            not raw.is_file()
            or raw.stat().st_size <= 0
            or raw.stat().st_size > MAX_POSTER_BYTES
        ):
            return None

        with Image.open(raw) as decoded:
            decoded.load()
            if max(decoded.size) > POSTER_EDGE:
                return None
            rgb = decoded.convert("RGB")
            clean = Image.new("RGB", rgb.size)
            clean.paste(rgb)
            output = io.BytesIO()
            clean.save(output, format="JPEG", quality=82)
            result = output.getvalue()
            if not result or len(result) > MAX_POSTER_BYTES:
                return None
            return result
    except (VideoRejectedError, OSError, ValueError, UnidentifiedImageError):
        return None
    finally:
        with contextlib.suppress(OSError):
            raw.unlink(missing_ok=True)


def process(source: Path, target: Path, rule: MediaRule) -> ProcessedVideo:
    """Validate, metadata-strip and re-probe one MP4/QuickTime file."""
    try:
        source_size = source.stat().st_size
    except OSError as error:
        raise VideoRejectedError("VIDEO_UNREADABLE") from error
    if source_size <= 0:
        raise VideoRejectedError("VIDEO_UNREADABLE")
    if source_size > rule.max_size:
        raise VideoRejectedError("ATTACHMENT_TOO_LARGE")

    before = _probe(source, rule.mime_type)
    _enforce(before, rule)
    _remux(source, target, rule)

    try:
        target_size = target.stat().st_size
    except OSError as error:
        raise VideoRejectedError("VIDEO_NOT_SANITIZABLE") from error
    if target_size <= 0 or target_size > rule.max_size:
        raise VideoRejectedError("VIDEO_NOT_SANITIZABLE")

    after = _probe(target, rule.mime_type, include_metadata=True)
    _enforce(after, rule)
    _validate_sanitized_metadata(after)
    if abs(after.duration - before.duration) > 0.5:
        raise VideoRejectedError("VIDEO_DURATION_CHANGED")

    return ProcessedVideo(
        mime_type=after.mime_type,
        width=after.width,
        height=after.height,
        duration_seconds=math.ceil(after.duration),
        captured_at=before.captured_at,
        orientation=before.orientation,
        size=target_size,
        poster=_poster(target),
    )
