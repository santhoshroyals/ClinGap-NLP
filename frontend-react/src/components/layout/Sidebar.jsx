import React from 'react';
import {
  LayoutDashboard,
  FileText,
  ScanSearch,
  Compass,
  AlertTriangle,
  Pill,
  History,
  Info,
  Activity,
  ChevronRight,
  ShieldCheck,
  Stethoscope
} from 'lucide-react';
import { useAnalysis } from '../../context/AnalysisContext';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, badgeKey: null },
  { id: 'input', label: 'Clinical Input', icon: FileText, badgeKey: null },
  { id: 'entities', label: 'Entity Extraction', icon: ScanSearch, badgeKey: 'entities' },
  { id: 'guidelines', label: 'Guideline Matching', icon: Compass, badgeKey: 'guidelines' },
  { id: 'gaps', label: 'Gap Detection', icon: AlertTriangle, badgeKey: 'gaps' },
  { id: 'prescriptions', label: 'Prescription Analysis', icon: Pill, badgeKey: 'prescriptions' },
  { id: 'timeline', label: 'Clinical Timeline', icon: History, badgeKey: null },
  { id: 'about', label: 'About & Method', icon: Info, badgeKey: null },
];

export function Sidebar() {
  const { activeTab, setActiveTab, analysisResult, backendHealth } = useAnalysis();

  const getBadgeCount = (key) => {
    if (!analysisResult) return null;
    if (key === 'entities') return analysisResult.entities?.length || 0;
    if (key === 'gaps') return analysisResult.gaps?.length || 0;
    if (key === 'guidelines') return analysisResult.explanation?.matched_rules?.length || 0;
    if (key === 'prescriptions') {
      return analysisResult.entities?.filter(e => e.entity_type === 'MEDICATION')?.length || 0;
    }
    return null;
  };

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col glass-panel border-r border-slate-800/80 bg-slate-950/80 z-20">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800/60 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-600 to-emerald-400 flex items-center justify-center shadow-lg shadow-teal-500/20 text-white font-bold">
          <Stethoscope className="w-6 h-6 text-slate-950" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <h1 className="font-bold text-base text-white tracking-tight">ClinGap<span className="text-teal-400 font-mono">.NLP</span></h1>
            <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.2 rounded bg-teal-500/10 text-teal-400 border border-teal-500/20">v2.0</span>
          </div>
          <p className="text-[11px] text-slate-400">Clinical Decision Support</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Navigation
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          const count = getBadgeCount(item.badgeKey);

          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-200 group ${
                isActive
                  ? 'bg-gradient-to-r from-teal-500/15 to-emerald-500/5 text-teal-300 border border-teal-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    isActive ? 'text-teal-400' : 'text-slate-500 group-hover:text-slate-300'
                  }`}
                />
                <span className="tracking-wide">{item.label}</span>
              </div>

              <div className="flex items-center gap-1.5">
                {count !== null && count > 0 && (
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                      item.badgeKey === 'gaps'
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : isActive
                        ? 'bg-teal-500/20 text-teal-300'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {count}
                  </span>
                )}
                {isActive && <ChevronRight className="w-3.5 h-3.5 text-teal-400" />}
              </div>
            </button>
          );
        })}
      </nav>

      {/* System Status Footprint */}
      <div className="p-4 border-t border-slate-800/60 bg-slate-950/50">
        <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
          <div className="flex items-center gap-2">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                backendHealth === 'connected'
                  ? 'bg-emerald-400 animate-pulse ring-4 ring-emerald-400/20'
                  : backendHealth === 'offline'
                  ? 'bg-rose-400 ring-4 ring-rose-400/20'
                  : 'bg-amber-400 animate-pulse ring-4 ring-amber-400/20'
              }`}
            />
            <span className="text-[11px] font-medium text-slate-300">
              {backendHealth === 'connected'
                ? 'Backend Online'
                : backendHealth === 'offline'
                ? 'Backend Offline'
                : 'Connecting...'}
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-500">:8001</span>
        </div>

        <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 px-1">
          <span className="flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-teal-400" /> Guideline Matcher
          </span>
          <span className="font-mono text-[10px] text-slate-400">FastAPI</span>
        </div>
      </div>
    </aside>
  );
}
