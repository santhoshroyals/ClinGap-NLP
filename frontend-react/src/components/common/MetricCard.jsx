import React from 'react';

export function MetricCard({ title, value, subtitle, icon: Icon, color = 'teal', alert = false }) {
  const colorMap = {
    teal: 'from-teal-500/10 to-teal-500/5 text-teal-400 border-teal-500/20 group-hover:border-teal-500/40',
    rose: 'from-rose-500/10 to-rose-500/5 text-rose-400 border-rose-500/20 group-hover:border-rose-500/40',
    sky: 'from-sky-500/10 to-sky-500/5 text-sky-400 border-sky-500/20 group-hover:border-sky-500/40',
    amber: 'from-amber-500/10 to-amber-500/5 text-amber-400 border-amber-500/20 group-hover:border-amber-500/40',
    indigo: 'from-indigo-500/10 to-indigo-500/5 text-indigo-400 border-indigo-500/20 group-hover:border-indigo-500/40',
  };

  const activeTheme = colorMap[color] || colorMap.teal;

  return (
    <div className={`group relative overflow-hidden rounded-xl p-5 border bg-gradient-to-b ${activeTheme} transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/40`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          {title}
        </span>
        {Icon && (
          <div className="p-2 rounded-lg bg-slate-900/60 border border-slate-700/50">
            <Icon className="w-5 h-5 opacity-90" />
          </div>
        )}
      </div>

      <div className="mt-4 flex items-baseline gap-2">
        <div className="text-3xl font-bold tracking-tight text-white font-mono">
          {value}
        </div>
        {alert && (
          <span className="inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30">
            Action Needed
          </span>
        )}
      </div>

      {subtitle && (
        <p className="mt-1 text-xs text-slate-400 leading-relaxed">
          {subtitle}
        </p>
      )}
    </div>
  );
}
