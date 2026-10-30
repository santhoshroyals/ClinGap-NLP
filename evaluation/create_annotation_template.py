"""
create_annotation_template.py - Human-Review Annotation Template Generator
ClinGap-NLP Evaluation Infrastructure (Phase 3)

Key Features:
- Stratified sampling from held-out test split (seed 42).
- Samples balanced cases across all 5 medical specialties and 10 clinical diagnoses.
- Exports structured JSON and reviewable CSV templates.
- Enforces strict blank ground-truth fields (NO auto-population from pipeline).
- Explicitly flags verification_status as "AWAITING_HUMAN_VERIFICATION".
- Produces ANNOTATION_GUIDELINES.md for clinical reviewers.
"""

import os
import sys
import json
import csv
import random
from collections import defaultdict
from typing import List, Dict, Any


def generate_annotation_template(
    dataset_path: str,
    test_ids_path: str,
    cluster_mapping_path: str,
    output_dir: str,
    sample_size: int = 50,
    seed: int = 42
) -> str:
    """
    Samples representative records from the held-out test split and generates blank annotation templates.
    """
    # 1. Load data
    with open(dataset_path, "r", encoding="utf-8") as f:
        all_notes = {d["id"]: d for d in json.load(f)}

    with open(test_ids_path, "r", encoding="utf-8") as f:
        test_ids = json.load(f)

    with open(cluster_mapping_path, "r", encoding="utf-8") as f:
        cluster_map = {r["record_id"]: r for r in json.load(f)}

    print(f"Loaded {len(test_ids)} held-out test IDs.")

    # 2. Stratify test IDs by (specialty, diagnosis)
    strata = defaultdict(list)
    for rid in test_ids:
        meta = cluster_map.get(rid)
        if meta:
            key = (meta["specialty"], meta["diagnosis"])
            strata[key].append(rid)

    rng = random.Random(seed)
    sampled_ids = []
    cases_per_stratum = max(1, sample_size // len(strata))

    for key, rids in sorted(strata.items()):
        rids_sorted = sorted(rids)
        rng.shuffle(rids_sorted)
        chosen = rids_sorted[:cases_per_stratum]
        sampled_ids.extend(chosen)

    # If rounding left a deficit, fill from remaining test IDs
    if len(sampled_ids) < sample_size:
        remaining = [rid for rid in sorted(test_ids) if rid not in set(sampled_ids)]
        rng.shuffle(remaining)
        sampled_ids.extend(remaining[:sample_size - len(sampled_ids)])

    sampled_ids.sort()
    print(f"Sampled {len(sampled_ids)} balanced records from held-out test partition.")

    # 3. Assemble blank annotation records
    cases = []
    for rid in sampled_ids:
        raw_rec = all_notes[rid]
        meta = cluster_map[rid]
        case = {
            "record_id": rid,
            "specialty": raw_rec.get("specialty", ""),
            "template_cluster_id": meta.get("cluster_id", ""),
            "partition": "held_out_test",
            "clinical_note": raw_rec.get("note", ""),
            # Layer 1: Text-extraction annotations (BLANK - FOR HUMAN REVIEW)
            "entities": [],
            "negations": [],
            "investigations": [],
            # Layer 2: Clinical guideline and gap judgments (BLANK - FOR HUMAN REVIEW)
            "guidelines": [],
            "decision_gaps": [],
            # Provenance
            "verification_status": "AWAITING_HUMAN_VERIFICATION",
            "annotator_id": None,
            "annotation_timestamp": None,
            "reviewer_notes": None
        }
        cases.append(case)

    batch_payload = {
        "batch_id": "BATCH_HELD_OUT_TEST_50_V1",
        "description": "Representative stratified sample of 50 held-out test notes for independent human expert annotation.",
        "created_date": "2026-10-30",
        "total_cases": len(cases),
        "sampling_method": "Stratified random sample from held-out cluster-disjoint split (seed=42)",
        "provenance_policy": "NO automated predictions populated. All ground truth requires independent domain verification.",
        "cases": cases
    }

    # 4. Save JSON template
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "annotation_template_sample.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(batch_payload, f, indent=2)
    print(f"Saved annotation template JSON to {json_path}")

    # 5. Save CSV template for spreadsheet-based human review
    csv_path = os.path.join(output_dir, "annotation_template_sample.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "record_id",
            "specialty",
            "template_cluster_id",
            "verification_status",
            "annotator_id",
            "clinical_note",
            "entities_json_review",
            "negations_json_review",
            "investigations_status_review",
            "guideline_activation_review",
            "decision_gaps_review",
            "reviewer_notes"
        ])
        for c in cases:
            writer.writerow([
                c["record_id"],
                c["specialty"],
                c["template_cluster_id"],
                c["verification_status"],
                c["annotator_id"] or "",
                c["clinical_note"],
                "[]",  # Blank entities list
                "[]",  # Blank negations list
                "[]",  # Blank investigations list
                "[]",  # Blank guidelines list
                "[]",  # Blank gaps list
                ""     # Blank notes
            ])
    print(f"Saved annotation template CSV to {csv_path}")

    # 6. Generate ANNOTATION_GUIDELINES.md
    guidelines_path = os.path.join(output_dir, "ANNOTATION_GUIDELINES.md")
    with open(guidelines_path, "w", encoding="utf-8") as f:
        f.write("# ClinGap-NLP: Human Annotation Guidelines & Protocol\n\n")
        f.write("**Target Batch:** `BATCH_HELD_OUT_TEST_50_V1` (50 Held-Out Stratified Cases)\n")
        f.write("**Status:** Reference Annotation Instructions (Academic Protocol)\n\n")
        f.write("## 1. Ethical & Academic Principles\n")
        f.write("1. **Zero System Contamination:** ClinGap-NLP model outputs must never be presented to the annotator during labeling to avoid anchoring bias.\n")
        f.write("2. **Separation of Layers:** Text-extraction spans (what is written) must be labeled separately from clinical care quality judgments (what ought to have been done).\n\n")
        f.write("## 2. Layer 1: Text-Extraction Annotation Rules\n\n")
        f.write("### 2.1 Clinical Entity Spans\n")
        f.write("- **Entity Types:** `DISEASE`, `SYMPTOM`, `MEDICATION`, `INVESTIGATION`, `DOSAGE`, `FREQUENCY`, `LAB_TEST`.\n")
        f.write("- Tag exact word spans with start and end character offsets.\n")
        f.write("- Administrative headers (UHID, Hospital Name, Doctor Signature) must NOT be tagged as clinical entities.\n\n")
        f.write("### 2.2 Negation Scoping\n")
        f.write("- Mark `is_negated: True` if the patient denies the symptom or the finding is explicitly stated as absent (e.g., 'no fever', 'denies chest pain', 'cyanosis: -').\n")
        f.write("- Record the negation cue word ('no', 'denies', 'without', '-').\n\n")
        f.write("### 2.3 Investigation Clinical Status\n")
        f.write("- `completed/performed`: Results or findings are explicitly documented.\n")
        f.write("- `ordered`: Test was requisitioned/sent, but results are not yet available.\n")
        f.write("- `pending`: Explicitly awaiting lab report/imaging review.\n")
        f.write("- `not performed/cancelled`: Explicitly declined, omitted, refused, or cancelled.\n")
        f.write("- `undocumented`: Not mentioned anywhere in the clinical encounter.\n\n")
        f.write("## 3. Layer 2: Clinical Guideline & Decision Gap Rules\n\n")
        f.write("### 3.1 Guideline Applicability\n")
        f.write("- Only activate guidelines whose prerequisite clinical indications are medically affirmed.\n")
        f.write("- Do not trigger diabetes guidelines on non-diabetic conditions.\n\n")
        f.write("### 3.2 Decision Gap Flagging\n")
        f.write("- Flag a gap ONLY if a medically necessary diagnostic test or therapy is omitted without clinical justification.\n")
        f.write("- A test that is already ordered or completed is NOT a missing gap.\n\n")
        f.write("## 4. Submission & Quality Control\n")
        f.write("Set `verification_status: EXPERT_VERIFIED` only after full review by an independent clinician or clinical informatics domain specialist.\n")

    print(f"Generated annotation guidelines at {guidelines_path}")
    return json_path


if __name__ == "__main__":
    eval_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_file = r"C:\Desktop\nlp project\Clinical Notes Based on Indian Format\synthetic_notes_medium_v2.json"
    test_ids_file = os.path.join(eval_dir, "held_out_test_record_ids.json")
    cluster_file = os.path.join(eval_dir, "record_cluster_mapping.json")

    generate_annotation_template(
        dataset_path=dataset_file,
        test_ids_path=test_ids_file,
        cluster_mapping_path=cluster_file,
        output_dir=eval_dir,
        sample_size=50,
        seed=42
    )
