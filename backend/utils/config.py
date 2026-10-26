"""
Configuration management for AI-Based Voice Cloning System.

Centralizes all application limits, audio constraints, model parameters,
and output retention rules.
"""

import os
from pathlib import Path
from typing import Dict, List, Set

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:
    pass

# Base directories
BASE_DIR: Path = Path(__file__).resolve().parent.parent
OUTPUT_DIR: Path = BASE_DIR / os.getenv("OUTPUT_DIR", "outputs")
SAMPLES_DIR: Path = BASE_DIR / os.getenv("SAMPLES_DIR", "samples")
TEMP_DIR: Path = BASE_DIR / "temp"

# Audio constraints
MAX_UPLOAD_SIZE_MB: float = float(os.getenv("MAX_UPLOAD_SIZE_MB", "15.0"))
MAX_UPLOAD_SIZE_BYTES: int = int(MAX_UPLOAD_SIZE_MB * 1024 * 1024)
MIN_AUDIO_DURATION_SEC: float = float(os.getenv("MIN_AUDIO_DURATION_SEC", "3.0"))
MAX_AUDIO_DURATION_SEC: float = float(os.getenv("MAX_AUDIO_DURATION_SEC", "30.0"))
TARGET_SAMPLE_RATE: int = int(os.getenv("TARGET_SAMPLE_RATE", "16000"))
ALLOWED_AUDIO_EXTENSIONS: Set[str] = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}

# Text constraints
MAX_TEXT_LENGTH: int = int(os.getenv("MAX_TEXT_LENGTH", "1000"))
MIN_TEXT_LENGTH: int = int(os.getenv("MIN_TEXT_LENGTH", "1"))

# Model configuration
DEFAULT_MODEL_NAME: str = os.getenv("VOICE_MODEL_NAME", "speecht5_tts")
PREFER_DEVICE: str = os.getenv("DEVICE", "auto")  # 'auto', 'cpu', 'cuda'
MODEL_CACHE_DIR: Path = BASE_DIR / "models_cache"

# Supported output languages
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "pl": "Polish",
    "tr": "Turkish",
    "ru": "Russian",
    "nl": "Dutch",
    "cs": "Czech",
    "ar": "Arabic",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "hi": "Hindi",
}

# Output retention
OUTPUT_RETENTION_HOURS: int = int(os.getenv("OUTPUT_RETENTION_HOURS", "24"))
CLEANUP_TEMP_FILES_ON_EXIT: bool = os.getenv("CLEANUP_TEMP_FILES", "true").lower() == "true"

# Ensure runtime directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
