"""
CLI tool to generate speech from text using an authorized reference recording.

Usage:
    python3 generate_sample.py --ref samples/sample_voice.wav --text "Hello world" --output outputs/sample.wav --authorized
"""

import argparse
from pathlib import Path
import sys

from services.audio_service import (
    decode_audio_with_ffmpeg,
    encode_samples_to_wav_bytes,
    extract_audio_metadata,
    preprocess_audio,
)
from services.model_service import VoiceCloningModelService
from services.output_service import save_audio_file
from services.validation_service import (
    validate_audio_content,
    validate_audio_file_header_and_size,
    validate_authorization,
    validate_text,
)
from utils.logger import get_logger

logger = get_logger("cli_generator")


def main():
    parser = argparse.ArgumentParser(description="AI Voice Cloning CLI Tool")
    parser.add_argument("--ref", required=True, help="Path to authorized reference audio file")
    parser.add_argument("--text", required=True, help="Text to convert into speech")
    parser.add_argument("--output", default="outputs/cli_speech.wav", help="Output WAV path")
    parser.add_argument("--lang", default="en", help="Language code (e.g. en, es, fr)")
    parser.add_argument(
        "--authorized",
        action="store_true",
        help="Confirms speaker consent/ownership of the reference audio recording",
    )

    args = parser.parse_args()

    # 1. Consent verification
    auth_res = validate_authorization(args.authorized)
    if not auth_res.is_valid:
        print(f"\n[ERROR] {auth_res.error_message}", file=sys.stderr)
        sys.exit(1)

    # 2. Text validation
    text_res = validate_text(args.text)
    if not text_res.is_valid:
        print(f"\n[ERROR] Text Validation: {text_res.error_message}", file=sys.stderr)
        sys.exit(1)

    ref_path = Path(args.ref)
    # 3. Audio header & size validation
    hdr_res = validate_audio_file_header_and_size(ref_path)
    if not hdr_res.is_valid:
        print(f"\n[ERROR] Reference Audio Header: {hdr_res.error_message}", file=sys.stderr)
        sys.exit(1)

    # 4. Audio decoding & content validation
    print(f"Decoding reference audio: {ref_path} ...")
    raw_samples, sr = decode_audio_with_ffmpeg(ref_path)
    meta = extract_audio_metadata(ref_path)

    content_res = validate_audio_content(
        duration_sec=meta.duration_sec,
        sample_rate=sr,
        num_samples=len(raw_samples),
        is_finite=True,
    )
    if not content_res.is_valid:
        print(f"\n[ERROR] Audio Content: {content_res.error_message}", file=sys.stderr)
        sys.exit(1)

    clean_samples, clean_sr = preprocess_audio(raw_samples, sr)
    print(f"Preprocessed audio: {len(clean_samples)} samples at {clean_sr} Hz (duration: {meta.duration_sec:.2f}s)")

    # 5. Model execution
    print("Initializing voice cloning model...")
    service = VoiceCloningModelService()
    service.load_model()

    print(f"Synthesizing speech: '{args.text}' (language={args.lang}) ...")
    gen_res = service.clone_voice(
        text=args.text,
        reference_samples=clean_samples,
        reference_sample_rate=clean_sr,
        language=args.lang,
    )

    if not gen_res.success:
        print(f"\n[ERROR] Synthesis Failed: {gen_res.error_message}", file=sys.stderr)
        sys.exit(1)

    # 6. Save output
    out_target = Path(args.output)
    wav_bytes = encode_samples_to_wav_bytes(gen_res.samples, gen_res.sample_rate)
    dest_path, filename = save_audio_file(
        wav_bytes,
        filename=out_target.name,
        output_dir=out_target.parent,
    )

    print("\n" + "=" * 50)
    print(" Voice Cloning Synthesis Succeeded")
    print("=" * 50)
    print(f" Output File:      {dest_path}")
    print(f" Audio Duration:   {gen_res.duration_sec:.2f} seconds")
    print(f" Sample Rate:      {gen_res.sample_rate} Hz")
    print(f" Inference Time:   {gen_res.inference_time_sec:.2f} seconds")
    print(f" Synthesizer:      {gen_res.model_name}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
