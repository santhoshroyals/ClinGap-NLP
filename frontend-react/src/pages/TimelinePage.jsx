import React from 'react';
import {
  History,
  Calendar,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowDown,
  Info,
  Pill,
  Stethoscope,
  Activity
} from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';
import { EntityBadge } from '../components/common/Badge';

export function TimelinePage() {
  const { analysisResult, rawText, loading, setActiveTab } = useAnalysis();

  const entities = analysisResult?.entities || [];
  const currentNote = analysisResult?.text || rawText || '';

  // Order entities by position of first appearance in the active analyzed clinical note
  // Strictly preserving the Streamlit implementation logic
  const orderedEntities = [...entities].sort((a, b) => {
    if (!currentNote) return 0;
    const posA = currentNote.toLowerCase().indexOf((a.entity_text || '').toLowerCase());
    const posB = currentNote.toLowerCase().indexOf((b.entity_text || '').toLowerCase());
    const finalA = posA >= 0 ? posA : 999999;
    const finalB = posB >= 0 ? posB : 999999;
    return finalA - finalB;
  });

  // Explicit calendar dates pattern (exact regex from Streamlit frontend)
  const datePattern = /\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:, \d{4})?)\b/gi;
  const datesFound = currentNote ? (currentNote.match(datePattern) || []) : [];

  // Categorized collections for summary
  const conditions = Array.from(
    new Set(
      orderedEntities
        .filter(e => ['DISEASE', 'CONDITION'].includes(e.entity_type))
        .map(e => e.entity_text)
    )
  );

  const investigations = orderedEntities.filter(e => e.entity_type === 'INVESTIGATION');

  const backendRegimens = Array.isArray(analysisResult?.regimens) && analysisResult.regimens.length > 0
    ? analysisResult.regimens
    : [];

  const meds = Array.from(
    new Set(
      orderedEntities
        .filter(e => e.entity_type === 'MEDICATION')
        .map(e => e.entity_text)
    )
  );

  // Map each medication to its reconstructed regimen dosage and frequency
  // Avoid independent array-index pairing that causes mismatches
  const regimenMap = new Map();
  backendRegimens.forEach((reg) => {
    if (reg.medication) {
      regimenMap.set(reg.medication.toLowerCase().trim(), reg);
    }
  });

  const medicationItems = [];
  const seenMeds = new Set();

  // First prioritize all reconstructed regimens from the backend
  backendRegimens.forEach((reg) => {
    const medKey = (reg.medication || '').toLowerCase().trim();
    if (medKey && !seenMeds.has(medKey)) {
      seenMeds.add(medKey);
      medicationItems.push({
        name: reg.medication,
        dosage: reg.dosage || 'Not specified',
        frequency: reg.frequency || 'Not specified',
      });
    }
  });

  // Then append any standalone extracted medication not in structured regimens
  meds.forEach((med) => {
    const medKey = (med || '').toLowerCase().trim();
    if (medKey && !seenMeds.has(medKey)) {
      seenMeds.add(medKey);
      const matched = regimenMap.get(medKey);
      medicationItems.push({
        name: med,
        dosage: matched?.dosage || 'Not specified',
        frequency: matched?.frequency || 'Not specified',
      });
    }
  });

  if (!analysisResult && !loading) {
    return (
      <div className="glass-card rounded-2xl p-12 text-center space-y-4 max-w-lg mx-auto mt-12">
        <History className="w-12 h-12 text-slate-500 mx-auto" />
        <h3 className="text-base font-bold text-white">No Timeline Data Available</h3>
        <p className="text-xs text-slate-400">
          Please upload or paste a clinical note on the Clinical Input page and run analysis to construct a clinical event timeline.
        </p>
        <button
          onClick={() => setActiveTab('input')}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-teal-500 text-slate-950 hover:bg-teal-400 transition-all"
        >
          Go to Clinical Input
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <History className="w-5 h-5 text-sky-400" />
            Clinical Timeline & Event Sequence
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Chronological documentation reconstruction preserving narrative progression without synthetic timestamps.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Sequential Events:</span>
          <span className="px-2.5 py-0.5 rounded-full font-mono text-xs font-bold bg-sky-500/15 text-sky-300 border border-sky-500/30">
            {orderedEntities.length} Steps
          </span>
        </div>
      </div>

      {/* Date Detection Callout */}
      <div className="glass-panel rounded-xl p-4 flex items-center gap-3">
        <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
          <Calendar className="w-4 h-4" />
        </div>
        <div className="text-xs">
          {datesFound.length > 0 ? (
            <p className="text-sky-200">
              📅 <strong className="font-semibold">Explicit document dates identified:</strong>{' '}
              <span className="font-mono text-teal-300">{datesFound.join(', ')}</span>
            </p>
          ) : (
            <p className="text-slate-400">
              ℹ️ <strong className="font-semibold text-slate-300">No explicit calendar dates detected</strong> in this clinical note. Events are presented in sequence of clinical documentation (order of appearance).
            </p>
          )}
        </div>
      </div>

      {/* Document Event Progression */}
      <div className="space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Document Event Progression (Step-by-Step)
        </h3>

        {orderedEntities.length === 0 ? (
          <div className="glass-panel rounded-xl p-8 text-center text-xs text-slate-500">
            No entities available to construct sequential timeline.
          </div>
        ) : (
          <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800">
            {orderedEntities.map((ent, idx) => {
              const etype = (ent.entity_type || '').toUpperCase();
              const isNeg = Boolean(ent.negated);
              const textVal = ent.entity_text;

              let cardBorder = 'border-slate-800';
              let badgeColor = 'bg-slate-800 text-slate-300';
              let statusText = isNeg ? 'Not present / Negated' : 'Documented / Active';
              let isInvestigation = etype === 'INVESTIGATION';

              if (isInvestigation) {
                const invStatus = (ent.status || (isNeg ? 'not performed' : 'ordered')).toLowerCase();
                if (invStatus === 'not performed' || invStatus === 'cancelled') {
                  cardBorder = 'border-rose-500/40 bg-rose-950/15';
                  statusText = 'Not performed';
                  badgeColor = 'bg-rose-500/20 text-rose-300 border-rose-500/30';
                } else if (invStatus === 'ordered/pending') {
                  cardBorder = 'border-amber-500/40 bg-amber-950/15';
                  statusText = 'Ordered / Pending';
                  badgeColor = 'bg-amber-500/20 text-amber-300 border-amber-500/30';
                } else if (invStatus === 'pending') {
                  cardBorder = 'border-amber-500/40 bg-amber-950/15';
                  statusText = 'Pending / Awaiting Result';
                  badgeColor = 'bg-amber-500/20 text-amber-300 border-amber-500/30';
                } else if (invStatus === 'ordered') {
                  cardBorder = 'border-sky-500/40 bg-sky-950/15';
                  statusText = 'Ordered / Requested';
                  badgeColor = 'bg-sky-500/20 text-sky-300 border-sky-500/30';
                } else {
                  cardBorder = 'border-emerald-500/40 bg-emerald-950/15';
                  statusText = 'Completed / Performed';
                  badgeColor = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
                }
              } else if (['DISEASE', 'CONDITION'].includes(etype)) {
                cardBorder = 'border-rose-500/30 bg-slate-900/60';
                statusText = isNeg ? 'Not present' : 'Active / Documented';
              } else if (etype === 'MEDICATION') {
                cardBorder = 'border-emerald-500/30 bg-slate-900/60';
                statusText = 'Prescribed Agent';
              } else if (etype === 'DOSAGE') {
                cardBorder = 'border-amber-500/30 bg-slate-900/60';
                statusText = 'Dosage Specification';
              } else if (etype === 'FREQUENCY') {
                cardBorder = 'border-indigo-500/30 bg-slate-900/60';
                statusText = 'Administration Frequency';
              }

              return (
                <div key={idx} className="relative group">
                  {/* Step Dot */}
                  <div
                    className={`absolute -left-6 top-3 w-5 h-5 rounded-full border flex items-center justify-center text-[10px] font-mono font-bold transition-all ${
                      isInvestigation && (ent.status === 'not performed' || isNeg)
                        ? 'bg-rose-500 border-rose-400 text-slate-950'
                        : isInvestigation && (ent.status === 'ORDERED/PENDING' || ent.status === 'pending' || (ent.status && ent.status.toLowerCase() === 'ordered/pending'))
                        ? 'bg-amber-500 border-amber-400 text-slate-950'
                        : isInvestigation && ent.status === 'ordered'
                        ? 'bg-sky-500 border-sky-400 text-slate-950'
                        : isInvestigation
                        ? 'bg-emerald-500 border-emerald-400 text-slate-950'
                        : isNeg
                        ? 'bg-rose-500 border-rose-400 text-slate-950'
                        : 'bg-slate-900 border-slate-700 text-slate-300 group-hover:border-teal-400'
                    }`}
                  >
                    {idx + 1}
                  </div>

                  {/* Step Card */}
                  <div className={`glass-card rounded-xl p-4 border ${cardBorder} flex flex-col sm:flex-row sm:items-center justify-between gap-3`}>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-semibold text-slate-400">
                          Step {idx + 1}
                        </span>
                        <EntityBadge type={etype}>
                          {etype}
                        </EntityBadge>
                      </div>

                      <div className="text-sm font-bold text-white tracking-wide">
                        {textVal}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {isInvestigation ? (
                        ent.status === 'not performed' || isNeg ? (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                            <XCircle className="w-3.5 h-3.5 text-rose-400" />
                            {statusText}
                          </span>
                        ) : (ent.status === 'ORDERED/PENDING' || ent.status === 'pending' || (ent.status && ent.status.toLowerCase() === 'ordered/pending')) ? (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                            <Clock className="w-3.5 h-3.5 text-amber-400" />
                            {statusText}
                          </span>
                        ) : ent.status === 'ordered' ? (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-sky-500/20 text-sky-300 border border-sky-500/30">
                            <Clock className="w-3.5 h-3.5 text-sky-400" />
                            {statusText}
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                            {statusText}
                          </span>
                        )
                      ) : isNeg ? (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                          <XCircle className="w-3.5 h-3.5 text-rose-400" />
                          {statusText}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          {statusText}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Summary by Category Grid */}
      <div className="border-t border-slate-800 pt-6 space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Clinical Summary by Category
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Column 1: Conditions & Investigations */}
          <div className="glass-card rounded-xl p-5 space-y-4">
            <h4 className="text-sm font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <Stethoscope className="w-4 h-4 text-rose-400" />
              Conditions & Diagnostic Investigations
            </h4>

            {/* Conditions list */}
            <div className="space-y-2 text-xs">
              <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] block">
                Conditions / Diseases
              </span>
              {conditions.length === 0 ? (
                <p className="text-slate-500 italic">No conditions extracted.</p>
              ) : (
                <ul className="space-y-1.5">
                  {conditions.map((c, i) => (
                    <li key={i} className="flex items-center gap-2 text-slate-200">
                      <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                      <strong className="text-white">{c}</strong>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Investigations list */}
            <div className="space-y-2 text-xs pt-2 border-t border-slate-800/60">
              <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] block">
                Diagnostic Investigations
              </span>
              {investigations.length === 0 ? (
                <p className="text-slate-500 italic">No investigations extracted.</p>
              ) : (
                <ul className="space-y-1.5">
                  {investigations.map((inv, i) => {
                    const rawStatus = (inv.status || (inv.negated ? 'not performed' : 'ordered')).toLowerCase().trim();
                    let statusLabel = 'Ordered';
                    let badgeClass = 'text-sky-400 bg-sky-500/10 border-sky-500/20';

                    if (rawStatus === 'not performed' || rawStatus === 'cancelled' || inv.negated) {
                      statusLabel = 'Not performed';
                      badgeClass = 'text-rose-400 bg-rose-500/10 border-rose-500/20';
                    } else if (rawStatus === 'ordered/pending') {
                      statusLabel = 'Ordered / Pending';
                      badgeClass = 'text-amber-400 bg-amber-500/10 border-amber-500/20';
                    } else if (rawStatus === 'pending' || rawStatus === 'pending results' || rawStatus.includes('pending')) {
                      statusLabel = 'Pending Results';
                      badgeClass = 'text-amber-400 bg-amber-500/10 border-amber-500/20';
                    } else if (rawStatus === 'completed/performed' || rawStatus === 'performed') {
                      statusLabel = 'Performed';
                      badgeClass = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
                    } else if (rawStatus === 'ordered') {
                      statusLabel = 'Ordered';
                      badgeClass = 'text-sky-400 bg-sky-500/10 border-sky-500/20';
                    }

                    return (
                      <li key={i} className="flex items-center justify-between text-slate-200 py-1 border-b border-slate-800/40 last:border-0">
                        <span className="font-medium text-white">{inv.entity_text}</span>
                        <span className={`text-[11px] font-bold px-2 py-0.5 rounded border ${badgeClass}`}>
                          {statusLabel}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </div>

          {/* Column 2: Medications & Dosing Regimen */}
          <div className="glass-card rounded-xl p-5 space-y-4">
            <h4 className="text-sm font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <Pill className="w-4 h-4 text-emerald-400" />
              Medications & Dosing Regimen
            </h4>

            {medicationItems.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No medications extracted.</p>
            ) : (
              <div className="space-y-3 text-xs">
                {medicationItems.map((item, i) => (
                  <div key={i} className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white text-sm">{item.name}</span>
                      <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        Active Prescription
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-slate-300 text-[11px] pt-1">
                      <div>
                        <span className="text-slate-500 block text-[10px]">Dosage</span>
                        <span className="font-mono font-semibold text-amber-300">{item.dosage}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px]">Frequency</span>
                        <span className="font-mono font-semibold text-indigo-300">{item.frequency}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
