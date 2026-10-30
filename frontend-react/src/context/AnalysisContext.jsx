import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';

const AnalysisContext = createContext(null);

export const DEMO_PRESETS = [
  {
    id: 'case1-diabetes-hypertension',
    title: 'Case 1: Diabetes & Hypertension (Full Note)',
    category: 'Endocrine / Cardiovascular',
    text: `The patient has diabetes mellitus and hypertension. The patient reports increased thirst and frequent urination for the past two weeks. Blood pressure is 150/95 mmHg. HbA1c was performed and the result was 8.2%. CBC was not performed. The patient is taking metformin 500 mg twice daily. The patient was advised to continue medication and follow up after two weeks.`
  },
  {
    id: 'case2-diabetes',
    title: 'Case 2: Diabetes, Metformin & Missing CBC',
    category: 'Endocrine',
    text: `The patient has diabetes mellitus. CBC was not performed. HbA1c was performed and the result was 8.2%. The patient is taking metformin 500 mg twice daily.`
  },
  {
    id: 'case3-complex',
    title: 'Case 3: Respiratory Infection & Full Regimen',
    category: 'General / Pulmonary',
    text: `Patient presents with acute respiratory symptoms and fatigue. Blood pressure noted as high. Aspirin 100 mg once daily was prescribed. Complete blood count (CBC) was not performed during this visit.`
  }
];

const STORAGE_KEY = 'clingap_nlp_current_analysis';

function getStoredAnalysis() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object' && Array.isArray(parsed.entities)) {
      return parsed;
    }
    // If parsed object is invalid/malformed, clear the invalid entry
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (_) {}
  } catch (err) {
    console.warn('Failed to parse analysis from localStorage, clearing:', err);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (_) {}
  }
  return null;
}

export function AnalysisProvider({ children }) {
  const initialSaved = getStoredAnalysis();
  const initialDate = initialSaved?.analyzed_at ? new Date(initialSaved.analyzed_at) : null;
  const validInitialDate = initialDate && !isNaN(initialDate.getTime()) ? initialDate : null;

  const [activeTab, setActiveTab] = useState('dashboard');
  const [rawText, setRawText] = useState(initialSaved?.text || '');
  const [patientId, setPatientId] = useState(initialSaved?.patient_id ?? 1);
  const [documentId, setDocumentId] = useState(initialSaved?.document_id ?? 1);
  const [analysisResult, setAnalysisResult] = useState(initialSaved);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [backendHealth, setBackendHealth] = useState('checking'); // 'connected' | 'offline' | 'checking'
  const [lastAnalyzedAt, setLastAnalyzedAt] = useState(validInitialDate);

  // Check health periodically
  const checkHealthStatus = useCallback(async () => {
    const res = await apiService.checkHealth();
    setBackendHealth(res.ok ? 'connected' : 'offline');
    return res.ok;
  }, []);

  useEffect(() => {
    checkHealthStatus();
    const interval = setInterval(checkHealthStatus, 15000);
    return () => clearInterval(interval);
  }, [checkHealthStatus]);

  // Run analysis function with single-source-of-truth commitment
  const runAnalysis = useCallback(async (params) => {
    let textToAnalyze = '';
    let pId = patientId;
    let dId = documentId;

    if (typeof params === 'string') {
      textToAnalyze = params;
    } else if (params && typeof params === 'object') {
      textToAnalyze = params.text !== undefined ? params.text : rawText;
      pId = params.patient_id !== undefined ? params.patient_id : (params.patientId !== undefined ? params.patientId : patientId);
      dId = params.document_id !== undefined ? params.document_id : (params.documentId !== undefined ? params.documentId : documentId);
    } else {
      textToAnalyze = rawText;
    }

    const cleanText = String(textToAnalyze || '').trim();
    if (!cleanText) {
      setError('Please provide a clinical note before running analysis.');
      return false;
    }

    const finalPatientId = Number(pId) || 1;
    const finalDocumentId = Number(dId) || 1;

    setLoading(true);
    setError(null);

    try {
      const res = await apiService.analyzeClinicalText({
        text: cleanText,
        patient_id: finalPatientId,
        document_id: finalDocumentId,
      });

      if (res.ok && res.data) {
        // Build single unified analysis state containing all results + request parameters
        const now = new Date();
        const fullResult = {
          ...res.data,
          entities: Array.isArray(res.data.entities) ? res.data.entities : [],
          gaps: Array.isArray(res.data.gaps) ? res.data.gaps : [],
          confidence: typeof res.data.confidence === 'number' ? res.data.confidence : 0,
          explanation: res.data.explanation || {},
          matched_rules: res.data.matched_rules || res.data.explanation?.matched_rules || [],
          patient_id: res.data.patient_id !== undefined ? Number(res.data.patient_id) : finalPatientId,
          document_id: res.data.document_id !== undefined ? Number(res.data.document_id) : finalDocumentId,
          text: res.data.text !== undefined ? String(res.data.text) : cleanText,
          analyzed_at: now.toISOString(),
        };

        const entityCount = Array.isArray(fullResult.entities) ? fullResult.entities.length : 0;
        console.log(
          `[ClinGap-NLP] Analysis successful. Patient: ${fullResult.patient_id}, Document: ${fullResult.document_id}, Entities: ${entityCount}`
        );

        // Update all related context states
        setAnalysisResult(fullResult);
        setPatientId(fullResult.patient_id);
        setDocumentId(fullResult.document_id);
        setRawText(fullResult.text);
        setLastAnalyzedAt(now);
        setError(null);

        // Persist to localStorage so tab reloads or external navigation never lose state
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(fullResult));
        } catch (sErr) {
          console.warn('Failed to save analysis to localStorage:', sErr);
        }

        return true;
      } else {
        setError(res.error || 'Failed to analyze clinical document.');
        return false;
      }
    } catch (err) {
      console.error('[ClinGap-NLP] Unexpected exception in runAnalysis:', err);
      setError(err.message || 'An unexpected error occurred.');
      return false;
    } finally {
      setLoading(false);
    }
  }, [rawText, patientId, documentId]);


  const loadPreset = (presetId) => {
    const found = DEMO_PRESETS.find(p => p.id === presetId);
    if (found) {
      const presetNum = presetId.includes('case1') ? 1 : (presetId.includes('case2') ? 2 : 3);
      setRawText(found.text);
      setPatientId(presetNum);
      setDocumentId(presetNum);
      runAnalysis({
        text: found.text,
        patient_id: presetNum,
        document_id: presetNum
      });
    }
  };

  const value = {
    activeTab,
    setActiveTab,
    rawText,
    setRawText,
    patientId,
    setPatientId,
    documentId,
    setDocumentId,
    // Active analyzed values derived from the single source of truth
    currentPatientId: analysisResult?.patient_id ?? patientId ?? 1,
    currentDocumentId: analysisResult?.document_id ?? documentId ?? 1,
    currentText: analysisResult?.text || rawText || '',
    analysisResult,
    loading,
    error,
    backendHealth,
    lastAnalyzedAt: (() => {
      if (!lastAnalyzedAt) return null;
      const d = lastAnalyzedAt instanceof Date ? lastAnalyzedAt : new Date(lastAnalyzedAt);
      return !isNaN(d.getTime()) ? d : null;
    })(),
    runAnalysis,
    loadPreset,
    checkHealthStatus,
  };

  return (
    <AnalysisContext.Provider value={value}>
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis() {
  const context = useContext(AnalysisContext);
  if (!context) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return context;
}
