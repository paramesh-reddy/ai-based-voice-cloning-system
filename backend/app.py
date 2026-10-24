"""
AI-Based Voice Cloning System - Streamlit Web Application.

An end-to-end interface allowing authorized users to upload reference voice samples,
input target text, condition a pretrained acoustic speech model, preview audio,
and download synthesized WAV speech.
"""

from datetime import datetime
import io
import os
from pathlib import Path
import tempfile
import time
from typing import Optional

import streamlit as st

from services.audio_service import (
    decode_audio_with_ffmpeg,
    encode_samples_to_wav_bytes,
    extract_audio_metadata,
    generate_waveform_peaks,
    preprocess_audio,
)
from services.model_service import VoiceCloningModelService
from services.output_service import (
    cleanup_expired_outputs,
    cleanup_temp_file,
    get_safe_filename,
    save_audio_file,
)
from services.validation_service import (
    validate_audio_content,
    validate_audio_file_header_and_size,
    validate_authorization,
    validate_text,
)
from utils.config import (
    ALLOWED_AUDIO_EXTENSIONS,
    MAX_AUDIO_DURATION_SEC,
    MAX_TEXT_LENGTH,
    MAX_UPLOAD_SIZE_MB,
    MIN_AUDIO_DURATION_SEC,
    OUTPUT_DIR,
    SAMPLES_DIR,
    SUPPORTED_LANGUAGES,
)
from utils.logger import get_logger

logger = get_logger("streamlit_app")

# Page configuration
st.set_page_config(
    page_title="AI-Based Voice Cloning System",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styling for a clean, professional aesthetic
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.25rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.25rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4b5563;
        margin-bottom: 1.5rem;
    }
    .badge-tag {
        display: inline-block;
        background: #e0e7ff;
        color: #3730a3;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.5rem;
        border-radius: 9999px;
        margin-right: 0.5rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
    }
    .disclaimer-box {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 12px;
        border-radius: 4px;
        font-size: 0.875rem;
        color: #92400e;
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def get_cached_model_service() -> VoiceCloningModelService:
    """Instantiates and caches the voice cloning model service singleton."""
    service = VoiceCloningModelService()
    service.load_model()
    return service


def render_sidebar():
    """Renders application parameters, retention status, and system info in the sidebar."""
    with st.sidebar:
        st.header("⚙️ System Configuration")
        st.markdown(
            """
            This system synthesizes speech using reference-conditioned acoustic modeling.
            Ensure you possess full rights or written consent before uploading voice data.
            """
        )

        st.subheader("Configured Limits")
        st.markdown(f"- **Max File Size:** {MAX_UPLOAD_SIZE_MB} MB")
        st.markdown(f"- **Duration Bounds:** {MIN_AUDIO_DURATION_SEC}s - {MAX_AUDIO_DURATION_SEC}s")
        st.markdown(f"- **Max Text Length:** {MAX_TEXT_LENGTH} characters")
        st.markdown(f"- **Supported Formats:** {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}")

        st.divider()

        # Maintenance trigger
        if st.button("🧹 Purge Expired Outputs", help="Deletes generated files older than the retention threshold"):
            cleaned = cleanup_expired_outputs()
            st.success(f"Purged {cleaned} expired audio files.")

        st.caption("Privacy Notice: Uploaded audio is processed locally and discarded after inference.")


def main():
    render_sidebar()

    # Application Header
    st.markdown('<div class="main-header">AI-Based Voice Cloning System</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Generate speech from text using an authorized reference voice recording.</div>',
        unsafe_allow_html=True,
    )

    # Initialize model service
    model_service = get_cached_model_service()

    col1, col2 = st.columns([1, 1], gap="large")

    # Column 1: Reference Voice & Legal Authorization
    with col1:
        st.subheader("1. Reference Voice Recording")
        st.markdown("Upload a high-fidelity mono/stereo voice recording of the target speaker.")

        # Sample audio loader option
        use_sample = st.checkbox("Use bundled authorized sample recording", value=False)
        uploaded_file = None
        ref_path = None

        if use_sample:
            sample_candidate = SAMPLES_DIR / "sample_voice.wav"
            if sample_candidate.exists():
                ref_path = sample_candidate
                st.info(f"Loaded bundled sample: `{sample_candidate.name}`")
            else:
                st.warning("No bundled sample found in `samples/` directory.")
        else:
            uploaded_file = st.file_uploader(
                "Upload Voice Audio (WAV, MP3, FLAC, M4A, OGG)",
                type=["wav", "mp3", "flac", "m4a", "ogg"],
                help="Recommended: 5 to 15 seconds of clear, noise-free speech.",
            )

        # Temporary file handling
        temp_input_path = None
        audio_valid = False
        decoded_samples = []
        decoded_sr = 16000

        if uploaded_file is not None or ref_path is not None:
            if uploaded_file is not None:
                # Write to temp file for robust inspection
                suffix = Path(uploaded_file.name).suffix.lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    temp_input_path = Path(tmp.name)
                eval_path = temp_input_path
                eval_name = uploaded_file.name
            else:
                eval_path = ref_path
                eval_name = ref_path.name

            # Run validation step 1: File header & size
            header_val = validate_audio_file_header_and_size(eval_path)
            if not header_val.is_valid:
                st.error(header_val.error_message)
            else:
                try:
                    # Run decoding & metadata extraction
                    raw_samples, sr = decode_audio_with_ffmpeg(eval_path)
                    metadata = extract_audio_metadata(eval_path)

                    # Content validation
                    content_val = validate_audio_content(
                        duration_sec=metadata.duration_sec,
                        sample_rate=sr,
                        num_samples=len(raw_samples),
                        is_finite=all(not math.isnan(s) for s in raw_samples[:1000]),
                    )

                    if not content_val.is_valid:
                        st.error(content_val.error_message)
                    else:
                        audio_valid = True
                        decoded_samples, decoded_sr = preprocess_audio(raw_samples, sr)

                        # Display audio inspection metadata
                        st.success("✅ Reference audio validated successfully!")
                        st.markdown(
                            f"""
                            <div class="metric-card">
                                <strong>File:</strong> {eval_name}<br>
                                <strong>Duration:</strong> {metadata.duration_sec:.2f}s | <strong>Sample Rate:</strong> {metadata.sample_rate} Hz<br>
                                <strong>Channels:</strong> {metadata.num_channels} | <strong>Codec:</strong> {metadata.format}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Playback preview
                        st.markdown("**Audio Preview:**")
                        with open(eval_path, "rb") as f:
                            st.audio(f.read(), format=f"audio/{eval_path.suffix.lstrip('.')}")

                except Exception as e:
                    logger.error(f"Error inspecting reference audio: {e}")
                    st.error(f"Failed to decode audio: {str(e)}")

        st.markdown("---")
        # Mandatory Authorization Checkbox
        st.subheader("2. Speaker Consent & Authorization")
        st.markdown(
            "Ethical and responsible AI usage requires explicit ownership or permission for vocal synthesis."
        )
        has_consent = st.checkbox(
            "I confirm that I own this voice recording or have obtained explicit permission from the speaker to clone their voice.",
            value=False,
        )

        if not has_consent and (uploaded_file or ref_path):
            st.warning("⚠️ Authorization required before generation can proceed.")

    # Column 2: Text Input & Generation
    with col2:
        st.subheader("3. Text Input")
        lang_options = list(SUPPORTED_LANGUAGES.keys())
        selected_lang = st.selectbox(
            "Select Output Language",
            options=lang_options,
            format_func=lambda x: f"{SUPPORTED_LANGUAGES[x]} ({x})",
            index=0,
        )

        text_input = st.text_area(
            "Enter the text you want to convert into speech.",
            placeholder="Type speech content here... (e.g., 'Hello! This is a synthesized demonstration of voice cloning technology.')",
            height=140,
        )

        char_count = len(text_input) if text_input else 0
        st.caption(f"Character Count: **{char_count}** / {MAX_TEXT_LENGTH}")

        # Validate text live
        text_val = validate_text(text_input)
        if text_input and not text_val.is_valid:
            st.warning(text_val.error_message)

        st.markdown("---")
        st.subheader("4. Speech Synthesis")

        generate_disabled = not (audio_valid and has_consent and text_val.is_valid)
        if st.button("🎙️ Generate Speech", type="primary", disabled=generate_disabled):
            # Final validation check
            auth_val = validate_authorization(has_consent)
            if not auth_val.is_valid:
                st.error(auth_val.error_message)
            elif not text_val.is_valid:
                st.error(text_val.error_message)
            elif not audio_valid:
                st.error("Please upload and validate a reference audio recording first.")
            else:
                progress_placeholder = st.empty()
                with progress_placeholder.container():
                    with st.spinner("Extracting speaker acoustics and generating speech..."):
                        gen_res = model_service.clone_voice(
                            text=text_input.strip(),
                            reference_samples=decoded_samples,
                            reference_sample_rate=decoded_sr,
                            language=selected_lang,
                        )

                if not gen_res.success:
                    st.error(f"❌ Speech Generation Failed: {gen_res.error_message}")
                else:
                    # Encode output to WAV
                    wav_bytes = encode_samples_to_wav_bytes(gen_res.samples, gen_res.sample_rate)
                    safe_filename = get_safe_filename()
                    out_path, saved_name = save_audio_file(wav_bytes, filename=safe_filename)

                    # Store in session state for persistence
                    st.session_state["last_generated"] = {
                        "path": str(out_path),
                        "filename": saved_name,
                        "bytes": wav_bytes,
                        "duration": gen_res.duration_sec,
                        "latency": gen_res.inference_time_sec,
                        "model": gen_res.model_name,
                        "sample_rate": gen_res.sample_rate,
                        "asr_note": gen_res.verification_notes,
                    }

        # Generated audio results section
        if "last_generated" in st.session_state:
            result = st.session_state["last_generated"]
            st.success("🎉 Speech successfully generated and validated!")

            st.markdown(
                f"""
                <div class="metric-card">
                    <strong>Output File:</strong> <code>{result['filename']}</code><br>
                    <strong>Audio Duration:</strong> {result['duration']:.2f}s | <strong>Format:</strong> 16-bit PCM WAV<br>
                    <strong>Sample Rate:</strong> {result['sample_rate']} Hz | <strong>Inference Time:</strong> {result['latency']:.2f}s
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.audio(result["bytes"], format="audio/wav")

            st.download_button(
                label="📥 Download Generated Audio (WAV)",
                data=result["bytes"],
                file_name=result["filename"],
                mime="audio/wav",
            )

            if result.get("asr_note"):
                st.info(f"ℹ️ {result['asr_note']}")

    # Educational Disclaimer & Responsible Use footer
    st.markdown(
        """
        <div class="disclaimer-box">
            <strong>Responsible AI Voice Use & Synthetic Audio Disclaimer:</strong><br>
            This application generates synthetic speech as an acoustic approximation of the provided reference voice.
            Synthetic voices must never be used for unauthorized impersonation, deception, fraud, or defamatory purposes.
            Generated audio should be clearly identified as synthetic.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Clean temporary upload if any
    if temp_input_path:
        cleanup_temp_file(temp_input_path)


if __name__ == "__main__":
    main()
