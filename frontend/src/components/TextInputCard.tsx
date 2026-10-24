import React from 'react';
import { Sparkles, RefreshCw, AlertCircle } from 'lucide-react';
import { LanguageOption } from '../types';

interface TextInputCardProps {
  text: string;
  onTextChange: (newText: string) => void;
  selectedLang: string;
  onLangChange: (lang: string) => void;
  languages: LanguageOption[];
  onGenerate: () => void;
  canGenerate: boolean;
  isGenerating: boolean;
  generationError: string | null;
  disabledReason?: string;
}

const PRESETS = [
  {
    label: 'Welcome Greeting',
    text: 'Welcome to the AI-Based Voice Cloning System. This speech is generated using reference-conditioned acoustic modeling.',
  },
  {
    label: 'Instructional Guide',
    text: 'Please upload an authorized reference voice recording and enter your target text to synthesize natural spoken audio.',
  },
  {
    label: 'Technical Brief',
    text: 'The acoustic feature pipeline extracts fundamental pitch and vocal tract formants from your reference recording to condition synthesis.',
  },
];

export const TextInputCard: React.FC<TextInputCardProps> = ({
  text,
  onTextChange,
  selectedLang,
  onLangChange,
  languages,
  onGenerate,
  canGenerate,
  isGenerating,
  generationError,
  disabledReason,
}) => {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="flex h-6 w-6 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold items-center justify-center">
            3
          </span>
          <h2 className="text-base font-bold text-slate-900">Speech Text &amp; Language</h2>
        </div>

        <div className="flex items-center space-x-2">
          <label className="text-xs text-slate-500 font-medium">Output Language:</label>
          <select
            value={selectedLang}
            onChange={(e) => onLangChange(e.target.value)}
            className="text-xs font-medium bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          >
            {languages.map((l) => (
              <option key={l.code} value={l.code}>
                {l.name} ({l.code})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Preset suggestions */}
      <div className="flex flex-wrap gap-1.5 items-center">
        <span className="text-[11px] text-slate-400 font-medium mr-1">Sample prompts:</span>
        {PRESETS.map((p, i) => (
          <button
            key={i}
            type="button"
            onClick={() => onTextChange(p.text)}
            className="text-[11px] px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 transition"
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Multiline Text Input */}
      <div className="space-y-1.5">
        <label className="block text-xs font-semibold text-slate-700">
          Enter the text you want to convert into speech:
        </label>
        <textarea
          rows={4}
          value={text}
          onChange={(e) => onTextChange(e.target.value)}
          placeholder="Enter speech script here..."
          className="w-full text-sm rounded-xl border border-slate-200 p-3.5 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 focus:outline-none transition resize-none leading-relaxed"
        />
        <div className="flex items-center justify-between text-xs">
          <span
            className={`font-mono text-[11px] ${
              text.length > 1000 ? 'text-rose-600 font-semibold' : 'text-slate-500'
            }`}
          >
            {text.length} / 1,000 characters
          </span>
          {text.length > 1000 && (
            <span className="text-rose-600 text-[11px] font-medium">
              Exceeds maximum limit of 1,000 characters.
            </span>
          )}
        </div>
      </div>

      {/* Error Banner */}
      {generationError && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-2 text-xs text-rose-800">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <strong className="font-semibold">Synthesis Error:</strong> {generationError}
          </div>
        </div>
      )}

      {/* Generate Speech Button */}
      <button
        type="button"
        onClick={onGenerate}
        disabled={!canGenerate}
        className={`w-full py-3.5 px-6 rounded-xl font-semibold text-sm flex items-center justify-center space-x-2 transition shadow-md ${
          canGenerate
            ? 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-indigo-200 active:scale-[0.99]'
            : 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'
        }`}
      >
        {isGenerating ? (
          <>
            <RefreshCw className="w-4 h-4 animate-spin text-white" />
            <span>Extracting speaker acoustics &amp; synthesizing speech...</span>
          </>
        ) : (
          <>
            <Sparkles className="w-4 h-4" />
            <span>Generate Speech</span>
          </>
        )}
      </button>

      {!canGenerate && disabledReason && (
        <p className="text-center text-[11px] text-slate-400">{disabledReason}</p>
      )}
    </div>
  );
};
