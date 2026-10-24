"""
Validation service for AI-Based Voice Cloning System.

Validates reference audio recordings, text input, and legal/consent
authorization before any synthesis pipeline execution.
"""

from dataclasses import dataclass, field
import io
import os
from pathlib import Path
import re
from typing import Any, Dict, Optional, Set

from utils.config import (
    ALLOWED_AUDIO_EXTENSIONS,
    MAX_AUDIO_DURATION_SEC,
    MAX_TEXT_LENGTH,
    MAX_UPLOAD_SIZE_BYTES,
    MAX_UPLOAD_SIZE_MB,
    MIN_AUDIO_DURATION_SEC,
    MIN_TEXT_LENGTH,
)
from utils.logger import get_logger

logger = get_logger("validation_service")


@dataclass
class ValidationResult:
    """Standardized validation result container."""
    is_valid: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


def validate_authorization(has_permission: bool) -> ValidationResult:
    """
    Validates that the user has explicitly confirmed authorization to clone the reference voice.

    Args:
        has_permission: Boolean flag indicating user consent/ownership.

    Returns:
        ValidationResult: Validity status with error message if unconfirmed.
    """
    if not has_permission:
        logger.warning("Synthesis attempted without explicit speaker authorization confirmation.")
        return ValidationResult(
            is_valid=False,
            error_message="You must confirm that you own this recording or have explicit permission from the speaker to clone their voice.",
        )
    return ValidationResult(is_valid=True)


def validate_text(
    text: Optional[str],
    max_length: int = MAX_TEXT_LENGTH,
    min_length: int = MIN_TEXT_LENGTH,
) -> ValidationResult:
    """
    Validates the text to be synthesized into speech.

    Args:
        text: Input string to convert into speech.
        max_length: Maximum allowed character count.
        min_length: Minimum allowed character count.

    Returns:
        ValidationResult: Validity status with detailed error messages.
    """
    if text is None or not isinstance(text, str):
        return ValidationResult(
            is_valid=False,
            error_message="Please enter the text you want to convert into speech.",
        )

    stripped = text.strip()

    if not stripped:
        return ValidationResult(
            is_valid=False,
            error_message="The entered text cannot be empty or contain only whitespace.",
        )

    char_count = len(text)
    if char_count > max_length:
        return ValidationResult(
            is_valid=False,
            error_message=f"Text exceeds the maximum allowed length of {max_length} characters (currently {char_count} characters). Please shorten your input.",
            metadata={"character_count": char_count, "max_length": max_length},
        )

    # Check for usable speech content (must contain at least one alphanumeric character)
    # Supports all international unicode alphabets, scripts, and digits
    has_alphanumeric = any(c.isalnum() for c in stripped)
    if not has_alphanumeric:
        return ValidationResult(
            is_valid=False,
            error_message="The entered text contains no pronounceable speech content. Please include words or sentences.",
            metadata={"character_count": char_count},
        )

    return ValidationResult(
        is_valid=True,
        metadata={"character_count": char_count, "normalized_text": stripped},
    )


def validate_audio_file_header_and_size(
    file_path: Path,
    max_size_bytes: int = MAX_UPLOAD_SIZE_BYTES,
    allowed_extensions: Optional[Set[str]] = None,
) -> ValidationResult:
    """
    Performs initial file-level checks (existence, size, extension, non-empty).

    Args:
        file_path: Path to the target audio file.
        max_size_bytes: Maximum allowed file size in bytes.
        allowed_extensions: Set of permitted lowercase file extensions.

    Returns:
        ValidationResult: Validity status and file size metadata.
    """
    allowed_exts = allowed_extensions or ALLOWED_AUDIO_EXTENSIONS

    if not file_path.exists():
        return ValidationResult(
            is_valid=False,
            error_message="Please upload a reference audio recording.",
        )

    file_ext = file_path.suffix.lower()
    if file_ext not in allowed_exts:
        valid_ext_str = ", ".join(sorted(allowed_exts))
        return ValidationResult(
            is_valid=False,
            error_message=f"Unsupported audio format '{file_ext}'. Allowed formats are: {valid_ext_str}.",
        )

    try:
        file_size = file_path.stat().st_size
    except OSError as e:
        logger.error(f"Failed to access audio file metadata: {e}")
        return ValidationResult(
            is_valid=False,
            error_message="The uploaded audio file could not be read. Please try again.",
        )

    if file_size == 0:
        return ValidationResult(
            is_valid=False,
            error_message="The uploaded audio file is empty. Please upload a valid recording.",
        )

    if file_size > max_size_bytes:
        return ValidationResult(
            is_valid=False,
            error_message=f"The uploaded file exceeds the maximum allowed size of {MAX_UPLOAD_SIZE_MB:.1f} MB (file size: {file_size / (1024*1024):.2f} MB).",
            metadata={"file_size_bytes": file_size},
        )

    return ValidationResult(
        is_valid=True,
        metadata={"file_size_bytes": file_size, "extension": file_ext},
    )


def validate_audio_content(
    duration_sec: float,
    sample_rate: int,
    num_samples: int,
    is_finite: bool,
    min_duration: float = MIN_AUDIO_DURATION_SEC,
    max_duration: float = MAX_AUDIO_DURATION_SEC,
) -> ValidationResult:
    """
    Validates decoded audio content characteristics.

    Args:
        duration_sec: Duration in seconds.
        sample_rate: Sampling frequency in Hz.
        num_samples: Total number of audio samples.
        is_finite: True if all audio samples are finite numbers (no NaN or Inf).
        min_duration: Minimum duration threshold in seconds.
        max_duration: Maximum duration threshold in seconds.

    Returns:
        ValidationResult: Validity status with clear error messages.
    """
    if sample_rate <= 0:
        return ValidationResult(
            is_valid=False,
            error_message="The audio recording has an invalid or corrupted sample rate.",
        )

    if num_samples <= 0:
        return ValidationResult(
            is_valid=False,
            error_message="The audio file contains no usable audio samples.",
        )

    if not is_finite:
        return ValidationResult(
            is_valid=False,
            error_message="The audio recording contains corrupted or non-finite audio values (NaN/Inf).",
        )

    if duration_sec < min_duration:
        return ValidationResult(
            is_valid=False,
            error_message=f"The audio recording is too short ({duration_sec:.1f}s). Minimum required duration is {min_duration:.1f} seconds for accurate voice cloning.",
            metadata={"duration_sec": duration_sec, "min_duration": min_duration},
        )

    if duration_sec > max_duration:
        return ValidationResult(
            is_valid=False,
            error_message=f"The audio recording exceeds the maximum allowed duration of {max_duration:.1f} seconds (currently {duration_sec:.1f}s). Please trim the sample.",
            metadata={"duration_sec": duration_sec, "max_duration": max_duration},
        )

    return ValidationResult(
        is_valid=True,
        metadata={"duration_sec": duration_sec, "sample_rate": sample_rate, "num_samples": num_samples},
    )
