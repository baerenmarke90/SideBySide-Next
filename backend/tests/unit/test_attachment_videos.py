"""Fail-closed Regeln des M2-Video-Slices ohne Host-ffmpeg-Abhaengigkeit."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from sidebyside.attachments import videos
from sidebyside.attachments.limits import rule_for


def _rule():  # type: ignore[no-untyped-def]
    rule = rule_for("video/mp4")
    assert rule is not None
    return rule


def _bmff(major: bytes, *compatible: bytes) -> bytes:
    box_size = 16 + 4 * len(compatible)
    return (
        box_size.to_bytes(4, "big")
        + b"ftyp"
        + major
        + b"\x00\x00\x00\x00"
        + b"".join(compatible)
        + b"\x00" * 32
    )


def _probe(
    *,
    width: int = 3840,
    height: int = 2160,
    duration: float = 180.0,
    document: dict[str, object] | None = None,
) -> videos._Probe:
    return videos._Probe(  # noqa: SLF001 - private boundary is the subject under test
        mime_type="video/mp4",
        width=width,
        height=height,
        duration=duration,
        captured_at=None,
        orientation=1,
        document=document or {},
    )


def test_magic_distinguishes_mp4_and_quicktime(tmp_path: Path) -> None:
    mp4 = tmp_path / "mp4.bin"
    mov = tmp_path / "mov.bin"
    mp4.write_bytes(_bmff(b"isom", b"mp42"))
    mov.write_bytes(_bmff(b"qt  "))

    assert videos._detect_container(mp4) == "video/mp4"  # noqa: SLF001
    assert videos._detect_container(mov) == "video/quicktime"  # noqa: SLF001


def test_unknown_iso_bmff_brand_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "unknown.bin"
    path.write_bytes(_bmff(b"3gp5"))

    with pytest.raises(videos.VideoRejectedError, match="VIDEO_TYPE_NOT_ALLOWED"):
        videos._detect_container(path)  # noqa: SLF001


def test_duration_and_orientation_independent_resolution_limits() -> None:
    rule = _rule()
    videos._enforce(_probe(), rule)  # noqa: SLF001
    videos._enforce(_probe(width=2160, height=3840), rule)  # noqa: SLF001

    with pytest.raises(videos.VideoRejectedError, match="VIDEO_TOO_LONG"):
        videos._enforce(_probe(duration=180.001), rule)  # noqa: SLF001
    with pytest.raises(videos.VideoRejectedError, match="VIDEO_RESOLUTION_TOO_LARGE"):
        videos._enforce(_probe(width=3841), rule)  # noqa: SLF001
    with pytest.raises(videos.VideoRejectedError, match="VIDEO_RESOLUTION_TOO_LARGE"):
        videos._enforce(_probe(width=3840, height=2161), rule)  # noqa: SLF001


def test_location_metadata_after_remux_is_rejected() -> None:
    document: dict[str, object] = {
        "format": {
            "tags": {
                "major_brand": "isom",
                "com.apple.quicktime.location.ISO6709": "+49.0000+007.0000/",
            }
        },
        "streams": [
            {
                "codec_type": "video",
                "tags": {"language": "und", "handler_name": "VideoHandler"},
            }
        ],
    }

    with pytest.raises(videos.VideoRejectedError, match="VIDEO_METADATA_UNSAFE"):
        videos._validate_sanitized_metadata(_probe(document=document))  # noqa: SLF001


def test_only_video_and_one_optional_audio_stream_survive() -> None:
    document: dict[str, object] = {
        "format": {"tags": {"major_brand": "isom", "encoder": "Lavf"}},
        "streams": [
            {
                "codec_type": "video",
                "tags": {"language": "und", "handler_name": "VideoHandler", "vendor_id": "FFMP"},
            },
            {
                "codec_type": "audio",
                "tags": {"language": "und", "handler_name": "SoundHandler", "vendor_id": "FFMP"},
            },
        ],
    }
    videos._validate_sanitized_metadata(_probe(document=document))  # noqa: SLF001

    document["streams"] = [
        {"codec_type": "video"},
        {"codec_type": "subtitle"},
    ]
    with pytest.raises(videos.VideoRejectedError, match="VIDEO_METADATA_UNSAFE"):
        videos._validate_sanitized_metadata(_probe(document=document))  # noqa: SLF001


def test_poster_is_rebuilt_without_exif(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    video = tmp_path / "sanitized.mp4"
    video.write_bytes(b"placeholder")

    def fake_run(args: list[str], **_: object) -> bytes:
        output_path = Path(args[-1])
        image = Image.new("RGB", (32, 24), (10, 20, 30))
        exif = Image.Exif()
        exif[0x010F] = "Secret Camera"
        image.save(output_path, "JPEG", exif=exif.tobytes())
        return b""

    monkeypatch.setattr(videos, "_run", fake_run)
    poster = videos._poster(video)  # noqa: SLF001

    assert poster is not None
    assert b"Secret Camera" not in poster
    with Image.open(io.BytesIO(poster)) as decoded:
        assert decoded.size == (32, 24)
        assert len(decoded.getexif()) == 0
