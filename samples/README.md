# Authorized Reference Audio Samples & Workflow

This directory contains reference audio samples and corresponding generated speech outputs for validating the AI-Based Voice Cloning System.

## Authorized Voice Sample Policy

Only voice recordings for which the user holds explicit copyright or documented written consent from the speaker are permitted for voice cloning. Never upload or distribute voice samples without explicit authorization.

## Bundled Sample Files

1. `sample_voice.wav`:
   - **Type:** Authorized reference voice recording.
   - **Duration:** 4.2 seconds.
   - **Sampling Rate:** 16,000 Hz.
   - **Format:** 16-bit PCM Mono WAV.
   - **Characteristics:** Neutral reading of standard phonetically balanced English speech.

2. `sample_generated_output.wav`:
   - **Type:** Generated speech output synthesized using the reference voice.
   - **Synthesized Text:** *"Welcome to the AI-Based Voice Cloning System. This speech is generated using reference-conditioned acoustic modeling."*
   - **Synthesizer:** SpeechT5 / Acoustic Resonance Voice Cloning Engine.
   - **Output Format:** 16-bit PCM Mono WAV.

## Generating Sample Speech via CLI

You can generate speech from a custom reference recording using the command-line interface:

```bash
python3 generate_sample.py \
  --ref samples/sample_voice.wav \
  --text "Hello! This is a verification test of the voice cloning pipeline." \
  --output outputs/cli_test_output.wav \
  --authorized
```

## How to Record Your Own Reference Audio

For optimal speaker acoustic conditioning:
1. Use a clear microphone with minimal background noise and room reverberation.
2. Record between 5 and 15 seconds of steady, natural conversational speech.
3. Save the file in WAV, MP3, or FLAC format.
4. Ensure the audio is between 3 and 30 seconds in duration.
5. Confirm your authorization in the application prior to synthesis.
