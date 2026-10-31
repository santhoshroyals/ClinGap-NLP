# ClinGap-NLP
### Clinical Decision Gap Intelligence System Using Natural Language Processing

<p align="center">
  <strong>Transforming Clinical Narratives into Structured Clinical Insights</strong>
</p>

---

## 1. Project Overview

**ClinGap-NLP** is an intelligent clinical decision-support system designed to analyze unstructured clinical notes and identify potential gaps between documented patient information and recommended clinical investigations or guideline-based actions.

Clinical notes often contain valuable information about symptoms, diagnoses, medications, investigations, and treatment plans. However, this information is usually documented in free-text format, making it difficult to systematically identify missing investigations, inconsistencies, and potential gaps in clinical decision-making.

ClinGap-NLP addresses this challenge by integrating Natural Language Processing (NLP), Clinical Named Entity Recognition (NER), contextual analysis, negation detection, guideline matching, and explainable gap detection into a unified pipeline.

The system processes clinical text, extracts relevant medical information, evaluates it against a structured clinical knowledge base, and presents the identified findings through an interactive dashboard.

> **Note:** ClinGap-NLP is an academic/research decision-support prototype. Its outputs are intended to assist analysis and research, not replace qualified medical professionals or independent clinical judgment.

---

## 2. Problem Statement

Clinical documentation is predominantly unstructured and contains complex medical terminology, contextual references, abbreviations, negations, and temporal information.

Identifying whether an expected clinical investigation or action has been documented can require considerable manual effort.

Existing keyword-based approaches may fail to understand:
- The clinical context in which a medical term appears.
- Whether a symptom or condition is explicitly denied.
- Whether an investigation has already been performed.
- The relationship between symptoms, diagnoses, and investigations.
- Whether a documented action aligns with a relevant clinical guideline.

Therefore, there is a need for an intelligent NLP-based framework that can extract clinical information, understand its context, match it with relevant guidelines, and identify potential clinical decision gaps in a structured and explainable manner.

---

## 3. Project Objectives

The primary objectives of ClinGap-NLP are:

1. **Clinical Information Extraction:** Extract important clinical entities such as symptoms, diseases, medications, and investigations from unstructured clinical notes.
2. **Contextual Understanding:** Analyze clinical statements while considering their surrounding context.
3. **Negation Detection:** Identify negated clinical findings to avoid treating denied symptoms or conditions as positive findings.
4. **Clinical Gap Detection:** Identify potential missing investigations or actions based on extracted clinical information and configured rules.
5. **Guideline Matching:** Compare extracted clinical information with structured clinical guidelines.
6. **Confidence Assessment:** Provide confidence information to help interpret system-generated findings.
7. **Explainability:** Present the reasoning and supporting information behind identified gaps.
8. **Interactive Visualization:** Provide an interface for exploring clinical entities, guideline matches, prescriptions, timelines, and gap-detection results.

---

## 4. System Architecture

The ClinGap-NLP system follows a modular processing architecture.

```text
             CLINICAL INPUT
                    |
                    v
          Clinical Document Upload
                    |
                    v
          Document Parsing
                    |
                    v
          Text Preprocessing
                    |
                    v
       Clinical Named Entity Recognition
                    |
                    v
          Contextual Analysis
                    |
                    v
             Negation Detection
                    |
                    v
       Clinical Information Extraction
                    |
                    v
          Guideline Matching Engine
                    |
                    v
           Clinical Gap Detection
                    |
                    v
        Confidence & Explainability
                    |
                    v
          Database / API Layer
                    |
                    v
          Interactive Dashboard
                    |
                    v
       Structured Clinical Insights
```

### Architecture Components

| Component | Responsibility |
|---|---|
| Clinical Input | Accepts clinical text and supported documents. |
| Document Parsing | Extracts text from uploaded documents. |
| Text Preprocessing | Cleans and prepares clinical text for analysis. |
| Clinical NER | Identifies medical entities from clinical narratives. |
| Contextual Analysis | Evaluates entities in their surrounding clinical context. |
| Negation Detection | Identifies explicitly negated clinical findings. |
| Guideline Engine | Matches clinical information against structured guidelines. |
| Gap Detection | Identifies potential missing clinical actions or investigations. |
| Confidence Service | Provides confidence-related information for findings. |
| Explainability Service | Helps interpret the generated results. |
| Database and API | Manages application data and communication between components. |
| Dashboard | Displays clinical analysis results interactively. |

---

## 5. Methodology

The system follows a multi-stage NLP pipeline.

### 5.1 Clinical Document Processing

The system accepts clinical information and extracts the textual content required for downstream analysis.

The extracted text is cleaned and prepared through preprocessing operations.

### 5.2 Clinical Named Entity Recognition

Clinical NER identifies relevant medical information from the input.

The system works with clinical NLP components and model integrations, including BioClinicalBERT-related and scispaCy-based approaches.

Important entity categories include:

- Symptoms
- Diseases and diagnoses
- Medications
- Clinical investigations
- Other relevant clinical concepts

### 5.3 Contextual Analysis

Extracted entities are evaluated using surrounding textual information to understand how they are used in the clinical note.

This helps distinguish between isolated keyword occurrences and meaningful clinical statements.

### 5.4 Negation Detection

Negation detection identifies statements that explicitly deny a symptom, condition, or clinical finding.

For example:

- "Patient has fever" — positive finding.
- "Patient denies fever" — negated finding.

This distinction is important because a denied symptom should not be interpreted as a confirmed clinical condition.

### 5.5 Clinical Guideline Matching

The guideline engine compares extracted clinical information with the structured knowledge base.

The knowledge base includes information related to:

- Diseases
- Symptoms
- Investigations
- Medications
- Clinical guidelines

The matching process helps determine whether relevant clinical recommendations correspond to the documented information.

### 5.6 Clinical Gap Detection

The gap-detection component analyzes the extracted information and guideline-matching results to identify potential gaps.

Examples of potential gaps include:

- An expected investigation not documented in the clinical note.
- A relevant clinical action not recorded.
- A mismatch between documented information and configured guideline conditions.

The identified gaps are presented as decision-support findings rather than definitive diagnoses.

### 5.7 Confidence and Explainability

The system includes confidence-related and explainability components to make generated findings easier to interpret.

The intention is to provide supporting context for why a particular entity or potential gap was identified.

### 5.8 Result Visualization

The analysis results are presented through an interactive dashboard, allowing users to explore the extracted entities, guideline matches, gap-detection findings, prescriptions, and clinical timelines.

---

## 6. Major Modules

| Module | Description |
|---|---|
| Clinical Input | Accepts clinical notes for processing. |
| Entity Extraction | Extracts relevant clinical entities. |
| Gap Detection | Identifies potential gaps in documented clinical actions. |
| Guideline Matching | Matches clinical information with the knowledge base. |
| Prescription Analysis | Processes prescription-related information. |
| Timeline Analysis | Organizes relevant clinical information temporally. |
| Confidence Analysis | Presents confidence-related information. |
| Explainability | Supports interpretation of generated findings. |
| Dashboard | Provides an interactive interface for viewing results. |
| Evaluation Framework | Supports dataset analysis, annotation, validation, and performance evaluation. |

---

## 7. Technology Stack

### Programming Languages
- Python
- JavaScript
- HTML
- CSS

### Artificial Intelligence and NLP
- Natural Language Processing
- Clinical Named Entity Recognition
- BioClinicalBERT
- scispaCy
- DistilBERT-related components
- Contextual analysis
- Negation detection

### Backend
- FastAPI
- Python
- SQLAlchemy / database integration

### Frontend
- React.js
- Vite
- Tailwind CSS
- JavaScript

### Database
- SQLite

### Visualization and Interface
- Streamlit (additional interface)
- React-based interactive dashboard

### Development and Testing
- Git
- GitHub
- Python virtual environments
- Pytest

*The listed technologies represent the project stack and integrations; individual components may be used in different parts of the application.*

---

## 8. Project Structure

```text
ClinGap-NLP/
│
├── api/
│   └── main.py
│
├── backend/
│   ├── api/
│   │   ├── analysis.py
│   │   ├── dataset.py
│   │   ├── health.py
│   │   └── upload.py
│   │
│   ├── models/
│   │   ├── clinical_entity.py
│   │   ├── document.py
│   │   └── patient.py
│   │
│   ├── services/
│   │   ├── clinical_pipeline.py
│   │   ├── confidence_service.py
│   │   ├── context_service.py
│   │   ├── dataset_service.py
│   │   ├── document_parser.py
│   │   ├── explainability_service.py
│   │   ├── gap_detection.py
│   │   ├── guideline_service.py
│   │   ├── model_manager.py
│   │   ├── negation_service.py
│   │   ├── ner_service.py
│   │   └── prescription_service.py
│   │
│   ├── database.py
│   └── main.py
│
├── db/
│   ├── models.py
│   └── session.py
│
├── docs/
│   ├── reports/
│   └── research and evaluation documentation
│
├── evaluation/
│   ├── evaluation_500_dataset/
│   ├── held_out_50_cases/
│   ├── mtsamples_evaluation/
│   ├── pilot_10_cases/
│   └── evaluation scripts
│
├── frontend-react/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── pages/
│   │   └── services/
│   ├── package.json
│   └── vite.config.js
│
├── frontend/
│   └── app.py
│
├── knowledge_base/
│   ├── diseases.json
│   ├── guidelines.json
│   ├── investigations.json
│   ├── medications.json
│   └── symptoms.json
│
├── models/
│
├── pipeline/
│   ├── confidence.py
│   ├── context_analysis.py
│   ├── gap_detection.py
│   ├── guideline_engine.py
│   ├── hybrid_ner.py
│   ├── investigation_extractor.py
│   ├── negation.py
│   ├── preprocess.py
│   ├── prescription_parser.py
│   ├── run.py
│   ├── text_processor.py
│   └── timeline.py
│
├── scripts/
├── tests/
│
├── .env.example
├── .gitignore
├── config.py
├── requirements.txt
└── README.md
```

---

## 9. Installation and Setup

### Prerequisites

Install the following before running the project:

- Python 3.10 or later
- Node.js and npm
- Git
- A code editor such as Visual Studio Code

### Step 1: Clone the Repository

```bash
git clone https://github.com/santhoshroyals/ClinGap-NLP.git
cd ClinGap-NLP
```

### Step 2: Create a Python Virtual Environment

**Windows:**

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

### Step 3: Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create your local `.env` file using the example configuration:

```powershell
Copy-Item .env.example .env
```

Update the values according to your local environment.

Do not upload `.env` files, credentials, API keys, or other secrets to GitHub.

### Step 5: Install Frontend Dependencies

Open a terminal inside the frontend directory:

```powershell
cd frontend-react
npm install
```

### Step 6: Start the Backend

From the project root, activate the virtual environment and run:

```powershell
uvicorn backend.main:app --reload
```

The backend is expected to be accessible at:

```text
http://127.0.0.1:8000
```

FastAPI interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### Step 7: Start the React Frontend

Open another terminal:

```powershell
cd frontend-react
npm run dev
```

Open the local URL printed by Vite in your terminal.

---

## 10. Evaluation Framework

ClinGap-NLP includes a dedicated evaluation framework for systematic analysis of the clinical NLP pipeline.

The evaluation directory contains utilities for:

- Dataset analysis.
- Annotation schema management.
- Annotation workflow support.
- Clinical entity evaluation.
- Held-out evaluation preparation.
- Pilot evaluation.
- Inter-annotator agreement analysis.
- Evaluation dataset validation.
- Pipeline prediction generation.
- Evaluation reporting.

The project also includes evaluation-related documentation describing annotation procedures, dataset methodology, and evaluation audits.

### Evaluation Considerations

The system should be assessed using suitable metrics for the individual tasks, including:

- Precision
- Recall
- F1-score
- Entity-level performance
- Gap-detection performance
- Guideline-matching correctness
- Confidence and explainability assessment

**Important:** Actual performance values should be reported only after running the corresponding evaluation scripts on the intended evaluation dataset. No accuracy or performance figure is assumed in this README.

---

## 11. Key Features

- Clinical text processing and information extraction.
- Clinical entity recognition.
- Context-aware clinical analysis.
- Negation-aware interpretation.
- Guideline-based clinical matching.
- Potential clinical decision-gap identification.
- Confidence-related analysis.
- Explainability support.
- Prescription information processing.
- Clinical timeline analysis.
- Interactive React dashboard.
- Modular backend architecture.
- Dedicated evaluation and validation utilities.

---

## 12. Research Significance

ClinGap-NLP explores how NLP techniques can support the analysis of clinical documentation by connecting extracted medical information with structured clinical knowledge.

The project focuses on moving beyond simple keyword extraction toward a more contextual approach that considers:

1. What clinical information is documented?
2. In what context is the information mentioned?
3. Is the finding positive or negated?
4. What relevant guideline information applies?
5. Are there potential gaps in the documented clinical actions?
6. Can the system provide understandable supporting information?

This modular approach provides a foundation for further research into clinical NLP, guideline-based reasoning, and explainable clinical decision-support systems.

---

## 13. Limitations

- The quality of results depends on the completeness and clarity of the clinical notes.
- Clinical terminology, abbreviations, and documentation styles may affect extraction.
- Guideline matching depends on the coverage and quality of the configured knowledge base.
- A missing documentation entry does not necessarily mean that a clinical action was not performed.
- Confidence values should not be interpreted as guarantees of clinical correctness.
- The system requires further validation before any real-world clinical deployment.

---

## 14. Future Enhancements

Potential future improvements include:

- Expanding clinical entity recognition using specialized transformer models.
- Improving contextual understanding of complex clinical narratives.
- Extending the clinical guideline knowledge base.
- Enhancing temporal reasoning across multiple clinical encounters.
- Improving explainability of gap-detection decisions.
- Evaluating generalization across additional clinical datasets.
- Adding broader clinical document formats and interoperability support.
- Conducting larger-scale independent clinical evaluations.
- Exploring integration with healthcare information systems.

---

## 15. Disclaimer

ClinGap-NLP is developed for academic, research, and educational purposes.

It is a clinical information analysis and decision-support prototype. It is not a medical diagnostic system and must not be used as a substitute for professional medical advice, diagnosis, or treatment.

All clinical findings and recommendations must be independently reviewed by qualified healthcare professionals.

---

## 16. Authors and Contributors

**Project:** ClinGap-NLP – Clinical Decision Gap Intelligence System

**Domain:** Natural Language Processing | Clinical AI | Healthcare Analytics | Explainable AI

**Repository:**  
https://github.com/santhoshroyals/ClinGap-NLP

---

## 17. License

A license has not yet been specified for this repository. Until a license is added, the project should not be assumed to permit reuse, modification, or redistribution.

---

<p align="center">
  <strong>ClinGap-NLP</strong><br/>
  <em>Bridging Clinical Documentation and Guideline-Based Intelligence</em>
</p>
