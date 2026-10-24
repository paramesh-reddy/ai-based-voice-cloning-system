"""
Tests for reference audio validation module.
"""

from pathlib import Path
import tempfile
import pytest

from services.audio_service import encode_samples_to_wav_bytes
from services.validation_service import (
    validate_audio_content,
    validate_audio_file_header_and_size,
)
from utils.config import (
    ALLOWED_AUDIO_EXTENSIONS,
    MAX_AUDIO_DURATION_SEC,
    MAX_UPLOAD_SIZE_BYTES,
    MIN_AUDIO_DURATION_SEC,
)


@pytest.fixture
def valid_wav_file(tmp_path) -> Path:
    """Creates a temporary valid mono WAV file with 4 seconds of audio."""
    sr = 16000
    duration = 4.0
    samples = [0.1 * ((i % 100) / 50.0 - 1.0) for i in range(int(sr * duration))]
    wav_bytes = encode_samples_to_wav_bytes(samples, sr)

    file_path = tmp_path / "valid_test.wav"
    file_path.write_bytes(wav_bytes)
    return file_path


def test_valid_audio_file(valid_wav_file):
    """Verify that a valid WAV file passes header and size checks."""
    result = validate_audio_file_header_and_size(valid_wav_file)
    assert result.is_valid is True
    assert result.error_message is None
    assert result.metadata["file_size_bytes"] > 0


def test_empty_audio_upload(tmp_path):
    """Verify that a 0-byte upload is rejected."""
    empty_file = tmp_path / "empty.wav"
    empty_file.write_bytes(b"")

    result = validate_audio_file_header_and_size(empty_file)
    assert result.is_valid is False
    assert "empty" in result.error_message.lower()


def test_unsupported_audio_extension(tmp_path):
    """Verify that unsupported extensions (e.g. .exe, .txt, .mp4) are rejected."""
    bad_file = tmp_path / "recording.txt"
    bad_file.write_text("not an audio file")

    result = validate_audio_file_header_and_size(bad_file)
    assert result.is_valid is False
    assert "unsupported" in result.error_message.lower()


def test_file_size_limit_exceeded(tmp_path):
    """Verify that files exceeding the size limit are rejected."""
    big_file = tmp_path / "oversized.wav"
    # Small test ceiling of 1024 bytes
    big_file.write_bytes(b"x" * 2048)

    result = validate_audio_file_header_and_size(big_file, max_size_bytes=1024)
    assert result.is_valid is False
    assert "exceeds" in result.error_message.lower()


def test_audio_duration_below_minimum():
    """Verify that recordings shorter than the minimum duration threshold are rejected."""
    result = validate_audio_content(
        duration_sec=1.5,
        sample_rate=16000,
        num_samples=24000,
        is_finite=True,
        min_duration=3.0,
        max_duration=30.0,
    )
    assert result.is_valid is False
    assert "too short" in result.error_message.lower()


def test_audio_duration_above_maximum():
    """Verify that recordings longer than the maximum duration threshold are rejected."""
    result = validate_audio_content(
        duration_sec=45.0,
        sample_rate=16000,
        num_samples=720000,
        is_finite=True,
        min_duration=3.0,
        max_duration=30.0,
    )
    assert result.is_valid is False
    assert "exceeds the maximum" in result.error_message.lower()


def test_audio_with_invalid_or_non_finite_samples():
    """Verify that recordings with NaN/Inf values are rejected."""
    result = validate_audio_content(
        duration_sec=5.0,
        sample_rate=16000,
        num_samples=80000,
        is_finite=False,
    )
    assert result.is_valid is False
    assert "corrupted or non-finite" in result.error_message.lower()


def test_audio_with_invalid_sample_rate():
    """Verify that recordings with invalid sample rates (0 or negative) are rejected."""
    result = validate_audio_content(
        duration_sec=5.0,
        sample_rate=0,
        num_samples=80000,
        is_finite=True,
    )
    assert result.is_valid is False
    assert "sample rate" in result.error_message.lower()
