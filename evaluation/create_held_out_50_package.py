"""
create_held_out_50_package.py - Independent 50-Case Held-Out Evaluation Dataset Generator
ClinGap-NLP Evaluation Infrastructure (Phase 3)

Generates:
- evaluation/held_out_50_cases/held_out_50_cases.json
- evaluation/held_out_50_cases/held_out_50_cases.csv
- evaluation/held_out_50_cases/dataset_manifest_50_cases.json
- evaluation/held_out_50_cases/validate_held_out_50_cases.py

Key Properties:
1. Deterministic selection with fixed random seed (seed=42).
2. Excludes all 10 contaminated pilot IDs (77, 64, 25, 16, 8, 15, 39, 6, 30, 22) and their clusters.
3. Strict cluster-disjoint partitioning: zero overlap with train/dev, validation, or pilot clusters.
4. Perfectly balanced across 5 specialties (10 cases each) and 10 diagnoses (5 cases each).
5. All 50 records drawn from 50 mutually distinct template clusters.
6. 100% blank ground-truth annotations (no model predictions or labels).
7. Status set to AWAITING_HUMAN_VERIFICATION (PENDING manual annotation).
"""

import os
import sys
import json
import csv
import random
from collections import defaultdict, Counter
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_DIR = os.path.join(BASE_DIR, "evaluation")
TARGET_DIR = os.path.join(EVAL_DIR, "held_out_50_cases")

SEED = 42

EXCLUDED_PILOT_IDS = [77, 64, 25, 16, 8, 15, 39, 6, 30, 22]


def build_held_out_50_package():
    os.makedirs(TARGET_DIR, exist_ok=True)

    # 1. Load source data
    raw_path = r"C:\Desktop\nlp project\Clinical Notes Based on Indian Format\synthetic_notes_medium_v2.json"
    with open(raw_path, "r", encoding="utf-8") as f:
        all_notes = {d["id"]: d for d in json.load(f)}

    with open(os.path.join(EVAL_DIR, "held_out_test_record_ids.json"), encoding="utf-8") as f:
        test_ids = set(json.load(f))

    with open(os.path.join(EVAL_DIR, "held_out_test_cluster_ids.json"), encoding="utf-8") as f:
        test_clusters = set(json.load(f))

    with open(os.path.join(EVAL_DIR, "train_dev_cluster_ids.json"), encoding="utf-8") as f:
        train_dev_clusters = set(json.load(f))

    with open(os.path.join(EVAL_DIR, "validation_cluster_ids.json"), encoding="utf-8") as f:
        val_clusters = set(json.load(f))

    with open(os.path.join(EVAL_DIR, "record_cluster_mapping.json"), encoding="utf-8") as f:
        records_meta = json.load(f)

    with open(os.path.join(EVAL_DIR, "pilot_10_cases", "pilot_10_cases.json"), encoding="utf-8") as f:
        pilot_cases = json.load(f)["cases"]

    pilot_id_set = set(EXCLUDED_PILOT_IDS)
    pilot_cluster_set = set(c["template_cluster_id"] for c in pilot_cases)

    # 2. Filter eligible records: must be in held_out_test, not in pilot IDs, not in pilot clusters
    clean_test_clusters = test_clusters - pilot_cluster_set
    eligible_records = [
        r for r in records_meta
        if r["cluster_id"] in clean_test_clusters
        and r["record_id"] not in pilot_id_set
        and r["record_id"] in test_ids
    ]

    print(f"Total held-out test records: {len(test_ids)}")
    print(f"Eligible records (excluding pilot IDs and pilot clusters): {len(eligible_records)}")
    print(f"Eligible clusters: {len(clean_test_clusters)}")

    # 3. Stratify by (specialty, diagnosis)
    strata = defaultdict(list)
    for r in eligible_records:
        key = (r["specialty"], r["diagnosis"])
        strata[key].append(r)

    # Deterministic sampling: 5 records from 5 distinct clusters per stratum
    rng = random.Random(SEED)
    selected_records = []
    selected_clusters = set()

    for (spec, diag), recs in sorted(strata.items()):
        cluster_to_recs = defaultdict(list)
        for r in recs:
            cluster_to_recs[r["cluster_id"]].append(r)

        avail_clusters = sorted(list(cluster_to_recs.keys()))
        rng.shuffle(avail_clusters)

        # Select 5 distinct clusters for this stratum
        chosen_clusters = avail_clusters[:5]
        for cid in chosen_clusters:
            recs_in_cluster = sorted(cluster_to_recs[cid], key=lambda x: x["record_id"])
            chosen_rec = rng.choice(recs_in_cluster)
            selected_records.append(chosen_rec)
            selected_clusters.add(cid)

    # Sort selected records deterministically by record_id
    selected_records.sort(key=lambda x: x["record_id"])
    assert len(selected_records) == 50, f"Expected 50 records, got {len(selected_records)}"
    assert len(selected_clusters) == 50, f"Expected 50 unique clusters, got {len(selected_clusters)}"

    # Leakage assertions
    assert selected_clusters.isdisjoint(train_dev_clusters), "Leakage error: selected clusters overlap with train_dev!"
    assert selected_clusters.isdisjoint(val_clusters), "Leakage error: selected clusters overlap with validation!"
    assert selected_clusters.isdisjoint(pilot_cluster_set), "Leakage error: selected clusters overlap with pilot clusters!"
    assert set(r["record_id"] for r in selected_records).isdisjoint(pilot_id_set), "Leakage error: pilot IDs included!"

    # 4. Construct JSON cases adhering strictly to annotation_schema.py
    cases = []
    for idx, r in enumerate(selected_records):
        rid = r["record_id"]
        raw_rec = all_notes[rid]
        case = {
            "record_id": rid,
            "specialty": raw_rec.get("specialty", r["specialty"]),
            "diagnosis": r["diagnosis"],
            "template_cluster_id": r["cluster_id"],
            "partition": "held_out_test",
            "clinical_note": raw_rec.get("note", ""),
            # Blank human-review layers (NO model predictions or auto-labels)
            "entities": [],
            "negations": [],
            "investigations": [],
            "guidelines": [],
            "decision_gaps": [],
            # Verification provenance
            "verification_status": "AWAITING_HUMAN_VERIFICATION",
            "annotator_id": None,
            "second_annotator_id": None,
            "annotation_timestamp": None,
            "reviewer_notes": None
        }
        cases.append(case)

    batch_payload = {
        "batch_id": "HELD_OUT_TEST_50_CASES_V1",
        "description": "50-case independent held-out evaluation dataset sampled from held-out test split for blinded researcher annotation.",
        "created_date": datetime.now().strftime("%Y-%m-%d"),
        "random_seed": SEED,
        "total_cases": len(cases),
        "cases": cases
    }

    # Save JSON dataset
    json_path = os.path.join(TARGET_DIR, "held_out_50_cases.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(batch_payload, f, indent=2)
    print(f"Saved JSON annotation dataset to: {json_path}")

    # 5. Save reviewable CSV template
    csv_path = os.path.join(TARGET_DIR, "held_out_50_cases.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "case_number",
            "record_id",
            "specialty",
            "diagnosis",
            "template_cluster_id",
            "partition",
            "verification_status",
            "clinical_note",
            "entities_tagged_json",
            "negations_tagged_json",
            "investigations_tagged_json",
            "guidelines_tagged_json",
            "decision_gaps_tagged_json",
            "reviewer_notes"
        ])
        for idx, c in enumerate(cases):
            writer.writerow([
                idx + 1,
                c["record_id"],
                c["specialty"],
                c["diagnosis"],
                c["template_cluster_id"],
                c["partition"],
                c["verification_status"],
                c["clinical_note"],
                "[]",
                "[]",
                "[]",
                "[]",
                "[]",
                ""
            ])
    print(f"Saved CSV annotation template to: {csv_path}")

    # 6. Save dataset manifest
    spec_dist = Counter(c["specialty"] for c in cases)
    diag_dist = Counter(c["diagnosis"] for c in cases)

    manifest = {
        "manifest_name": "HELD_OUT_TEST_50_CASES_MANIFEST",
        "batch_id": "HELD_OUT_TEST_50_CASES_V1",
        "creation_date": datetime.now().strftime("%Y-%m-%d"),
        "random_seed": SEED,
        "sample_size": len(cases),
        "selection_method": "stratified_cluster_disjoint_sampling",
        "source_partition": "held_out_test",
        "source_file": raw_path,
        "exclusions": {
            "excluded_pilot_record_ids": EXCLUDED_PILOT_IDS,
            "excluded_pilot_clusters_count": len(pilot_cluster_set),
            "excluded_pilot_clusters": sorted(list(pilot_cluster_set)),
            "excluded_train_dev_clusters_count": len(train_dev_clusters),
            "excluded_validation_clusters_count": len(val_clusters)
        },
        "verification_guarantees": {
            "cluster_disjoint_from_train_dev": True,
            "cluster_disjoint_from_validation": True,
            "cluster_disjoint_from_pilot_10_cases": True,
            "record_id_disjoint_from_pilot_10_cases": True,
            "within_sample_unique_clusters": len(selected_clusters),
            "model_predictions_included": False,
            "annotation_state": "AWAITING_HUMAN_VERIFICATION (PENDING)"
        },
        "selected_records": [
            {
                "case_number": idx + 1,
                "record_id": c["record_id"],
                "specialty": c["specialty"],
                "diagnosis": c["diagnosis"],
                "template_cluster_id": c["template_cluster_id"]
            }
            for idx, c in enumerate(cases)
        ],
        "distributions": {
            "specialty_distribution": dict(spec_dist),
            "diagnosis_distribution": dict(diag_dist)
        }
    }

    manifest_path = os.path.join(TARGET_DIR, "dataset_manifest_50_cases.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved manifest to: {manifest_path}")

    # 7. Create validation script
    val_script_path = os.path.join(TARGET_DIR, "validate_held_out_50_cases.py")
    val_script_content = '''"""
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
'''
    with open(val_script_path, "w", encoding="utf-8") as f:
        f.write(val_script_content)
    print(f"Saved validation script to: {val_script_path}")

    return {
        "json_path": json_path,
        "csv_path": csv_path,
        "manifest_path": manifest_path,
        "validation_script": val_script_path,
        "records_count": len(cases),
        "specialties": dict(spec_dist),
        "diagnoses": dict(diag_dist)
    }


if __name__ == "__main__":
    build_held_out_50_package()
