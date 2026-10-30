"""
generate_blinded_package.py - Generate Blinded Annotation Workflow Package
ClinGap-NLP Evaluation Infrastructure (Phase 3)

Generates:
1. evaluation/held_out_50_cases/held_out_50_cases_blinded.csv
   - Blinded CSV for external/independent annotator.
   - Hides: diagnosis, ICD code, specialty, template_cluster_id, database record_id.
   - Preserves: case_number, clinical_note, and empty annotation columns.
2. evaluation/held_out_50_cases/held_out_50_cases_blinded.json
   - Blinded JSON for use with annotation_tool.py.
   - Masks: specialty, diagnosis, cluster_id, record_id.
   - Fully compatible with CLI tool (cases 1-50).
3. evaluation/held_out_50_cases/researcher_unblinding_manifest.json
   - Researcher-only confidential unblinding key.
   - Maps case_number (1-50) <-> original record_id, specialty, diagnosis, cluster_id.
   - Includes verbatim clinical note SHA256 hashes to guarantee data integrity.

Strict Constraints:
- Leaves held_out_50_cases.json and dataset_manifest_50_cases.json 100% UNCHANGED.
- Zero model predictions or auto-labeled entities.
"""

import os
import re
import json
import csv
import hashlib
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HELD_OUT_DIR = os.path.join(BASE_DIR, "evaluation", "held_out_50_cases")

JSON_50_PATH = os.path.join(HELD_OUT_DIR, "held_out_50_cases.json")
MANIFEST_50_PATH = os.path.join(HELD_OUT_DIR, "dataset_manifest_50_cases.json")

BLINDED_CSV_PATH = os.path.join(HELD_OUT_DIR, "held_out_50_cases_blinded.csv")
BLINDED_JSON_PATH = os.path.join(HELD_OUT_DIR, "held_out_50_cases_blinded.json")
UNBLINDING_MANIFEST_PATH = os.path.join(HELD_OUT_DIR, "researcher_unblinding_manifest.json")


def extract_icd_code(diagnosis_str: str) -> str:
    match = re.search(r"ICD:\s*([^)]+)", diagnosis_str)
    if match:
        return match.group(1).strip()
    return "UNKNOWN"


def generate_blinded_package():
    print(f"Reading unblinded 50-case dataset from: {JSON_50_PATH}")
    with open(JSON_50_PATH, "r", encoding="utf-8") as f:
        unblinded_data = json.load(f)

    with open(MANIFEST_50_PATH, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    cases = unblinded_data.get("cases", [])
    assert len(cases) == 50, f"Expected 50 cases, found {len(cases)}"

    # 1. Create Blinded CSV
    # Headers hide diagnosis, ICD code, specialty, template cluster ID, and raw record ID.
    csv_headers = [
        "case_number",
        "clinical_note",
        "verification_status",
        "annotator_id",
        "entities_tagged_json",
        "negations_tagged_json",
        "investigations_tagged_json",
        "guidelines_tagged_json",
        "decision_gaps_tagged_json",
        "reviewer_notes"
    ]

    with open(BLINDED_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)
        for idx, c in enumerate(cases):
            case_num = idx + 1
            writer.writerow([
                case_num,
                c["clinical_note"],
                c["verification_status"],
                "",  # annotator_id
                "[]",
                "[]",
                "[]",
                "[]",
                "[]",
                ""   # reviewer_notes
            ])
    print(f"Created Blinded CSV at: {BLINDED_CSV_PATH}")

    # 2. Create Blinded JSON (for annotation_tool.py)
    blinded_cases = []
    for idx, c in enumerate(cases):
        case_num = idx + 1
        blinded_case = {
            "case_number": case_num,
            "record_id": f"BLINDED_CASE_{case_num:02d}",
            "specialty": "[BLINDED]",
            "diagnosis": "[BLINDED]",
            "template_cluster_id": "[BLINDED]",
            "partition": "held_out_test",
            "clinical_note": c["clinical_note"],
            "entities": [],
            "negations": [],
            "investigations": [],
            "guidelines": [],
            "decision_gaps": [],
            "verification_status": "AWAITING_HUMAN_VERIFICATION",
            "annotator_id": None,
            "second_annotator_id": None,
            "annotation_timestamp": None,
            "reviewer_notes": None
        }
        blinded_cases.append(blinded_case)

    blinded_json_payload = {
        "batch_id": "HELD_OUT_TEST_50_CASES_BLINDED_V1",
        "description": "Blinded 50-case independent held-out evaluation dataset for manual researcher annotation. Diagnosis, specialty, record ID, and cluster IDs are masked.",
        "created_date": unblinded_data.get("created_date", "2026-10-31"),
        "random_seed": unblinded_data.get("random_seed", 42),
        "is_blinded": True,
        "total_cases": len(blinded_cases),
        "cases": blinded_cases
    }

    with open(BLINDED_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(blinded_json_payload, f, indent=2)
    print(f"Created Blinded JSON at: {BLINDED_JSON_PATH}")

    # 3. Create Researcher-Only Unblinding Manifest
    case_mappings = []
    for idx, c in enumerate(cases):
        case_num = idx + 1
        note_text = c["clinical_note"]
        note_hash = hashlib.sha256(note_text.encode("utf-8")).hexdigest()
        icd_code = extract_icd_code(c["diagnosis"])

        mapping_entry = {
            "case_number": case_num,
            "blinded_case_id": f"CASE_{case_num:02d}",
            "original_record_id": c["record_id"],
            "specialty": c["specialty"],
            "diagnosis": c["diagnosis"],
            "icd_code": icd_code,
            "template_cluster_id": c["template_cluster_id"],
            "note_char_length": len(note_text),
            "note_sha256": note_hash
        }
        case_mappings.append(mapping_entry)

    unblinding_manifest = {
        "manifest_name": "RESEARCHER_UNBLINDING_MANIFEST_50_CASES",
        "batch_id": "HELD_OUT_TEST_50_CASES_V1",
        "blinded_batch_id": "HELD_OUT_TEST_50_CASES_BLINDED_V1",
        "confidentiality_notice": (
            "RESTRICTED TO RESEARCH LEAD - CONFIDENTIAL. "
            "Contains unblinded mapping between annotator-facing case IDs and database record IDs/diagnoses. "
            "Do NOT distribute to annotators prior to finalization of manual annotations."
        ),
        "creation_date": "2026-10-31",
        "random_seed": unblinded_data.get("random_seed", 42),
        "total_cases": len(case_mappings),
        "source_files": {
            "original_cases_json": "held_out_50_cases.json",
            "dataset_manifest_json": "dataset_manifest_50_cases.json",
            "blinded_csv": "held_out_50_cases_blinded.csv",
            "blinded_json": "held_out_50_cases_blinded.json"
        },
        "case_mappings": case_mappings
    }

    with open(UNBLINDING_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(unblinding_manifest, f, indent=2)
    print(f"Created Researcher Unblinding Manifest at: {UNBLINDING_MANIFEST_PATH}")


if __name__ == "__main__":
    generate_blinded_package()
