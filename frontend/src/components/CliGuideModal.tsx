import React from 'react';
import { Terminal } from 'lucide-react';

interface CliGuideModalProps {
  onClose: () => void;
}

export const CliGuideModal: React.FC<CliGuideModalProps> = ({ onClose }) => {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 max-w-4xl mx-auto space-y-6">
      <div className="border-b border-slate-100 pb-4">
        <h2 className="text-xl font-bold text-slate-900 flex items-center">
          <Terminal className="w-5 h-5 mr-2 text-indigo-600" />
          Backend Services &amp; CLI Execution Guide
        </h2>
        <p className="text-sm text-slate-600 mt-1">
          The project is cleanly decoupled into <code>backend/</code> (Python, Streamlit, PyTorch, Pytest) and{' '}
          <code>frontend/</code> (React, Tailwind CSS, TypeScript).
        </p>
      </div>

      <div className="space-y-4">
        <div className="bg-slate-900 text-slate-100 rounded-xl p-4 font-mono text-xs overflow-x-auto space-y-3">
          <p className="text-slate-400"># 1. Run the Streamlit web application from backend</p>
          <p className="text-emerald-400">streamlit run backend/app.py</p>

          <p className="text-slate-400"># 2. Run the automated test suite (pytest)</p>
          <p className="text-emerald-400">pytest -v backend/tests/</p>
          <p className="text-slate-400"># or via the integrated test runner:</p>
          <p className="text-emerald-400">python3 backend/run_tests.py</p>

          <p className="text-slate-400"># 3. Generate speech from CLI with authorized voice</p>
          <p className="text-emerald-400">
            python3 backend/generate_sample.py \<br />
            &nbsp;&nbsp;--ref backend/samples/sample_voice.wav \<br />
            &nbsp;&nbsp;--text "Synthesizing custom speech using authorized reference audio." \<br />
            &nbsp;&nbsp;--output backend/outputs/cli_output.wav \<br />
            &nbsp;&nbsp;--authorized
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl border border-slate-100 bg-slate-50">
            <h3 className="font-semibold text-slate-900 text-sm mb-1">Backend Architecture (Python)</h3>
            <ul className="text-xs text-slate-600 space-y-1">
              <li>• <code>backend/services/model_service.py</code> - SpeechT5 and acoustic modeling</li>
              <li>• <code>backend/services/audio_service.py</code> - FFmpeg decoding, resampling, normalization</li>
              <li>• <code>backend/services/validation_service.py</code> - Audio, text, and consent validation</li>
              <li>• <code>backend/services/output_service.py</code> - Safe unique filenames and retention</li>
            </ul>
          </div>

          <div className="p-4 rounded-xl border border-slate-100 bg-slate-50">
            <h3 className="font-semibold text-slate-900 text-sm mb-1">Frontend Architecture (React)</h3>
            <ul className="text-xs text-slate-600 space-y-1">
              <li>• <code>frontend/src/components/</code> - Modular UI components</li>
              <li>• <code>frontend/src/types.ts</code> - TypeScript interfaces</li>
              <li>• <code>server.ts</code> - Full-stack API bridge connecting frontend to backend</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="pt-2 text-right">
        <button
          onClick={onClose}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 transition"
        >
          Return to Voice Cloning Console
        </button>
      </div>
    </div>
  );
};
