import React, { useRef, useState } from 'react';
import { CheckCircle2, Download, Play, Pause, Info } from 'lucide-react';
import { GenerationResponse } from '../types';

interface OutputPlayerCardProps {
  result: GenerationResponse;
}

export const OutputPlayerCard: React.FC<OutputPlayerCardProps> = ({ result }) => {
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
    <div className="bg-white rounded-2xl border border-emerald-200 shadow-md shadow-emerald-50 p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="h-6 w-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <h3 className="font-bold text-slate-900 text-base">Generated Speech Output</h3>
        </div>

        <a
          href={`/api/download/${result.filename}`}
          download={result.filename}
          className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition"
        >
          <Download className="w-3.5 h-3.5 mr-1.5" />
          Download WAV
        </a>
      </div>

      {/* Audio Player Card */}
      <div className="bg-slate-900 rounded-xl p-4 text-white space-y-3">
        <audio
          ref={audioRef}
          src={`data:${result.mimeType};base64,${result.base64Audio}`}
          onEnded={() => setIsPlaying(false)}
        />

        <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
          <span>{result.filename}</span>
          <span>{result.duration.toFixed(2)}s</span>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={togglePlayback}
            className="flex items-center justify-center h-10 w-10 rounded-full bg-emerald-500 text-white hover:bg-emerald-400 transition shadow"
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
          </button>

          <div className="flex-1 flex items-center space-x-1 h-8">
            {Array.from({ length: 36 }).map((_, i) => (
              <div
                key={i}
                className={`flex-1 rounded-full transition-all ${
                  isPlaying ? 'bg-emerald-400 animate-pulse' : 'bg-slate-700'
                }`}
                style={{
                  height: `${20 + Math.sin(i * 0.45) * 40 + Math.cos(i * 0.3) * 35}%`,
                }}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Output Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
        <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
          <span className="text-slate-400 block text-[10px] uppercase">Duration</span>
          <span className="font-semibold text-slate-800">{result.duration.toFixed(2)}s</span>
        </div>
        <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
          <span className="text-slate-400 block text-[10px] uppercase">Inference Time</span>
          <span className="font-semibold text-slate-800">{result.latency.toFixed(2)}s</span>
        </div>
        <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
          <span className="text-slate-400 block text-[10px] uppercase">Format</span>
          <span className="font-semibold text-slate-800">16-bit PCM WAV</span>
        </div>
        <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
          <span className="text-slate-400 block text-[10px] uppercase">Sample Rate</span>
          <span className="font-semibold text-slate-800">{result.sampleRate} Hz</span>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="text-[11px] text-slate-500 bg-slate-50 p-3 rounded-lg border border-slate-200 flex items-start space-x-2">
        <Info className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
        <span>
          {result.disclaimer} Generated speech is synthetic and must not be presented as an authentic recording.
        </span>
      </div>
    </div>
  );
};
