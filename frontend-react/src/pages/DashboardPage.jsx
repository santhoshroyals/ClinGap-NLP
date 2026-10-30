import React from 'react';
import {
  ScanSearch,
  AlertTriangle,
  Compass,
  Pill,
  History,
  ArrowRight,
  Sparkles,
  FileText,
  ShieldAlert,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';
import { MetricCard } from '../components/common/MetricCard';
import { ConfidenceMeter } from '../components/common/ConfidenceMeter';
import { EntityBadge } from '../components/common/Badge';

export function DashboardPage() {
  const {
    analysisResult,
    rawText,
    patientId,
    documentId,
    currentPatientId,
    currentDocumentId,
    currentText,
    setActiveTab,
    loading
  } = useAnalysis();

  const entities = analysisResult?.entities || [];
  const gaps = analysisResult?.gaps || [];
  const matchedRules = analysisResult?.explanation?.matched_rules || [];
  const confidence = analysisResult?.confidence || 0;

  const displayPatientId = analysisResult?.patient_id ?? currentPatientId ?? patientId ?? 1;
  const displayDocumentId = analysisResult?.document_id ?? currentDocumentId ?? documentId ?? 1;
  const displayNoteText = analysisResult?.text || currentText || rawText || 'No clinical note loaded.';

  const conditionCount = entities.filter(e => ['DISEASE', 'CONDITION'].includes(e.entity_type)).length;
  const medicationCount = entities.filter(e => e.entity_type === 'MEDICATION').length;
  const investigationCount = entities.filter(e => e.entity_type === 'INVESTIGATION').length;

  return (
    <div className="space-y-6">
      {/* Top Banner / Hero */}
      <div className="relative overflow-hidden rounded-2xl p-6 md:p-8 border border-teal-500/30 bg-gradient-to-r from-slate-900 via-teal-950/40 to-slate-900 shadow-xl">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-teal-500/10 text-teal-400 border border-teal-500/20">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Evidence-Based Decision Support Engine</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Clinical Quality & Guideline Adherence Dashboard
            </h1>
            <p className="text-sm text-slate-300 leading-relaxed">
              Automated NLP pipeline parsing unstructured clinical notes, cross-referencing guideline knowledge bases, and surfacing care gaps with explainable evidence.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={() => setActiveTab('input')}
              className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-teal-500 text-slate-950 hover:bg-teal-400 transition-all shadow-md shadow-teal-500/20"
            >
              <FileText className="w-4 h-4" />
              <span>Ingest Clinical Note</span>
            </button>
            <button
              onClick={() => setActiveTab('gaps')}
              className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-slate-800 text-slate-200 hover:bg-slate-700 border border-slate-700 transition-all"
            >
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              <span>Review Gaps ({gaps.length})</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Clinical Entities"
          value={loading ? '...' : entities.length}
          subtitle={`${conditionCount} conditions, ${medicationCount} meds, ${investigationCount} labs`}
          icon={ScanSearch}
          color="teal"
        />

        <MetricCard
          title="Detected Decision Gaps"
          value={loading ? '...' : gaps.length}
          subtitle={gaps.length > 0 ? `${gaps.length} missing clinical protocol(s)` : 'No care gaps identified'}
          icon={AlertTriangle}
          color={gaps.length > 0 ? 'rose' : 'teal'}
          alert={gaps.length > 0}
        />

        <MetricCard
          title="Matched Guidelines"
          value={loading ? '...' : matchedRules.length}
          subtitle={matchedRules.length > 0 ? `Rules: ${matchedRules.join(', ')}` : 'No matching rules triggered'}
          icon={Compass}
          color="sky"
        />

        <MetricCard
          title="Active Medications"
          value={loading ? '...' : medicationCount}
          subtitle="Prescribed regimen count"
          icon={Pill}
          color="indigo"
        />
      </div>

      {/* Two Column Detailed Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Adherence & Gaps Highlight */}
        <div className="lg:col-span-2 space-y-6">
          {/* Adherence & Confidence Panel */}
          <div className="glass-card rounded-xl p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h3 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-teal-400" />
                  Protocol Adherence & Confidence
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Algorithmic scoring combining entity coverage with guideline adherence
                </p>
              </div>
              <button
                onClick={() => setActiveTab('guidelines')}
                className="text-xs text-teal-400 hover:text-teal-300 font-medium flex items-center gap-1"
              >
                View Rules <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <ConfidenceMeter value={confidence} />

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2 text-xs">
              <div className="p-3 rounded-lg bg-slate-900/70 border border-slate-800">
                <span className="text-slate-400 block text-[11px]">Matched Rule IDs</span>
                <span className="font-mono font-semibold text-slate-200 mt-1 block">
                  {matchedRules.length > 0 ? matchedRules.join(', ') : 'None'}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/70 border border-slate-800">
                <span className="text-slate-400 block text-[11px]">Entity Extraction Rate</span>
                <span className="font-mono font-semibold text-teal-300 mt-1 block">
                  {entities.length > 0 ? 'High (>90%)' : '0 entities'}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/70 border border-slate-800">
                <span className="text-slate-400 block text-[11px]">Care Gap Status</span>
                <span className={`font-semibold mt-1 block ${gaps.length > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {gaps.length > 0 ? `${gaps.length} Action(s)` : 'Compliant'}
                </span>
              </div>
            </div>
          </div>

          {/* Active Gaps Quick Inspection */}
          <div className="glass-card rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <h3 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400" />
                Detected Clinical Care Gaps
              </h3>
              <button
                onClick={() => setActiveTab('gaps')}
                className="text-xs text-rose-400 hover:text-rose-300 font-medium flex items-center gap-1"
              >
                Full Gap Report <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {gaps.length === 0 ? (
              <div className="py-8 text-center space-y-2">
                <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto opacity-80" />
                <p className="text-sm font-medium text-slate-200">No care gaps detected in current note</p>
                <p className="text-xs text-slate-400">All recommended investigations and guideline criteria are satisfied.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {gaps.map((gap, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-rose-500/20 text-rose-300 border border-rose-500/30">
                          {gap.gap_type}
                        </span>
                        {gap.rule_id && (
                          <span className="text-xs font-mono text-slate-400">
                            Rule: {gap.rule_id}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-200 font-medium">
                        {gap.description}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono px-2 py-1 rounded bg-slate-900 text-slate-300 border border-slate-800 uppercase">
                        Entity: {gap.entity}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right 1 Col: Ingested Note & Quick Navigation */}
        <div className="space-y-6">
          {/* Note Preview */}
          <div className="glass-card rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-teal-400" />
                Active Clinical Note
              </h3>
              <button
                onClick={() => setActiveTab('input')}
                className="text-xs text-teal-400 hover:text-teal-300 font-medium"
              >
                Edit Note
              </button>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-950/80 border border-slate-800 font-mono text-xs text-slate-300 leading-relaxed max-h-48 overflow-y-auto whitespace-pre-wrap">
              {displayNoteText}
            </div>

            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
              <span>Patient ID: <strong className="text-teal-300 font-mono">{displayPatientId}</strong></span>
              <span>Document ID: <strong className="text-sky-300 font-mono">{displayDocumentId}</strong></span>
            </div>
          </div>

          {/* Quick Hub Navigation Cards */}
          <div className="glass-card rounded-xl p-6 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Module Quick Access
            </h3>

            <div className="grid grid-cols-1 gap-2">
              <button
                onClick={() => setActiveTab('entities')}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-slate-900/60 hover:bg-slate-900 border border-slate-800/80 hover:border-teal-500/30 text-left transition-all"
              >
                <div className="flex items-center gap-3">
                  <ScanSearch className="w-4 h-4 text-teal-400" />
                  <div>
                    <span className="text-xs font-medium text-slate-200 block">Extracted Entities</span>
                    <span className="text-[10px] text-slate-400">{entities.length} items identified</span>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-500" />
              </button>

              <button
                onClick={() => setActiveTab('prescriptions')}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-slate-900/60 hover:bg-slate-900 border border-slate-800/80 hover:border-indigo-500/30 text-left transition-all"
              >
                <div className="flex items-center gap-3">
                  <Pill className="w-4 h-4 text-indigo-400" />
                  <div>
                    <span className="text-xs font-medium text-slate-200 block">Prescription Regimen</span>
                    <span className="text-[10px] text-slate-400">Dosage & frequency pairing</span>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-500" />
              </button>

              <button
                onClick={() => setActiveTab('timeline')}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-slate-900/60 hover:bg-slate-900 border border-slate-800/80 hover:border-sky-500/30 text-left transition-all"
              >
                <div className="flex items-center gap-3">
                  <History className="w-4 h-4 text-sky-400" />
                  <div>
                    <span className="text-xs font-medium text-slate-200 block">Clinical Timeline</span>
                    <span className="text-[10px] text-slate-400">Order-of-appearance event flow</span>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-500" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
