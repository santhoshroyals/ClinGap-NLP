import React, { useState } from 'react';
import {
  ScanSearch,
  Filter,
  Search,
  CheckCircle2,
  XCircle,
  Database,
  Layers,
  Sparkles,
  Info
} from 'lucide-react';
import { useAnalysis } from '../context/AnalysisContext';
import { EntityBadge, StatusBadge } from '../components/common/Badge';

export function EntityExtractionPage() {
  const { analysisResult, loading, setActiveTab } = useAnalysis();
  const [selectedType, setSelectedType] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [negationFilter, setNegationFilter] = useState('ALL'); // 'ALL' | 'AFFIRMED' | 'NEGATED'

  // Normalize entities: ensure every required field is present so no entity is silently dropped
  const entities = (analysisResult?.entities || [])
    .filter(e => e && typeof e.entity_text === 'string' && e.entity_text.trim() !== '' && typeof e.entity_type === 'string')
    .map(e => ({
      entity_text: e.entity_text,
      entity_type: e.entity_type,
      normalized_value: e.normalized_value ?? null,
      confidence: typeof e.confidence === 'number' ? e.confidence : 0.9,
      negated: e.negated === true,
      source: e.source ?? 'Clinical Dictionary',
    }));

  const types = ['ALL', ...Array.from(new Set(entities.map(e => e.entity_type)))];
  const activeSelectedType = types.includes(selectedType) ? selectedType : 'ALL';

  const filteredEntities = entities.filter(ent => {
    const matchesType = activeSelectedType === 'ALL' || ent.entity_type === activeSelectedType;
    const matchesSearch =
      ent.entity_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (ent.normalized_value && ent.normalized_value.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesNegation =
      negationFilter === 'ALL' ||
      (negationFilter === 'NEGATED' && ent.negated) ||
      (negationFilter === 'AFFIRMED' && !ent.negated);

    return matchesType && matchesSearch && matchesNegation;
  });

  if (!analysisResult && !loading) {
    return (
      <div className="glass-card rounded-2xl p-12 text-center space-y-4 max-w-lg mx-auto mt-12">
        <ScanSearch className="w-12 h-12 text-slate-500 mx-auto" />
        <h3 className="text-base font-bold text-white">No analysis available. Analyze a clinical note first.</h3>
        <p className="text-xs text-slate-400">
          Run an analysis on the Clinical Input page to inspect clinical entities, normalized vocabulary mappings, and negation tags.
        </p>
        <button
          onClick={() => setActiveTab('input')}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-teal-500 text-slate-950 hover:bg-teal-400 transition-all cursor-pointer"
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
            <ScanSearch className="w-5 h-5 text-teal-400" />
            Clinical Entity Extraction (NER)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Hybrid clinical entity recognition with canonical ontology mapping and contextual negation tagging.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-400">Total Entities:</span>
          <span className="px-2.5 py-0.5 rounded-full font-mono text-xs font-bold bg-teal-500/15 text-teal-300 border border-teal-500/30">
            {entities.length}
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter entities or normalized terms..."
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-teal-500/50"
          />
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
          <span className="text-[11px] font-semibold text-slate-500 mr-1 flex items-center gap-1">
            <Filter className="w-3 h-3" /> Type:
          </span>
          {types.map((type) => (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all ${
                activeSelectedType === type
                  ? 'bg-teal-500 text-slate-950 font-bold shadow-sm'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-800'
              }`}
            >
              {type}
            </button>
          ))}
        </div>

        {/* Negation Selector */}
        <div className="flex items-center gap-1.5 self-end md:self-auto">
          <span className="text-[11px] font-semibold text-slate-500">Status:</span>
          <select
            value={negationFilter}
            onChange={(e) => setNegationFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-300 focus:outline-none focus:border-teal-500/50 font-medium"
          >
            <option value="ALL">All Statuses</option>
            <option value="AFFIRMED">Affirmed Only</option>
            <option value="NEGATED">Negated Only</option>
          </select>
        </div>
      </div>

      {/* Entities Table */}
      <div className="glass-panel rounded-2xl overflow-hidden border border-slate-800/80 shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/80 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                <th className="py-3.5 px-4">Entity Text</th>
                <th className="py-3.5 px-4">Category / Type</th>
                <th className="py-3.5 px-4">Normalized Value</th>
                <th className="py-3.5 px-4">Extraction Source</th>
                <th className="py-3.5 px-4">Confidence</th>
                <th className="py-3.5 px-4">Negation Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-xs">
              {filteredEntities.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500 text-xs">
                    No entities matched the specified filters.
                  </td>
                </tr>
              ) : (
                filteredEntities.map((ent, idx) => (
                  <tr
                    key={idx}
                    className="hover:bg-slate-900/50 transition-colors group"
                  >
                    {/* Entity Text */}
                    <td className="py-3 px-4 font-semibold text-white">
                      <div className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-teal-400 opacity-60" />
                        <span>{ent.entity_text}</span>
                      </div>
                    </td>

                    {/* Entity Type Badge */}
                    <td className="py-3 px-4">
                      <EntityBadge type={ent.entity_type}>
                        {ent.entity_type}
                      </EntityBadge>
                    </td>

                    {/* Normalized Value */}
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {ent.normalized_value || <span className="text-slate-600">—</span>}
                    </td>

                    {/* Source */}
                    <td className="py-3 px-4 text-slate-400 font-medium">
                      <span className="inline-flex items-center gap-1.5">
                        <Database className="w-3 h-3 text-slate-500" />
                        {ent.source}
                      </span>
                    </td>

                    {/* Confidence */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2 font-mono text-xs">
                        <div className="w-12 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                          <div
                            className="h-full bg-teal-400 rounded-full"
                            style={{ width: `${(ent.confidence || 0) * 100}%` }}
                          />
                        </div>
                        <span className="text-slate-300">
                          {((ent.confidence || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>

                    {/* Negation Status */}
                    <td className="py-3 px-4">
                      {ent.negated ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">
                          <XCircle className="w-3.5 h-3.5" />
                          Negated / Absent
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Affirmed / Present
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
