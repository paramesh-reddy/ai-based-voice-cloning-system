"""
Tests for output file management service.
"""

from pathlib import Path
import time
import pytest

from services.output_service import (
    cleanup_expired_outputs,
    cleanup_temp_file,
    ensure_output_directory,
    get_safe_filename,
    save_audio_file,
)


def test_unique_filename_generation():
    """Verify that multiple filename requests generate distinct, safe names."""
    names = [get_safe_filename() for _ in range(50)]
    assert len(set(names)) == 50
    for name in names:
        assert name.startswith("generated_speech_")
        assert name.endswith(".wav")
        # Ensure no path traversal characters
        assert "/" not in name
        assert "\\" not in name
        assert ".." not in name


def test_ensure_output_directory(tmp_path):
    """Verify that output directories are created if missing."""
    target_dir = tmp_path / "custom_outputs" / "sub"
    assert not target_dir.exists()

    result_dir = ensure_output_directory(target_dir)
    assert result_dir.exists()
    assert result_dir.is_dir()


def test_save_valid_audio_file(tmp_path):
    """Verify that valid audio bytes are saved and readable."""
    audio_content = b"RIFFtestdummydataWAVEfmt "
    out_path, filename = save_audio_file(audio_content, output_dir=tmp_path)

    assert out_path.exists()
    assert out_path.is_file()
    assert out_path.read_bytes() == audio_content
    assert filename == out_path.name


def test_save_empty_audio_raises_error(tmp_path):
    """Verify that saving empty audio bytes raises ValueError."""
    with pytest.raises(ValueError, match="Cannot write empty audio data"):
        save_audio_file(b"", output_dir=tmp_path)


def test_cleanup_expired_outputs(tmp_path):
    """Verify that files older than the retention threshold are deleted."""
    # Create an old file
    old_file = tmp_path / "old_speech.wav"
    old_file.write_bytes(b"old")
    # Set mtime to 48 hours ago
    past_mtime = time.time() - (48 * 3600)
    import os
    os.utime(old_file, (past_mtime, past_mtime))

    # Create a fresh file
    fresh_file = tmp_path / "fresh_speech.wav"
    fresh_file.write_bytes(b"fresh")

    # Run cleanup with 24 hours threshold
    deleted_count = cleanup_expired_outputs(retention_hours=24, target_dir=tmp_path)

    assert deleted_count == 1
    assert not old_file.exists()
    assert fresh_file.exists()


def test_cleanup_temp_file(tmp_path):
    """Verify that temporary files are deleted safely."""
    temp_f = tmp_path / "test_temp.tmp"
    temp_f.write_text("temporary data")
    assert temp_f.exists()

    cleanup_temp_file(temp_f)
    assert not temp_f.exists()

    # Calling on nonexistent file should not raise
    cleanup_temp_file(temp_f)
    cleanup_temp_file(None)
