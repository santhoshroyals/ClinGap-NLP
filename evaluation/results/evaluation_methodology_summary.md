# ClinGap-NLP: Scientific Evaluation Methodology Summary (Audited)

## 1. Study Design & Evaluation Framework
This study establishes an objective, reproducible benchmark for evaluating **ClinGap-NLP**, an automated decision-support prototype. The system couples transformer-based token classification (`d4data/biomedical-ner-all`), dense contextual sentence representation (`emilyalsentzer/Bio_ClinicalBERT`), clausal negation scoping, multi-class diagnostic status resolution, and deterministic guideline matching.

*Architectural Role Distinction:*
- **Biomedical NER (RoBERTa token classification):** Identifies entity token spans for clinical entities (Disease, Symptom, Investigation, Medication, Dosage, Frequency).
- **Bio_ClinicalBERT:** Computes a 768-dimensional dense sentence embedding representing the lexical context of the note. It acts solely as a numerical representation feature and does NOT execute clinical logic or decision rules.
- **GuidelineEngine:** Executes deterministic, criteria-based rules against extracted non-negated entities to identify unperformed or omitted investigations.

## 2. Dataset Construction & Scientific Integrity Disclosures
- **Target Corpus:** 800 synthetic clinical records partitioned into **200 Development/Validation** cases and **600 Held-Out Final Test** cases under a fixed seed (`SEED = 42`).
- **Stratification:** Evenly stratified across 10 major medical specialties (Internal Medicine, Cardiology, Pulmonology, Endocrinology, Gastroenterology, Neurology, Nephrology, Pediatrics, Geriatrics, Oncology; 60 test notes each).
- **Clinical Scenario Archetypes:** Spans 12 distinct scenario archetypes (50 notes each): missing acute labs, chronic monitoring omissions, explicit test refusals, completed investigations, active pending orders, coordinated negations, and non-target disease boundary cases.
- **Ground-Truth Label Generation:** Ground-truth labels were authored programmatically based on clinical guideline logic. They were NOT derived from model predictions, but also NOT annotated by blinded external physician panels. This represents a controlled programmatic benchmark.
- **Template Diversity & Leakage Analysis:**
  - Unique Test Notes: 558 out of 600 (42 template-level duplicates across different specialties due to combinatorial demographic sampling).
  - Unique Dev Notes: 196 out of 200.
  - Text Overlap between Dev and Test: 25 notes share identical template text due to independent uniform sampling.
  - Test IDs and Dev IDs are 100% disjoint (0 ID overlap).

## 3. Metrics Formulation & Audit
- **Decision Gap Detection:** Evaluated via 2x2 Confusion Matrix, Accuracy, Precision (PPV), Recall / Sensitivity (TPR), Specificity (TNR), F1-Score, False Positive Rate (FPR), and False Negative Rate (FNR). Wilson Score 95% Confidence Intervals are computed.
- **Negation Detection:** Evaluated across clausal and coordinated clinical entities ($N = 785$).
- **Investigation Status Classification:** Evaluated across a 4x4 multi-class matrix (`completed/performed`, `pending`, `ordered`, `not performed`). The `ordered` class had 0 ground-truth support and is explicitly flagged as undefined (N/A) rather than assigned an artificial zero F1.
- **Clinical NER:** Strict normalized entity category and canonical value matching across 6 evaluated categories, reporting micro-averaged span F1 and macro-averaged category F1.

## 4. Clinical Safety & Scope Disclaimer
ClinGap-NLP is an academic research prototype. The system operates on educational demonstration rules and has NOT undergone prospective clinical validation or regulatory evaluation. It does not diagnose medical conditions or constitute clinical advice.
