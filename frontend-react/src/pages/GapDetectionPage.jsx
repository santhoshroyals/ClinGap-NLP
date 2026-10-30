import React from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  HelpCircle,
  FileWarning,
  Activity,
  ArrowRight
} from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';
import { ConfidenceMeter } from '../components/common/ConfidenceMeter';

export function GapDetectionPage() {
  const { analysisResult, loading, setActiveTab } = useAnalysis();

  const gaps = analysisResult?.gaps || [];
  const confidence = analysisResult?.confidence || 0;
  const entities = analysisResult?.entities || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-rose-400" />
            Clinical Decision Gap Detection
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Automated discovery of omitted diagnostics, missing laboratory orders, or documentation lapses against guideline benchmarks.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Gaps Found:</span>
          <span
            className={`px-3 py-1 rounded-full font-mono text-xs font-bold border ${
              gaps.length > 0
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
            }`}
          >
            {gaps.length} Issue{gaps.length === 1 ? '' : 's'}
          </span>
        </div>
      </div>

      {/* Confidence & Score Card */}
      <div className="glass-card rounded-2xl p-6">
        <ConfidenceMeter value={confidence} />
        <div className="mt-4 pt-3 border-t border-slate-800 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
          <span>Formula: <code className="font-mono text-slate-300 text-[11px]">(Entity Score + Gap Score) × 100</code></span>
          <span>Score: <strong className="font-mono text-teal-300">{confidence}%</strong></span>
        </div>
      </div>

      {/* Gaps List Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Audit Findings & Gap Inventory
          </h3>
          <span className="text-xs text-slate-500">
            {gaps.length === 0 ? 'Optimal documentation' : 'Requires clinical review'}
          </span>
        </div>

        {gaps.length === 0 ? (
          <div className="glass-panel rounded-2xl p-12 text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto shadow-lg shadow-emerald-500/10">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <div className="space-y-1 max-w-md mx-auto">
              <h4 className="text-base font-bold text-white">No Clinical Decision Gaps Identified</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                The current clinical documentation satisfies all active evidence-based guideline recommendations. No missing investigations were detected.
              </p>
            </div>
            <button
              onClick={() => setActiveTab('entities')}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-200 hover:bg-slate-700 border border-slate-700 transition-all inline-flex items-center gap-1.5"
            >
              Inspect Extracted Findings <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {gaps.map((gap, idx) => (
              <div
                key={idx}
                className="glass-card rounded-xl p-6 border-l-4 border-l-rose-500 border border-slate-800/80 bg-gradient-to-r from-rose-950/20 via-slate-900 to-slate-900 shadow-md space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                      {gap.gap_type}
                    </span>
                    {gap.rule_id ? (
                      <span className="text-xs font-mono text-teal-300 bg-teal-500/10 px-2 py-0.5 rounded border border-teal-500/20">
                        Triggered by Rule: {gap.rule_id}
                      </span>
                    ) : (
                      <span className="text-xs font-mono text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                        Explicit Negation in Note
                      </span>
                    )}
                  </div>

                  <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-950 text-slate-300 border border-slate-800 uppercase">
                    Target Entity: <strong className="text-white">{gap.entity}</strong>
                  </span>
                </div>

                <div className="space-y-1">
                  <p className="text-sm font-semibold text-rose-200 leading-relaxed">
                    {gap.description}
                  </p>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    {gap.rule_id
                      ? `Guideline protocol ${gap.rule_id} indicates that an investigation for '${gap.entity}' is standard care for the documented clinical condition.`
                      : `The clinical note explicitly documented that the investigation '${gap.entity}' was absent or not completed.`}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <span className="flex items-center gap-1.5 text-rose-400 font-medium">
                    <AlertTriangle className="w-3.5 h-3.5" /> Clinical Action Recommended
                  </span>
                  <button
                    onClick={() => setActiveTab('timeline')}
                    className="text-teal-400 hover:text-teal-300 font-medium flex items-center gap-1"
                  >
                    View in Timeline <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
