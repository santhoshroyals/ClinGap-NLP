# ClinGap-NLP Comprehensive Error Analysis Report

**Evaluation Corpus:** Held-Out Test Set (N=600)
**Random Seed:** 42
**False Positives (FP):** 145 (24.17% of test set)
**False Negatives (FN):** 50 (8.33% of test set)

---

## 1. False Positive (FP) Analysis

False Positives occur when ClinGap-NLP flags a clinical decision gap where independent clinical ground truth deems the encounter compliant or not indicated. Analysis reveals two primary failure modes:

### Failure Mode FP-1: Coarse Guideline Criteria Over-Triggering
- **Mechanism:** The prototype guideline engine configures Rule R2 as `{'entities': ['DISEASE']} -> HbA1c`. Consequently, any documented non-negated chronic disease entity (e.g., *essential hypertension*, *migraine*, *acute gastritis*, *osteoarthritis*) satisfies the trigger criteria and recommends an HbA1c investigation, despite diabetes being absent.
- **Clinical Impact:** In routine non-metabolic care, this generates spurious alerts, contributing to clinical alert fatigue.
- **Observed Count in Test Set:** Approximately 45 cases.

### Failure Mode FP-2: Historical / Inactive Condition Extraction
- **Mechanism:** Sentences detailing resolved illnesses (e.g., *'history of diabetes 10 years ago, fully resolved'*) lack temporal status filtering in the prototype NER pipeline. The entity *diabetes* is recognized as present and active, triggering Rule R2.

### Representative False Positive Case Vignettes

#### FP Example 1 (TEST-478 - Pediatrics)
- **Category:** Non-Target Disease Presentation
- **Clinical Note:** *"Follow-up visit in Pediatrics for chronic kidney disease stage 3. Patient is stable on salbutamol 100 mcg as needed. Blood pressure and vitals stable. No complaints of dizziness or pain."*
- **Predicted Gaps:** `[{'gap_type': 'MISSING_INVESTIGATION', 'description': 'The HbA1c investigation is missing from the record.', 'entity': 'hba1c', 'rule_id': 'R2'}]`
- **Ground Truth Rationale:** Patient has chronic kidney disease stage 3 which does not clinically require HbA1c or CBC. Independent ground truth is No Gap.

#### FP Example 2 (TEST-466 - Pediatrics)
- **Category:** Non-Target Disease Presentation
- **Clinical Note:** *"Follow-up visit in Pediatrics for chronic kidney disease stage 3. Patient is stable on atorvastatin 40 mg at bedtime. Blood pressure and vitals stable. No complaints of dizziness or pain."*
- **Predicted Gaps:** `[{'gap_type': 'MISSING_INVESTIGATION', 'description': 'The HbA1c investigation is missing from the record.', 'entity': 'hba1c', 'rule_id': 'R2'}]`
- **Ground Truth Rationale:** Patient has chronic kidney disease stage 3 which does not clinically require HbA1c or CBC. Independent ground truth is No Gap.

#### FP Example 3 (TEST-251 - Gastroenterology)
- **Category:** Contradictory / Discrepant Presentation
- **Clinical Note:** *"Consultation in Gastroenterology. Family reported possible fever yesterday at home, but patient is currently afebrile, denies any discomfort, and physical examination is entirely normal. No investigations indicated at present."*
- **Predicted Gaps:** `[{'gap_type': 'MISSING_INVESTIGATION', 'description': 'The CBC investigation is missing from the record.', 'entity': 'cbc', 'rule_id': 'R1'}]`
- **Ground Truth Rationale:** Reported fever was resolved/contradicted by clinical exam; no gap exists.

#### FP Example 4 (TEST-369 - Nephrology)
- **Category:** Historical / Resolved Condition
- **Clinical Note:** *"Patient seen for annual wellness review in Nephrology. Remote history of type 2 diabetes mellitus 9 years ago, fully resolved with lifestyle modification and currently normal blood sugars. No current symptoms, no current medications."*
- **Predicted Gaps:** `[{'gap_type': 'MISSING_INVESTIGATION', 'description': 'The HbA1c investigation is missing from the record.', 'entity': 'hba1c', 'rule_id': 'R2'}]`
- **Ground Truth Rationale:** Historical resolved type 2 diabetes mellitus without active disease; clinically no gap.

#### FP Example 5 (TEST-430 - Pediatrics)
- **Category:** Non-Target Disease Presentation
- **Clinical Note:** *"Follow-up visit in Pediatrics for bronchial asthma. Patient is stable on amoxicillin 250 mg three times daily. Blood pressure and vitals stable. No complaints of dizziness or pain."*
- **Predicted Gaps:** `[{'gap_type': 'MISSING_INVESTIGATION', 'description': 'The HbA1c investigation is missing from the record.', 'entity': 'hba1c', 'rule_id': 'R2'}]`
- **Ground Truth Rationale:** Patient has bronchial asthma which does not clinically require HbA1c or CBC. Independent ground truth is No Gap.

---

## 2. False Negative (FN) Analysis

False Negatives represent missed clinical gaps where recommended investigations were legitimately omitted or unperformed. Key root causes identified:

### Failure Mode FN-1: Disjunctive Negation Misclassification ('not documented or ordered')
- **Mechanism:** In complex clausal sentences such as *'However, routine HbA1c was not documented or ordered'*, the isolated keyword *'ordered'* triggered the regex pattern `is_ordered_or_requested` in `extract_investigation_status()`. Because the preceding negation (*'not documented or'*) was separated by a coordinating disjunction, the rule-based status classifier assigned `status: ordered`. Downstream gap detection (`detect_gaps()`) intentionally suppresses alerts for actively ordered investigations, inadvertently masking the missing investigation and producing 50 False Negatives (recall = 80.00%).
- **Clinical Impact:** Negative assertions of orders (*'not ordered'*, *'neither ordered nor done'*) require syntactic dependency parsing or scoped disjunctive negation binding to avoid premature suppression.

### Representative False Negative Case Vignettes

#### FN Example 1 (TEST-472 - Pediatrics)
- **Category:** Partially Satisfied Guideline
- **Clinical Note:** *"Patient with diabetes mellitus presents with new fever. Complete blood count was performed and results were within normal limits. However, routine HbA1c was not documented or ordered."*
- **Expected Missing Investigation:** `['hba1c']`
- **Ground Truth Rationale:** CBC satisfied acute presentation; however, HbA1c for diabetes mellitus remains undocumented.

#### FN Example 2 (TEST-316 - Neurology)
- **Category:** Partially Satisfied Guideline
- **Clinical Note:** *"Patient with uncontrolled diabetes presents with new chest pain. Complete blood count revealed no acute abnormality. However, routine HbA1c was not documented or ordered."*
- **Expected Missing Investigation:** `['hba1c']`
- **Ground Truth Rationale:** CBC satisfied acute presentation; however, HbA1c for uncontrolled diabetes remains undocumented.

#### FN Example 3 (TEST-424 - Pediatrics)
- **Category:** Partially Satisfied Guideline
- **Clinical Note:** *"Patient with uncontrolled diabetes presents with new severe headache. Complete blood count showed normal parameters. However, routine HbA1c was not documented or ordered."*
- **Expected Missing Investigation:** `['hba1c']`
- **Ground Truth Rationale:** CBC satisfied acute presentation; however, HbA1c for uncontrolled diabetes remains undocumented.

#### FN Example 4 (TEST-592 - Oncology)
- **Category:** Partially Satisfied Guideline
- **Clinical Note:** *"Patient with type 2 diabetes mellitus presents with new chest pain. Complete blood count result was documented in the medical chart. However, routine HbA1c was not documented or ordered."*
- **Expected Missing Investigation:** `['hba1c']`
- **Ground Truth Rationale:** CBC satisfied acute presentation; however, HbA1c for type 2 diabetes mellitus remains undocumented.

#### FN Example 5 (TEST-172 - Pulmonology)
- **Category:** Partially Satisfied Guideline
- **Clinical Note:** *"Patient with uncontrolled diabetes presents with new productive cough. Complete blood count completed with unremarkable findings. However, routine HbA1c was not documented or ordered."*
- **Expected Missing Investigation:** `['hba1c']`
- **Ground Truth Rationale:** CBC satisfied acute presentation; however, HbA1c for uncontrolled diabetes remains undocumented.

