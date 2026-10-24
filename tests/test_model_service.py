"""
Tests for voice cloning model service and inference pipelines.
"""

import math
from unittest.mock import MagicMock, patch
import pytest

from services.model_service import GenerationResult, VoiceCloningModelService


@pytest.fixture
def dummy_reference_samples():
    """Generates synthetic reference audio samples (1 second at 16kHz)."""
    sr = 16000
    return [0.2 * math.sin(2 * math.pi * 220 * i / sr) for i in range(sr)]


def test_model_service_initialization():
    """Verify that model service initializes with default parameters."""
    service = VoiceCloningModelService()
    assert service.model_name is not None
    assert service.active_device in ("cpu", "cuda")
    assert service.is_loaded is False


def test_model_service_load():
    """Verify that loading initializes the service and caches state."""
    service = VoiceCloningModelService()
    success = service.load_model()
    assert success is True
    assert service.is_loaded is True


def test_inference_with_empty_text(dummy_reference_samples):
    """Verify that empty text is rejected prior to inference."""
    service = VoiceCloningModelService()
    service.load_model()

    result = service.clone_voice(
        text="",
        reference_samples=dummy_reference_samples,
        reference_sample_rate=16000,
    )
    assert result.success is False
    assert "empty" in result.error_message.lower()


def test_inference_with_empty_reference_audio():
    """Verify that missing reference samples are rejected."""
    service = VoiceCloningModelService()
    service.load_model()

    result = service.clone_voice(
        text="Hello world, this is a test.",
        reference_samples=[],
        reference_sample_rate=16000,
    )
    assert result.success is False
    assert "no usable audio samples" in result.error_message.lower()


def test_successful_inference(dummy_reference_samples):
    """Verify end-to-end voice cloning generation produces valid samples and metadata."""
    service = VoiceCloningModelService()
    service.load_model()

    text = "The quick brown fox jumps over the lazy dog."
    result = service.clone_voice(
        text=text,
        reference_samples=dummy_reference_samples,
        reference_sample_rate=16000,
        language="en",
    )

    assert result.success is True
    assert len(result.samples) > 0
    assert result.sample_rate > 0
    assert result.duration_sec > 0.0
    assert result.inference_time_sec >= 0.0
    # Samples must be within [-1.0, 1.0] and finite
    assert all(-1.0 <= s <= 1.0 for s in result.samples[:500])
    assert all(not math.isnan(s) and not math.isinf(s) for s in result.samples[:500])


def test_model_initialization_failure_handling():
    """Verify graceful handling when model fails to initialize."""
    service = VoiceCloningModelService()
    with patch.object(service, "load_model", return_value=False):
        result = service.clone_voice(
            text="Testing failure state.",
            reference_samples=[0.1] * 1000,
            reference_sample_rate=16000,
        )
        assert result.success is False
        assert "failed to initialize" in result.error_message.lower()
