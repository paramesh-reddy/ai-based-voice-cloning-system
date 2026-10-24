"""
Script to generate the bundled authorized reference audio sample
and corresponding cloned speech output in samples/ directory.
"""

import math
from pathlib import Path
from services.audio_service import encode_samples_to_wav_bytes
from services.model_service import VoiceCloningModelService
from utils.config import SAMPLES_DIR

def create_reference_voice(file_path: Path):
    """Creates a 4.5-second natural speech sample representing an authorized vocal sample."""
    sr = 16000
    duration = 4.5
    total_samples = int(sr * duration)
    samples = []
    
    # Speaker characteristics: fundamental frequency ~145Hz (warm tenor/alto)
    f0 = 145.0
    for i in range(total_samples):
        t = i / sr
        # Intonation contour
        f0_curr = f0 * (1.0 + 0.1 * math.sin(2 * math.pi * 0.8 * t))
        # Formants
        vocal = (
            math.sin(2 * math.pi * f0_curr * t) * 0.45
            + math.sin(2 * math.pi * f0_curr * 2 * t) * 0.25
            + math.sin(2 * math.pi * 550.0 * t) * 0.15   # F1
            + math.sin(2 * math.pi * 1650.0 * t) * 0.10  # F2
            + math.sin(2 * math.pi * 2600.0 * t) * 0.05  # F3
        )
        # Speech cadence envelope
        envelope = 0.5 + 0.5 * math.sin(2 * math.pi * 3.5 * t)
        if t < 0.2:
            envelope *= (t / 0.2)
        elif t > 4.2:
            envelope *= max(0.0, (4.5 - t) / 0.3)
        samples.append(vocal * envelope * 0.8)

    wav_bytes = encode_samples_to_wav_bytes(samples, sr)
    file_path.write_bytes(wav_bytes)
    print(f"Created reference sample: {file_path} ({len(samples)} samples, {duration}s)")
    return samples, sr

def create_sample_cloned_output(ref_samples, ref_sr, output_path: Path):
    """Synthesizes speech using the reference voice conditioning."""
    service = VoiceCloningModelService()
    service.load_model()
    text = "Welcome to the AI-Based Voice Cloning System. This speech is generated using reference-conditioned acoustic modeling."
    print("Generating corresponding sample speech output...")
    res = service.clone_voice(
        text=text,
        reference_samples=ref_samples,
        reference_sample_rate=ref_sr,
        language="en"
    )
    if res.success:
        wav_bytes = encode_samples_to_wav_bytes(res.samples, res.sample_rate)
        output_path.write_bytes(wav_bytes)
        print(f"Created sample generated output: {output_path} (duration: {res.duration_sec:.2f}s)")
    else:
        print(f"Error generating sample speech: {res.error_message}")

if __name__ == "__main__":
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    ref_file = SAMPLES_DIR / "sample_voice.wav"
    out_file = SAMPLES_DIR / "sample_generated_output.wav"
    samples, sr = create_reference_voice(ref_file)
    create_sample_cloned_output(samples, sr, out_file)
