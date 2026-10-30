# ClinGap-NLP: Human Annotation Guidelines & Protocol

**Target Batch:** `BATCH_HELD_OUT_TEST_50_V1` (50 Held-Out Stratified Cases)
**Status:** Reference Annotation Instructions (Academic Protocol)

## 1. Ethical & Academic Principles
1. **Zero System Contamination:** ClinGap-NLP model outputs must never be presented to the annotator during labeling to avoid anchoring bias.
2. **Separation of Layers:** Text-extraction spans (what is written) must be labeled separately from clinical care quality judgments (what ought to have been done).

## 2. Layer 1: Text-Extraction Annotation Rules

### 2.1 Clinical Entity Spans
- **Entity Types:** `DISEASE`, `SYMPTOM`, `MEDICATION`, `INVESTIGATION`, `DOSAGE`, `FREQUENCY`, `LAB_TEST`.
- Tag exact word spans with start and end character offsets.
- Administrative headers (UHID, Hospital Name, Doctor Signature) must NOT be tagged as clinical entities.

### 2.2 Negation Scoping
- Mark `is_negated: True` if the patient denies the symptom or the finding is explicitly stated as absent (e.g., 'no fever', 'denies chest pain', 'cyanosis: -').
- Record the negation cue word ('no', 'denies', 'without', '-').

### 2.3 Investigation Clinical Status
- `completed/performed`: Results or findings are explicitly documented.
- `ordered`: Test was requisitioned/sent, but results are not yet available.
- `pending`: Explicitly awaiting lab report/imaging review.
- `not performed/cancelled`: Explicitly declined, omitted, refused, or cancelled.
- `undocumented`: Not mentioned anywhere in the clinical encounter.

## 3. Layer 2: Clinical Guideline & Decision Gap Rules

### 3.1 Guideline Applicability
- Only activate guidelines whose prerequisite clinical indications are medically affirmed.
- Do not trigger diabetes guidelines on non-diabetic conditions.

### 3.2 Decision Gap Flagging
- Flag a gap ONLY if a medically necessary diagnostic test or therapy is omitted without clinical justification.
- A test that is already ordered or completed is NOT a missing gap.

## 4. Submission & Quality Control
Set `verification_status: EXPERT_VERIFIED` only after full review by an independent clinician or clinical informatics domain specialist.
