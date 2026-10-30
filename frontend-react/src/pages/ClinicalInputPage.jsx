import React, { useState, useEffect } from 'react';
import {
  FileText,
  Play,
  RotateCcw,
  Sparkles,
  Trash2,
  Copy,
  Check,
  User,
  Hash,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
  Database,
  UploadCloud,
  Search,
  Filter,
  FileCheck,
  BookOpen
} from 'lucide-react';
import { useAnalysis, DEMO_PRESETS } from '../context/AnalysisContext';
import { apiService } from '../services/api';

export function ClinicalInputPage() {
  const {
    rawText,
    setRawText,
    patientId,
    setPatientId,
    documentId,
    setDocumentId,
    runAnalysis,
    loading,
    error,
    loadPreset,
    setActiveTab,
  } = useAnalysis();

  // Mode: 'demo' | 'mtsamples' | 'upload'
  const [inputMode, setInputMode] = useState('demo');

  const [copied, setCopied] = useState(false);
  const [successNotif, setSuccessNotif] = useState(false);

  // MTSamples Dataset State
  const [specialties, setSpecialties] = useState([]);
  const [selectedSpecialty, setSelectedSpecialty] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [datasetRecords, setDatasetRecords] = useState([]);
  const [datasetLoading, setDatasetLoading] = useState(false);
  const [selectedMTSample, setSelectedMTSample] = useState(null);
  const [datasetTotal, setDatasetTotal] = useState(0);

  // Upload State
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState(null);

  const wordCount = rawText.trim() ? rawText.trim().split(/\s+/).length : 0;
  const charCount = rawText.length;

  // Load Specialties once
  useEffect(() => {
    let isMounted = true;
    apiService.getSpecialties().then((res) => {
      if (isMounted && res.ok && Array.isArray(res.data)) {
        setSpecialties(res.data);
      }
    });
    return () => { isMounted = false; };
  }, []);

  // Fetch MTSamples Records when query or specialty changes
  useEffect(() => {
    if (inputMode !== 'mtsamples') return;
    let isMounted = true;
    setDatasetLoading(true);

    const timer = setTimeout(() => {
      apiService.getDatasetRecords({
        q: searchQuery,
        specialty: selectedSpecialty,
        limit: 30,
        offset: 0,
      }).then((res) => {
        if (!isMounted) return;
        setDatasetLoading(false);
        if (res.ok && res.data) {
          setDatasetRecords(res.data.records || []);
          setDatasetTotal(res.data.total || 0);
        }
      });
    }, 250);

    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [inputMode, selectedSpecialty, searchQuery]);

  const handleSelectMTSample = async (recordId) => {
    setDatasetLoading(true);
    setSuccessNotif(false);
    try {
      const res = await apiService.getDatasetRecord(recordId);
      if (res.ok && res.data) {
        setSelectedMTSample(res.data);
        const sampleText = res.data.transcription || '';
        setRawText(sampleText);
        setDocumentId(recordId);
        const pId = Number(patientId) || 1;
        const success = await runAnalysis({
          text: sampleText,
          patient_id: pId,
          document_id: recordId,
        });
        if (success) {
          setSuccessNotif(true);
        }
      }
    } catch (err) {
      console.error('Failed to load MTSamples record:', err);
    } finally {
      setDatasetLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadFile(file);
    setUploadLoading(true);
    setUploadError(null);
    setUploadResult(null);
    setSuccessNotif(false);

    try {
      const res = await apiService.uploadDocument(file);
      if (res.ok && res.data) {
        setUploadResult(res.data);
        const extractedText = res.data.text || '';
        setRawText(extractedText);

        const pId = Number(patientId) || 1;
        const dId = Number(documentId) || 1;
        const success = await runAnalysis({
          text: extractedText,
          patient_id: pId,
          document_id: dId,
        });
        if (success) {
          setSuccessNotif(true);
        }
      } else {
        setUploadError(res.error || 'Failed to extract text from uploaded document.');
      }
    } catch (err) {
      setUploadError(err.message || 'File upload failed.');
    } finally {
      setUploadLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(rawText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleClear = () => {
    setRawText('');
    setSelectedMTSample(null);
    setUploadResult(null);
    setUploadFile(null);
    setSuccessNotif(false);
  };

  const handleAnalyze = async (e) => {
    if (e && e.preventDefault) {
      e.preventDefault();
    }

    const noteText = String(rawText || '').trim();
    if (!noteText) {
      return;
    }

    const pId = Number(patientId) || 1;
    const dId = Number(documentId) || 1;

    console.log('[ClinicalInputPage] Triggering analysis with:', { patient_id: pId, document_id: dId, textLength: noteText.length });

    const success = await runAnalysis({
      text: noteText,
      patient_id: pId,
      document_id: dId,
    });

    if (success) {
      setSuccessNotif(true);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <FileText className="w-5 h-5 text-teal-400" />
            Clinical Note Ingestion & Ingestion Modes
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Choose between standard demo presets, the 4,966-record MTSamples clinical corpus, or upload real clinical documents (.txt, .pdf, .docx).
          </p>
        </div>

        {/* Input Mode Selector */}
        <div className="flex items-center p-1 bg-slate-900 border border-slate-800 rounded-xl">
          <button
            type="button"
            onClick={() => setInputMode('demo')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
              inputMode === 'demo'
                ? 'bg-teal-500 text-slate-950 shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Demo Presets</span>
          </button>
          <button
            type="button"
            onClick={() => setInputMode('mtsamples')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
              inputMode === 'mtsamples'
                ? 'bg-teal-500 text-slate-950 shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>MTSamples Dataset</span>
          </button>
          <button
            type="button"
            onClick={() => setInputMode('upload')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
              inputMode === 'upload'
                ? 'bg-teal-500 text-slate-950 shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* Mode Sub-Panels */}
      {inputMode === 'demo' && (
        <div className="glass-card rounded-xl p-4 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-300 font-semibold flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-teal-400" />
              Controlled Benchmark Cases:
            </span>
            <span className="text-[11px] text-slate-500">3 verified demonstration clinical narratives</span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {DEMO_PRESETS.map((preset, idx) => (
              <button
                key={preset.id}
                type="button"
                onClick={() => {
                  setSuccessNotif(false);
                  setSelectedMTSample(null);
                  setUploadResult(null);
                  loadPreset(preset.id);
                }}
                className="px-3.5 py-1.5 rounded-lg text-xs font-medium bg-slate-900 hover:bg-slate-800 text-teal-300 border border-slate-700 hover:border-teal-500/40 transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <BookOpen className="w-3 h-3 text-teal-400" />
                <span>Case {idx + 1}: {preset.title}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {inputMode === 'mtsamples' && (
        <div className="glass-card rounded-xl p-4 border border-slate-800 space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div>
              <span className="text-xs text-white font-semibold flex items-center gap-2">
                <Database className="w-4 h-4 text-teal-400" />
                Real MTSamples Clinical Transcriptions
              </span>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Query 4,966 records from <code className="text-slate-300">mtsamples_clean.csv</code> and run them directly through the ClinGap NLP pipeline.
              </p>
            </div>

            {/* Quick Test Shortcuts */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] text-slate-400 font-medium">Quick Test:</span>
              <button
                type="button"
                onClick={() => handleSelectMTSample(3552)}
                className="px-2.5 py-1 rounded-md text-[11px] font-mono bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 border border-teal-500/30 transition-all cursor-pointer"
              >
                Record 3552 (Endoscopy - 3)
              </button>
              <button
                type="button"
                onClick={() => handleSelectMTSample(3739)}
                className="px-2.5 py-1 rounded-md text-[11px] font-mono bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 transition-all cursor-pointer"
              >
                Record 3739 (Jaw Pain)
              </button>
            </div>
          </div>

          {/* Search & Specialty Filter */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-2 relative">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search by keyword, procedure name, or record ID (e.g. 3552, bypass, biopsy)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-teal-500"
              />
            </div>
            <div>
              <select
                value={selectedSpecialty}
                onChange={(e) => setSelectedSpecialty(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-teal-500"
              >
                <option value="all">All Specialties ({specialties.length})</option>
                {specialties.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Search Results Preview Cards */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span>Matching Records: <strong className="text-white">{datasetTotal}</strong></span>
              {datasetLoading && <span className="text-teal-400 animate-pulse">Loading dataset...</span>}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-1">
              {datasetRecords.map((rec) => (
                <div
                  key={rec.id}
                  onClick={() => handleSelectMTSample(rec.id)}
                  className={`p-2.5 rounded-lg border text-left cursor-pointer transition-all ${
                    selectedMTSample?.id === rec.id
                      ? 'bg-teal-500/10 border-teal-500/50 text-white'
                      : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-xs text-teal-300 truncate">
                      #{rec.id} — {rec.sample_name}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800 shrink-0">
                      {rec.medical_specialty}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-1 mt-1">
                    {rec.description || rec.preview}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Selected Sample Information Banner */}
          {selectedMTSample && (
            <div className="p-3 rounded-lg bg-teal-500/10 border border-teal-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
              <div>
                <span className="font-bold text-teal-300">Selected Record #{selectedMTSample.id}:</span>{' '}
                <span className="text-white">{selectedMTSample.sample_name}</span>{' '}
                <span className="text-slate-400">({selectedMTSample.medical_specialty})</span>
              </div>
              <div className="text-[11px] font-mono text-teal-300">
                {selectedMTSample.word_count} words | {selectedMTSample.char_count} chars
              </div>
            </div>
          )}
        </div>
      )}

      {inputMode === 'upload' && (
        <div className="glass-card rounded-xl p-5 border border-slate-800 space-y-4">
          <div>
            <span className="text-xs text-white font-semibold flex items-center gap-2">
              <UploadCloud className="w-4 h-4 text-teal-400" />
              Upload Clinical Document or Prescription
            </span>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Supports plain text (<code className="text-slate-300">.txt</code>), PDF reports (<code className="text-slate-300">.pdf</code>), and Word documents (<code className="text-slate-300">.docx</code>). Real text is extracted and forwarded to the NLP pipeline.
            </p>
          </div>

          {/* Upload Drop/Picker Area */}
          <div className="border-2 border-dashed border-slate-800 hover:border-teal-500/50 rounded-xl p-6 text-center transition-colors bg-slate-950/40">
            <input
              type="file"
              id="clinical-file-upload"
              accept=".txt,.pdf,.docx,.doc"
              onChange={handleFileUpload}
              className="hidden"
            />
            <label
              htmlFor="clinical-file-upload"
              className="cursor-pointer flex flex-col items-center justify-center space-y-2"
            >
              <div className="p-3 rounded-full bg-slate-900 text-teal-400 border border-slate-800">
                <UploadCloud className="w-6 h-6" />
              </div>
              <div className="text-xs font-semibold text-slate-200">
                Click to browse or drop document here
              </div>
              <div className="text-[11px] text-slate-500">
                Accepts: .txt, .pdf, .docx (Max 10MB)
              </div>
            </label>
          </div>

          {uploadLoading && (
            <div className="flex items-center gap-2 text-xs text-teal-400 animate-pulse">
              <RotateCcw className="w-3.5 h-3.5 animate-spin" />
              <span>Extracting text from uploaded document...</span>
            </div>
          )}

          {uploadError && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          {uploadResult && (
            <div className="p-3.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 space-y-1.5 text-xs">
              <div className="flex items-center justify-between text-emerald-300 font-semibold">
                <span className="flex items-center gap-1.5">
                  <FileCheck className="w-4 h-4 text-emerald-400" />
                  Successfully Extracted: {uploadResult.filename} ({uploadResult.file_type})
                </span>
                <span className="font-mono text-[11px] text-emerald-400">
                  {uploadResult.word_count} words | {uploadResult.char_count} chars
                </span>
              </div>
              <p className="text-[11px] text-slate-300 line-clamp-2">
                Preview: {uploadResult.preview}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Metadata Form: Patient & Document IDs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="glass-card rounded-xl p-4 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-teal-500/10 text-teal-400 border border-teal-500/20">
            <User className="w-4 h-4" />
          </div>
          <div className="flex-1">
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Patient ID
            </label>
            <input
              type="number"
              min="1"
              value={patientId}
              onChange={(e) => setPatientId(Math.max(1, parseInt(e.target.value, 10) || 1))}
              className="mt-1 w-full bg-slate-900 border border-slate-800 rounded-md px-3 py-1 text-xs text-white font-mono focus:outline-none focus:border-teal-500 transition-colors"
            />
          </div>
        </div>

        <div className="glass-card rounded-xl p-4 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <Hash className="w-4 h-4" />
          </div>
          <div className="flex-1">
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Document ID
            </label>
            <input
              type="number"
              min="1"
              value={documentId}
              onChange={(e) => setDocumentId(Math.max(1, parseInt(e.target.value, 10) || 1))}
              className="mt-1 w-full bg-slate-900 border border-slate-800 rounded-md px-3 py-1 text-xs text-white font-mono focus:outline-none focus:border-sky-500 transition-colors"
            />
          </div>
        </div>
      </div>

      {/* Text Area Card */}
      <div className="glass-panel rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span className="font-semibold text-slate-300">Raw Clinical Narrative</span>
            <span>|</span>
            <span className="font-mono">{wordCount} words</span>
            <span>|</span>
            <span className="font-mono">{charCount} chars</span>
            {selectedMTSample && (
              <span className="hidden sm:inline-block px-2 py-0.5 rounded bg-teal-500/10 text-teal-300 text-[10px] border border-teal-500/20">
                MTSample #{selectedMTSample.id}
              </span>
            )}
            {uploadResult && (
              <span className="hidden sm:inline-block px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 text-[10px] border border-emerald-500/20">
                Uploaded {uploadResult.file_type}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopy}
              disabled={!rawText}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors disabled:opacity-40 cursor-pointer"
              title="Copy text"
            >
              {copied ? <Check className="w-4 h-4 text-teal-400" /> : <Copy className="w-4 h-4" />}
            </button>
            <button
              type="button"
              onClick={handleClear}
              disabled={!rawText}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors disabled:opacity-40 cursor-pointer"
              title="Clear text"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        <textarea
          rows={12}
          value={rawText}
          onChange={(e) => {
            setRawText(e.target.value);
            setSuccessNotif(false);
          }}
          placeholder="Paste, type, or load clinical note here..."
          className="w-full bg-slate-950/90 border border-slate-800/80 rounded-xl p-4 font-mono text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-teal-500/50 focus:ring-1 focus:ring-teal-500/50 leading-relaxed resize-y transition-all"
        />

        {/* Error Alert */}
        {error && (
          <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 flex items-center gap-2 text-xs text-rose-300 animate-fadeIn">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Success Alert */}
        {successNotif && !error && !loading && (
          <div className="p-3.5 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-between gap-3 text-xs text-emerald-300 animate-fadeIn">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>Analysis complete! Extracted entities, guidelines, and gaps are updated.</span>
            </div>
            <button
              type="button"
              onClick={() => setActiveTab('dashboard')}
              className="flex items-center gap-1 px-3 py-1 rounded-lg bg-emerald-500 text-slate-950 font-bold hover:bg-emerald-400 transition-colors text-[11px] flex-shrink-0 cursor-pointer"
            >
              <span>View Dashboard</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Action Controls */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
          <div className="text-[11px] text-slate-400">
            Target Endpoint:{' '}
            <code className="text-teal-400 font-mono bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
              POST http://127.0.0.1:8001/api/analyze
            </code>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              type="button"
              onClick={handleAnalyze}
              disabled={loading || !rawText.trim()}
              className="flex-1 sm:flex-initial flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-xs font-bold uppercase tracking-wider bg-gradient-to-r from-teal-500 to-emerald-500 text-slate-950 hover:from-teal-400 hover:to-emerald-400 transition-all duration-200 shadow-lg shadow-teal-500/20 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {loading ? (
                <>
                  <RotateCcw className="w-4 h-4 animate-spin" />
                  <span>Processing NLP Pipeline...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Analyze Clinical Note</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
