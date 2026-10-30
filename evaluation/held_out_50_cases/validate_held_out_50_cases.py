"""
validate_held_out_50_cases.py - Independent 50-Case Held-Out Dataset Validator
ClinGap-NLP Evaluation Infrastructure

Validates:
1. Exact count of 50 records.
2. Complete schema conformity with CaseAnnotation.
3. Blank annotation layers (no pre-populated entities or model predictions).
4. Status is AWAITING_HUMAN_VERIFICATION.
5. Zero overlap with train/dev, validation, or the 10 pilot cases.
6. Perfectly balanced distribution across specialties and diagnoses.
"""

import os
import sys
import json
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVAL_DIR = os.path.join(BASE_DIR, "evaluation")
CASES_JSON = os.path.join(EVAL_DIR, "held_out_50_cases", "held_out_50_cases.json")

EXCLUDED_PILOT_IDS = {77, 64, 25, 16, 8, 15, 39, 6, 30, 22}


def validate():
    print(f"Validating: {CASES_JSON}")
    assert os.path.exists(CASES_JSON), f"File not found: {CASES_JSON}"

    with open(CASES_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("batch_id") == "HELD_OUT_TEST_50_CASES_V1"
    cases = data.get("cases", [])
    assert len(cases) == 50, f"Expected 50 cases, found {len(cases)}"

    # Load partition cluster files
    with open(os.path.join(EVAL_DIR, "train_dev_cluster_ids.json")) as f:
        train_dev_clusters = set(json.load(f))
    with open(os.path.join(EVAL_DIR, "validation_cluster_ids.json")) as f:
        val_clusters = set(json.load(f))
    with open(os.path.join(EVAL_DIR, "pilot_10_cases", "pilot_10_cases.json"), encoding="utf-8") as f:
        pilot_cases = json.load(f)["cases"]
    pilot_clusters = set(c["template_cluster_id"] for c in pilot_cases)

    rec_ids = set()
    cluster_ids = set()
    specs = Counter()
    diags = Counter()

    for idx, c in enumerate(cases):
        rid = c.get("record_id")
        cid = c.get("template_cluster_id")
        assert rid is not None, f"Case {idx+1} missing record_id"
        assert cid is not None, f"Case {idx+1} missing template_cluster_id"
        assert rid not in EXCLUDED_PILOT_IDS, f"Contaminated pilot ID {rid} found in case {idx+1}!"

        rec_ids.add(rid)
        cluster_ids.add(cid)
        specs[c.get("specialty")] += 1
        diags[c.get("diagnosis")] += 1

        # Check blank annotation fields
        assert c.get("entities") == [], f"Case {idx+1} has non-empty entities!"
        assert c.get("negations") == [], f"Case {idx+1} has non-empty negations!"
        assert c.get("investigations") == [], f"Case {idx+1} has non-empty investigations!"
        assert c.get("guidelines") == [], f"Case {idx+1} has non-empty guidelines!"
        assert c.get("decision_gaps") == [], f"Case {idx+1} has non-empty decision_gaps!"

        # Check status and provenance
        assert c.get("verification_status") == "AWAITING_HUMAN_VERIFICATION", f"Case {idx+1} status must be AWAITING_HUMAN_VERIFICATION!"
        assert c.get("annotator_id") is None, f"Case {idx+1} has pre-assigned annotator!"
        assert len(c.get("clinical_note", "")) > 50, f"Case {idx+1} clinical note is empty or too short!"

    # Assert cluster disjointness
    assert cluster_ids.isdisjoint(train_dev_clusters), "CRITICAL: Overlaps with train_dev clusters!"
    assert cluster_ids.isdisjoint(val_clusters), "CRITICAL: Overlaps with validation clusters!"
    assert cluster_ids.isdisjoint(pilot_clusters), "CRITICAL: Overlaps with pilot clusters!"
    assert len(cluster_ids) == 50, f"Expected 50 unique clusters, got {len(cluster_ids)}"

    # Assert distributions: exactly 10 per specialty, 5 per diagnosis
    assert len(specs) == 5, f"Expected 5 specialties, got {len(specs)}"
    for sp, cnt in specs.items():
        assert cnt == 10, f"Specialty '{sp}' has {cnt} records, expected 10"

    assert len(diags) == 10, f"Expected 10 diagnoses, got {len(diags)}"
    for dg, cnt in diags.items():
        assert cnt == 5, f"Diagnosis '{dg}' has {cnt} records, expected 5"

    print("SUCCESS: 50-case held-out dataset strictly validated!")
    print(f"  Total records: {len(rec_ids)}")
    print(f"  Unique clusters: {len(cluster_ids)}")
    print("  Cluster disjointness: 100% verified (0 overlap with train/dev, validation, or pilot)")
    print("  Annotation layers: 100% blank (clean for human review)")
    print("  Specialties: 5 (10 records each)")
    print("  Diagnoses: 10 (5 records each)")
    return True


if __name__ == "__main__":
    validate()
