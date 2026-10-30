import axios from 'axios';

// FastAPI backend running on port 8001
const API_BASE_URL = 'http://127.0.0.1:8001';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  async checkHealth() {
    try {
      const response = await client.get('/api/health');
      return { ok: response.data?.status === 'ok', data: response.data };
    } catch (error) {
      try {
        // Direct fetch fallback
        const fallback = await fetch('http://127.0.0.1:8001/api/health');
        const data = await fallback.json();
        return { ok: data?.status === 'ok', data };
      } catch (fErr) {
        console.warn('Backend health check error:', error.message);
        return { ok: false, error: error.message };
      }
    }
  },

  async analyzeClinicalText(params) {
    let text = '';
    let patient_id = 1;
    let document_id = 1;

    if (typeof params === 'string') {
      text = params;
    } else if (params && typeof params === 'object') {
      text = params.text || params.rawText || '';
      patient_id = params.patient_id ?? params.patientId ?? 1;
      document_id = params.document_id ?? params.documentId ?? 1;
    }

    const payload = {
      patient_id: Number(patient_id) || 1,
      document_id: Number(document_id) || 1,
      text: String(text || '').trim(),
    };

    console.log('[ClinGap-NLP] Dispatching POST http://127.0.0.1:8001/api/analyze', payload);

    try {
      // First attempt with Axios
      const response = await client.post('/api/analyze', payload);
      const data = {
        ...response.data,
        patient_id: response.data?.patient_id ?? payload.patient_id,
        document_id: response.data?.document_id ?? payload.document_id,
        text: response.data?.text ?? payload.text,
      };
      return { ok: true, data };
    } catch (error) {
      console.warn('[ClinGap-NLP] Axios POST error, trying direct fetch fallback:', error.message);
      try {
        // Direct fetch fallback to ensure request is dispatched under any browser environment
        const fetchRes = await fetch('http://127.0.0.1:8001/api/analyze', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        });

        if (!fetchRes.ok) {
          const errData = await fetchRes.json().catch(() => ({ detail: fetchRes.statusText }));
          throw new Error(errData.detail || `Server returned ${fetchRes.status}`);
        }

        const rawData = await fetchRes.json();
        const data = {
          ...rawData,
          patient_id: rawData?.patient_id ?? payload.patient_id,
          document_id: rawData?.document_id ?? payload.document_id,
          text: rawData?.text ?? payload.text,
        };
        console.log('[ClinGap-NLP] Analysis successful via Fetch fallback');
        return { ok: true, data };
      } catch (fallbackError) {
        const message =
          error.response?.data?.detail ||
          error.response?.data?.message ||
          fallbackError.message ||
          error.message ||
          'Failed to communicate with ClinGap-NLP backend at http://127.0.0.1:8001';
        console.error('[ClinGap-NLP] Both Axios and Fetch failed:', message);
        return { ok: false, error: message };
      }
    }
  },

  async getSpecialties() {
    try {
      const response = await client.get('/api/dataset/mtsamples/specialties');
      return { ok: true, data: response.data };
    } catch (error) {
      try {
        const fallback = await fetch('http://127.0.0.1:8001/api/dataset/mtsamples/specialties');
        const data = await fallback.json();
        return { ok: true, data };
      } catch (fErr) {
        return { ok: false, error: error.message };
      }
    }
  },

  async getDatasetRecords(params = {}) {
    const { q, specialty, limit = 50, offset = 0 } = params;
    const queryParams = new URLSearchParams();
    if (q) queryParams.append('q', q);
    if (specialty && specialty !== 'all') queryParams.append('specialty', specialty);
    queryParams.append('limit', limit);
    queryParams.append('offset', offset);

    const url = `/api/dataset/mtsamples/records?${queryParams.toString()}`;
    try {
      const response = await client.get(url);
      return { ok: true, data: response.data };
    } catch (error) {
      try {
        const fallback = await fetch(`http://127.0.0.1:8001${url}`);
        const data = await fallback.json();
        return { ok: true, data };
      } catch (fErr) {
        return { ok: false, error: error.message };
      }
    }
  },

  async getDatasetRecord(recordId) {
    const url = `/api/dataset/mtsamples/${recordId}`;
    try {
      const response = await client.get(url);
      return { ok: true, data: response.data };
    } catch (error) {
      try {
        const fallback = await fetch(`http://127.0.0.1:8001${url}`);
        const data = await fallback.json();
        return { ok: true, data };
      } catch (fErr) {
        return { ok: false, error: error.message };
      }
    }
  },

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await client.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return { ok: true, data: response.data };
    } catch (error) {
      try {
        const fallback = await fetch('http://127.0.0.1:8001/api/upload', {
          method: 'POST',
          body: formData,
        });
        if (!fallback.ok) {
          const errData = await fallback.json().catch(() => ({ detail: fallback.statusText }));
          throw new Error(errData.detail || `Upload failed: ${fallback.status}`);
        }
        const data = await fallback.json();
        return { ok: true, data };
      } catch (fErr) {
        return { ok: false, error: fErr.message || error.message };
      }
    }
  },
};

