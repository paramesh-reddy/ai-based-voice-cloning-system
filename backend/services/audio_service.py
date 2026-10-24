"""
Audio processing service for AI-Based Voice Cloning System.

Provides audio decoding, metadata inspection, format normalization,
resampling, channel conversion, and waveform feature extraction.
"""

from dataclasses import dataclass, field
import io
import math
import os
from pathlib import Path
import struct
import subprocess
from typing import Any, Dict, List, Optional, Tuple, Union

from utils.config import TARGET_SAMPLE_RATE
from utils.logger import get_logger

logger = get_logger("audio_service")


@dataclass
class AudioMetadata:
    """Detailed metadata extracted from decoded audio."""
    duration_sec: float
    sample_rate: int
    num_channels: int
    num_samples: int
    format: str
    file_size_bytes: int
    peak_amplitude: float = 0.0
    rms_amplitude: float = 0.0
    is_finite: bool = True


@dataclass
class DecodedAudio:
    """Decoded audio array representation."""
    samples: List[float]  # Mono floating point samples in [-1.0, 1.0]
    sample_rate: int
    metadata: AudioMetadata


def decode_audio_with_ffmpeg(file_path: Union[str, Path], target_sr: Optional[int] = None) -> Tuple[List[float], int]:
    """
    Decodes arbitrary audio formats (MP3, M4A, FLAC, WAV, OGG) to 16-bit mono PCM via FFmpeg.

    Args:
        file_path: Path to the input audio file.
        target_sr: Desired sampling rate (defaults to preserving or target_sr).

    Returns:
        Tuple[List[float], int]: (mono samples normalized to [-1.0, 1.0], sample_rate)

    Raises:
        RuntimeError: If FFmpeg fails or file is corrupted.
    """
    path_str = str(file_path)
    sr = target_sr if target_sr else TARGET_SAMPLE_RATE

    cmd = [
        "ffmpeg",
        "-v", "error",
        "-i", path_str,
        "-f", "s16le",
        "-acodec", "pcm_s16le",
        "-ac", "1",
        "-ar", str(sr),
        "-",
    ]

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode("utf-8", errors="ignore")
        logger.error(f"FFmpeg decoding failed for '{path_str}': {err_msg}")
        raise RuntimeError(f"Audio decoding failed: {err_msg.strip() or 'Corrupted file'}")
    except FileNotFoundError:
        logger.error("FFmpeg binary not found on the system path.")
        raise RuntimeError("FFmpeg is required for audio decoding but was not found.")

    raw_bytes = proc.stdout
    if not raw_bytes:
        raise ValueError("Decoded audio stream contains zero bytes.")

    num_samples = len(raw_bytes) // 2
    # Unpack 16-bit signed integers little-endian
    integers = struct.unpack(f"<{num_samples}h", raw_bytes[:num_samples * 2])
    # Normalize to [-1.0, 1.0]
    samples = [val / 32768.0 for val in integers]

    return samples, sr


def extract_audio_metadata(file_path: Union[str, Path]) -> AudioMetadata:
    """
    Extracts duration, format, sample rate, and channels using ffprobe or file inspection.

    Args:
        file_path: Path to the audio file.

    Returns:
        AudioMetadata: Parsed metadata.
    """
    p = Path(file_path)
    file_size = p.stat().st_size if p.exists() else 0

    # Use ffprobe if available for deep inspection
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "stream=channels,sample_rate,duration,codec_name:format=duration,size,format_name",
        "-of", "default=noprint_wrappers=1",
        str(file_path),
    ]

    duration_sec = 0.0
    sample_rate = 0
    channels = 1
    codec = p.suffix.lstrip(".").upper()

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        lines = proc.stdout.decode("utf-8", errors="ignore").splitlines()
        for line in lines:
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                if key == "duration" and duration_sec == 0.0:
                    try:
                        duration_sec = float(val)
                    except ValueError:
                        pass
                elif key == "sample_rate":
                    try:
                        sample_rate = int(val)
                    except ValueError:
                        pass
                elif key == "channels":
                    try:
                        channels = int(val)
                    except ValueError:
                        pass
                elif key == "codec_name":
                    codec = val.upper()
    except Exception as e:
        logger.warning(f"ffprobe extraction fallback: {e}")

    # Fallback if ffprobe duration wasn't obtained: decode stream
    if duration_sec <= 0.0 or sample_rate <= 0:
        samples, sr = decode_audio_with_ffmpeg(file_path)
        sample_rate = sr
        duration_sec = len(samples) / sr
        num_samples = len(samples)
    else:
        num_samples = int(duration_sec * sample_rate)

    return AudioMetadata(
        duration_sec=round(duration_sec, 2),
        sample_rate=sample_rate,
        num_channels=channels,
        num_samples=num_samples,
        format=codec,
        file_size_bytes=file_size,
    )


def preprocess_audio(
    samples: List[float],
    sample_rate: int,
    target_sample_rate: int = TARGET_SAMPLE_RATE,
    normalize_peak: bool = True,
    target_peak: float = 0.95,
) -> Tuple[List[float], int]:
    """
    Cleans and pre-processes reference audio samples:
    - Verifies finiteness
    - Normalizes amplitude to target peak
    - Resamples to target sampling rate if needed

    Args:
        samples: List of float samples in [-1.0, 1.0].
        sample_rate: Current sampling frequency.
        target_sample_rate: Required sampling rate for acoustic conditioning.
        normalize_peak: Whether to scale peak volume.
        target_peak: Peak amplitude ceiling.

    Returns:
        Tuple[List[float], int]: (Processed samples, target sample rate).
    """
    if not samples:
        return [], target_sample_rate

    # Check finite
    clean_samples = []
    max_amp = 0.0
    for s in samples:
        if math.isnan(s) or math.isinf(s):
            clean_samples.append(0.0)
        else:
            clamped = max(-1.0, min(1.0, s))
            clean_samples.append(clamped)
            abs_s = abs(clamped)
            if abs_s > max_amp:
                max_amp = abs_s

    # Normalize amplitude
    if normalize_peak and max_amp > 1e-4:
        scale = target_peak / max_amp
        clean_samples = [s * scale for s in clean_samples]

    # Simple linear interpolation resampling if rates differ
    if sample_rate != target_sample_rate and sample_rate > 0:
        ratio = target_sample_rate / sample_rate
        new_length = int(len(clean_samples) * ratio)
        resampled = []
        for i in range(new_length):
            orig_idx = i / ratio
            idx_floor = int(orig_idx)
            idx_ceil = min(idx_floor + 1, len(clean_samples) - 1)
            frac = orig_idx - idx_floor
            val = (1.0 - frac) * clean_samples[idx_floor] + frac * clean_samples[idx_ceil]
            resampled.append(val)
        return resampled, target_sample_rate

    return clean_samples, sample_rate


def generate_waveform_peaks(samples: List[float], num_buckets: int = 64) -> List[float]:
    """
    Computes downsampled RMS waveform peaks for UI visualization.

    Args:
        samples: Audio sample list.
        num_buckets: Number of visualization bars.

    Returns:
        List[float]: Normalized peak amplitudes between 0.05 and 1.0.
    """
    if not samples:
        return [0.1] * num_buckets

    bucket_size = max(1, len(samples) // num_buckets)
    peaks: List[float] = []

    for i in range(num_buckets):
        start = i * bucket_size
        end = min(start + bucket_size, len(samples))
        chunk = samples[start:end]
        if not chunk:
            peaks.append(0.05)
            continue
        # RMS of chunk
        sum_sq = sum(s * s for s in chunk)
        rms = math.sqrt(sum_sq / len(chunk))
        # Normalized display value
        peaks.append(max(0.08, min(1.0, round(rms * 2.8, 3))))

    return peaks


def encode_samples_to_wav_bytes(samples: List[float], sample_rate: int) -> bytes:
    """
    Encodes float audio samples [-1.0, 1.0] into a valid 16-bit mono PCM WAV file byte buffer.

    Args:
        samples: List of float samples in [-1.0, 1.0].
        sample_rate: Sampling frequency in Hz.

    Returns:
        bytes: Complete WAV file binary content.
    """
    num_samples = len(samples)
    num_channels = 1
    bytes_per_sample = 2
    byte_rate = sample_rate * num_channels * bytes_per_sample
    block_align = num_channels * bytes_per_sample
    data_size = num_samples * bytes_per_sample
    chunk_size = 36 + data_size

    # WAV Header (RIFF + fmt + data)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        chunk_size,
        b"WAVE",
        b"fmt ",
        16,                 # Subchunk1Size for PCM
        1,                  # AudioFormat 1 = PCM
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        16,                 # BitsPerSample
        b"data",
        data_size,
    )

    # Convert floats to int16
    pcm_integers = [int(max(-1.0, min(1.0, s)) * 32767.0) for s in samples]
    raw_audio = struct.pack(f"<{num_samples}h", *pcm_integers)

    return header + raw_audio
