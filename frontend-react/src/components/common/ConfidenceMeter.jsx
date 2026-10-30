import React from 'react';

export function ConfidenceMeter({ value = 0, size = 'md' }) {
  const percentage = Math.min(100, Math.max(0, Number(value) || 0));

  let colorClass = 'from-rose-500 to-amber-500 text-rose-400';
  let badgeText = 'Low Confidence';
  if (percentage >= 70) {
    colorClass = 'from-teal-500 to-emerald-400 text-teal-300';
    badgeText = 'High Adherence';
  } else if (percentage >= 40) {
    colorClass = 'from-sky-500 to-indigo-500 text-sky-300';
    badgeText = 'Moderate';
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium text-slate-400">Guideline Match Confidence</span>
        <div className="flex items-center gap-2">
          <span className="font-mono font-bold text-sm text-slate-100">{percentage.toFixed(1)}%</span>
          <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
            {badgeText}
          </span>
        </div>
      </div>
      <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-slate-800/80 p-0.5 border border-slate-700/50">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${colorClass} transition-all duration-700 ease-out shadow-sm`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-slate-500 font-mono">
        <span>0%</span>
        <span>50%</span>
        <span>100%</span>
      </div>
    </div>
  );
}
