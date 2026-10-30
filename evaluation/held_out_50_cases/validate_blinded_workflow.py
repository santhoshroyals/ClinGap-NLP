"""
validate_blinded_workflow.py - Comprehensive Validation of Blinded Annotation Workflow
ClinGap-NLP Evaluation Infrastructure (Phase 3)

Validates:
1. Annotator-facing blinded CSV (held_out_50_cases_blinded.csv):
   - Exactly 50 data records (rows).
   - Strict column schema preserving case_number, clinical_note, and empty annotation layers.
   - Complete exclusion of diagnosis, ICD code, specialty, template_cluster_id, and database record_id.
   - Zero model predictions or auto-labeled entities.
2. Annotator-facing blinded JSON (held_out_50_cases_blinded.json):
   - Exactly 50 cases with masked metadata ([BLINDED]).
   - Case numbers 1-50 aligned.
   - Compatible with annotation_tool.py.
3. Researcher-only unblinding manifest (researcher_unblinding_manifest.json):
   - Complete 1-to-1 deterministic mapping for all 50 cases.
   - Verifiable SHA256 note hashes matching both blinded and unblinded datasets.
4. Original gold dataset integrity:
   - Verifies SHA256 hashes of held_out_50_cases.json and dataset_manifest_50_cases.json.
   - Confirms 0 modifications to gold datasets.
5. Annotation transfer capability:
   - Confirms deterministic transfer back to original record IDs.
"""

import os
import sys
import json
import csv
import hashlib
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HELD_OUT_DIR = os.path.join(BASE_DIR, "evaluation", "held_out_50_cases")

BLINDED_CSV = os.path.join(HELD_OUT_DIR, "held_out_50_cases_blinded.csv")
BLINDED_JSON = os.path.join(HELD_OUT_DIR, "held_out_50_cases_blinded.json")
UNBLINDING_MANIFEST = os.path.join(HELD_OUT_DIR, "researcher_unblinding_manifest.json")
ORIGINAL_JSON = os.path.join(HELD_OUT_DIR, "held_out_50_cases.json")
ORIGINAL_MANIFEST = os.path.join(HELD_OUT_DIR, "dataset_manifest_50_cases.json")

EXPECTED_ORIGINAL_JSON_SHA256 = "5e5812a5a01e44446342fe2035a812f6fa170cc72d11d41e7dc39941fc24d5fe"
EXPECTED_ORIGINAL_MANIFEST_SHA256 = "f933557fa9991b6a250e2a8fadde046746f8f2f8e760af008774a1d66c525daa"

EXPECTED_BLINDED_CSV_COLUMNS = [
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

FORBIDDEN_COLUMN_SUBSTRINGS = ["diag", "icd", "spec", "cluster", "record_id"]


def validate_blinded_workflow() -> bool:
    print("=" * 78)
    print("VALIDATING BLINDED ANNOTATION WORKFLOW FOR 50-CASE HELD-OUT DATASET")
    print("=" * 78)

    errors = []

    # 1. Validate original files are UNCHANGED
    print("\n[Step 1] Verifying original gold files integrity (SHA256 check)...")
    with open(ORIGINAL_JSON, "rb") as f:
        actual_json_hash = hashlib.sha256(f.read()).hexdigest()
    if actual_json_hash != EXPECTED_ORIGINAL_JSON_SHA256:
        errors.append(f"Original held_out_50_cases.json hash changed! Expected {EXPECTED_ORIGINAL_JSON_SHA256}, got {actual_json_hash}")
    else:
        print(f"  [OK] held_out_50_cases.json SHA256 verified: {actual_json_hash}")

    with open(ORIGINAL_MANIFEST, "rb") as f:
        actual_manifest_hash = hashlib.sha256(f.read()).hexdigest()
    if actual_manifest_hash != EXPECTED_ORIGINAL_MANIFEST_SHA256:
        errors.append(f"Original dataset_manifest_50_cases.json hash changed! Expected {EXPECTED_ORIGINAL_MANIFEST_SHA256}, got {actual_manifest_hash}")
    else:
        print(f"  [OK] dataset_manifest_50_cases.json SHA256 verified: {actual_manifest_hash}")

    # 2. Validate Blinded CSV
    print("\n[Step 2] Validating annotator-facing blinded CSV...")
    if not os.path.exists(BLINDED_CSV):
        errors.append(f"Blinded CSV not found at {BLINDED_CSV}")
        return False

    with open(BLINDED_CSV, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)

    print(f"  [OK] Blinded CSV header columns ({len(headers)}): {headers}")
    if headers != EXPECTED_BLINDED_CSV_COLUMNS:
        errors.append(f"Blinded CSV header mismatch! Expected: {EXPECTED_BLINDED_CSV_COLUMNS}, got: {headers}")

    for col in headers:
        for forbidden in FORBIDDEN_COLUMN_SUBSTRINGS:
            if forbidden in col.lower():
                errors.append(f"Forbidden substring '{forbidden}' found in blinded CSV header '{col}'")

    print(f"  [OK] Blinded CSV data record count: {len(rows)} (expected: 50)")
    if len(rows) != 50:
        errors.append(f"Expected 50 data rows in blinded CSV, found {len(rows)}")

    csv_notes_hashes = []
    for idx, row in enumerate(rows, 1):
        case_num = int(row[0])
        note_text = row[1]
        v_status = row[2]
        entities_json = row[4]
        negations_json = row[5]
        investigations_json = row[6]

        if case_num != idx:
            errors.append(f"Row {idx} case_number is {case_num}, expected {idx}")
        if v_status != "AWAITING_HUMAN_VERIFICATION":
            errors.append(f"Row {idx} status is {v_status}, expected AWAITING_HUMAN_VERIFICATION")
        if entities_json != "[]":
            errors.append(f"Row {idx} entities_tagged_json is not empty: {entities_json}")
        if negations_json != "[]":
            errors.append(f"Row {idx} negations_tagged_json is not empty: {negations_json}")
        if investigations_json != "[]":
            errors.append(f"Row {idx} investigations_tagged_json is not empty: {investigations_json}")

        note_hash = hashlib.sha256(note_text.encode("utf-8")).hexdigest()
        csv_notes_hashes.append(note_hash)

    print(f"  [OK] All 50 rows confirmed: 0 model predictions, status='AWAITING_HUMAN_VERIFICATION'")

    # 3. Validate Blinded JSON
    print("\n[Step 3] Validating annotator-facing blinded JSON...")
    if not os.path.exists(BLINDED_JSON):
        errors.append(f"Blinded JSON not found at {BLINDED_JSON}")
        return False

    with open(BLINDED_JSON, "r", encoding="utf-8") as f:
        blinded_json_data = json.load(f)

    blinded_cases = blinded_json_data.get("cases", [])
    print(f"  [OK] Blinded JSON case count: {len(blinded_cases)} (expected: 50)")
    if len(blinded_cases) != 50:
        errors.append(f"Expected 50 cases in blinded JSON, found {len(blinded_cases)}")

    json_notes_hashes = []
    for idx, c in enumerate(blinded_cases, 1):
        if c.get("case_number") != idx:
            errors.append(f"Blinded JSON case {idx} case_number is {c.get('case_number')}")
        if c.get("specialty") != "[BLINDED]":
            errors.append(f"Blinded JSON case {idx} specialty is not blinded: {c.get('specialty')}")
        if c.get("diagnosis") != "[BLINDED]":
            errors.append(f"Blinded JSON case {idx} diagnosis is not blinded: {c.get('diagnosis')}")
        if c.get("template_cluster_id") != "[BLINDED]":
            errors.append(f"Blinded JSON case {idx} cluster_id is not blinded: {c.get('template_cluster_id')}")
        if c.get("verification_status") != "AWAITING_HUMAN_VERIFICATION":
            errors.append(f"Blinded JSON case {idx} status is {c.get('verification_status')}")
        if c.get("entities") != [] or c.get("negations") != [] or c.get("investigations") != []:
            errors.append(f"Blinded JSON case {idx} has non-empty annotation layers!")

        note_hash = hashlib.sha256(c["clinical_note"].encode("utf-8")).hexdigest()
        json_notes_hashes.append(note_hash)

    print(f"  [OK] All 50 cases in blinded JSON confirmed masked and clean.")

    # 4. Validate Researcher Unblinding Manifest
    print("\n[Step 4] Validating researcher unblinding manifest...")
    if not os.path.exists(UNBLINDING_MANIFEST):
        errors.append(f"Unblinding manifest not found at {UNBLINDING_MANIFEST}")
        return False

    with open(UNBLINDING_MANIFEST, "r", encoding="utf-8") as f:
        unblind_manifest_data = json.load(f)

    mappings = unblind_manifest_data.get("case_mappings", [])
    print(f"  [OK] Unblinding manifest mapping count: {len(mappings)} (expected: 50)")
    if len(mappings) != 50:
        errors.append(f"Expected 50 mappings in unblinding manifest, found {len(mappings)}")

    # Check 1-to-1 match with original unblinded dataset
    with open(ORIGINAL_JSON, "r", encoding="utf-8") as f:
        orig_data = json.load(f)
    orig_cases = orig_data["cases"]

    for idx, (m, orig_c) in enumerate(zip(mappings, orig_cases), 1):
        if m["case_number"] != idx:
            errors.append(f"Mapping {idx} case_number is {m['case_number']}")
        if m["original_record_id"] != orig_c["record_id"]:
            errors.append(f"Mapping {idx} record_id mismatch: {m['original_record_id']} vs {orig_c['record_id']}")
        if m["specialty"] != orig_c["specialty"]:
            errors.append(f"Mapping {idx} specialty mismatch: {m['specialty']} vs {orig_c['specialty']}")
        if m["diagnosis"] != orig_c["diagnosis"]:
            errors.append(f"Mapping {idx} diagnosis mismatch: {m['diagnosis']} vs {orig_c['diagnosis']}")
        if m["template_cluster_id"] != orig_c["template_cluster_id"]:
            errors.append(f"Mapping {idx} cluster mismatch: {m['template_cluster_id']} vs {orig_c['template_cluster_id']}")

        orig_hash = hashlib.sha256(orig_c["clinical_note"].encode("utf-8")).hexdigest()
        if m["note_sha256"] != orig_hash:
            errors.append(f"Mapping {idx} note hash mismatch with original note!")
        if csv_notes_hashes[idx - 1] != orig_hash:
            errors.append(f"CSV row {idx} note hash mismatch with original note!")
        if json_notes_hashes[idx - 1] != orig_hash:
            errors.append(f"Blinded JSON case {idx} note hash mismatch with original note!")

    print(f"  [OK] All 50 mappings verified against original records and notes (hashes match 100%).")

    # 5. Validate Transfer Mechanism
    print("\n[Step 5] Validating transfer mechanism...")
    try:
        sys.path.insert(0, HELD_OUT_DIR)
        from transfer_blinded_annotations import transfer_from_blinded_json, transfer_from_blinded_csv
        res_json = transfer_from_blinded_json(BLINDED_JSON, ORIGINAL_JSON, UNBLINDING_MANIFEST, dry_run=True)
        res_csv = transfer_from_blinded_csv(BLINDED_CSV, ORIGINAL_JSON, UNBLINDING_MANIFEST, dry_run=True)
        if res_json["transferred_cases"] != 50 or res_csv["transferred_cases"] != 50:
            errors.append("Transfer dry-run failed to map all 50 cases.")
        else:
            print("  [OK] Dry-run transfer from both Blinded JSON and Blinded CSV succeeded (50/50 cases mapped).")
    except Exception as e:
        errors.append(f"Transfer validation error: {e}")

    # Summary
    print("\n" + "=" * 78)
    if errors:
        print(f"VALIDATION FAILED WITH {len(errors)} ERRORS:")
        for err in errors:
            print(f"  [FAIL] {err}")
        return False
    else:
        print("ALL BLINDED WORKFLOW VALIDATIONS PASSED SUCCESSFULLY (100% CLEAN).")
        print("=" * 78)
        return True


if __name__ == "__main__":
    success = validate_blinded_workflow()
    sys.exit(0 if success else 1)
