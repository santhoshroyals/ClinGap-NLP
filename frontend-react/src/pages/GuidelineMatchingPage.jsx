import React from 'react';
import {
  Compass,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  FileCheck,
  ShieldCheck,
  ArrowRight,
  Sparkles
} from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';

// Knowledge base guidelines known to ClinGap-NLP backend
const REGISTERED_GUIDELINES = [
  {
    rule_id: 'R1',
    name: 'Respiratory Infection Protocol',
    description: 'Educational Demonstration Rule: Respiratory infection – recommend CBC',
    criteria: ['DISEASE', 'SYMPTOM'],
    recommendation: {
      type: 'INVESTIGATION',
      name: 'CBC'
    }
  },
  {
    rule_id: 'R2',
    name: 'Diabetes Mellitus Diagnostic Protocol',
    description: 'Educational Demonstration Rule: Diabetes evaluation – recommend HbA1c',
    criteria: ['DISEASE'],
    recommendation: {
      type: 'INVESTIGATION',
      name: 'HbA1c'
    }
  },
  {
    rule_id: 'R3',
    name: 'General Baseline Control Rule',
    description: 'Educational Demonstration Rule: No gap case – recommend nothing',
    criteria: [],
    recommendation: null
  }
];

export function GuidelineMatchingPage() {
  const { analysisResult, loading, setActiveTab } = useAnalysis();

  const matchedRuleIds = analysisResult?.explanation?.matched_rules || [];
  const entities = analysisResult?.entities || [];
  const nonNegatedTypes = new Set(
    entities.filter(e => !e.negated).map(e => e.entity_type)
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Compass className="w-5 h-5 text-teal-400" />
            Evidence-Based Guideline Matching
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic inference engine cross-referencing extracted clinical entity phenotypes with clinical guideline rule sets.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Matched Rules:</span>
          <span className="px-2.5 py-0.5 rounded-full font-mono text-xs font-bold bg-teal-500/15 text-teal-300 border border-teal-500/30">
            {matchedRuleIds.length} / {REGISTERED_GUIDELINES.length}
          </span>
        </div>
      </div>

      {/* Matched Rules Banner */}
      <div className="glass-panel rounded-xl p-5 flex items-start gap-4">
        <div className="p-2.5 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20 flex-shrink-0 mt-0.5">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <h3 className="text-sm font-bold text-white">
            Active Guideline Matching Engine
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            Guideline rules trigger when all required entity criteria are present in non-negated form. When triggered, the system inspects whether the recommended investigation or clinical action has been satisfied.
          </p>
          <div className="pt-2 flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-semibold text-slate-400">Current non-negated entity types:</span>
            {nonNegatedTypes.size === 0 ? (
              <span className="text-xs font-mono text-slate-500">None detected</span>
            ) : (
              Array.from(nonNegatedTypes).map(t => (
                <span key={t} className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px] font-mono border border-slate-700">
                  {t}
                </span>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Guidelines List */}
      <div className="space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Knowledge Base Guidelines Evaluation
        </h3>

        <div className="grid grid-cols-1 gap-4">
          {REGISTERED_GUIDELINES.map((rule) => {
            const isMatched = matchedRuleIds.includes(rule.rule_id);

            return (
              <div
                key={rule.rule_id}
                className={`glass-card rounded-xl p-6 transition-all border ${
                  isMatched
                    ? 'border-teal-500/40 bg-gradient-to-r from-teal-950/20 to-slate-900 shadow-md'
                    : 'border-slate-800/80 bg-slate-900/40 opacity-75'
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
                  <div className="flex items-center gap-3">
                    <span className="px-3 py-1 rounded-lg font-mono text-xs font-bold bg-slate-800 text-teal-300 border border-slate-700">
                      Rule {rule.rule_id}
                    </span>
                    <div>
                      <h4 className="text-sm font-bold text-white tracking-wide">
                        {rule.name}
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {rule.description}
                      </p>
                    </div>
                  </div>

                  <div>
                    {isMatched ? (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-500/20 text-teal-300 border border-teal-500/30 shadow-sm">
                        <CheckCircle2 className="w-4 h-4 text-teal-400" />
                        Matched & Triggered
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-800/80 text-slate-400 border border-slate-700">
                        <AlertCircle className="w-4 h-4 text-slate-500" />
                        Criteria Not Met
                      </span>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 text-xs">
                  {/* Criteria Column */}
                  <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                      Required Entity Criteria
                    </span>
                    {rule.criteria.length === 0 ? (
                      <span className="text-slate-500 italic">No prerequisite entities required (baseline control)</span>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {rule.criteria.map((crit) => {
                          const hasCrit = nonNegatedTypes.has(crit);
                          return (
                            <span
                              key={crit}
                              className={`inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-mono font-medium border ${
                                hasCrit
                                  ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                                  : 'bg-slate-800 text-slate-500 border-slate-700'
                              }`}
                            >
                              {hasCrit ? (
                                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                              ) : (
                                <HelpCircle className="w-3 h-3 text-slate-500" />
                              )}
                              {crit}
                            </span>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* Recommendation Column */}
                  <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                      Guideline Recommendation
                    </span>
                    {rule.recommendation ? (
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">
                            {rule.recommendation.type}
                          </span>
                          <span className="font-semibold text-white">
                            {rule.recommendation.name}
                          </span>
                        </div>
                        {isMatched && (
                          <button
                            onClick={() => setActiveTab('gaps')}
                            className="text-[11px] text-teal-400 hover:text-teal-300 font-medium flex items-center gap-1"
                          >
                            Check Gap Status <ArrowRight className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-500 italic">No action required</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
