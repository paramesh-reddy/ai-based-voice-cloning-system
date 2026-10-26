import dotenv from 'dotenv';
import express, { Request, Response } from 'express';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { spawn, execFileSync } from 'child_process';
import { createServer as createViteServer } from 'vite';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.resolve(__dirname, '..', '.env') });

const BACKEND_DIR = __dirname;
const ROOT_DIR = path.resolve(__dirname, '..');
const FRONTEND_DIR = path.join(ROOT_DIR, 'frontend');

const app = express();
const PORT = Number(process.env.PORT) || 3000;

app.use(express.json({ limit: '30mb' }));
app.use(express.urlencoded({ extended: true, limit: '30mb' }));

const SAMPLES_DIR = path.join(BACKEND_DIR, 'samples');
const OUTPUTS_DIR = path.join(BACKEND_DIR, 'outputs');
const TEMP_DIR = path.join(BACKEND_DIR, 'temp');

for (const dir of [OUTPUTS_DIR, TEMP_DIR, SAMPLES_DIR]) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

type PythonCommand = { command: string; prefix: string[] };

function isRealPython(command: string, prefix: string[] = []): boolean {
  if ((command.includes('\\') || command.includes('/')) && !fs.existsSync(command)) {
    return false;
  }
  try {
    const output = execFileSync(command, [...prefix, '-c', 'import sys; print(sys.executable)'], {
      encoding: 'utf8',
      timeout: 15000,
      windowsHide: true,
    });
    const executable = output.trim().toLowerCase();
    return executable.endsWith('.exe') ? !executable.includes('windowsapps') : executable.length > 0;
  } catch {
    return false;
  }
}

function resolvePython(): PythonCommand | null {
  const localAppData = process.env.LOCALAPPDATA || '';
  const versions = ['Python313', 'Python312', 'Python311', 'Python310'];
  const candidates: PythonCommand[] = [];

  for (const version of versions) {
    if (localAppData) {
      candidates.push({ command: path.join(localAppData, 'Programs', 'Python', version, 'python.exe'), prefix: [] });
    }
    candidates.push({ command: path.join('C:\\Program Files', version, 'python.exe'), prefix: [] });
  }
  candidates.push({ command: 'py', prefix: ['-3'] });
  if (process.platform === 'win32') {
    candidates.push({ command: 'python', prefix: [] });
  } else {
    candidates.push({ command: 'python3', prefix: [] }, { command: 'python', prefix: [] });
  }

  for (const candidate of candidates) {
    if (isRealPython(candidate.command, candidate.prefix)) return candidate;
  }
  return null;
}

const PYTHON = resolvePython();

function runPython(args: string[]) {
  if (!PYTHON) {
    throw new Error('Python is not installed. Install Python 3.11 and restart the server.');
  }
  return spawn(PYTHON.command, [...PYTHON.prefix, ...args], {
    cwd: BACKEND_DIR,
    windowsHide: true,
    env: {
      ...process.env,
      PYTHONPATH: BACKEND_DIR,
      PYTHONIOENCODING: 'utf-8',
      LOG_LEVEL: process.env.LOG_LEVEL || 'INFO',
    },
  });
}

function parsePythonJson(output: string): Record<string, unknown> | null {
  const trimmed = output.trim();
  if (!trimmed) return null;
  try {
    return JSON.parse(trimmed);
  } catch {
    const lines = trimmed
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line.startsWith('{') && line.endsWith('}'));
    if (!lines.length) return null;
    try {
      return JSON.parse(lines[lines.length - 1]);
    } catch {
      return null;
    }
  }
}

app.get('/api/sample-audio', (_req: Request, res: Response) => {
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

app.post('/api/validate-audio', async (req: Request, res: Response) => {
  try {
    const { base64Audio, filename } = req.body;
    if (!base64Audio) {
      return res.status(400).json({ is_valid: false, error_message: 'Please upload a reference audio recording.' });
    }

    const buffer = Buffer.from(base64Audio, 'base64');
    const sizeBytes = buffer.length;
    const maxSizeBytes = 15 * 1024 * 1024;

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

    const tempFile = path.join(TEMP_DIR, `validate_${Date.now()}_${path.basename(filename || 'audio.wav')}`);
    fs.writeFileSync(tempFile, buffer);

    const pyProcess = runPython([
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
    let errorData = '';
    pyProcess.stdout.on('data', (chunk) => {
      outputData += chunk.toString();
    });
    pyProcess.stderr.on('data', (chunk) => {
      errorData += chunk.toString();
    });
    pyProcess.on('error', (error) => {
      try {
        fs.unlinkSync(tempFile);
      } catch {
        /* temp file already removed */
      }
      if (!res.headersSent) {
        res.status(500).json({
          is_valid: false,
          error_message: `Audio inspection failed to start: ${error.message}`,
        });
      }
    });

    pyProcess.on('close', () => {
      try {
        fs.unlinkSync(tempFile);
      } catch {
        /* temp file already removed */
      }

      const result = parsePythonJson(outputData);
      if (!result) {
        const detail = (errorData || outputData || 'Python produced no output.').trim().slice(0, 500);
        console.error('Audio validation failed:', detail);
        if (!res.headersSent) {
          res.status(500).json({
            is_valid: false,
            error_message: `Failed to inspect audio metadata. ${detail}`,
          });
        }
        return;
      }

      res.json({
        ...result,
        fileSizeBytes: sizeBytes,
        filename: path.basename(filename || 'recording.wav'),
      });
    });
  } catch (err: any) {
    res.status(500).json({ is_valid: false, error_message: err.message || 'Internal audio validation error.' });
  }
});

app.post('/api/clone-voice', async (req: Request, res: Response) => {
  try {
    const { text, base64Audio, filename, language, hasPermission } = req.body;

    if (!hasPermission) {
      return res.status(403).json({
        success: false,
        error_message: 'You must confirm that you own this recording or have explicit permission from the speaker to clone their voice.',
      });
    }

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
    const scriptPath = path.join(BACKEND_DIR, 'generate_sample.py');

    const pyProcess = runPython([
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
      try {
        fs.unlinkSync(tempRefPath);
      } catch {
        /* temp file already removed */
      }

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
        disclaimer: 'Spoken from your text with a speech engine. This is synthetic speech, not a recording of the reference speaker.',
      });
    });
  } catch (err: any) {
    res.status(500).json({
      success: false,
      error_message: err.message || 'Speech generation encountered an internal error.',
    });
  }
});

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

async function startServer() {
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      configFile: path.join(FRONTEND_DIR, 'vite.config.ts'),
      root: FRONTEND_DIR,
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distDir = path.join(FRONTEND_DIR, 'dist');
    app.use(express.static(distDir));
    app.get('*', (_req: Request, res: Response) => {
      res.sendFile(path.join(distDir, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server is running at http://localhost:${PORT}`);
  });
}

startServer();
