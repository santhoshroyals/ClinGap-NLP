"""
dataset_analysis.py - Dataset Quality, Template Analysis, and Manifest Generator
ClinGap-NLP Evaluation Infrastructure (Phase 1)

Analyzes synthetic_notes_medium_v2.json:
- Exact duplicate and near-duplicate analysis.
- Determines the exact underlying narrative template clusters.
- Maps all records to their deterministic template cluster ID.
- Generates reproducible dataset manifest.
- Does NOT modify the original dataset.
"""

import os
import sys
import json
import re
from collections import Counter, defaultdict
from typing import Dict, List, Any, Tuple


# Specialty slot templates from note_generator_v2.py
SPECIALTY_SLOT_PATTERNS = {
    'cardiology': {
        'complaints': ['Chest pain aur saans phoolna for', 'Palpitations and dizziness for'],
        'hpi': ['Substernal pain on exertion, with diaphoresis.', 'Irregular heartbeat, no syncope.'],
        'past': ['Hypertension since', 'Coronary artery disease, post-stent.'],
        'exam': ['Heart: S1/S2 normal, no murmur.', 'Pulse: Irregular.'],
        'invest': ['ST elevation; Trop-I: Positive; Echo: EF'],
        'diag': ['NSTEMI (ICD: I21.4).', 'Atrial Fibrillation (ICD: I48.91).'],
        'course': ['Admitted to CCU. Thrombolysis kiya gaya, then angioplasty with stent.', 'Antiarrhythmics given, rhythm stabilized.'],
        'advice': ['Tab. Aspirin 75mg OD, Tab. Atorvastatin 40mg HS.', 'Diet: Low-salt; Follow-up: 7 days.']
    },
    'neurology': {
        'complaints': ['Right side weakness aur bolne mein difficulty for', 'Severe headache with nausea for'],
        'hpi': ['Sudden onset, with facial droop.', 'Migraine-like, photophobia.'],
        'past': ['Hypertension, smoker.', 'Epilepsy since childhood.'],
        'exam': ['right limbs; Reflexes: Hyperactive.', 'Cranial nerves: Intact.'],
        'invest': ['MRI: Left MCA infarct; CT: No bleed.', 'EEG: Abnormal spikes.'],
        'diag': ['Ischemic Stroke (ICD: I63.9).', 'Migraine (ICD: G43.9).'],
        'course': ['IV thrombolysis, physiotherapy. Improved.', 'Antimigraine prophylaxis started.'],
        'advice': ['Tab. Clopidogrel 75mg OD.', 'Avoid triggers; Follow-up: 10 days.']
    },
    'pediatrics': {
        'complaints': ['Loose motions aur vomiting for', 'Fever and rash for'],
        'hpi': ['Acute, with mild dehydration.', 'High fever, measles-like rash.'],
        'past': ['Vaccinations up-to-date.', 'Recent URI.'],
        'exam': ['Dehydrated, abdomen soft.', 'throat congested.'],
        'invest': ['CBC: WBC elevated; Stool: No parasites.', 'CRP: Positive.'],
        'diag': ['Acute Gastroenteritis (ICD: A09).', 'Viral Exanthem (ICD: B09).'],
        'course': ['ORS and IV fluids. Zinc given.', 'Symptomatic treatment, resolved.'],
        'advice': ['Syrup Zinc 5ml OD.', 'Diet: Breastfeed; Follow-up: 5 days.']
    },
    'general_medicine': {
        'complaints': ['Fever aur cough for', 'Abdominal pain for'],
        'hpi': ['Productive cough, no hemoptysis.', 'Epigastric, post-meal.'],
        'past': ['Diabetes on insulin.', 'GERD history.'],
        'exam': ['Chest: Crepitations.', 'Abdomen: Tender epigastrium.'],
        'invest': ['X-ray: Pneumonia.', 'Endoscopy: Gastritis.'],
        'diag': ['Community-Acquired Pneumonia (ICD: J18.9).', 'Acute Gastritis (ICD: K29.00).'],
        'course': ['IV antibiotics. Fever subsided.', 'PPI and antacids given.'],
        'advice': ['Tab. Amoxicillin 500mg TDS.', 'Diet: Bland; Follow-up: 1 week.']
    },
    'oncology': {
        'complaints': ['Unexplained weight loss and fatigue for', 'Lump in the breast for'],
        'hpi': ['Patient noticed a gradual loss of appetite.', 'The lump is painless and hard to touch.'],
        'past': ['Family history of cancer.', 'No history of major illness.'],
        'exam': ['Cachexic look, pallor present.', 'hard lump in the upper outer quadrant of the left breast.'],
        'invest': ['CBC shows anemia. PET scan shows metastasis.', 'Mammogram and biopsy confirmed malignancy.'],
        'diag': ['Metastatic Adenocarcinoma of unknown primary (ICD: C80.0).', 'Carcinoma of the Breast (ICD: C50.9).'],
        'course': ['Patient started on palliative chemotherapy.', 'Underwent mastectomy followed by chemotherapy.'],
        'advice': ['High protein diet.', 'Regular follow-up in the oncology OPD.']
    }
}

SLOT_ORDER = ['complaints', 'hpi', 'past', 'exam', 'invest', 'diag', 'course', 'advice']

HINGLISH_PHRASES = [
    'Patient ko fever tha', 'dard ho raha tha', 'saans lene mein takleef thi',
    'chakkar aa rahe the', 'bahut weakness feel kar raha tha',
    'Abhi theek hai', 'condition stable hai', 'thoda better feel kar rahe hain',
    'pain kam hua hai', 'koi improvement nahi hai',
    'Dawa time pe lena', 'pura course complete karna', 'tension mat lo',
    'paani jyada peena', 'report leke aana'
]


def identify_template_cluster(note: str, specialty: str) -> Tuple[str, Tuple[int, ...]]:
    """
    Identifies the exact combinatorial template slot index for each section of the note.
    Returns (cluster_id_str, slot_indices_tuple).
    """
    if specialty not in SPECIALTY_SLOT_PATTERNS:
        return (f"{specialty}_UNKNOWN", (-1,) * len(SLOT_ORDER))
    
    spec_data = SPECIALTY_SLOT_PATTERNS[specialty]
    slots = []
    for slot_name in SLOT_ORDER:
        matched_idx = -1
        for idx, pattern in enumerate(spec_data[slot_name]):
            if pattern in note:
                matched_idx = idx
                break
        slots.append(matched_idx)
    
    slots_tuple = tuple(slots)
    # Compact cluster signature: e.g. "cardiology_S_0_1_0_0_0_1_0_0"
    cluster_id = f"{specialty}_S_" + "_".join(str(s) for s in slots)
    return (cluster_id, slots_tuple)


def extract_diagnosis(note: str) -> str:
    """Extract canonical diagnosis line from clinical note."""
    m = re.search(r'Diagnosis:\s*(.+)', note)
    if m:
        return m.group(1).strip()
    return "UNKNOWN"


def extract_clinical_body(note: str) -> str:
    """Extract clinical body text omitting administrative header and signature."""
    idx = note.find('Chief Complaints:')
    if idx != -1:
        body = note[idx:]
    else:
        body = note
    sig_idx = body.rfind('Signature')
    if sig_idx != -1:
        body = body[:sig_idx].rsplit('\n', 2)[0]
    return body.strip()


def run_dataset_analysis(
    dataset_path: str,
    output_dir: str = None
) -> Dict[str, Any]:
    """
    Performs comprehensive dataset quality, duplicate, and template analysis.
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    print(f"Loading dataset from: {dataset_path}")
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_records = len(data)
    print(f"Loaded {total_records} records.")

    # 1. Integrity and Malformed Record Verification
    malformed_records = []
    missing_fields_counts = defaultdict(int)
    for idx, rec in enumerate(data):
        if not isinstance(rec, dict):
            malformed_records.append({"index": idx, "reason": "Not a JSON dictionary"})
            continue
        for field in ["id", "version", "specialty", "length", "note"]:
            if field not in rec or rec[field] is None or str(rec[field]).strip() == "":
                missing_fields_counts[field] += 1
                malformed_records.append({"index": idx, "reason": f"Missing/empty field: {field}"})

    # 2. Specialty & Length Distribution
    specialty_counter = Counter(r.get("specialty", "MISSING") for r in data)
    length_counter = Counter(r.get("length", "MISSING") for r in data)
    version_counter = Counter(r.get("version", "MISSING") for r in data)

    # 3. Diagnosis Distribution
    diagnoses = [extract_diagnosis(r.get("note", "")) for r in data]
    diagnosis_counter = Counter(diagnoses)

    # 4. Duplicate Analysis
    # Exact raw note duplicates
    raw_notes = [r.get("note", "") for r in data]
    unique_raw_notes = len(set(raw_notes))
    exact_raw_duplicates = total_records - unique_raw_notes

    # Clinical narrative bodies (excluding headers like UHID, Dates, Consultant)
    clinical_bodies = [extract_clinical_body(n) for n in raw_notes]
    unique_clinical_bodies = len(set(clinical_bodies))

    # Bodies with numbers masked
    bodies_no_nums = [re.sub(r'\d+', '<NUM>', b) for b in clinical_bodies]
    unique_bodies_no_nums = len(set(bodies_no_nums))

    # Bodies with numbers and Hinglish removed
    def strip_hinglish(text: str) -> str:
        for hp in HINGLISH_PHRASES:
            text = text.replace(hp, '')
        return re.sub(r'\s+', ' ', text).strip()

    bodies_core = [strip_hinglish(b) for b in bodies_no_nums]
    unique_bodies_core = len(set(bodies_core))

    # 5. Underlying Combinatorial Template Clusters
    record_cluster_map = []
    cluster_counts = Counter()
    unmatched_records = 0

    for idx, rec in enumerate(data):
        cid, slots = identify_template_cluster(rec.get("note", ""), rec.get("specialty", ""))
        if -1 in slots:
            unmatched_records += 1
        cluster_counts[cid] += 1
        record_cluster_map.append({
            "record_id": rec.get("id", idx + 1),
            "specialty": rec.get("specialty", ""),
            "cluster_id": cid,
            "diagnosis": diagnoses[idx],
            "slots": list(slots)
        })

    total_clusters = len(cluster_counts)
    clusters_per_specialty = defaultdict(int)
    for cid in cluster_counts:
        spec = cid.split("_S_")[0]
        clusters_per_specialty[spec] += 1

    manifest = {
        "dataset_metadata": {
            "source_file": os.path.abspath(dataset_path),
            "total_records": total_records,
            "version_distribution": dict(version_counter),
            "length_distribution": dict(length_counter),
            "data_nature": "Synthetic generated discharge summaries (Indian format) - NOT real patient data"
        },
        "integrity_metrics": {
            "malformed_records_count": len(malformed_records),
            "missing_fields": dict(missing_fields_counts),
            "unmatched_template_records": unmatched_records
        },
        "distributions": {
            "specialty_distribution": dict(specialty_counter),
            "diagnosis_distribution": dict(diagnosis_counter)
        },
        "duplicate_analysis": {
            "exact_raw_duplicates_count": exact_raw_duplicates,
            "unique_raw_notes_count": unique_raw_notes,
            "unique_clinical_bodies_exact": unique_clinical_bodies,
            "near_duplicates_clinical_bodies_count": total_records - unique_clinical_bodies,
            "unique_clinical_bodies_number_normalized": unique_bodies_no_nums,
            "unique_clinical_bodies_core_normalized": unique_bodies_core
        },
        "template_cluster_analysis": {
            "total_unique_template_clusters": total_clusters,
            "theoretical_max_clusters": 1152,
            "coverage_pct": round((total_clusters / 1152) * 100, 2),
            "clusters_by_specialty": dict(clusters_per_specialty),
            "records_per_cluster_mean": round(total_records / total_clusters, 2),
            "records_per_cluster_min": min(cluster_counts.values()) if cluster_counts else 0,
            "records_per_cluster_max": max(cluster_counts.values()) if cluster_counts else 0,
            "cluster_counts_sample_top10": dict(cluster_counts.most_common(10))
        }
    }

    # Save outputs if output_dir provided
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        manifest_path = os.path.join(output_dir, "dataset_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print(f"Saved dataset manifest to {manifest_path}")

        records_map_path = os.path.join(output_dir, "record_cluster_mapping.json")
        with open(records_map_path, "w", encoding="utf-8") as f:
            json.dump(record_cluster_map, f, indent=2)
        print(f"Saved record-cluster mapping to {records_map_path}")

    return manifest


if __name__ == "__main__":
    default_dataset = r"C:\Desktop\nlp project\Clinical Notes Based on Indian Format\synthetic_notes_medium_v2.json"
    default_out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    run_dataset_analysis(default_dataset, default_out_dir)
