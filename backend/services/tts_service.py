"""
Turns text into spoken audio.

The acoustic fallback in the model service only stacks sine waves, so it
sounds like a tone. This service speaks the actual words.
"""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.error
import urllib.request
from typing import List, Tuple

from services.audio_service import decode_audio_with_ffmpeg
from utils.logger import get_logger

logger = get_logger("tts_service")

OPENAI_SPEECH_URL = "https://api.openai.com/v1/audio/speech"


def synthesize_spoken_audio(
    text: str,
    reference_samples: List[float],
    reference_sample_rate: int,
) -> Tuple[List[float], int, str]:
    """
    Speaks `text` and returns mono samples, sample rate, and engine name.

    Uses OpenAI speech when a key is configured, then Windows speech.
    """
    errors = []
    api_key = os.getenv("OPENAI_API_KEY", "").strip().strip('"').strip("'")
    if api_key and not api_key.startswith("MY_"):
        try:
            voice = _voice_for_reference(reference_samples, reference_sample_rate)
            samples, sample_rate = _openai_speech(text, api_key, voice)
            return samples, sample_rate, "openai-tts-1"
        except Exception as exc:
            logger.warning(f"OpenAI speech failed: {exc}")
            errors.append(str(exc))

    if os.name == "nt":
        try:
            samples, sample_rate = _windows_speech(text)
            return samples, sample_rate, "windows-sapi"
        except Exception as exc:
            logger.warning(f"Windows speech failed: {exc}")
            errors.append(str(exc))

    detail = " ".join(errors) if errors else "No speech engine is available."
    raise RuntimeError(f"Could not speak the text. {detail}")


def _voice_for_reference(samples: List[float], sample_rate: int) -> str:
    """Picks a lower or higher preset voice from the reference pitch."""
    pitch = _estimate_pitch(samples, sample_rate)
    if pitch < 145:
        return "onyx"
    if pitch < 190:
        return "echo"
    return "nova"


def _estimate_pitch(samples: List[float], sample_rate: int) -> float:
    if sample_rate <= 0 or len(samples) < 1000:
        return 160.0
    limit = min(len(samples), sample_rate // 2)
    crossings = 0
    for index in range(1, limit):
        if samples[index] >= 0 and samples[index - 1] < 0:
            crossings += 1
    if limit == 0:
        return 160.0
    return crossings / (limit / sample_rate)


def _openai_speech(text: str, api_key: str, voice: str) -> Tuple[List[float], int]:
    payload = json.dumps(
        {
            "model": "tts-1",
            "voice": voice,
            "input": text,
            "response_format": "wav",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        OPENAI_SPEECH_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            wav_bytes = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")[:300]
        raise RuntimeError(f"OpenAI speech request failed ({exc.code}): {body}") from exc

    if not wav_bytes.startswith(b"RIFF"):
        raise RuntimeError("OpenAI speech response was not a WAV file.")
    return _samples_from_wav_bytes(wav_bytes)


def _windows_speech(text: str) -> Tuple[List[float], int]:
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        text_path = folder / "speech.txt"
        wav_path = folder / "speech.wav"
        script_path = folder / "speak.ps1"
        text_path.write_text(text, encoding="utf-8")
        script_path.write_text(
            "\n".join(
                [
                    "Add-Type -AssemblyName System.Speech",
                    "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer",
                    "$synth.SetOutputToWaveFile($args[0])",
                    "$spoken = Get-Content -Raw -Encoding UTF8 $args[1]",
                    "$synth.Speak($spoken)",
                    "$synth.Dispose()",
                ]
            ),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
                str(wav_path),
                str(text_path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if completed.returncode != 0 or not wav_path.exists():
            detail = (completed.stderr or completed.stdout or "Windows speech produced no audio.").strip()
            raise RuntimeError(detail[:300])
        return _samples_from_wav_bytes(wav_path.read_bytes())


def _samples_from_wav_bytes(wav_bytes: bytes) -> Tuple[List[float], int]:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
        handle.write(wav_bytes)
        temp_path = handle.name
    try:
        return decode_audio_with_ffmpeg(temp_path)
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass
