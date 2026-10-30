import React from 'react';
import {
  Pill,
  Clock,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ShieldCheck,
  Sparkles,
  Info
} from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';
import { EntityBadge } from '../components/common/Badge';

export function PrescriptionPage() {
  const { analysisResult, loading, setActiveTab } = useAnalysis();

  const entities = analysisResult?.entities || [];

  const noteText = analysisResult?.text || '';
  const NOISE_WORDS = new Set(['medication', 'medications', 'medicine', 'medicines', 'drug', 'drugs', 'tablet', 'tablets', 'pill', 'pills']);

  const medications = entities.filter(
    e => e.entity_type === 'MEDICATION' && !NOISE_WORDS.has((e.entity_text || '').toLowerCase().trim())
  );
  const rawDosages = entities.filter(e => e.entity_type === 'DOSAGE');
  const rawFrequencies = entities.filter(e => e.entity_type === 'FREQUENCY');

  // Expanded dosage and frequency patterns supporting all clinical intervals
  const DOSAGE_RE = /\b\d+(?:\.\d+)?\s*(?:mg|g|ml|mL|units|mcg|µg)(?!\s*\/\s*(?:d[lL]|[lL]|m[lL]|u[lL]|µ[lL]|mm3|kg|min|hr|h|day)|%)\b/i;
  const FREQ_RE = /\b(?:every\s+\d+\s+(?:hours?|days?|weeks?)|once\s+daily|twice\s+daily|three\s+times\s+daily|four\s+times\s+daily|once\s+weekly|twice\s+weekly|once\s+monthly|\d+\s+times?\s+(?:a|per)\s+day|as\s+needed|daily|weekly|monthly|q\d+h|bid|tid|qid|od|bd|qd|qhs|prn)\b/i;

  const dosages = [];
  const extraFrequencies = [];

  rawDosages.forEach(d => {
    const textVal = d.entity_text || '';
    const dMatch = DOSAGE_RE.exec(textVal);
    const fMatch = FREQ_RE.exec(textVal);
    if (dMatch) {
      dosages.push({ ...d, entity_text: dMatch[0] });
      if (fMatch) {
        extraFrequencies.push({ entity_text: fMatch[0], entity_type: 'FREQUENCY', confidence: d.confidence });
      }
    } else {
      dosages.push(d);
    }
  });

  const frequencies = [...rawFrequencies, ...extraFrequencies];

  // Also discover any frequency phrases present in the note text directly
  if (noteText) {
    const globalFreqRe = new RegExp(FREQ_RE.source, 'gi');
    let fm;
    while ((fm = globalFreqRe.exec(noteText)) !== null) {
      const matchText = fm[0].trim();
      if (!frequencies.some(f => (f.entity_text || '').toLowerCase() === matchText.toLowerCase())) {
        frequencies.push({ entity_text: matchText, entity_type: 'FREQUENCY', confidence: 1.0 });
      }
    }
  }

  const distinctMedNames = Array.from(new Set(medications.map(m => m.entity_text)));

  // Use structured regimens returned directly from the backend pipeline if available
  const backendRegimens = Array.isArray(analysisResult?.regimens) && analysisResult.regimens.length > 0
    ? analysisResult.regimens
    : null;

  const parsedRegimens = backendRegimens
    ? backendRegimens.map((reg) => {
        const medObj = medications.find(
          m => (m.entity_text || '').toLowerCase().trim() === (reg.medication || '').toLowerCase().trim()
        );
        return {
          medication: reg.medication,
          normalized: medObj?.normalized_value || reg.medication,
          confidence: medObj?.confidence || 0.95,
          dosage: reg.dosage || null,
          frequency: reg.frequency || null,
          isComplete: Boolean(reg.dosage && reg.frequency),
        };
      })
    : distinctMedNames.map((medName, index) => {
        const medObj = medications.find(m => m.entity_text === medName);

        let assignedDosage = null;
        let assignedFrequency = null;

        if (noteText) {
          // Find all occurrences of this medication in noteText
          const medRegex = new RegExp(`\\b${medName.replace(/[.*+?^${}()|[\\]\\]/g, '\\$&')}\\b`, 'gi');
          const medOccurrences = [];
          let mMatch;
          while ((mMatch = medRegex.exec(noteText)) !== null) {
            medOccurrences.push({ start: mMatch.index, end: mMatch.index + mMatch[0].length });
          }

          // Find spans of all dosages in noteText
          const dosageSpans = [];
          dosages.forEach(d => {
            const dText = d.entity_text;
            if (!dText) return;
            const re = new RegExp(`\\b${dText.replace(/[.*+?^${}()|[\\]\\]/g, '\\$&')}\\b`, 'gi');
            let dm;
            while ((dm = re.exec(noteText)) !== null) {
              dosageSpans.push({ text: dText, start: dm.index, end: dm.index + dm[0].length });
            }
          });

          // Find spans of all frequencies in noteText
          const freqSpans = [];
          frequencies.forEach(f => {
            const fText = f.entity_text;
            if (!fText) return;
            const re = new RegExp(`\\b${fText.replace(/[.*+?^${}()|[\\]\\]/g, '\\$&')}\\b`, 'gi');
            let fm;
            while ((fm = re.exec(noteText)) !== null) {
              freqSpans.push({ text: fText, start: fm.index, end: fm.index + fm[0].length });
            }
          });

          // Proximity search for the best dosage and frequency
          let minDoseDist = Infinity;
          let minFreqDist = Infinity;

          medOccurrences.forEach(occ => {
            dosageSpans.forEach(ds => {
              const dist = ds.start >= occ.end ? (ds.start - occ.end) : (occ.start - ds.end) * 2;
              if (dist >= 0 && dist < 120 && dist < minDoseDist) {
                minDoseDist = dist;
                assignedDosage = ds.text;
              }
            });

            freqSpans.forEach(fs => {
              const dist = fs.start >= occ.end ? (fs.start - occ.end) : (occ.start - fs.end) * 2;
              if (dist >= 0 && dist < 150 && dist < minFreqDist) {
                minFreqDist = dist;
                assignedFrequency = fs.text;
              }
            });
          });
        }

        // Fallback if proximity did not locate match or no noteText available
        if (!assignedDosage && dosages[index]) {
          assignedDosage = dosages[index].entity_text;
        }
        if (!assignedFrequency && frequencies[index]) {
          assignedFrequency = frequencies[index].entity_text;
        }

        return {
          medication: medName,
          normalized: medObj?.normalized_value || medName,
          confidence: medObj?.confidence || 0.9,
          dosage: assignedDosage,
          frequency: assignedFrequency,
          isComplete: Boolean(assignedDosage && assignedFrequency),
        };
      });

  const activeMedCount = parsedRegimens.length > 0 ? parsedRegimens.length : distinctMedNames.length;
  const dosageCount = Math.max(dosages.length, parsedRegimens.filter(r => r.dosage).length);
  const frequencyCount = Math.max(frequencies.length, parsedRegimens.filter(r => r.frequency).length);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Pill className="w-5 h-5 text-emerald-400" />
            Prescription & Medication Regimen Analysis
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Structured pharmacological extraction pairing pharmaceutical agents with dosage strengths and dosing frequencies.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Extracted Medications:</span>
          <span className="px-2.5 py-0.5 rounded-full font-mono text-xs font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
            {activeMedCount}
          </span>
        </div>
      </div>

      {/* Regimen Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-card rounded-xl p-4 space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Active Medications
          </span>
          <div className="text-2xl font-bold font-mono text-emerald-400">
            {activeMedCount}
          </div>
          <p className="text-[11px] text-slate-500">Identified via clinical lexicon</p>
        </div>

        <div className="glass-card rounded-xl p-4 space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Dosage Patterns
          </span>
          <div className="text-2xl font-bold font-mono text-amber-400">
            {dosageCount}
          </div>
          <p className="text-[11px] text-slate-500">Regex-matched strengths</p>
        </div>

        <div className="glass-card rounded-xl p-4 space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Frequency Instructions
          </span>
          <div className="text-2xl font-bold font-mono text-indigo-400">
            {frequencyCount}
          </div>
          <p className="text-[11px] text-slate-500">Chronotherapeutic intervals</p>
        </div>
      </div>

      {/* Prescriptions Table */}
      <div className="space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Reconstructed Medication Regimens
        </h3>

        {parsedRegimens.length === 0 ? (
          <div className="glass-panel rounded-2xl p-12 text-center space-y-3">
            <Pill className="w-10 h-10 text-slate-600 mx-auto" />
            <h4 className="text-sm font-semibold text-white">No Prescriptions Extracted</h4>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              The current clinical note does not mention any recognized pharmaceuticals from the knowledge base.
            </p>
          </div>
        ) : (
          <div className="glass-panel rounded-2xl overflow-hidden border border-slate-800/80 shadow-lg">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/80 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                  <th className="py-3.5 px-4">Medication Name</th>
                  <th className="py-3.5 px-4">Canonical / Generic</th>
                  <th className="py-3.5 px-4">Dosage / Strength</th>
                  <th className="py-3.5 px-4">Frequency</th>
                  <th className="py-3.5 px-4">Regimen Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs">
                {parsedRegimens.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/50 transition-colors">
                    {/* Medication */}
                    <td className="py-3.5 px-4 font-bold text-white flex items-center gap-2">
                      <div className="p-1 rounded-md bg-emerald-500/10 text-emerald-400">
                        <Pill className="w-3.5 h-3.5" />
                      </div>
                      <span>{item.medication}</span>
                    </td>

                    {/* Generic */}
                    <td className="py-3.5 px-4 font-mono text-slate-300">
                      {item.normalized}
                    </td>

                    {/* Dosage */}
                    <td className="py-3.5 px-4">
                      {item.dosage ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded font-mono text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                          {item.dosage}
                        </span>
                      ) : (
                        <span className="text-slate-500 italic">Not specified</span>
                      )}
                    </td>

                    {/* Frequency */}
                    <td className="py-3.5 px-4">
                      {item.frequency ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded font-mono text-xs font-semibold bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">
                          {item.frequency}
                        </span>
                      ) : (
                        <span className="text-slate-500 italic">Not specified</span>
                      )}
                    </td>

                    {/* Completeness Status */}
                    <td className="py-3.5 px-4">
                      {item.isComplete ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Complete Regimen
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
                          <AlertCircle className="w-3.5 h-3.5" />
                          Partial Info
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Raw Regex Entity Trace */}
      <div className="glass-card rounded-xl p-5 space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <Info className="w-4 h-4 text-teal-400" />
          Regimen Parsing Trace
        </h4>
        <p className="text-xs text-slate-300 leading-relaxed">
          The ClinGap-NLP regex parser extracts pharmaceutical strengths (e.g. <code className="text-amber-300 font-mono">mg, g, ml</code>) and frequency tokens (<code className="text-indigo-300 font-mono">once daily, twice daily, tid, bid</code>), associating them with pharmaceutical ontology records.
        </p>
      </div>
    </div>
  );
}
