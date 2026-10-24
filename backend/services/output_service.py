"""
Output management service for AI-Based Voice Cloning System.

Handles directory management, safe unique file naming, atomic saving,
retention cleanup, and download preparation.
"""

from datetime import datetime, timedelta
import os
from pathlib import Path
import re
import shutil
import time
from typing import List, Optional, Tuple
import uuid

from utils.config import OUTPUT_DIR, OUTPUT_RETENTION_HOURS, TEMP_DIR
from utils.logger import get_logger

logger = get_logger("output_service")


def get_safe_filename(prefix: str = "generated_speech", ext: str = ".wav") -> str:
    """
    Generates a secure, collision-free timestamped filename.

    Example: generated_speech_20261024_051530_a1b2c3d4.wav

    Args:
        prefix: Base prefix name (sanitized).
        ext: Target extension with leading dot.

    Returns:
        str: Secure, unique filename.
    """
    sanitized_prefix = re.sub(r"[^\w\-]", "_", prefix)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    random_token = uuid.uuid4().hex[:8]
    clean_ext = ext if ext.startswith(".") else f".{ext}"
    return f"{sanitized_prefix}_{timestamp}_{random_token}{clean_ext}"


def ensure_output_directory(dir_path: Optional[Path] = None) -> Path:
    """
    Ensures that the output directory exists and is writable.

    Args:
        dir_path: Path to verify or create (defaults to OUTPUT_DIR).

    Returns:
        Path: Verified directory path.

    Raises:
        OSError: If directory cannot be created or accessed.
    """
    target = dir_path or OUTPUT_DIR
    target.mkdir(parents=True, exist_ok=True)
    if not os.access(target, os.W_OK):
        raise PermissionError(f"Output directory '{target}' is not writable.")
    return target


def save_audio_file(
    audio_data: bytes,
    filename: Optional[str] = None,
    output_dir: Optional[Path] = None,
) -> Tuple[Path, str]:
    """
    Atomically writes audio bytes to disk within the secure output directory.

    Args:
        audio_data: Raw audio binary data (e.g. WAV encoded).
        filename: Optional desired filename (sanitized).
        output_dir: Target directory (defaults to OUTPUT_DIR).

    Returns:
        Tuple[Path, str]: (Full Path on disk, User-facing filename).

    Raises:
        ValueError: If audio_data is empty.
        IOError: If file write fails.
    """
    if not audio_data:
        raise ValueError("Cannot write empty audio data to output file.")

    target_dir = ensure_output_directory(output_dir)

    safe_name = filename if filename else get_safe_filename()
    # Strip path traversal elements
    safe_name = Path(safe_name).name
    # Ensure safe characters only
    safe_name = re.sub(r"[^\w\-.]", "_", safe_name)

    dest_path = target_dir / safe_name
    temp_path = target_dir / f".tmp_{uuid.uuid4().hex}_{safe_name}"

    try:
        with open(temp_path, "wb") as f:
            f.write(audio_data)
        # Atomic rename to prevent partial file exposure
        temp_path.replace(dest_path)
        logger.info(f"Successfully saved output audio file '{safe_name}' ({len(audio_data)} bytes).")
        return dest_path, safe_name
    except Exception as e:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
        logger.error(f"Failed to write audio output: {e}")
        raise IOError(f"Failed to write generated speech file: {str(e)}")


def cleanup_expired_outputs(
    retention_hours: int = OUTPUT_RETENTION_HOURS,
    target_dir: Optional[Path] = None,
) -> int:
    """
    Removes generated output audio files older than the configured retention threshold.

    Args:
        retention_hours: Number of hours to keep files before deletion.
        target_dir: Directory to clean (defaults to OUTPUT_DIR).

    Returns:
        int: Number of deleted expired files.
    """
    directory = target_dir or OUTPUT_DIR
    if not directory.exists():
        return 0

    cutoff_time = time.time() - (retention_hours * 3600)
    deleted_count = 0

    for file_path in directory.iterdir():
        # Do not delete .gitkeep or hidden config files
        if file_path.name.startswith(".") or file_path.name == "README.md":
            continue

        try:
            if file_path.is_file():
                file_mtime = file_path.stat().st_mtime
                if file_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
        except Exception as e:
            logger.warning(f"Failed to purge expired file '{file_path.name}': {e}")

    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} expired output audio file(s) older than {retention_hours} hours.")
    return deleted_count


def cleanup_temp_file(file_path: Optional[Path]) -> None:
    """
    Safely removes a temporary file from the filesystem.

    Args:
        file_path: Path of the temporary file to remove.
    """
    if file_path is None:
        return
    try:
        p = Path(file_path)
        if p.exists() and p.is_file():
            p.unlink()
    except Exception as e:
        logger.warning(f"Could not remove temporary file '{file_path}': {e}")
