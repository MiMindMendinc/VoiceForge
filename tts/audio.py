"""Bounded sentence splitting and optional system-FFmpeg audio encoding."""
from __future__ import annotations

import io
import re
import shutil
import subprocess

import soundfile as sf


class EncoderError(Exception):
    """An optional encoder is unavailable or failed."""


def split_sentences(text: str) -> list[str]:
    # Deliberately simple English punctuation heuristic, not a linguistic parser.
    return [part for part in re.split(r'(?<=[.!?])\s+', text.strip()) if part]


def require_encoder(fmt: str) -> None:
    if fmt not in {"wav", "mp3", "opus"}:
        raise EncoderError("Unsupported audio format.")
    if fmt != "wav" and shutil.which("ffmpeg") is None:
        raise EncoderError("MP3/Opus require system FFmpeg with libmp3lame/libopus. Use WAV instead.")


def encode_audio(audio, sample_rate: int, fmt: str = "wav") -> tuple[bytes, str]:
    require_encoder(fmt)
    buffer = io.BytesIO()
    sf.write(buffer, audio, sample_rate, format="WAV", subtype="PCM_16")
    if fmt == "wav":
        return buffer.getvalue(), "audio/wav"
    codec, container, media = {
        "mp3": ("libmp3lame", "mp3", "audio/mpeg"),
        "opus": ("libopus", "ogg", "audio/ogg"),
    }[fmt]
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-i", "pipe:0",
             "-vn", "-c:a", codec, "-b:a", "64k", "-f", container, "pipe:1"],
            input=buffer.getvalue(), capture_output=True, timeout=60, check=True,
        )
    except (OSError, subprocess.SubprocessError):
        raise EncoderError("Audio encoding failed. Check FFmpeg supports libmp3lame/libopus.") from None
    return result.stdout, media
