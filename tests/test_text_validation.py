"""
Tests for text validation module.
"""

try:
    import pytest
except ImportError:
    pytest = None

from services.validation_service import validate_authorization, validate_text
from utils.config import MAX_TEXT_LENGTH


def test_valid_text():
    """Verify that normal speech text passes validation."""
    result = validate_text("Hello, this is a clear reference sentence for voice cloning.")
    assert result.is_valid is True
    assert result.error_message is None
    assert result.metadata["character_count"] > 0
    assert "normalized_text" in result.metadata


def test_empty_string():
    """Verify that an empty string is rejected with an informative message."""
    result = validate_text("")
    assert result.is_valid is False
    assert "empty" in result.error_message.lower()


def test_none_text():
    """Verify that None input is handled cleanly without an unhandled exception."""
    result = validate_text(None)
    assert result.is_valid is False
    assert "enter the text" in result.error_message.lower()


def test_whitespace_only_text():
    """Verify that whitespace-only strings are rejected."""
    result = validate_text("   \n\t   ")
    assert result.is_valid is False
    assert "whitespace" in result.error_message.lower()


def test_text_exceeding_character_limit():
    """Verify that strings exceeding MAX_TEXT_LENGTH are rejected."""
    long_text = "a" * (MAX_TEXT_LENGTH + 25)
    result = validate_text(long_text, max_length=MAX_TEXT_LENGTH)
    assert result.is_valid is False
    assert "exceeds" in result.error_message.lower()
    assert result.metadata["character_count"] == len(long_text)


def test_text_without_usable_speech_content():
    """Verify that text with only punctuation or symbols is rejected."""
    result = validate_text("!@#$%^&*()_+=-{}[]:;'<>?,./")
    assert result.is_valid is False
    assert "pronounceable speech content" in result.error_message.lower()


def test_multilingual_characters_valid():
    """Verify that international characters (Spanish, French, German, Chinese, Japanese, etc.) pass."""
    samples = [
        "Bonjour, ceci est un test de synthèse vocale.",
        "Hola, esta es una prueba de clonación de voz.",
        "Hallo, dies ist ein Sprachsynthese-Test.",
        "你好，这是一个语音合成测试。",
        "こんにちは、音声合成のテストです。",
    ]
    for text in samples:
        res = validate_text(text)
        assert res.is_valid is True, f"Failed for valid text: {text}"


def test_authorization_confirmation():
    """Verify that authorization confirmation is strictly enforced."""
    rejected = validate_authorization(False)
    assert rejected.is_valid is False
    assert "explicit permission" in rejected.error_message.lower()

    accepted = validate_authorization(True)
    assert accepted.is_valid is True
    assert accepted.error_message is None
