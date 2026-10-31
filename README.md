# ClinGap-NLP

### Clinical Decision Gap Intelligence System Using Natural Language Processing

**Transforming Clinical Narratives into Structured Clinical Insights**

---

## 1. Project Overview

**ClinGap-NLP** is an NLP-based clinical decision-support prototype designed to analyze unstructured clinical notes and identify potential gaps between documented patient information and recommended clinical investigations or guideline-based actions.

Clinical notes contain valuable information about symptoms, diagnoses, medications, investigations, and treatment plans. However, this information is generally recorded in free-text format, making it difficult to systematically identify missing investigations, inconsistencies, and potential gaps in clinical documentation.

ClinGap-NLP addresses this challenge by integrating Natural Language Processing (NLP), Clinical Named Entity Recognition (NER), contextual analysis, negation detection, guideline matching, and explainable gap detection into a unified pipeline.

The system processes clinical text, extracts relevant medical information, evaluates it against a structured clinical knowledge base, and presents the identified findings through an interactive dashboard.

> **Note:** ClinGap-NLP is an academic and research prototype. Its outputs are intended to support clinical documentation analysis and research, not replace qualified medical professionals or independent clinical judgment.

---

## 2. Problem Statement

Clinical documentation is predominantly unstructured and contains complex medical terminology, contextual references, abbreviations, negations, and temporal information.

Identifying whether an expected clinical investigation or action has been documented can require considerable manual effort.

Traditional keyword-based approaches may fail to understand:

- The clinical context in which a medical term appears.
- Whether a symptom or condition is explicitly denied.
- Whether an investigation has already been performed.
- The relationship between symptoms, diagnoses, and investigations.
- Whether a documented action aligns with a relevant clinical guideline.

Therefore, there is a need for an intelligent NLP-based framework that can extract clinical information, understand its context, match it with structured guidelines, and identify potential clinical decision gaps in an explainable manner.

---

## 3. Project Objectives

The primary objectives of ClinGap-NLP are:

1. **Clinical Information Extraction:** Extract important clinical entities such as symptoms, diseases, medications, and investigations from unstructured clinical notes.
2. **Contextual Understanding:** Analyze clinical statements while considering their surrounding context.
3. **Negation Detection:** Identify negated clinical findings to avoid treating denied symptoms or conditions as positive findings.
4. **Clinical Gap Detection:** Identify potential missing investigations or actions based on extracted clinical information and configured rules.
5. **Guideline Matching:** Compare extracted clinical information with structured clinical guidelines.
6. **Confidence Assessment:** Provide confidence-related information to help interpret system-generated findings.
7. **Explainability:** Present supporting information behind identified potential gaps.
8. **Interactive Visualization:** Provide an interface for exploring clinical entities, guideline matches, prescriptions, timelines, and gap-detection results.

---

## 4. System Architecture

ClinGap-NLP follows a modular processing architecture that transforms unstructured clinical notes into structured clinical insights.

### Overall Workflow

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
          STRUCTURED CLINICAL INSIGHTS
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

The project uses clinical NLP components and model integrations, including BioClinicalBERT-related and scispaCy-based approaches.

Important entity categories include:

- Symptoms
- Diseases and diagnoses
- Medications
- Clinical investigations
- Dosages and frequencies
- Other relevant clinical concepts

### 5.3 Contextual Analysis

Extracted entities are evaluated using surrounding textual information to understand how they are used in the clinical note.

This helps distinguish isolated keyword occurrences from meaningful clinical statements.

### 5.4 Negation Detection

Negation detection identifies statements that explicitly deny a symptom, condition, or clinical finding.

**Examples:**

- "Patient has fever" — Positive finding.
- "Patient denies fever" — Negated finding.

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

Examples include:

- An expected investigation not documented in the clinical note.
- A relevant clinical action not recorded.
- A mismatch between documented information and configured guideline conditions.

The identified gaps are presented as decision-support findings rather than definitive diagnoses.

### 5.7 Confidence and Explainability

The system includes confidence-related and explainability components to make generated findings easier to interpret.

These components provide supporting context for why a particular entity or potential gap was identified.

### 5.8 Result Visualization

The analysis results are presented through an interactive dashboard, allowing users to explore:

- Extracted clinical entities.
- Guideline matches.
- Gap-detection findings.
- Prescription-related information.
- Clinical timelines.
- Confidence and explainability information.

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
- Contextual Analysis
- Negation Detection

### Backend

- FastAPI
- Python
- SQLAlchemy / Database Integration

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
- Python Virtual Environments
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

```bash
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

```bash
cd frontend-react
npm install
```

### Step 6: Start the Backend

From the project root, activate the virtual environment and run:

```bash
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

```bash
cd frontend-react
npm run dev
```

Open the local URL printed by Vite in your terminal.

---

## 10. Evaluation Framework

ClinGap-NLP includes a dedicated evaluation framework to assess the performance of its major clinical NLP components.

The evaluation covers:

- Clinical Named Entity Recognition.
- Negation Detection.
- Investigation Status Classification.
- Clinical Decision Gap Detection.
- Computational Performance.

### 10.1 Evaluation Dataset

The final reported evaluation used a controlled synthetic clinical benchmark.

| Dataset | Number of Records |
|---|---:|
| Development Dataset | 200 |
| Held-Out Test Dataset | 600 |
| Total | 800 |

**Test dataset characteristics:**

- 600 held-out test records.
- 10 medical specialties.
- 60 records per specialty.
- 12 clinical scenario archetypes.
- 50 records per scenario archetype.
- 558 unique narratives in the test set.
- 25 exact text overlaps between development and test datasets.

The ground-truth labels were generated programmatically using predefined clinical logic, independently of model predictions. The benchmark is intended for controlled prototype evaluation and is not an independent expert-annotated clinical trial.

### 10.2 Overall Component Performance

The following results were reported on the held-out evaluation data.

| Evaluation Component | Metric | Result |
|---|---|---:|
| Gap Detection | Accuracy | 67.50% |
| Gap Detection | Precision | 57.97% |
| Gap Detection | Recall | 80.00% |
| Gap Detection | F1-score | 67.23% |
| Negation Detection | Accuracy | 95.03% |
| Negation Detection | Precision | 100.00% |
| Negation Detection | Recall | 83.68% |
| Negation Detection | F1-score | 91.12% |
| Investigation Status | Accuracy | 88.86% |
| Investigation Status | Macro F1 (supported classes) | 88.17% |
| Clinical NER | Micro F1 | 77.66% |
| Clinical NER | Macro F1 | 83.81% |

### 10.3 Clinical Decision Gap Detection

Gap detection was evaluated using 600 test notes.

**Confusion Matrix**

| | Predicted Gap | Predicted No Gap |
|---|---:|---:|
| Actual Gap | 200 | 50 |
| Actual No Gap | 145 | 205 |

**Performance Metrics**

| Metric | Result |
|---|---:|
| Accuracy | 67.50% |
| Precision | 57.97% |
| Recall / Sensitivity | 80.00% |
| Specificity | 58.57% |
| F1-score | 67.23% |
| False Positive Rate | 41.43% |
| False Negative Rate | 20.00% |

The system achieved 80% recall, identifying a substantial proportion of potential clinical gaps. However, the false-positive rate of 41.43% indicates that guideline conditions and contextual interpretation require further improvement.

### 10.4 Negation Detection

Negation detection was evaluated across 785 annotated clinical mentions.

| Metric | Result |
|---|---:|
| Accuracy | 95.03% |
| Precision | 100.00% |
| Recall | 83.68% |
| F1-score | 91.12% |
| Specificity | 100.00% |

The evaluation recorded zero false-positive negation predictions. However, some complex negated statements were not identified, indicating scope for improvement in handling coordinated and disjunctive negation.

### 10.5 Investigation Status Classification

Investigation status classification was evaluated across 350 explicit investigation mentions.

The system classified investigation mentions into four categories:

- Completed / Performed
- Pending
- Ordered
- Not Performed

| Metric | Result |
|---|---:|
| Overall Accuracy | 88.86% |
| Macro Precision (supported classes) | 100.00% |
| Macro Recall (supported classes) | 81.50% |
| Macro F1 (supported classes) | 88.17% |

The Ordered class had zero ground-truth support in the evaluation dataset. Therefore, its recall and F1-score are undefined, and it is excluded from the supported-class macro F1 calculation.

### 10.6 Clinical Named Entity Recognition

Clinical NER was evaluated across six supported entity categories.

| Entity | Precision | Recall | F1-score |
|---|---:|---:|---:|
| Disease | 93.22% | 91.67% | 92.44% |
| Medication | 100.00% | 93.46% | 96.62% |
| Frequency | 100.00% | 94.00% | 96.91% |
| Dosage | 71.94% | 100.00% | 83.68% |
| Symptom | 72.01% | 82.20% | 76.77% |
| Investigation | 39.59% | 100.00% | 56.73% |

**Overall NER Performance**

| Metric | Result |
|---|---:|
| Micro Precision | 67.30% |
| Micro Recall | 91.84% |
| Micro F1-score | 77.66% |
| Macro F1-score | 83.81% |

The investigation entity category achieved 100% recall but lower precision, indicating that the extraction component sometimes identifies broader diagnostic text as investigation-related information.

### 10.7 Computational Performance

The pipeline was evaluated on 600 notes using CPU-based execution.

| Metric | Result |
|---|---:|
| Total Runtime | 70.02 seconds |
| Average Latency | 116.62 ms per note |
| Median Latency | 97.42 ms |
| 95th Percentile Latency | 129.50 ms |
| Throughput | 8.57 notes/second |
| Cold-Start Model Loading | 10.73 seconds |

These measurements describe the reported evaluation environment and should not be interpreted as guaranteed performance on other hardware.

### 10.8 Evaluation Limitations and Error Analysis

The evaluation identified several important limitations:

- **Synthetic Benchmark:** The test dataset contains controlled synthetic clinical narratives rather than independently collected real-world clinical records.
- **Programmatic Ground Truth:** Labels were generated using predefined clinical logic and were not independently validated through multi-annotator clinical expert review.
- **Dataset Overlap:** Twenty-five exact text overlaps were identified between development and test datasets.
- **False-Positive Gap Alerts:** Broad guideline conditions contributed to unnecessary gap predictions. One identified issue involved a disease-based rule triggering HbA1c recommendations for non-target chronic conditions.
- **Missed Gap Alerts:** Complex disjunctive negation, such as statements combining "not documented" and "not ordered," contributed to missed omissions.
- **Temporal Reasoning:** Resolved historical conditions may be interpreted as active because temporal reasoning is limited.
- **Investigation Extraction:** Broad diagnostic phrases can reduce investigation entity precision.

These findings identify specific areas for improving the system's contextual understanding, guideline matching, temporal analysis, and gap-detection logic.

**Important:** The reported metrics demonstrate prototype-level performance on a controlled synthetic benchmark. They do not establish clinical effectiveness, diagnostic accuracy, or patient safety.

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
- Component-wise performance evaluation.

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

The integration of clinical entity extraction, contextual analysis, negation detection, and deterministic guideline matching provides a foundation for further research into clinical NLP, guideline-based reasoning, and explainable clinical decision-support systems.

---

## 13. Limitations

- The quality of results depends on the completeness and clarity of clinical notes.
- Clinical terminology, abbreviations, and documentation styles may affect extraction.
- Guideline matching depends on the coverage and quality of the configured knowledge base.
- A missing documentation entry does not necessarily mean that a clinical action was not performed.
- Broad guideline conditions can generate unnecessary gap alerts.
- Complex negation and temporal references require further improvement.
- Confidence values should not be interpreted as guarantees of clinical correctness.
- The current evaluation uses synthetic data and programmatically generated ground-truth labels.
- The system requires independent expert validation before any real-world clinical deployment.

---

## 14. Future Enhancements

Potential future improvements include:

- Expanding clinical entity recognition using specialized transformer models.
- Improving contextual understanding of complex clinical narratives.
- Extending the clinical guideline knowledge base.
- Improving guideline matching to reduce false-positive alerts.
- Enhancing negation handling for complex clinical statements.
- Introducing stronger temporal reasoning across multiple clinical encounters.
- Improving explainability of gap-detection decisions.
- Evaluating generalization across additional clinical datasets.
- Adding broader clinical document formats and interoperability support.
- Conducting larger-scale independent clinical evaluations.
- Exploring integration with healthcare information systems.

---

## 15. Disclaimer

ClinGap-NLP is developed for academic, research, and educational purposes.

It is a clinical information analysis and decision-support prototype. It is not a medical diagnostic system and must not be used as a substitute for professional medical advice, diagnosis, or treatment.

The identified gaps and generated findings are not definitive evidence of inappropriate clinical care. Absence of documentation does not necessarily indicate that an investigation or treatment was not performed.

All clinical findings and recommendations must be independently reviewed by qualified healthcare professionals.

---

## 16. Authors and Contributors

**Project:** ClinGap-NLP – Clinical Decision Gap Intelligence System

**Domain:** Natural Language Processing | Clinical AI | Healthcare Analytics | Explainable AI

**Repository:**  
[https://github.com/santhoshroyals/ClinGap-NLP](https://github.com/santhoshroyals/ClinGap-NLP)

---

## 17. License

A license has not yet been specified for this repository. Until a license is added, the project should not be assumed to permit reuse, modification, or redistribution.

---

**ClinGap-NLP**  
*Bridging Clinical Documentation and Guideline-Based Intelligence*