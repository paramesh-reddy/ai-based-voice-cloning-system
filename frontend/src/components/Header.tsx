import React from 'react';
import { Mic, Terminal } from 'lucide-react';

interface HeaderProps {
  activeTab: 'app' | 'cli';
  onToggleTab: () => void;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, onToggleTab }) => {
  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur sticky top-0 z-30 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-200">
            <Mic className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900">
              AI-Based Voice Cloning System
            </h1>
            <p className="text-xs text-slate-500 font-medium">
              Generate speech from text using an authorized reference voice recording.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={onToggleTab}
            className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-200 bg-slate-100 hover:bg-slate-200 text-slate-700 transition"
          >
            <Terminal className="w-3.5 h-3.5 mr-1.5 text-indigo-600" />
            {activeTab === 'app' ? 'Backend & CLI Docs' : 'Back to Voice Console'}
          </button>
          <span className="hidden sm:inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse"></span>
            Acoustic Pipeline Ready
          </span>
        </div>
      </div>
    </header>
  );
};
