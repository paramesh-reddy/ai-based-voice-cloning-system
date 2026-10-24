import React, { useRef, useState } from 'react';
import { Sparkles, FileAudio, RefreshCw, AlertCircle, CheckCircle2, Play, Pause } from 'lucide-react';
import { AudioMetadata } from '../types';

interface ReferenceAudioCardProps {
  metadata: AudioMetadata | null;
  audioBase64: string | null;
  loading: boolean;
  error: string | null;
  onLoadSample: () => void;
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export const ReferenceAudioCard: React.FC<ReferenceAudioCardProps> = ({
  metadata,
  audioBase64,
  loading,
  error,
  onLoadSample,
  onFileUpload,
}) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const togglePlayback = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="flex h-6 w-6 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold items-center justify-center">
            1
          </span>
          <h2 className="text-base font-bold text-slate-900">Reference Voice Recording</h2>
        </div>
        <button
          onClick={onLoadSample}
          disabled={loading}
          className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center transition"
        >
          <Sparkles className="w-3.5 h-3.5 mr-1" />
          Load Sample Voice
        </button>
      </div>

      <p className="text-xs text-slate-600">
        Upload an audio recording of the speaker to clone (3s to 30s). Supported: WAV, MP3, FLAC, M4A, OGG up to 15 MB.
      </p>

      {/* Upload Drag/Drop Box */}
      <div className="relative border-2 border-dashed border-slate-300 hover:border-indigo-400 rounded-xl p-5 text-center transition bg-slate-50/50">
        <input
          type="file"
          accept=".wav,.mp3,.flac,.m4a,.ogg,audio/*"
          onChange={onFileUpload}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        <div className="flex flex-col items-center justify-center space-y-2">
          <div className="p-2.5 rounded-full bg-white shadow-sm border border-slate-200 text-indigo-600">
            <FileAudio className="w-5 h-5" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-800">
              Drop audio file here or <span className="text-indigo-600 underline">browse</span>
            </p>
            <p className="text-xs text-slate-500 mt-0.5">WAV, MP3, FLAC, M4A, OGG (Max 15MB)</p>
          </div>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center space-x-2 p-3 bg-slate-50 rounded-xl text-xs text-slate-600">
          <RefreshCw className="w-4 h-4 animate-spin text-indigo-600" />
          <span>Analyzing audio format, duration, and sampling rate...</span>
        </div>
      )}

      {error && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-2.5 text-xs text-rose-800">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <strong className="font-semibold">Validation Error:</strong> {error}
          </div>
        </div>
      )}

      {metadata && metadata.is_valid && (
        <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span className="text-xs font-semibold text-emerald-800">Audio Validated &amp; Ready</span>
            </div>
            <span className="text-xs text-slate-500 font-mono">
              {(metadata.fileSizeBytes / 1024).toFixed(1)} KB
            </span>
          </div>

          <div className="text-xs font-medium text-slate-800 truncate" title={metadata.filename}>
            {metadata.filename}
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div className="bg-white p-2 rounded-lg border border-slate-200">
              <span className="text-slate-400 block text-[10px] uppercase">Duration</span>
              <span className="font-semibold text-slate-800">{metadata.duration.toFixed(1)}s</span>
            </div>
            <div className="bg-white p-2 rounded-lg border border-slate-200">
              <span className="text-slate-400 block text-[10px] uppercase">Sample Rate</span>
              <span className="font-semibold text-slate-800">{metadata.sampleRate} Hz</span>
            </div>
            <div className="bg-white p-2 rounded-lg border border-slate-200">
              <span className="text-slate-400 block text-[10px] uppercase">Channels</span>
              <span className="font-semibold text-slate-800">
                {metadata.channels === 1 ? 'Mono' : 'Stereo'}
              </span>
            </div>
          </div>

          {/* Audio Player Preview */}
          {audioBase64 && (
            <div className="pt-2 flex items-center space-x-3">
              <audio
                ref={audioRef}
                src={`data:audio/wav;base64,${audioBase64}`}
                onEnded={() => setIsPlaying(false)}
              />
              <button
                onClick={togglePlayback}
                className="flex items-center justify-center h-8 w-8 rounded-full bg-indigo-600 text-white hover:bg-indigo-700 transition shadow-sm"
                title={isPlaying ? 'Pause Reference' : 'Play Reference'}
              >
                {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 ml-0.5" />}
              </button>
              <div className="flex-1 flex items-center space-x-1 h-6">
                {(metadata.peaks || [0.4, 0.6, 0.3, 0.7, 0.5, 0.8, 0.4, 0.6, 0.5]).map((p, i) => (
                  <div
                    key={i}
                    className={`flex-1 rounded-full transition-all ${
                      isPlaying ? 'bg-indigo-500 animate-pulse' : 'bg-slate-300'
                    }`}
                    style={{ height: `${Math.max(15, p * 100)}%` }}
                  />
                ))}
              </div>
              <span className="text-[11px] font-mono text-slate-500">
                {metadata.duration.toFixed(1)}s
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
