import React from 'react';
import { Play, RotateCcw, Activity, Clock, CheckCircle2, AlertCircle } from 'lucide-react';
import { useAnalysis, DEMO_PRESETS } from '../../context/AnalysisContext';

export function Header() {
  const {
    activeTab,
    loading,
    backendHealth,
    lastAnalyzedAt,
    runAnalysis,
    loadPreset,
    rawText,
    patientId,
    documentId,
    error,
  } = useAnalysis();

  const getPageTitle = () => {
    switch (activeTab) {
      case 'dashboard': return 'Executive Analytics Dashboard';
      case 'input': return 'Clinical Note & Document Ingestion';
      case 'entities': return 'Extracted Named Entities (NER)';
      case 'guidelines': return 'Evidence-Based Guideline Matching';
      case 'gaps': return 'Clinical Decision Gap Detection';
      case 'prescriptions': return 'Prescription & Regimen Analysis';
      case 'timeline': return 'Clinical Event Timeline & Sequence';
      case 'about': return 'Architecture, Methodology & Disclaimer';
      default: return 'ClinGap-NLP';
    }
  };

  return (
    <header className="h-16 flex-shrink-0 glass-panel border-b border-slate-800/80 px-6 flex items-center justify-between z-10">
      <div className="flex items-center gap-4">
        <div>
          <h2 className="text-sm font-semibold text-white tracking-tight">
            {getPageTitle()}
          </h2>
          <p className="text-[11px] text-slate-400">
            Source: <span className="text-teal-400 font-mono">http://127.0.0.1:8001/api/analyze</span>
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Preset Selector */}
        <div className="hidden md:flex items-center gap-2">
          <span className="text-[11px] text-slate-400 font-medium">Quick Cases:</span>
          <div className="flex rounded-lg bg-slate-900/90 p-0.5 border border-slate-800">
            {DEMO_PRESETS.map((preset, idx) => (
              <button
                key={preset.id}
                onClick={() => loadPreset(preset.id)}
                className="px-2.5 py-1 text-xs font-medium rounded-md text-slate-300 hover:text-white hover:bg-slate-800/70 transition-colors"
                title={preset.title}
              >
                Case {idx + 1}
              </button>
            ))}
          </div>
        </div>

        {/* Re-analyze Button */}
        <button
          onClick={() => runAnalysis({ text: rawText, patient_id: patientId, document_id: documentId })}
          disabled={loading || !rawText.trim()}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-teal-500 to-emerald-500 text-slate-950 hover:from-teal-400 hover:to-emerald-400 transition-all duration-200 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          {loading ? (
            <>
              <RotateCcw className="w-3.5 h-3.5 animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Run Pipeline</span>
            </>
          )}
        </button>

        {/* Timestamp */}
        {lastAnalyzedAt && (
          <div className="hidden lg:flex items-center gap-1.5 text-[11px] text-slate-400 pl-2 border-l border-slate-800">
            <Clock className="w-3 h-3 text-slate-500" />
            <span>
              {(() => {
                try {
                  const d = lastAnalyzedAt instanceof Date ? lastAnalyzedAt : new Date(lastAnalyzedAt);
                  return !isNaN(d.getTime()) ? d.toLocaleTimeString() : '';
                } catch {
                  return '';
                }
              })()}
            </span>
          </div>
        )}
      </div>
    </header>
  );
}
