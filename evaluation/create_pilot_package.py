"""
create_pilot_package.py - Generates a 10-Record Pilot Annotation Package
ClinGap-NLP Evaluation Infrastructure (Phase 3)

Selects 10 representative records (2 per specialty: 1 per diagnosis)
from the held-out test split.
Outputs:
- evaluation/pilot_10_cases/pilot_10_cases.json
- evaluation/pilot_10_cases/pilot_10_cases.csv
- evaluation/pilot_10_cases/validate_pilot_annotations.py
"""

import os
import sys
import json
import csv
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_DIR = os.path.join(BASE_DIR, "evaluation")
PILOT_DIR = os.path.join(EVAL_DIR, "pilot_10_cases")

def create_pilot_package():
    os.makedirs(PILOT_DIR, exist_ok=True)

    # 1. Load held-out test IDs and metadata
    raw_path = r"C:\Desktop\nlp project\Clinical Notes Based on Indian Format\synthetic_notes_medium_v2.json"
    with open(raw_path, "r", encoding="utf-8") as f:
        all_notes = {d["id"]: d for d in json.load(f)}

    with open(os.path.join(EVAL_DIR, "held_out_test_record_ids.json")) as f:
        test_ids = set(json.load(f))

    with open(os.path.join(EVAL_DIR, "record_cluster_mapping.json")) as f:
        records_meta = [r for r in json.load(f) if r["record_id"] in test_ids]

    # Group by (specialty, diagnosis)
    strata = defaultdict(list)
    for r in records_meta:
        key = (r["specialty"], r["diagnosis"])
        strata[key].append(r["record_id"])

    # Pick exactly 1 record per (specialty, diagnosis) -> exactly 10 records
    pilot_ids = []
    for key in sorted(strata.keys()):
        # deterministic choice: smallest record_id in stratum
        chosen_id = sorted(strata[key])[0]
        pilot_ids.append(chosen_id)

    print(f"Selected {len(pilot_ids)} pilot record IDs: {pilot_ids}")

    pilot_cases = []
    for rid in pilot_ids:
        raw_rec = all_notes[rid]
        meta = [r for r in records_meta if r["record_id"] == rid][0]
        case = {
            "record_id": rid,
            "specialty": raw_rec.get("specialty", ""),
            "diagnosis": meta.get("diagnosis", ""),
            "template_cluster_id": meta.get("cluster_id", ""),
            "partition": "held_out_test",
            "clinical_note": raw_rec.get("note", ""),
            # Blank fields for human reviewer
            "entities": [],
            "negations": [],
            "investigations": [],
            "guidelines": [],
            "decision_gaps": [],
            "verification_status": "AWAITING_HUMAN_VERIFICATION",
            "annotator_id": None,
            "annotation_timestamp": None,
            "reviewer_notes": None
        }
        pilot_cases.append(case)

    pilot_batch = {
        "batch_id": "PILOT_10_HELD_OUT_CASES_V1",
        "description": "10-case pilot annotation package (2 per specialty, 1 per diagnosis) for annotator calibration.",
        "created_date": "2026-10-30",
        "total_cases": len(pilot_cases),
        "cases": pilot_cases
    }

    # Save JSON
    json_path = os.path.join(PILOT_DIR, "pilot_10_cases.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(pilot_batch, f, indent=2)
    print(f"Saved pilot JSON to {json_path}")

    # Save human-friendly CSV with clean tabular format
    csv_path = os.path.join(PILOT_DIR, "pilot_10_cases.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "record_id",
            "specialty",
            "diagnosis",
            "verification_status",
            "annotator_id",
            "clinical_note",
            "entities_tagged_json",
            "negations_scoped_json",
            "investigation_status_json",
            "guideline_activation_json",
            "decision_gaps_json",
            "reviewer_notes"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in pilot_cases:
            writer.writerow({
                "record_id": c["record_id"],
                "specialty": c["specialty"],
                "diagnosis": c["diagnosis"],
                "verification_status": c["verification_status"],
                "annotator_id": "",
                "clinical_note": c["clinical_note"],
                "entities_tagged_json": "[]",
                "negations_scoped_json": "[]",
                "investigation_status_json": "[]",
                "guideline_activation_json": "[]",
                "decision_gaps_json": "[]",
                "reviewer_notes": ""
            })
    print(f"Saved pilot CSV to {csv_path}")

    # Create validation script in pilot folder
    val_script_path = os.path.join(PILOT_DIR, "validate_pilot_annotations.py")
    with open(val_script_path, "w", encoding="utf-8") as f:
        f.write('''"""
validate_pilot_annotations.py - Validates completed pilot annotations against schema
"""
import sys, os, json
from pydantic import ValidationError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
from evaluation.annotation_schema import CaseAnnotation

def validate_file(file_path):
    print(f"Validating annotations in: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cases = data.get("cases", data if isinstance(data, list) else [])
    
    errors = 0
    for idx, c in enumerate(cases):
        try:
            # Check character span bounds
            note = c.get("clinical_note", "")
            for e in c.get("entities", []):
                start, end = e.get("start_char", 0), e.get("end_char", 0)
                if start < 0 or end > len(note) or start >= end:
                    print(f"  [ERROR] Case {c.get('record_id')}: Invalid span [{start}:{end}] for text '{e.get('entity_text')}'")
                    errors += 1
                elif note[start:end] != e.get("entity_text"):
                    print(f"  [WARNING] Case {c.get('record_id')}: Text mismatch at [{start}:{end}]. Note has '{note[start:end]}', entity specifies '{e.get('entity_text')}'")
            CaseAnnotation(**c)
        except ValidationError as ve:
            print(f"  [ERROR] Case {c.get('record_id')} schema validation failure:\n{ve}")
            errors += 1
            
    if errors == 0:
        print(f"SUCCESS: All {len(cases)} cases strictly conform to the evaluation schema!")
    else:
        print(f"FAILED: Found {errors} validation errors.")
    return errors == 0

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "pilot_10_cases.json")
    validate_file(target)
''')
    print(f"Saved validation script to {val_script_path}")

if __name__ == "__main__":
    create_pilot_package()
