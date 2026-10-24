import React from 'react';
import { ShieldCheck, Info } from 'lucide-react';

interface ConsentCardProps {
  hasPermission: boolean;
  onConsentChange: (value: boolean) => void;
}

export const ConsentCard: React.FC<ConsentCardProps> = ({ hasPermission, onConsentChange }) => {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
      <div className="flex items-center space-x-2">
        <span className="flex h-6 w-6 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold items-center justify-center">
          2
        </span>
        <h2 className="text-base font-bold text-slate-900">Speaker Authorization &amp; Consent</h2>
      </div>

      <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200/80 text-xs text-amber-900 space-y-1.5">
        <div className="flex items-center space-x-1.5 font-semibold text-amber-800">
          <ShieldCheck className="w-4 h-4 text-amber-600 shrink-0" />
          <span>Responsible AI Voice Policy</span>
        </div>
        <p>
          Voice synthesis is only permitted when you own the reference voice recording or have documented
          consent from the speaker. Unconsented voice impersonation is strictly prohibited.
        </p>
      </div>

      <label className="flex items-start space-x-3 cursor-pointer group select-none">
        <input
          type="checkbox"
          checked={hasPermission}
          onChange={(e) => onConsentChange(e.target.checked)}
          className="mt-1 h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
        />
        <span className="text-xs font-medium text-slate-700 leading-snug group-hover:text-slate-900 transition">
          I confirm that I own this voice recording or have explicit permission from the speaker to clone their voice.
        </span>
      </label>

      {!hasPermission && (
        <p className="text-[11px] text-amber-600 flex items-center">
          <Info className="w-3.5 h-3.5 mr-1 shrink-0" />
          Authorization confirmation is required before speech generation.
        </p>
      )}
    </div>
  );
};
