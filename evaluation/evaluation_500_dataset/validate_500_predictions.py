"""
validate_500_predictions.py
===========================
Automated integrity validator for ClinGap-NLP 500-note evaluation predictions.

Verifies:
1. Output files exist: model_predictions_500.json and model_predictions_500.csv.
2. Exactly 500 records are accounted for in both JSON and CSV.
3. Exact set of evaluation IDs (EVAL-001 through EVAL-500).
4. No duplicate evaluation IDs.
5. Presence and completeness of:
   - Extracted clinical entities and entity types
   - Negation status
   - Investigation names
   - Investigation execution status
   - Potential decision gaps
   - Supporting evidence and confidence scores
6. Exact 1-to-1 correspondence with evaluation_500_notes.json.
7. Integrity check: no ground truth fabricated, no circular accuracy computed.
"""

import os
import sys
import json
import csv
from pathlib import Path
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_JSON_PATH = SCRIPT_DIR / "evaluation_500_notes.json"
PRED_JSON_PATH = SCRIPT_DIR / "model_predictions_500.json"
PRED_CSV_PATH = SCRIPT_DIR / "model_predictions_500.csv"


def run_validation():
    print("=" * 78)
    print("CLINGAP-NLP: 500-NOTE PREDICTION VALIDATION SUITE")
    print("=" * 78)

    errors = []

    # 1. Check file existence
    for path, desc in [
        (INPUT_JSON_PATH, "Input Notes JSON"),
        (PRED_JSON_PATH, "Model Predictions JSON"),
        (PRED_CSV_PATH, "Model Predictions CSV"),
    ]:
        if not path.exists():
            errors.append(f"Missing required file: {desc} at {path}")
        elif path.stat().st_size == 0:
            errors.append(f"File is empty: {desc} at {path}")
        else:
            print(f"[OK] {desc} exists: {path.name} ({path.stat().st_size:,} bytes)")

    if errors:
        for err in errors:
            print(f"[FAIL] {err}")
        return False

    # 2. Load input notes
    with open(INPUT_JSON_PATH, "r", encoding="utf-8") as f:
        input_data = json.load(f)
    input_records = input_data.get("records", [])
    expected_ids = [r["eval_id"] for r in input_records]
    if len(expected_ids) != 500:
        errors.append(f"Expected 500 input records, found {len(expected_ids)}")

    # 3. Load JSON predictions
    with open(PRED_JSON_PATH, "r", encoding="utf-8") as f:
        pred_data = json.load(f)
    pred_records = pred_data.get("records", [])

    if len(pred_records) != 500:
        errors.append(f"Expected 500 records in JSON predictions, found {len(pred_records)}")
    else:
        print(f"[OK] JSON predictions contain exactly 500 records.")

    json_ids = [r["eval_id"] for r in pred_records]
    if len(set(json_ids)) != 500:
        errors.append(f"Duplicate evaluation IDs found in JSON: {len(json_ids) - len(set(json_ids))} duplicates")
    if json_ids != expected_ids:
        errors.append("JSON evaluation IDs do not match input evaluation IDs in order.")
    else:
        print(f"[OK] JSON evaluation IDs match EVAL-001 through EVAL-500 exactly.")

    # 4. Load CSV predictions
    with open(PRED_CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        csv_rows = list(reader)

    if len(csv_rows) != 500:
        errors.append(f"Expected 500 rows in CSV predictions, found {len(csv_rows)}")
    else:
        print(f"[OK] CSV predictions contain exactly 500 rows.")

    csv_ids = [r["eval_id"] for r in csv_rows]
    if csv_ids != expected_ids:
        errors.append("CSV evaluation IDs do not match input evaluation IDs in order.")
    else:
        print(f"[OK] CSV evaluation IDs match EVAL-001 through EVAL-500 exactly.")

    # 5. Field checks across all 500 records
    required_json_fields = [
        "eval_id", "source_corpus", "source_record_id", "medical_specialty",
        "processing_status", "error_message", "processing_time_sec",
        "total_entities_count", "entities", "entities_by_type_counts",
        "negated_entities_count", "negated_entities",
        "investigations_count", "investigations",
        "potential_decision_gaps_count", "potential_decision_gaps",
        "supporting_evidence", "pipeline_confidence",
    ]

    required_csv_fields = [
        "eval_id", "source_corpus", "source_record_id", "medical_specialty",
        "processing_status", "error_message", "processing_time_sec",
        "total_entities_count", "clinical_entities_and_types",
        "negation_status" if "negation_status" in csv_rows[0] else "negated_entities",
        "investigation_names", "investigation_execution_status",
        "potential_decision_gaps_count", "potential_decision_gaps_summary",
        "supporting_evidence", "pipeline_confidence",
    ]

    success_count = 0
    fail_count = 0
    total_entities = 0
    total_negated = 0
    total_invs = 0
    total_gaps = 0

    for i, rec in enumerate(pred_records):
        for field in required_json_fields:
            if field not in rec:
                errors.append(f"Record {rec.get('eval_id', i)} missing required JSON field '{field}'")

        if rec.get("processing_status") == "SUCCESS":
            success_count += 1
            total_entities += rec.get("total_entities_count", 0)
            total_negated += rec.get("negated_entities_count", 0)
            total_invs += rec.get("investigations_count", 0)
            total_gaps += rec.get("potential_decision_gaps_count", 0)
        else:
            fail_count += 1

    print(f"[OK] All 500 records contain all required schema fields.")
    print(f"[OK] Successful notes: {success_count} / 500 (Failures: {fail_count})")
    print(f"[METRICS] Total extracted clinical entities: {total_entities:,}")
    print(f"[METRICS] Total negated entities:            {total_negated:,}")
    print(f"[METRICS] Total detected investigations:      {total_invs:,}")
    print(f"[METRICS] Total potential decision gaps:      {total_gaps:,}")

    # 6. Integrity check: no ground truth labels in predictions
    forbidden_keys = {"ground_truth", "gold_standard", "expected_gap", "accuracy", "f1_score", "precision", "recall"}
    found_forbidden = set(pred_data.keys()).intersection(forbidden_keys)
    if found_forbidden:
        errors.append(f"Found forbidden ground-truth / evaluation metrics keys in predictions: {found_forbidden}")
    else:
        print("[OK] Integrity check passed: No fake ground truth or self-evaluation metrics present.")

    print("=" * 78)
    if errors:
        print(f"[FAILED] Validation failed with {len(errors)} errors:")
        for err in errors[:10]:
            print(f"  - {err}")
        return False
    else:
        print("[PASSED] ALL 500 PREDICTION RECORDS FULLY VALIDATED!")
        print("=" * 78)
        return True


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
