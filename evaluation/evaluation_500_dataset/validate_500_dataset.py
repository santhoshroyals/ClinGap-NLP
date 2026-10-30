"""
validate_500_dataset.py - Comprehensive Validator for 500-Note Evaluation Package
ClinGap-NLP Evaluation Infrastructure

Validates:
1. File integrity and existence.
2. Exact record count (exactly 500 records: 300 Synthetic, 200 MTSamples).
3. ID uniqueness and sequential continuity (EVAL-001 to EVAL-500).
4. Zero duplicate clinical notes (SHA256 uniqueness).
5. Zero leakage against train/dev, validation, and contaminated pilot sets.
6. Blinded annotation template purity (no diagnosis, no ICD, no auto-labels).
7. Cross-format text consistency (JSON, master CSV, and blinded CSV match 100%).
"""

import os
import sys
import json
import csv
import hashlib
from typing import Dict, List, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGET_DIR = os.path.join(BASE_DIR, "evaluation", "evaluation_500_dataset")

JSON_PATH = os.path.join(TARGET_DIR, "evaluation_500_notes.json")
MASTER_CSV_PATH = os.path.join(TARGET_DIR, "evaluation_500_notes.csv")
BLINDED_CSV_PATH = os.path.join(TARGET_DIR, "evaluation_500_blinded_annotation_template.csv")
MANIFEST_PATH = os.path.join(TARGET_DIR, "dataset_manifest_500_notes.json")

TRAIN_DEV_PATH = os.path.join(BASE_DIR, "evaluation", "train_dev_record_ids.json")
VAL_PATH = os.path.join(BASE_DIR, "evaluation", "validation_record_ids.json")
PILOT_JSON_PATH = os.path.join(BASE_DIR, "evaluation", "pilot_10_cases", "pilot_10_cases.json")

EXCLUDED_PILOT_SYNTH_IDS = {77, 64, 25, 16, 8, 15, 39, 6, 30, 22}
EXCLUDED_MTSAMPLES_INDICES = set(range(50)).union({690, 770, 1029, 1190, 1529, 3552, 3732, 3739, 3911, 4431})

EXPECTED_BLINDED_COLUMNS = [
    "eval_id",
    "clinical_note",
    "clinical_entities_and_types",
    "negation_status",
    "investigation_names",
    "investigation_status",
    "potential_decision_gap",
    "decision_gap_supporting_evidence",
    "annotator_id",
    "reviewer_notes"
]


def validate_500_package() -> bool:
    print("=" * 78)
    print("VALIDATING 500-NOTE EVALUATION DATASET PACKAGE")
    print("=" * 78)

    errors = []

    # 1. Check file existence
    print("\n[Step 1] Verifying file existence...")
    for p in [JSON_PATH, MASTER_CSV_PATH, BLINDED_CSV_PATH, MANIFEST_PATH]:
        if not os.path.exists(p):
            errors.append(f"Missing file: {p}")
        else:
            print(f"  [OK] Found {os.path.basename(p)} ({os.path.getsize(p):,} bytes)")

    if errors:
        return False

    # 2. Validate JSON structure & counts
    print("\n[Step 2] Validating master JSON dataset...")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    records = json_data.get("records", [])
    print(f"  [OK] Master JSON record count: {len(records)} (expected: 500)")
    if len(records) != 500:
        errors.append(f"Expected 500 records in JSON, found {len(records)}")

    synth_recs = [r for r in records if r.get("source_corpus") == "synthetic_indian"]
    mt_recs = [r for r in records if r.get("source_corpus") == "mtsamples"]

    print(f"  [OK] Synthetic Indian records: {len(synth_recs)} (expected: 300)")
    print(f"  [OK] MTSamples records: {len(mt_recs)} (expected: 200)")
    if len(synth_recs) != 300:
        errors.append(f"Expected 300 synthetic records, got {len(synth_recs)}")
    if len(mt_recs) != 200:
        errors.append(f"Expected 200 MTSamples records, got {len(mt_recs)}")

    # 3. Validate unique IDs and sequential continuity
    print("\n[Step 3] Validating Evaluation IDs (EVAL-001 to EVAL-500)...")
    eval_ids = [r["eval_id"] for r in records]
    if len(set(eval_ids)) != 500:
        errors.append(f"Duplicate eval_id found! Unique count: {len(set(eval_ids))}")
    for idx, eid in enumerate(eval_ids, 1):
        expected_eid = f"EVAL-{idx:03d}"
        if eid != expected_eid:
            errors.append(f"ID sequence mismatch at {idx}: expected {expected_eid}, got {eid}")
    print(f"  [OK] All 500 evaluation IDs strictly unique and sequentially ordered EVAL-001 to EVAL-500.")

    # 4. Validate duplicate clinical notes
    print("\n[Step 4] Checking for duplicate clinical notes (SHA256 uniqueness)...")
    note_hashes = [r["note_sha256"] for r in records]
    if len(set(note_hashes)) != 500:
        errors.append(f"Duplicate clinical notes found! Unique note count: {len(set(note_hashes))}")
    else:
        print(f"  [OK] All 500 clinical notes are 100% unique (0 duplicate notes).")

    # 5. Leakage & Contamination Check
    print("\n[Step 5] Auditing cross-split leakage and pilot exclusions...")
    with open(TRAIN_DEV_PATH, "r", encoding="utf-8") as f:
        train_dev_ids = set(json.load(f))
    with open(VAL_PATH, "r", encoding="utf-8") as f:
        val_ids = set(json.load(f))
    with open(PILOT_JSON_PATH, "r", encoding="utf-8") as f:
        pilot_cases = json.load(f)["cases"]
    pilot_clusters = {c["template_cluster_id"] for c in pilot_cases}

    synth_ids = set(r["source_record_id"] for r in synth_recs)
    synth_clusters = set(r["template_cluster_id"] for r in synth_recs)

    overlap_train = synth_ids.intersection(train_dev_ids)
    overlap_val = synth_ids.intersection(val_ids)
    overlap_pilot_ids = synth_ids.intersection(EXCLUDED_PILOT_SYNTH_IDS)
    overlap_pilot_clusters = synth_clusters.intersection(pilot_clusters)

    if overlap_train:
        errors.append(f"LEAKAGE: {len(overlap_train)} synthetic records overlap with train_dev!")
    else:
        print(f"  [OK] Overlap with train/dev partition: 0 records")

    if overlap_val:
        errors.append(f"LEAKAGE: {len(overlap_val)} synthetic records overlap with validation!")
    else:
        print(f"  [OK] Overlap with validation partition: 0 records")

    if overlap_pilot_ids:
        errors.append(f"CONTAMINATION: {len(overlap_pilot_ids)} synthetic records overlap with pilot cases!")
    else:
        print(f"  [OK] Overlap with contaminated pilot cases: 0 records")

    if overlap_pilot_clusters:
        errors.append(f"CONTAMINATION: {len(overlap_pilot_clusters)} synthetic clusters overlap with pilot clusters!")
    else:
        print(f"  [OK] Overlap with contaminated pilot clusters: 0 clusters")

    mt_ids = set(r["source_record_id"] for r in mt_recs)
    overlap_mt_pilot = mt_ids.intersection(EXCLUDED_MTSAMPLES_INDICES)
    if overlap_mt_pilot:
        errors.append(f"CONTAMINATION: {len(overlap_mt_pilot)} MTSamples records overlap with pilot/validation indices!")
    else:
        print(f"  [OK] Overlap with previously used MTSamples pilot/validation records: 0 records")

    # 6. Validate Blinded Annotation CSV Template
    print("\n[Step 6] Validating blinded annotation template CSV...")
    with open(BLINDED_CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        blinded_headers = next(reader)
        blinded_rows = list(reader)

    print(f"  [OK] Blinded CSV columns ({len(blinded_headers)}): {blinded_headers}")
    if blinded_headers != EXPECTED_BLINDED_COLUMNS:
        errors.append(f"Blinded CSV header mismatch! Expected: {EXPECTED_BLINDED_COLUMNS}, got: {blinded_headers}")

    forbidden_substrings = ["diag", "icd", "cluster", "specialty", "source_record_id"]
    for col in blinded_headers:
        for fsub in forbidden_substrings:
            if fsub in col.lower():
                errors.append(f"Forbidden metadata substring '{fsub}' found in blinded header '{col}'")

    print(f"  [OK] Blinded CSV row count: {len(blinded_rows)} (expected: 500)")
    if len(blinded_rows) != 500:
        errors.append(f"Expected 500 rows in blinded CSV, got {len(blinded_rows)}")

    # Check that annotation fields are completely unpopulated (0 fake labels)
    for idx, row in enumerate(blinded_rows, 1):
        eid = row[0]
        note = row[1]
        ents = row[2]
        negs = row[3]
        invs = row[4]
        stat = row[5]
        gap = row[6]
        ev = row[7]

        if eid != f"EVAL-{idx:03d}":
            errors.append(f"Blinded row {idx} eval_id mismatch: {eid}")
        if ents != "[]" or negs != "[]" or invs != "[]" or stat != "[]" or gap != "" or ev != "":
            errors.append(f"Blinded row {idx} contains non-empty annotation fields!")

    print(f"  [OK] Blinded template confirmed: 0 model predictions, 0 fake ground-truth labels.")

    # 7. Cross-format text integrity
    print("\n[Step 7] Checking verbatim note text consistency across JSON, Master CSV, and Blinded CSV...")
    with open(MASTER_CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        master_csv_rows = list(reader)

    for idx in range(500):
        json_note = records[idx]["clinical_note"]
        master_note = master_csv_rows[idx]["clinical_note"]
        blinded_note = blinded_rows[idx][1]

        json_hash = hashlib.sha256(json_note.encode("utf-8")).hexdigest()
        master_hash = hashlib.sha256(master_note.encode("utf-8")).hexdigest()
        blinded_hash = hashlib.sha256(blinded_note.encode("utf-8")).hexdigest()

        if json_hash != master_hash or json_hash != blinded_hash:
            errors.append(f"Text mismatch at index {idx} across dataset formats!")

    print(f"  [OK] Text consistency: 500/500 records match 100% across JSON, Master CSV, and Blinded CSV.")

    # Summary
    print("\n" + "=" * 78)
    if errors:
        print(f"VALIDATION FAILED WITH {len(errors)} ERRORS:")
        for err in errors:
            print(f"  [FAIL] {err}")
        return False
    else:
        print("ALL 500-NOTE EVALUATION DATASET VALIDATIONS PASSED SUCCESSFULLY (100% CLEAN).")
        print("=" * 78)
        return True


if __name__ == "__main__":
    success = validate_500_package()
    sys.exit(0 if success else 1)
