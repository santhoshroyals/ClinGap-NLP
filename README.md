# ClinGap-NLP

**ClinGap-NLP** – *Explainable Clinical Decision Gap Detection using NLP and Evidence-Based Guidelines*

A complete, runnable clinical decision-support and documentation quality assurance prototype that ingests unstructured clinical notes, extracts clinical entities via a hybrid 4-tier NLP pipeline (BioBERT transformer, spaCy, curated dictionaries, regex), evaluates contextual negation, matches patient findings against deterministic guidelines, detects documentation omissions/gaps, reconstructs medication regimens, and visualizes the results in a React 18 Single Page Application.

---

## Architecture & System Overview

- **Frontend**: React 18 + Vite SPA (`frontend-react/`) running on **Port 3001** with Tailwind CSS and Lucide icons.
- **Backend**: FastAPI asynchronous REST API (`backend/`) running on **Port 8001** via Uvicorn.
- **NLP / NER**: Hybrid 4-Tier pipeline (`d4data/biomedical-ner-all` BioBERT transformer + spaCy fallback + clinical dictionaries + regex patterns).
- **Negation & Context**: Bidirectional clausal scoping (`no CBC`, `denies cough`, `not performed`) + Bio_ClinicalBERT 768-dim embeddings.
- **Clinical Guidelines**: Deterministic rules engine evaluating non-negated prerequisites against `knowledge_base/guidelines.json`.
- **Prescription Studio**: Clause-aware proximity pairing of medications with dosages and frequencies, filtering clinical stop words.
- **Dataset Integration**: Searchable, paginated browser across 4,966 clinical records in 40 medical specialties (`data/datasets/mtsamples_clean.csv`).
- **Persistence**: SQLite database (`clinngap.db` / `clinngap_nlp.db`) via SQLAlchemy models.

---

## Project Structure

```
clinngap_nlp/
├── backend/                   # FastAPI backend server
│   ├── api/                   # REST route handlers (/api/analyze, /api/upload, /api/dataset)
│   ├── models/                # SQLAlchemy database models (Patient, Document, etc.)
│   ├── services/              # Core business & NLP services
│   │   ├── ner_service.py     # Hybrid 4-Tier NER pipeline
│   │   ├── negation_service.py# Clausal negation detection
│   │   ├── guideline_service.py# Deterministic guideline matcher
│   │   ├── gap_detection.py   # Missing / unperformed investigation auditor
│   │   ├── prescription_service.py # Regimen proximity reconstructor
│   │   ├── context_service.py # Bio_ClinicalBERT embeddings & TF-IDF
│   │   ├── document_parser.py # Multi-format parser (.txt, .pdf, .docx)
│   │   └── dataset_service.py # MTSamples query & cache service
│   ├── database.py            # SQLite session & engine setup
│   └── main.py                # FastAPI ASGI application entrypoint
├── frontend-react/            # Primary React 18 SPA (Vite + Tailwind CSS)
│   ├── src/
│   │   ├── components/        # Layout (Sidebar, Header), common UI elements
│   │   ├── pages/             # 8 interactive modules (Dashboard, Input, Entities, Gaps, etc.)
│   │   ├── context/           # AnalysisContext single-source-of-truth state provider
│   │   └── services/          # Axios API client
│   └── package.json
├── knowledge_base/            # Curated JSON dictionaries & clinical guidelines
│   ├── diseases.json
│   ├── symptoms.json
│   ├── medications.json
│   ├── investigations.json
│   └── guidelines.json
├── data/
│   ├── datasets/              # MTSamples cleaned dataset (4,966 records)
│   └── demo/                  # Synthetic benchmark notes
├── scripts/                   # Database seeding and utility scripts
├── tests/                     # Automated test suite (NER, Prescriptions, Pipeline)
├── clinngap.db                # SQLite database
├── config.py                  # Environment configuration
└── requirements.txt           # Python backend dependencies
```

---

## Getting Started

### 1. Backend Setup & Startup
```powershell
# From the clinngap_nlp directory:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Seed the database:
python scripts/seed_database.py

# Launch FastAPI on port 8001:
python -m uvicorn backend.main:app --reload --port 8001
```
*API Swagger Documentation will be available at: http://localhost:8001/docs*

### 2. Frontend Setup & Startup
```powershell
# In a separate terminal, navigate to frontend-react:
cd frontend-react
npm install
npm run dev -- --port 3001
```
*Open http://localhost:3001 in your browser.*

---

## Running Automated Tests

Run the complete backend test suite:
```powershell
# From clinngap_nlp:
python -m pytest tests

# Or from project root:
python -m pytest clinngap_nlp/tests
```

Production frontend build validation:
```powershell
cd frontend-react
npm run build
```

---

## Clinical Safety & Research Disclaimer

**ClinGap-NLP is an educational, research, and documentation quality assurance tool.** It does **NOT** provide medical advice, establish diagnoses, or automate clinical treatment decisions. All flagged documentation gaps and guideline recommendations must be evaluated and verified by a licensed healthcare professional prior to clinical intervention.