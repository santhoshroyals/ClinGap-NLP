# ClinGap-NLP: 100-Note Blinded Ground-Truth Annotation Guidelines

**Version:** 1.0 (Evaluation Phase 4)  
**Target File:** [`evaluation_100_blinded_annotation_template.csv`](evaluation_100_blinded_annotation_template.csv)  
**Sample Size:** Exactly 100 clinical notes (50 Synthetic Indian + 50 MTSamples)  
**Provenance Manifest:** [`evaluation_100_subset_manifest.json`](evaluation_100_subset_manifest.json)  

---

> [!IMPORTANT]
> **BLINDED ANNOTATION INTEGRITY RULES:**
> 1. Annotators must inspect **only the clinical narrative** (`clinical_note`) to record reference judgments.
> 2. Diagnosis labels, ICD codes, and model predictions have been strictly hidden from this template to eliminate confirmation bias.
> 3. Do NOT edit or modify `eval_id` or `clinical_note`.
> 4. Do NOT leave required fields blank. If no entity or gap applies, explicitly enter `None` or `NO_GAP`.

---

## 1. Column Reference & Allowed Value Specifications

| Column Name | Required | Allowed Formats / Values | Description |
| :--- | :---: | :--- | :--- |
| `eval_id` | **Yes** | Read-Only (e.g., `EVAL-001`) | Unique evaluation identifier. Do not alter. |
| `clinical_note` | **Yes** | Read-Only | Complete verbatim narrative of the patient encounter. |
| `clinical_entities_and_types` | **Yes** | JSON array or semicolon list: `text: CATEGORY` | Clinical findings identified in the note with their semantic categories. |
| `negation_status` | **Yes** | `None negated` or list: `text: NEGATED` | Identifies clinical entities explicitly negated, denied, or absent. |
| `investigation_names` | **Yes** | Semicolon list: `test1; test2` | Diagnostic investigations mentioned in the note. |
| `investigation_status` | **Yes** | List: `test_name: STATUS` | Clinical execution status of each mentioned investigation. |
| `potential_decision_gap` | **Yes** | `GAP_PRESENT` or `NO_GAP` | Whether an omission or guideline gap exists. |
| `decision_gap_supporting_evidence` | **Yes** | Clinical text rationale | Medical evidence or clinical reason supporting the gap judgment. |
| `annotator_id` | **Yes** | String (e.g., `CLINICIAN-01`) | Identifier of the annotator. |
| `reviewer_notes` | Optional | Free text | Discrepancies, ambiguous phrasing, or comments. |

---

## 2. Allowed Semantic Categories for NER (`clinical_entities_and_types`)

Every identified clinical entity span must be assigned exactly one of the eight standardized categories:

1. **`SYMPTOM`**: Patient-reported complaints, sensations, or clinical signs.
   - *Examples:* `headache`, `fever`, `nausea`, `chest pain`, `saans lene mein takleef`, `vomiting`, `rash`, `palpitations`.
2. **`DISEASE`**: Formal diagnoses, pathological conditions, or known comorbidities.
   - *Examples:* `ischemic stroke`, `migraine`, `type 2 diabetes`, `hypertension`, `pneumonia`, `acute gastritis`, `atrial fibrillation`.
3. **`MEDICATION`**: Pharmacological agents, generic drug names, brand names, or infusions.
   - *Examples:* `clopidogrel`, `aspirin`, `amoxicillin`, `metformin`, `lisinopril`, `iv thrombolysis`.
4. **`INVESTIGATION`**: Diagnostic procedures, laboratory panels, or imaging modalities.
   - *Examples:* `MRI`, `CT scan`, `chest x-ray`, `CBC`, `ECG`, `upper GI endoscopy`, `biopsy`, `HbA1c`, `ultrasound`.
5. **`LAB_TEST`**: Specific test findings, quantitative metrics, or diagnostic observations.
   - *Examples:* `left MCA infarct`, `no bleed`, `ST elevation`, `WBC elevated`, `sinus rhythm`, `normal cardiac enzymes`.
6. **`DOSAGE`**: Strength or quantitative amount of a prescribed drug.
   - *Examples:* `75mg`, `500mg`, `5ml`, `10 units`.
7. **`FREQUENCY`**: Timing, frequency, or dosing schedule.
   - *Examples:* `OD`, `BD`, `TID`, `QID`, `daily`, `once daily`, `prn`.
8. **`DURATION`**: Time span or onset duration.
   - *Examples:* `for 7 days`, `since childhood`, `for 2 weeks`, `acute`.

### Accepted Formats:
- **Option A (Delimited):** `severe headache: SYMPTOM; MRI: INVESTIGATION; Tab. Clopidogrel: MEDICATION; 75mg: DOSAGE; OD: FREQUENCY`
- **Option B (JSON):** `[{"text": "severe headache", "category": "SYMPTOM"}, {"text": "MRI", "category": "INVESTIGATION"}]`

---

## 3. Negation Polarity Specification (`negation_status`)

- **`AFFIRMED` (Default):** The condition is present, affirmed, or observed in the patient.
- **`NEGATED`:** The condition is explicitly negated, denied, ruled out, or absent within the clinical clause.
  - *English triggers:* `no`, `denies`, `without`, `absence of`, `not`, `never`, `negative for`.
  - *Hindi/Hinglish triggers:* `nahi`, `nahin`, `na`, `koi nahi`, `bina`.

### Accepted Formats:
- If all entities in the note are affirmed: enter `None negated`
- If specific entities are negated: enter `saans lene mein takleef: NEGATED; photophobia: NEGATED` or JSON `[{"entity": "saans lene mein takleef", "negated": true}]`

---

## 4. Investigation Execution Status Specification (`investigation_status`)

Each diagnostic investigation mentioned in the note must be classified into one of four mutually exclusive execution states:

1. **`completed/performed`**:
   - The test was performed and its results, images, or qualitative findings are documented in the record.
   - *Examples:* `"MRI: Left MCA infarct"` $\rightarrow$ `MRI: completed/performed`
2. **`ordered`**:
   - The test was ordered, requested, scheduled, or recommended, but results are not yet recorded.
   - *Examples:* `"Recommend upper GI endoscopy"`, `"CBC ordered"` $\rightarrow$ `CBC: ordered`
3. **`pending`**:
   - The test was collected or performed, but results are explicitly noted as pending or awaited.
   - *Examples:* `"Blood cultures pending"`, `"Biopsy awaited"` $\rightarrow$ `biopsy: pending`
4. **`not performed`**:
   - The test was explicitly not conducted, deferred, refused, omitted, or cancelled.
   - *Examples:* `"Patient declined colonoscopy"`, `"X-ray was not performed"` $\rightarrow$ `x-ray: not performed`

### Accepted Format:
- Semicolon list: `mri: completed/performed; ct: completed/performed; cbc: ordered`

---

## 5. Potential Decision-Gap Specification (`potential_decision_gap`)

A potential clinical decision gap occurs when standard-of-care guidelines or clinical evidence indicate that an essential diagnostic or therapeutic step is missing, omitted, or undocumented.

### Allowed Values:
- **`GAP_PRESENT`** (or `true`): A standard-of-care guideline omission exists.
  - *Standard Types:* `MISSING_INVESTIGATION`, `UNPERFORMED_ORDERED_TEST`, `MEDICATION_OMISSION`.
- **`NO_GAP`** (or `false`): All expected standard-of-care investigations and therapies are accounted for, or the encounter was fully compliant.

### Accompanying Evidence (`decision_gap_supporting_evidence`):
- Annotator must state the clinical justification (e.g., *"Patient with suspected stroke/T2DM presentation has no documented HbA1c or glycemic evaluation in the record."* or *"Routine post-operative follow-up without unfulfilled guideline orders."*).

---

## 6. Concrete Annotation Examples

### Example 1: Synthetic Indian Note (`EVAL-001`)
```csv
eval_id: EVAL-001
clinical_entities_and_types: severe headache: SYMPTOM; nausea: SYMPTOM; photophobia: SYMPTOM; saans lene mein takleef: SYMPTOM; epilepsy: DISEASE; MRI: INVESTIGATION; CT: INVESTIGATION; Left MCA infarct: LAB_TEST; no bleed: LAB_TEST; Tab. Clopidogrel: MEDICATION; 75mg: DOSAGE; OD: FREQUENCY; IV thrombolysis: MEDICATION
negation_status: saans lene mein takleef: NEGATED
investigation_names: mri; ct
investigation_status: mri: completed/performed; ct: completed/performed
potential_decision_gap: GAP_PRESENT
decision_gap_supporting_evidence: In acute ischemic stroke presenting with vascular risk factors, baseline glycemic assessment (HbA1c / blood glucose) and hematologic screen (CBC) are standard guidelines but omitted from discharge summary.
annotator_id: CLINICIAN-01
reviewer_notes: saans lene mein takleef negated in HPI ("thi" past phrasing indicates resolved or denied).
```

### Example 2: Real-World MTSamples Record (`EVAL-305`)
```csv
eval_id: EVAL-305
clinical_entities_and_types: right knee pain: SYMPTOM; swelling: SYMPTOM; osteoarthritis: DISEASE; right knee arthroscopy: INVESTIGATION; x-ray: INVESTIGATION; joint space narrowing: LAB_TEST; Ibuprofen: MEDICATION; 600mg: DOSAGE; TID: FREQUENCY
negation_status: None negated
investigation_names: right knee arthroscopy; x-ray
investigation_status: x-ray: completed/performed; right knee arthroscopy: ordered
potential_decision_gap: NO_GAP
decision_gap_supporting_evidence: Conservative management and imaging completed appropriately prior to elective arthroscopy order. No missing standard-of-care investigations.
annotator_id: CLINICIAN-02
reviewer_notes: Elective orthopedics case, complete workup documented.
```

---

## 7. Submission and Next Steps

Once the 100 rows in [`evaluation_100_blinded_annotation_template.csv`](evaluation_100_blinded_annotation_template.csv) are completed:
1. Save the file in the same directory (or as `evaluation_100_completed_annotations.csv`).
2. Run the evaluation script [`evaluate_100_annotations.py`](evaluate_100_annotations.py) to generate unbiased statistical metrics.
