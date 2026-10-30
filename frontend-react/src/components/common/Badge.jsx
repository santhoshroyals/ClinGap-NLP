import React from 'react';

const TYPE_STYLES = {
  DISEASE: 'bg-rose-500/10 text-rose-400 border-rose-500/30 hover:bg-rose-500/20',
  CONDITION: 'bg-rose-500/10 text-rose-400 border-rose-500/30 hover:bg-rose-500/20',
  INVESTIGATION: 'bg-sky-500/10 text-sky-400 border-sky-500/30 hover:bg-sky-500/20',
  MEDICATION: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20',
  DOSAGE: 'bg-amber-500/10 text-amber-400 border-amber-500/30 hover:bg-amber-500/20',
  FREQUENCY: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30 hover:bg-indigo-500/20',
  SYMPTOM: 'bg-purple-500/10 text-purple-400 border-purple-500/30 hover:bg-purple-500/20',
  DEFAULT: 'bg-slate-500/10 text-slate-400 border-slate-500/30 hover:bg-slate-500/20',
};

export function EntityBadge({ type, children, className = '' }) {
  const normalizedType = type?.toUpperCase() || 'DEFAULT';
  const style = TYPE_STYLES[normalizedType] || TYPE_STYLES.DEFAULT;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border tracking-wide transition-colors ${style} ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-80" />
      {children || type}
    </span>
  );
}

export function StatusBadge({ status, label, className = '' }) {
  const isPositive = status === 'performed' || status === 'active' || status === 'normal' || status === 'connected';
  const isNegative = status === 'not_performed' || status === 'negated' || status === 'gap' || status === 'offline';
  
  let style = 'bg-slate-800 text-slate-300 border-slate-700';
  if (isPositive) style = 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
  if (isNegative) style = 'bg-rose-500/15 text-rose-400 border-rose-500/30';

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${style} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${isPositive ? 'bg-emerald-400' : isNegative ? 'bg-rose-400' : 'bg-slate-400'}`} />
      {label}
    </span>
  );
}
