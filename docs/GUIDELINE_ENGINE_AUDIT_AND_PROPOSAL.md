# ClinGap-NLP: Guideline Engine Audit & Proposal for Faculty Review

**Component Audited:** `knowledge_base/guidelines.json` and `backend/services/guideline_service.py`  
**Date:** October 2026  
**Status:** Audit & Proposal (Existing Production Rules Preserved Unchanged)  

---

## 1. Executive Summary & Audit Scope

ClinGap-NLP’s guideline matching component aims to identify when clinical documentation omits necessary diagnostic or therapeutic care steps according to established clinical practice guidelines. 

This audit analyzes the current active rules in `knowledge_base/guidelines.json`, identifies the causes of clinically irrelevant matches and false-positive gap alerts, and outlines a disease-specific rule architecture for future faculty review.

> **Policy Confirmation:** In accordance with user directives, **no modifications have been made to existing production rules**. Demonstration rules remain clearly identified as educational prototypes.

---

## 2. Audit of Existing Active Guideline Rules

The active rule base currently comprises three rules:

```json
[
  {
    "rule_id": "R1",
    "description": "Educational Demonstration Rule: Respiratory/symptomatic presentation – recommend CBC",
    "criteria": { "entities": ["SYMPTOM"] },
    "recommendation": { "type": "INVESTIGATION", "name": "CBC" }
  },
  {
    "rule_id": "R2",
    "description": "Educational Demonstration Rule: Diabetes evaluation – recommend HbA1c",
    "criteria": { "entities": ["DISEASE"] },
    "recommendation": { "type": "INVESTIGATION", "name": "HbA1c" }
  },
  {
    "rule_id": "R3",
    "description": "Educational Demonstration Rule: No gap case – recommend nothing",
    "criteria": { "entities": [] },
    "recommendation": null
  }
]
```

### 2.1 Critical Trigger Deficiencies

#### Deficiency 1: Rule R1 (Any Symptom $\rightarrow$ Recommend CBC)
- **Mechanism:** In `backend/services/guideline_service.py`, Rule R1 evaluates whether any non-negated entity of type `SYMPTOM` is present.
- **Clinical Consequence:** Symptoms such as *headache*, *dizziness*, *epigastric discomfort*, *back pain*, or *knee joint stiffness* trigger a clinical recommendation for a Complete Blood Count (`CBC`).
- **Impact:** In routine clinical practice, a CBC is not universally indicated for isolated tension headaches or mechanical joint pain. When evaluated on the 10,000 synthetic notes, Rule R1 flags missing CBC gaps indiscriminately across neurology and orthopedics notes.

#### Deficiency 2: Rule R2 (Any Disease $\rightarrow$ Recommend HbA1c)
- **Mechanism:** Rule R2 evaluates whether any non-negated entity of type `DISEASE` is present.
- **Clinical Consequence:** Diagnoses such as *Metastatic Adenocarcinoma*, *Ischemic Stroke*, *Community-Acquired Pneumonia*, *Migraine*, or *Osteoarthritis* trigger a clinical recommendation for `HbA1c` (glycated hemoglobin).
- **Impact:** In our empirical test of `ClinicalPipeline` on oncology and neurology records from the Indian dataset, Rule R2 triggered on *Adenocarcinoma* and *Stroke*, generating false-positive gaps stating: `"The HbA1c investigation is missing from the record"`. Glycated hemoglobin is a glycemic monitoring marker specific to diabetes mellitus, not a universal biomarker for all human diseases.

---

## 3. Proposed Disease-Specific Guideline Architecture (For Faculty Review)

To transition ClinGap-NLP from educational prototype rules to academically defensible clinical decision intelligence, rules should require **specific normalized concepts** rather than coarse grammatical categories.

### 3.1 Proposed Rule Schema Structure

```json
{
  "rule_id": "GL-T2DM-HBA1C",
  "rule_name": "Type 2 Diabetes Mellitus: Glycemic Monitoring Protocol",
  "rule_type": "DISEASE_SPECIFIC",
  "status": "PROPOSED_FOR_FACULTY_REVIEW",
  "evidence_source": "ICMR Guidelines for Management of Type 2 Diabetes / ADA Standards of Care",
  "criteria": {
    "required_disease_concepts": [
      "diabetes mellitus",
      "type 2 diabetes mellitus",
      "t2dm",
      "non-insulin dependent diabetes mellitus"
    ],
    "negation_allowed": false,
    "contextual_exclusions": [
      "gestational diabetes"
    ]
  },
  "recommendation": {
    "target_category": "INVESTIGATION",
    "canonical_name": "HbA1c",
    "accepted_synonyms": [
      "glycated hemoglobin",
      "hemoglobin a1c",
      "a1c",
      "glycosylated hemoglobin"
    ],
    "acceptable_statuses": [
      "completed/performed",
      "ordered",
      "pending"
    ],
    "severity_if_missing": "moderate"
  },
  "rationale": "Patients diagnosed with Type 2 Diabetes require documented assessment of glycated hemoglobin (HbA1c) to evaluate long-term glycemic control and prevent microvascular complications."
}
```

### 3.2 Candidate Disease-Specific Rules for Future Implementation

| Rule ID | Clinical Condition | Prerequisite Concepts | Recommended Action | Clinical Guideline Standard |
|---|---|---|---|---|
| `GL-T2DM-HBA1C` | Diabetes Mellitus | `diabetes mellitus`, `t2dm`, `t1dm` | `HbA1c` | ICMR / ADA Standards |
| `GL-HTN-LIPID` | Hypertension / ASCVD | `hypertension`, `essential hypertension` | `Lipid Profile` | ICMR / ACC/AHA Guidelines |
| `GL-CAP-CXR` | Suspected Pneumonia | `community-acquired pneumonia` | `Chest X-ray (CXR)` | IDSA / ATS Guidelines |
| `GL-AFIB-ECG` | Atrial Fibrillation | `atrial fibrillation`, `afib` | `ECG (12-lead)` | ESC / AHA Guidelines |
| `GL-DKA-KETONES` | Diabetic Ketoacidosis | `diabetic ketoacidosis`, `dka` | `Urine/Serum Ketones` | Endocrine Society |

---

## 4. Summary & Preservation Notice

- **Active Rules Preserved:** `knowledge_base/guidelines.json` remains untouched.
- **Existing Tests Intact:** All 56 existing regression tests continue to pass without regression.
- **Action Required:** Faculty and domain-expert review is recommended before transitioning from educational rules (`R1`, `R2`) to disease-specific concept matching (`GL-*`).
