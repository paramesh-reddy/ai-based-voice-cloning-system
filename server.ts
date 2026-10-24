import express, { Request, Response } from 'express';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';
import { createServer as createViteServer } from 'vite';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = Number(process.env.PORT) || 3000;

app.use(express.json({ limit: '30mb' }));
app.use(express.urlencoded({ extended: true, limit: '30mb' }));

const SAMPLES_DIR = fs.existsSync(path.join(__dirname, 'backend', 'samples'))
  ? path.join(__dirname, 'backend', 'samples')
  : path.join(__dirname, 'samples');
const OUTPUTS_DIR = fs.existsSync(path.join(__dirname, 'backend', 'outputs'))
  ? path.join(__dirname, 'backend', 'outputs')
  : path.join(__dirname, 'outputs');
const TEMP_DIR = path.join(__dirname, 'temp');

if (!fs.existsSync(OUTPUTS_DIR)) fs.mkdirSync(OUTPUTS_DIR, { recursive: true });
if (!fs.existsSync(TEMP_DIR)) fs.mkdirSync(TEMP_DIR, { recursive: true });
if (!fs.existsSync(SAMPLES_DIR)) fs.mkdirSync(SAMPLES_DIR, { recursive: true });

// Endpoint: Fetch bundled sample audio
app.get('/api/sample-audio', (req: Request, res: Response) => {
  const samplePath = path.join(SAMPLES_DIR, 'sample_voice.wav');
  if (!fs.existsSync(samplePath)) {
    return res.status(404).json({ error: 'Sample audio file not found' });
  }
  const fileBuffer = fs.readFileSync(samplePath);
  res.json({
    filename: 'sample_voice.wav',
    duration: 4.5,
    sampleRate: 16000,
    channels: 1,
    format: 'WAV',
    sizeBytes: fileBuffer.length,
    base64: fileBuffer.toString('base64'),
    mimeType: 'audio/wav',
  });
});

// Endpoint: Validate uploaded audio
app.post('/api/validate-audio', async (req: Request, res: Response) => {
  try {
    const { base64Audio, filename } = req.body;
    if (!base64Audio) {
      return res.status(400).json({ is_valid: false, error_message: 'Please upload a reference audio recording.' });
    }

    const buffer = Buffer.from(base64Audio, 'base64');
    const sizeBytes = buffer.length;
    const maxSizeBytes = 15 * 1024 * 1024; // 15 MB

    if (sizeBytes === 0) {
      return res.status(400).json({ is_valid: false, error_message: 'The uploaded audio file is empty.' });
    }
    if (sizeBytes > maxSizeBytes) {
      return res.status(400).json({
        is_valid: false,
        error_message: `The uploaded file exceeds the maximum allowed size of 15 MB (${(sizeBytes / (1024 * 1024)).toFixed(2)} MB).`,
      });
    }

    const ext = path.extname(filename || 'recording.wav').toLowerCase();
    const allowedExts = ['.wav', '.mp3', '.flac', '.m4a', '.ogg'];
    if (!allowedExts.includes(ext)) {
      return res.status(400).json({
        is_valid: false,
        error_message: `Unsupported audio format '${ext}'. Allowed formats: ${allowedExts.join(', ')}.`,
      });
    }

    // Write temp file to probe via ffprobe/ffmpeg
    const tempFile = path.join(TEMP_DIR, `validate_${Date.now()}_${path.basename(filename || 'audio.wav')}`);
    fs.writeFileSync(tempFile, buffer);

    // Call python inspection script
    const pyProcess = spawn('python3', [
      '-c',
      `
import sys, json
from services.audio_service import decode_audio_with_ffmpeg, extract_audio_metadata, generate_waveform_peaks
from services.validation_service import validate_audio_content
try:
    path = sys.argv[1]
    samples, sr = decode_audio_with_ffmpeg(path)
    meta = extract_audio_metadata(path)
    content_res = validate_audio_content(
        duration_sec=meta.duration_sec,
        sample_rate=sr,
        num_samples=len(samples),
        is_finite=True
    )
    peaks = generate_waveform_peaks(samples, num_buckets=48)
    print(json.dumps({
        "is_valid": content_res.is_valid,
        "error_message": content_res.error_message,
        "duration": meta.duration_sec,
        "sampleRate": sr,
        "channels": meta.num_channels,
        "format": meta.format,
        "peaks": peaks
    }))
except Exception as e:
    print(json.dumps({"is_valid": False, "error_message": f"Audio decoding failed: {str(e)}"}))
      `,
      tempFile,
    ]);

    let outputData = '';
    pyProcess.stdout.on('data', (chunk) => {
      outputData += chunk.toString();
    });

    pyProcess.on('close', () => {
      // Clean up temp file
      try {
        fs.unlinkSync(tempFile);
      } catch (e) {}

      try {
        const result = JSON.parse(outputData.trim());
        res.json({
          ...result,
          fileSizeBytes: sizeBytes,
          filename: path.basename(filename || 'recording.wav'),
        });
      } catch (e) {
        res.status(500).json({ is_valid: false, error_message: 'Failed to inspect audio metadata.' });
      }
    });
  } catch (err: any) {
    res.status(500).json({ is_valid: false, error_message: err.message || 'Internal audio validation error.' });
  }
});

// Endpoint: Generate Speech (Voice Cloning)
app.post('/api/clone-voice', async (req: Request, res: Response) => {
  try {
    const { text, base64Audio, filename, language, hasPermission } = req.body;

    // 1. Authorization check
    if (!hasPermission) {
      return res.status(403).json({
        success: false,
        error_message: 'You must confirm that you own this recording or have explicit permission from the speaker to clone their voice.',
      });
    }

    // 2. Text check
    if (!text || !text.trim()) {
      return res.status(400).json({
        success: false,
        error_message: 'The entered text cannot be empty or contain only whitespace.',
      });
    }
    if (text.length > 1000) {
      return res.status(400).json({
        success: false,
        error_message: `Text exceeds the maximum allowed length of 1000 characters (currently ${text.length}).`,
      });
    }

    if (!base64Audio) {
      return res.status(400).json({
        success: false,
        error_message: 'Please upload a reference audio recording before generating speech.',
      });
    }

    const refBuffer = Buffer.from(base64Audio, 'base64');
    const safeRefExt = path.extname(filename || 'ref.wav') || '.wav';
    const tempRefPath = path.join(TEMP_DIR, `ref_${Date.now()}_${Math.random().toString(36).substring(7)}${safeRefExt}`);
    fs.writeFileSync(tempRefPath, refBuffer);

    const safeTimestamp = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 15);
    const outputFilename = `generated_speech_${safeTimestamp}_${Math.random().toString(36).substring(7)}.wav`;
    const outputPath = path.join(OUTPUTS_DIR, outputFilename);

    const startTime = Date.now();

    const scriptPath = fs.existsSync(path.join(__dirname, 'backend', 'generate_sample.py'))
      ? path.join(__dirname, 'backend', 'generate_sample.py')
      : path.join(__dirname, 'generate_sample.py');

    const pyProcess = spawn('python3', [
      scriptPath,
      '--ref', tempRefPath,
      '--text', text.trim(),
      '--output', outputPath,
      '--lang', language || 'en',
      '--authorized',
    ]);

    let stderr = '';
    let stdout = '';

    pyProcess.stdout.on('data', (d) => {
      stdout += d.toString();
    });
    pyProcess.stderr.on('data', (d) => {
      stderr += d.toString();
    });

    pyProcess.on('close', (code) => {
      // Clean temp reference file
      try {
        fs.unlinkSync(tempRefPath);
      } catch (e) {}

      if (code !== 0 || !fs.existsSync(outputPath)) {
        return res.status(500).json({
          success: false,
          error_message: stderr.trim() || stdout.trim() || 'Speech synthesis failed during model inference.',
        });
      }

      const generatedBytes = fs.readFileSync(outputPath);
      const latencySec = ((Date.now() - startTime) / 1000).toFixed(2);
      const durationSec = (generatedBytes.length / (16000 * 2)).toFixed(2);

      res.json({
        success: true,
        filename: outputFilename,
        duration: parseFloat(durationSec),
        latency: parseFloat(latencySec),
        sampleRate: 16000,
        format: '16-bit PCM WAV',
        base64Audio: generatedBytes.toString('base64'),
        mimeType: 'audio/wav',
        disclaimer: 'Synthetic speech output generated with reference-conditioned acoustic modeling for authorized use.',
      });
    });
  } catch (err: any) {
    res.status(500).json({
      success: false,
      error_message: err.message || 'Speech generation encountered an internal error.',
    });
  }
});

// Endpoint: Download generated audio file
app.get('/api/download/:filename', (req: Request, res: Response) => {
  const safeName = path.basename(req.params.filename);
  const filePath = path.join(OUTPUTS_DIR, safeName);
  if (!fs.existsSync(filePath)) {
    return res.status(404).json({ error: 'Requested audio file not found or expired.' });
  }
  res.setHeader('Content-Disposition', `attachment; filename="${safeName}"`);
  res.setHeader('Content-Type', 'audio/wav');
  fs.createReadStream(filePath).pipe(res);
});

// Setup Vite middleware for local development
async function startServer() {
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.join(__dirname, 'dist')));
    app.get('*', (req: Request, res: Response) => {
      res.sendFile(path.join(__dirname, 'dist', 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server is running at http://0.0.0.0:${PORT}`);
  });
}

startServer();
