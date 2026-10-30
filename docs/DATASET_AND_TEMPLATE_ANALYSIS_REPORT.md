# ClinGap-NLP: Dataset Quality, Template Clustering & Integrity Analysis

**Dataset File:** `C:\Desktop\nlp project\Clinical Notes Based on Indian Format\synthetic_notes_medium_v2.json`  
**Generator Script:** `C:\Desktop\nlp project\Clinical Notes Based on Indian Format\note_generator_v2.py`  
**Date:** October 2026  
**Status:** Reproducible Dataset Quality Audit (Zero Modification to Raw Dataset)  

---

## 1. Dataset Overview & Schema Inspection

The dataset consists of **10,000 synthetic discharge summary records** generated according to typical Indian hospital formatting conventions.

### Schema Fields
Every record contains exactly 5 top-level JSON fields:
- `id`: Integer (1 to 10,000)
- `version`: Constant `"2.0"`
- `specialty`: String (One of 5 medical specialties: `neurology`, `oncology`, `cardiology`, `general_medicine`, `pediatrics`)
- `length`: Constant `"medium"`
- `note`: String containing the multi-line unstructured clinical narrative.

### Integrity & Missing Values
- **Malformed records:** 0 (0.0%)
- **Missing or empty fields:** 0 across all 50,000 key-value pairs.
- **Unmatched records against generation logic:** 0 (100.0% match rate).

---

## 2. Statistical Distributions

### 2.1 Specialty Distribution

| Medical Specialty | Record Count | Percentage Share | Available in Generator Script |
|---|:---:|:---:|:---:|
| `neurology` | 2,099 | 20.99% | Yes |
| `oncology` | 1,998 | 19.98% | Yes |
| `cardiology` | 1,992 | 19.92% | Yes |
| `general_medicine` | 1,983 | 19.83% | Yes |
| `pediatrics` | 1,928 | 19.28% | Yes |
| `orthopaedics` | 0 | 0.00% | Defined in script, not sampled (`num_types=5`) |
| **Total** | **10,000** | **100.00%** | — |

### 2.2 Diagnosis Distribution
Across the entire 10,000-note corpus, there are **exactly 10 discrete diagnoses** (2 per specialty):

| Specialty | Diagnosis Name | ICD-10 Code | Record Count | Share of Specialty |
|---|---|:---:|:---:|:---:|
| `neurology` | Migraine | G43.9 | 1,101 | 52.45% |
| `neurology` | Ischemic Stroke | I63.9 | 998 | 47.55% |
| `oncology` | Metastatic Adenocarcinoma of unknown primary | C80.0 | 1,015 | 50.80% |
| `oncology` | Carcinoma of the Breast | C50.9 | 983 | 49.20% |
| `cardiology` | NSTEMI | I21.4 | 1,019 | 51.15% |
| `cardiology` | Atrial Fibrillation | I48.91 | 973 | 48.85% |
| `general_medicine` | Community-Acquired Pneumonia | J18.9 | 1,042 | 52.55% |
| `general_medicine` | Acute Gastritis | K29.00 | 941 | 47.45% |
| `pediatrics` | Viral Exanthem | B09 | 1,042 | 54.05% |
| `pediatrics` | Acute Gastroenteritis | A09 | 886 | 45.95% |
| **Total** | **All 10 Diagnoses** | — | **10,000** | **100.00%** |

---

## 3. Duplicate and Near-Duplicate Analysis

| Duplicate Level | Count | Share | Explanation |
|---|:---:|:---:|---|
| **Exact Raw Text Duplicates** | **0** | 0.00% | Every note has a unique randomized UHID (`random.randint(100000000, 999999999)`), admission number, and timestamp. |
| **Unique Clinical Bodies (Exact)** | **9,998** | 99.98% | Narrative text omitting header and signature (2 near-duplicates occurred by random slot collision). |
| **Unique Bodies (Numbers Normalized)** | **9,819** | 98.19% | Clinical bodies after masking integers (`days`, `years`, `BP`, `power`, `EF`, `blockage`). |
| **Unique Bodies (Core + Hinglish Stripped)** | **9,295** | 92.95% | Clinical bodies after masking numbers and stripping 13 dynamic Hinglish phrases. |
| **Underlying Narrative Template Clusters** | **1,152** | 11.52% | Theoretical and empirical maximum combinations of the 8 clinical section options across 5 specialties. |

---

## 4. Underlying Narrative Template Clustering

### 4.1 Combinatorial Architecture
In `note_generator_v2.py`, notes are constructed via combinatorial slot-filling across 8 discrete narrative sections:
1. `Chief Complaints` ($N=2$ options per specialty)
2. `History of Present Illness` ($N=2$ options per specialty)
3. `Past History` ($N=2$ options per specialty)
4. `Physical Examination` ($N=2$ options per specialty)
5. `Investigations` ($N=1$ option in cardiology; $N=2$ options in others)
6. `Diagnosis` ($N=2$ options per specialty)
7. `Course in Hospital` ($N=2$ options per specialty)
8. `Advice on Discharge` ($N=2$ options per specialty)

The theoretical number of combinations is:
$$\text{Clusters}_{\text{cardiology}} = 2^7 = 128$$
$$\text{Clusters}_{\text{neurology}} = \text{Clusters}_{\text{oncology}} = \text{Clusters}_{\text{general\_med}} = \text{Clusters}_{\text{pediatrics}} = 2^8 = 256$$
$$\text{Total Clusters} = 128 + 256 + 256 + 256 + 256 = \mathbf{1,152}$$

### 4.2 Empirical Coverage
Our deterministic cluster mapper (`evaluation/dataset_analysis.py`) successfully identified:
- **Total empirical clusters discovered:** **1,152** (100.0% coverage of theoretical combinations).
- **Records per cluster (mean):** 8.68 records.
- **Records per cluster (range):** 1 to 28 records.

---

## 5. Critical Clinical & Quality Observations

1. **Absence of Real Patient Identifiers:**  
   UHID and Admission numbers are randomized integers. The dataset cannot support longitudinal patient journey modeling or multi-encounter episode analysis.
2. **Independent Sampling Incongruities:**  
   Because demographic arrays and clinical templates are sampled independently:
   - Record 0 pairs pediatric name `"Baby Saanvi"` with `"Age/Sex: 68/F"` treated by a Cardiac Surgeon in Oncology.
   - Record 8 pairs `"Age/Sex: Newborn/M"` with `"Past History: Hypertension, smoker"`.
3. **Absence of Reference Ground Truth:**  
   The dataset contains no span annotations, negation labels, or decision-gap classifications. It represents synthetic supplementary text, not an evaluation ground truth.
