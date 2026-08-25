"""Video validation helpers for M2 attachments.

The lifecycle service remains authoritative. This module only converts an
untrusted video object into a validated, sanitized representation.
"""

from __future__ import annotations

import io
import json
import math
import os
import resource
import signal
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from PIL import Image, UnidentifiedImageError

FFPROBE = "/usr/bin/ffprobe"
FFMPEG = "/usr/bin/ffmpeg"
FFPROBE_TIMEOUT_SECONDS = 10
FFMPEG_TIMEOUT_SECONDS = 45
POSTER_TIMEOUT_SECONDS = 20
PROCESS_ADDRESS_SPACE_BYTES = 768 * 1024 * 1024
MAX_PROBE_OUTPUT_BYTES = 1024 * 1024
MAX_POSTER_BYTES = 4 * 1024 * 1024
POSTER_EDGE = 512

_MP4_BRANDS = {b"isom", b"iso2", b"iso4", b"iso5", b"iso6", b"mp41", b"mp42", b"avc1", b"hvc1", b"hev1"}
_QUICKTIME_BRAND = b"qt  "
_SAFE_FORMAT_TAGS = {"major_brand", "minor_version", "compatible_brands", "encoder"}
_SAFE_STREAM_TAGS = {"language", "handler_name", "vendor_id"}


class VideoRejectedError(Exception):
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
    rotation_degrees: int | None
    poster: bytes | None


@dataclass(frozen=True)
class _Probe:
    mime_type: str
    width: int
    height: int
    duration: float
    captured_at: datetime | None
    rotation_degrees: int | None


@dataclass(frozen=True)
class VideoRule:
    mime_type: str
    max_size: int
    max_edge: int
    max_short_edge: int
    max_duration_seconds: int


def _resource_limiter(cpu_seconds: int, max_file_size: int | None) -> Callable[[], None]:
    def apply() -> None:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 1))
        resource.setrlimit(resource.RLIMIT_AS, (PROCESS_ADDRESS_SPACE_BYTES, PROCESS_ADDRESS_SPACE_BYTES))
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
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
    try:
        process = subprocess.Popen(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE if capture_stdout else subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "HOME": "/nonexistent"},
            shell=False,
            start_new_session=True,
            preexec_fn=_resource_limiter(cpu_seconds, max_file_size),
        )
    except OSError as error:
        raise VideoRejectedError(failure_code) from error

    try:
        stdout, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        raise VideoRejectedError("VIDEO_PROCESSING_TIMEOUT") from error

    if process.returncode != 0:
        raise VideoRejectedError(failure_code)

    data = stdout or b""
    if len(data) > MAX_PROBE_OUTPUT_BYTES:
        raise VideoRejectedError("VIDEO_PROBE_OUTPUT_TOO_LARGE")
    return data


def _detect_container(path: Path) -> str:
    try:
        size = path.stat().st_size
        with path.open("rb") as file:
            head = file.read(4096)
    except OSError as error:
        raise VideoRejectedError("VIDEO_UNREADABLE") from error

    if size < 16 or head[4:8] != b"ftyp":
        raise VideoRejectedError("VIDEO_TYPE_NOT_ALLOWED")

    box_size = int.from_bytes(head[:4], "big")
    if box_size < 16 or box_size > 4096 or box_size > size or box_size > len(head):
        raise VideoRejectedError("VIDEO_TYPE_NOT_ALLOWED")

    major = head[8:12]
    compatibles = {head[index : index + 4] for index in range(16, box_size, 4)}
    if major == _QUICKTIME_BRAND or _QUICKTIME_BRAND in compatibles:
        return "video/quicktime"
    if major in _MP4_BRANDS or compatibles & _MP4_BRANDS:
        return "video/mp4"
    raise VideoRejectedError("VIDEO_TYPE_NOT_ALLOWED")


def _probe(path: Path, expected_mime: str) -> _Probe:
    output = _run(
        [FFPROBE, "-v", "error", "-protocol_whitelist", "file", "-of", "json", "-show_entries", "format=format_name,duration:format_tags=creation_time:stream=index,codec_type,width,height,duration:stream_tags=rotate,creation_time:stream_side_data=rotation", str(path)],
        timeout=FFPROBE_TIMEOUT_SECONDS,
        cpu_seconds=8,
        capture_stdout=True,
        failure_code="VIDEO_UNREADABLE",
    )
    try:
        parsed = json.loads(output)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise VideoRejectedError("VIDEO_UNREADABLE") from error

    if _detect_container(path) != expected_mime:
        raise VideoRejectedError("VIDEO_TYPE_MISMATCH")

    streams = parsed.get("streams") if isinstance(parsed, dict) else None
    fmt = parsed.get("format") if isinstance(parsed, dict) else None
    if not isinstance(streams, list) or not isinstance(fmt, dict):
        raise VideoRejectedError("VIDEO_UNREADABLE")

    video_streams = [stream for stream in streams if isinstance(stream, dict) and stream.get("codec_type") == "video"]
    if len(video_streams) != 1:
        raise VideoRejectedError("VIDEO_STREAMS_NOT_ALLOWED")

    stream = video_streams[0]
    width = stream.get("width")
    height = stream.get("height")
    if not isinstance(width, int) or not isinstance(height, int):
        raise VideoRejectedError("VIDEO_UNREADABLE")

    duration = float(fmt.get("duration") or stream.get("duration") or 0)
    if not math.isfinite(duration) or duration <= 0:
        raise VideoRejectedError("VIDEO_DURATION_INVALID")

    tags = fmt.get("tags") if isinstance(fmt.get("tags"), dict) else {}
    captured = None
    if isinstance(tags.get("creation_time"), str):
        try:
            captured = datetime.fromisoformat(tags["creation_time"].replace("Z", "+00:00"))
        except ValueError:
            captured = None

    return _Probe(expected_mime, width, height, duration, captured, None)


def _enforce(probe: _Probe, rule: VideoRule) -> None:
    if probe.duration > rule.max_duration_seconds:
        raise VideoRejectedError("VIDEO_TOO_LONG")
    long_edge, short_edge = sorted((probe.width, probe.height), reverse=True)
    if long_edge > rule.max_edge or short_edge > rule.max_short_edge:
        raise VideoRejectedError("VIDEO_RESOLUTION_TOO_LARGE")


def _remux(source: Path, target: Path, rule: VideoRule) -> None:
    mux = "mov" if rule.mime_type == "video/quicktime" else "mp4"
    _run(
        [FFMPEG, "-v", "error", "-y", "-protocol_whitelist", "file", "-i", str(source), "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy", "-map_metadata", "-1", "-map_chapters", "-1", "-f", mux, str(target)],
        timeout=FFMPEG_TIMEOUT_SECONDS,
        cpu_seconds=30,
        max_file_size=rule.max_size,
        failure_code="VIDEO_NOT_SANITIZABLE",
    )


def _poster(path: Path) -> bytes | None:
    return None


def process(source: Path, target: Path, rule: VideoRule) -> ProcessedVideo:
    if source.stat().st_size > rule.max_size:
        raise VideoRejectedError("ATTACHMENT_TOO_LARGE")
    before = _probe(source, rule.mime_type)
    _enforce(before, rule)
    _remux(source, target, rule)
    after = _probe(target, rule.mime_type)
    _enforce(after, rule)
    return ProcessedVideo(after.mime_type, after.width, after.height, math.ceil(after.duration), before.captured_at, before.rotation_degrees, _poster(target))
