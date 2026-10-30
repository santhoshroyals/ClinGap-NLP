import React from 'react';
import {
  Info,
  Layers,
  Cpu,
  Database,
  ShieldAlert,
  CheckCircle2,
  Workflow,
  BookOpen,
  Sparkles,
  ExternalLink
} from 'lucide-react';

const PIPELINE_STEPS = [
  {
    step: 1,
    title: 'Clinical Note Ingestion & Preprocessing',
    desc: 'Cleans, segments sentences, and normalizes unstructured clinical text from EHR consultation notes.',
    tech: 'Regex / String Preprocessing'
  },
  {
    step: 2,
    title: 'Hybrid Named Entity Recognition (NER)',
    desc: 'Extracts diseases, medications, investigations, symptoms, dosages, and administration frequencies using clinical lexicons and regex patterns.',
    tech: 'Lexical Knowledge Base & Regular Expressions'
  },
  {
    step: 3,
    title: 'Contextual Negation Detection',
    desc: 'Analyzes pre-negation (e.g., "no", "denies") and post-negation (e.g., "not performed", "negative") syntax within sentence clauses.',
    tech: 'Clause-bounded Negation Patterns'
  },
  {
    step: 4,
    title: 'Clinical Context Analysis',
    desc: 'Contextual embeddings and document-level semantics evaluating clinical domain and note type.',
    tech: 'Bio_Clinical_BERT / TF-IDF Vectorizer'
  },
  {
    step: 5,
    title: 'Guideline Matching Engine',
    desc: 'Deterministic rule evaluation verifying if patient phenotypes satisfy guideline prerequisites (e.g., R1, R2).',
    tech: 'Rule Inference Engine & Guidelines KB'
  },
  {
    step: 6,
    title: 'Decision Gap Detection',
    desc: 'Identifies omitted diagnostics, missing laboratory orders, or negated investigations mandated by evidence standards.',
    tech: 'Gap Detection Algorithm'
  },
  {
    step: 7,
    title: 'Adherence Confidence Scoring',
    desc: 'Mathematical model combining entity density with gap severity into a normalized 0–100% confidence index.',
    tech: 'Weighted Multi-factor Scoring'
  },
  {
    step: 8,
    title: 'Explainability & Evidence Audit',
    desc: 'Generates transparent clinical audit traces showing triggered rules, matched entities, and diagnostic recommendations.',
    tech: 'Explainability Layer'
  },
];

export function AboutPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <Info className="w-5 h-5 text-teal-400" />
          System Methodology & Pipeline Architecture
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Technical specifications, theoretical foundation, and clinical governance principles powering ClinGap-NLP.
        </p>
      </div>

      {/* Academic Disclaimer Notice */}
      <div className="rounded-xl p-4 bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-amber-200 leading-relaxed">
          <strong className="font-bold text-white uppercase tracking-wider block mb-1">
            Academic Demonstration & Research Disclaimer
          </strong>
          This software is an academic research prototype developed strictly for demonstration, evaluation, and scholarly purposes. It is <strong className="text-white underline">not intended for real clinical decision-making</strong>, patient diagnosis, prescription guidance, or medical care delivery without board-certified clinical supervision.
        </div>
      </div>

      {/* Pipeline Flowchart / Visualizer */}
      <div className="glass-panel rounded-2xl p-6 space-y-5">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Workflow className="w-4 h-4 text-teal-400" />
            End-to-End NLP Pipeline Flow
          </h3>
          <span className="text-[11px] font-mono text-teal-300">FastAPI Orchestrator</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {PIPELINE_STEPS.map((s) => (
            <div
              key={s.step}
              className="glass-card rounded-xl p-4 border border-slate-800/80 space-y-2 hover:border-teal-500/30 transition-all"
            >
              <div className="flex items-center justify-between">
                <span className="w-6 h-6 rounded-full bg-teal-500/20 text-teal-300 font-mono text-xs font-bold flex items-center justify-center border border-teal-500/30">
                  {s.step}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                  {s.tech}
                </span>
              </div>
              <h4 className="text-xs font-bold text-white tracking-wide">
                {s.title}
              </h4>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                {s.desc}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Technical Specifications & Knowledge Base */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card rounded-xl p-5 space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <Database className="w-4 h-4 text-sky-400" />
            Knowledge Base Schemas
          </h4>
          <p className="text-xs text-slate-300 leading-relaxed">
            ClinGap-NLP relies on structured clinical knowledge bases located in <code className="text-teal-300 font-mono text-[11px]">clinngap_nlp/knowledge_base/</code>:
          </p>
          <ul className="text-xs space-y-2 text-slate-400">
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
              <span><strong className="text-slate-200 font-mono">guidelines.json</strong>: Evidence-based criteria & recommendations (R1, R2, R3).</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
              <span><strong className="text-slate-200 font-mono">diseases.json</strong>: Canonical terms and synonym ontology.</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
              <span><strong className="text-slate-200 font-mono">investigations.json</strong>: Diagnostic lab tests (CBC, Chest X-ray, HbA1c).</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
              <span><strong className="text-slate-200 font-mono">medications.json</strong>: Pharmaceutical names and strengths.</span>
            </li>
          </ul>
        </div>

        <div className="glass-card rounded-xl p-5 space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-emerald-400" />
            System Architecture
          </h4>
          <p className="text-xs text-slate-300 leading-relaxed">
            Separation of concerns between high-performance asynchronous microservices and stateful presentation layers:
          </p>
          <ul className="text-xs space-y-2 text-slate-400">
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span><strong className="text-slate-200">Backend</strong>: FastAPI with CORS, SQLite ORM, and Pydantic validation schemas.</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span><strong className="text-slate-200">Frontend</strong>: React 18 single-page application bundled with Vite and Tailwind CSS.</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span><strong className="text-slate-200">Inference</strong>: Hybrid heuristic rules, regex patterns, and deterministic audit trails.</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
