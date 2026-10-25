# AI-Based Voice Cloning System

A production-grade, end-to-end voice cloning system that synthesizes spoken audio from text using an authorized reference voice recording and speaker-conditioned acoustic modeling.

---

## 1. Project Overview

The **AI-Based Voice Cloning System** enables authorized users to convert written text into high-fidelity speech matching the vocal timbre, pitch contour, and acoustic resonance of an uploaded reference speaker. Designed with privacy, security, and strict speaker consent as foundational requirements, the system processes reference audio through acoustic feature extraction, verifies phonetic content, runs speaker-conditioned synthesis, and produces downloadable 16-bit PCM WAV audio files.

---

## 2. Problem Statement

Voice cloning technologies offer immense utility in education, assistive speech devices, audiobook narration, and localized media production. However, unconstrained voice synthesis poses severe risks of unauthorized impersonation, fraud, and deceptive audio generation.

This system addresses these challenges by:
1. **Enforcing Mandatory Authorization**: Requiring positive confirmation of voice ownership or explicit speaker consent before any synthesis execution.
2. **Validating Audio Integrity**: Inspecting reference audio duration (3s–30s), sample rate, finiteness, channels, and codec headers to prevent numerical instability or corrupted audio pipelines.
3. **Ensuring Phonetic Correspondence**: Validating that input text contains pronounceable linguistic tokens within configured bounds (1–1,000 characters) without silent truncation.
4. **Preserving Privacy**: Processing reference recordings locally and discarding temporary inputs immediately after inference, avoiding long-term storage or third-party leakage.

---

## 3. Key Features

- **Reference Audio Upload & Validation**: Supports WAV, MP3, FLAC, M4A, and OGG recordings with automatic FFmpeg decoding, channel conversion to mono, and amplitude normalization.
- **Acoustic Speaker Conditioning**: Extracts fundamental pitch ($F_0$), vocal tract formant frequencies ($F_1, F_2, F_3$), and spectral envelope from reference samples to condition synthesis.
- **Real-Time Interactive Web Interface**: Dual-panel UI featuring waveform visualization, file metadata inspection (duration, sample rate, channels, codec), live character counter, audio preview players, and one-click downloads.
- **Streamlit Desktop/Web Application**: Native Python Streamlit UI (`app.py`) for data science and machine learning research workflows.
- **Multilingual Support**: Supports 16 languages including English, Spanish, French, German, Italian, Portuguese, Japanese, Chinese, and Arabic.
- **Collision-Free Output Management**: Generates timestamped filenames (`generated_speech_YYYYMMDD_HHMMSS_token.wav`), ensures atomic writes, and executes configurable retention policies.
- **CLI Automation**: Standalone CLI script (`generate_sample.py`) for automated or batch speech generation pipelines.
- **Comprehensive Automated Test Suite**: 28 unit tests covering audio validation, text bounds, output management, retention cleanup, and model error handling.

---

## 4. Technology Stack

- **Programming Language**: Python 3.10 / 3.11 & TypeScript / Node.js
- **Machine Learning & Synthesis**: PyTorch, Hugging Face Transformers (`microsoft/speecht5_tts`, `microsoft/speecht5_hifigan`), and Acoustic Vocal Tract Resonance Modeling
- **Audio Processing**: Librosa, SoundFile, FFmpeg, SciPy, NumPy
- **User Interface**: Streamlit (`backend/app.py`) and React 19 with Tailwind CSS (`frontend/src/App.tsx`)
- **Backend Server**: Express with TypeScript (`backend/server.ts`)
- **Testing**: Pytest 9.x (`pytest -v backend/tests`) & native runner (`python backend/run_tests.py`)
- **Configuration**: Python Dotenv & centralized dataclass configs (`utils/config.py`)

---

## 5. Project Architecture

The codebase follows a modular separation of concerns:

```
voice-cloning-system/
├── backend/                               # Python services and Express API
│   ├── server.ts                          # Express API, Python bridge, and Vite dev middleware
│   ├── app.py                             # Streamlit web application entry point
│   ├── generate_sample.py                 # CLI speech synthesis tool
│   ├── run_tests.py                       # Automated test runner (pytest / native)
│   ├── create_sample_files.py             # Script to build reference & synthesized WAVs
│   ├── requirements.txt                   # Pinned Python package dependencies
│   ├── services/
│   │   ├── __init__.py
│   │   ├── model_service.py               # Pretrained model caching, acoustic conditioning, inference
│   │   ├── audio_service.py               # FFmpeg decoding, normalization, resampling, WAV encoding
│   │   ├── validation_service.py          # Audio bounds, text constraints, and consent validation
│   │   └── output_service.py              # Unique file generation, atomic writes, retention cleanup
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py                      # Centralized configuration and environment variable loading
│   │   └── logger.py                      # Privacy-safe structured logger (no audio or text leaking)
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_audio_validation.py       # Audio constraints, codecs, durations, corruptions, NaN/Inf
│   │   ├── test_text_validation.py        # Text bounds, empty strings, whitespace, Unicode, consent
│   │   ├── test_output_service.py         # File uniqueness, directory auto-creation, retention purge
│   │   └── test_model_service.py          # Model initialization, caching, inference error handling
│   ├── samples/
│   │   ├── README.md                      # Documentation on authorized voice sample workflow
│   │   ├── sample_voice.wav               # Authorized reference recording (4.5s mono 16kHz WAV)
│   │   └── sample_generated_output.wav    # Synthesized speech corresponding to sample text
│   └── outputs/
│       └── .gitkeep                       # Destination directory for generated speech WAV files
│
├── frontend/                              # React web console
│   ├── index.html                         # Frontend HTML entry point
│   ├── vite.config.ts                     # Vite and Tailwind configuration
│   ├── tsconfig.json                      # Frontend TypeScript configuration
│   └── src/
│       ├── App.tsx                        # Main voice cloning console container
│       ├── types.ts                       # TypeScript interfaces for audio metadata & responses
│       ├── components/
│       │   ├── Header.tsx                 # Header navigation & tab switcher
│       │   ├── ReferenceAudioCard.tsx     # Audio uploader, waveform visualizer, metadata inspector
│       │   ├── ConsentCard.tsx            # Mandatory speaker authorization confirmation
│       │   ├── TextInputCard.tsx          # Multiline speech text area, language selector, presets
│       │   ├── OutputPlayerCard.tsx       # Synthesized audio playback, metrics & download button
│       │   └── CliGuideModal.tsx          # Interactive documentation for CLI & Streamlit
│       ├── main.tsx
│       └── index.css
│
├── package.json                           # Node/npm scripts and dependencies
├── .env.example                           # Environment configuration template
└── README.md                              # Complete system documentation
```

---

## 6. Model Selection and Rationale

### Selected Architecture: SpeechT5 + Reference-Conditioned Acoustic Resonator Pipeline

During evaluation of voice cloning models:

1. **Coqui XTTS-v2**:
   - *Strengths*: High-fidelity multi-lingual voice cloning from a 3–10s audio prompt.
   - *Limitations*: Heavy memory footprint (~1.8 GB model weights), dependency on CUDA for reasonable latency (CPU inference takes 30–60+ seconds per sentence), and the CPML (Coqui Public Model License) restricts non-commercial/commercial usage.
2. **Microsoft SpeechT5 (`microsoft/speecht5_tts`)**:
   - *Strengths*: Apache 2.0 license (permissive open-source), conditioned directly on 512-dimensional speaker x-vector embeddings extracted from reference audio, uses a HiFi-GAN neural vocoder, runs in 1.5–3.0 seconds on standard CPU cores, and fits within 4 GB RAM.
3. **Reference-Conditioned Acoustic Synthesizer**:
   - *Strengths*: Zero external network dependencies, extracts speaker pitch ($F_0$), vocal tract formant distributions, and cadence directly from reference audio samples, providing consistent real-time inference across all architectures without memory exhaustion.

The application dynamically leverages **SpeechT5 speaker conditioning** when Hugging Face weights are cached and seamlessly falls back to **speaker acoustic formant modeling** in lightweight/constrained environments, ensuring reliability.

---

## 7. Model Limitations and Licensing Considerations

- **Approximation Nature**: Synthetic voice output represents an *acoustic approximation* of the speaker. It is not an identical replica and must never be portrayed as authentic or unaltered.
- **Licensing**:
  - The codebase is released under standard open-source terms.
  - Pretrained SpeechT5 models from Microsoft are licensed under **Apache 2.0**.
  - Any user-supplied reference recordings remain the sole property of their respective owners/speakers.

---

## 8. Supported Languages and Audio Formats

### Supported Audio Formats
- **Input Audio**: WAV, MP3, FLAC, M4A, OGG
- **Input Duration**: 3.0 seconds to 30.0 seconds
- **Max Input File Size**: 15.0 MB (configurable)
- **Output Audio**: 16-bit Mono Linear PCM WAV at 16,000 Hz

### Supported Output Languages
1. English (`en`)
2. Spanish (`es`)
3. French (`fr`)
4. German (`de`)
5. Italian (`it`)
6. Portuguese (`pt`)
7. Polish (`pl`)
8. Turkish (`tr`)
9. Russian (`ru`)
10. Dutch (`nl`)
11. Czech (`cs`)
12. Arabic (`ar`)
13. Chinese (`zh`)
14. Japanese (`ja`)
15. Korean (`ko`)
16. Hindi (`hi`)

---

## 9. System Requirements

- **Operating System**: Linux (Ubuntu 20.04+, Debian 11+), macOS 12+, or Windows 10/11 (WSL2 recommended)
- **CPU**: 2+ cores (x86_64 or Apple Silicon)
- **RAM**: Minimum 2 GB (4 GB recommended for neural vocoders)
- **Disk Space**: ~500 MB for Python dependencies and runtime outputs
- **GPU (Optional)**: NVIDIA GPU with CUDA 11.8+ for accelerated neural vocoder inference

---

## 10. Python-Version Compatibility

- **Recommended**: Python 3.10 or 3.11
- **Supported**: Python 3.9 through 3.12

---

## 11. Installation Instructions

### Linux & macOS

```bash
# 1. Clone repository and navigate to folder
cd voice-cloning-system

# 2. Install FFmpeg
# On Ubuntu/Debian:
sudo apt-get update && sudo apt-get install -y ffmpeg libsndfile1
# On macOS via Homebrew:
brew install ffmpeg libsndfile

# 3. Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install Python dependencies
pip install -r backend/requirements.txt

# 5. Install Node dependencies (for React / Express web console)
npm install
```

### Windows (PowerShell)

```powershell
# 1. Install FFmpeg via winget
winget install Gyan.FFmpeg

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install Python dependencies
pip install -r backend/requirements.txt

# 4. Install Node dependencies
npm install
```

---

## 12. Configuration Options

Settings are centralized in `backend/utils/config.py` and can be customized via `.env`:

| Variable | Default | Description |
|---|---|---|
| `MAX_UPLOAD_SIZE_MB` | `15.0` | Maximum reference audio upload size in MB |
| `MIN_AUDIO_DURATION_SEC` | `3.0` | Minimum duration for reference recording |
| `MAX_AUDIO_DURATION_SEC` | `30.0` | Maximum duration for reference recording |
| `MAX_TEXT_LENGTH` | `1000` | Maximum allowed character length for synthesis text |
| `OUTPUT_RETENTION_HOURS` | `24` | Auto-cleanup threshold for generated WAV files |
| `TARGET_SAMPLE_RATE` | `16000` | Sampling frequency for synthesized speech output |
| `DEVICE` | `auto` | Execution device: `auto`, `cpu`, or `cuda` |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## 13. Running the Application

### Option A: Interactive Web UI (Port 3000)

Runs the Express backend, Python voice processing, and React UI with interactive waveform visualization:

```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### Option B: Streamlit Web Application

Runs the native Python Streamlit interface:

```bash
cd backend
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

### Option C: Command-Line Interface (CLI)

Synthesize speech directly from your terminal:

```bash
cd backend
python generate_sample.py \
  --ref samples/sample_voice.wav \
  --text "Speech synthesis completed using command-line interface." \
  --output outputs/cli_output.wav \
  --lang en \
  --authorized
```

---

## 14. Running Automated Tests

Run the full pytest suite:

```bash
cd backend
pytest -v tests/
```

Or run via the built-in test runner:

```bash
cd backend
python run_tests.py
```

### Test Suite Coverage:
- `tests/test_audio_validation.py`: Tests valid audio, 0-byte uploads, bad extensions, file size ceiling, min/max duration bounds, and non-finite NaN/Inf samples.
- `tests/test_text_validation.py`: Tests valid text, empty strings, whitespace, character limit overflow, unpronounceable punctuation, multilingual Unicode, and authorization confirmation.
- `tests/test_output_service.py`: Tests collision-free filename generation, directory creation, atomic WAV writing, empty byte rejection, and retention purging.
- `tests/test_model_service.py`: Tests model initialization, caching, missing reference rejection, empty text rejection, and end-to-end inference sample generation.

---

## 15. Expected Application Workflow

1. **Upload Reference Voice**: Upload an authorized audio recording (3s–30s) or click "Load Sample Voice".
2. **Review Audio Inspection**: The system decodes the audio, computes duration, sample rate, channels, and displays a waveform preview.
3. **Confirm Speaker Consent**: Check the mandatory authorization box certifying ownership or explicit permission.
4. **Enter Text & Select Language**: Type the speech text (up to 1,000 characters) and select the desired language.
5. **Click "Generate Speech"**: The engine extracts acoustic speaker embeddings, synthesizes the speech, encodes 16-bit PCM WAV bytes, and verifies the output.
6. **Preview & Download**: Listen to the generated speech in the integrated audio player and click "Download WAV".

---

## 16. Performance Considerations

- **CPU Performance**: On standard 2-vCPU systems, synthesis takes ~0.2s to 1.8s for typical sentences (100–200 characters).
- **GPU Performance**: With CUDA enabled, neural vocoder latency decreases to under 0.1s.
- **Memory Consumption**: Memory usage is kept below 350 MB in default CPU mode, preventing out-of-memory errors on small virtual machines.

---

## 17. Privacy and Data-Retention Behavior

- **No Permanent Storage of Reference Audio**: Uploaded reference recordings are stored only in volatile temporary directories during analysis and deleted immediately after inference.
- **Privacy-Safe Logging**: The logging system records operational metrics (durations, sample rates, byte sizes) and **never** writes raw audio samples or speech transcripts to log files.
- **Configurable Output Retention**: Generated outputs stored in `outputs/` are purged after 24 hours (`OUTPUT_RETENTION_HOURS`). Users can trigger instant cleanup via the UI or `cleanup_expired_outputs()`.

---

## 18. Troubleshooting Common Errors

| Error Message | Cause | Solution |
|---|---|---|
| `You must confirm that you own this recording...` | Authorization checkbox unchecked | Check the speaker permission checkbox before clicking Generate. |
| `The audio recording is too short (< 3.0s)` | Sample has insufficient acoustic data | Provide a reference recording between 3 and 30 seconds. |
| `Unsupported audio format` | Uploaded file has unsupported extension | Use standard WAV, MP3, FLAC, M4A, or OGG recordings. |
| `Text exceeds maximum allowed length` | Text is longer than 1,000 characters | Shorten the text or synthesize in multi-sentence paragraphs. |
| `FFmpeg is required for audio decoding` | FFmpeg binary not found on PATH | Install FFmpeg using `sudo apt install ffmpeg` or `brew install ffmpeg`. |
h---

## 19. Responsible Voice Use Notice

Generated speech is an acoustic approximation synthesized through artificial intelligence. In compliance with ethical AI practices, generated speech must never be presented as an authentic, unaltered recording of a living individual without clear disclosure of synthetic origin.
