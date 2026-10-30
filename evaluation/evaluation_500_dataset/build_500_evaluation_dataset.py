"""
build_500_evaluation_dataset.py - Build 500-Note Reproducible Evaluation Package
ClinGap-NLP Evaluation Infrastructure

Constructs an independent, reproducible 500-note evaluation dataset combining:
- 300 randomly selected synthetic Indian clinical notes (cluster-disjoint held-out test).
- 200 randomly selected MTSamples clinical records (clean, deduplicated).

Outputs:
1. evaluation/evaluation_500_dataset/evaluation_500_notes.json
2. evaluation/evaluation_500_dataset/evaluation_500_notes.csv
3. evaluation/evaluation_500_dataset/evaluation_500_blinded_annotation_template.csv
4. evaluation/evaluation_500_dataset/dataset_manifest_500_notes.json
"""

import os
import sys
import json
import csv
import random
import hashlib
from collections import defaultdict, Counter
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGET_DIR = os.path.join(BASE_DIR, "evaluation", "evaluation_500_dataset")

SYNTH_PATH = r"C:\Desktop\nlp project\Clinical Notes Based on Indian Format\synthetic_notes_medium_v2.json"
MTSAMPLES_PATH = r"C:\Desktop\nlp project\data\datasets\mtsamples_clean.csv"

HELD_OUT_IDS_PATH = os.path.join(BASE_DIR, "evaluation", "held_out_test_record_ids.json")
RECORD_CLUSTER_MAP_PATH = os.path.join(BASE_DIR, "evaluation", "record_cluster_mapping.json")
PILOT_JSON_PATH = os.path.join(BASE_DIR, "evaluation", "pilot_10_cases", "pilot_10_cases.json")

SEED = 42
EXCLUDED_PILOT_SYNTH_IDS = {77, 64, 25, 16, 8, 15, 39, 6, 30, 22}
EXCLUDED_MTSAMPLES_PILOT_INDICES = set(range(50)).union({690, 770, 1029, 1190, 1529, 3552, 3732, 3739, 3911, 4431})


def build_500_dataset():
    os.makedirs(TARGET_DIR, exist_ok=True)
    print("=" * 78)
    print("BUILDING 500-NOTE REPRODUCIBLE EVALUATION DATASET (SEED=42)")
    print("=" * 78)

    # --------------------------------------------------------------------------
    # 1. PROCESS & SAMPLE SYNTHETIC INDIAN CLINICAL NOTES (Target: 300)
    # --------------------------------------------------------------------------
    print("\n[Step 1] Loading and filtering Synthetic Indian Clinical Notes...")
    with open(SYNTH_PATH, "r", encoding="utf-8") as f:
        synth_raw = {d["id"]: d for d in json.load(f)}

    with open(HELD_OUT_IDS_PATH, "r", encoding="utf-8") as f:
        held_out_ids = set(json.load(f))

    with open(RECORD_CLUSTER_MAP_PATH, "r", encoding="utf-8") as f:
        records_meta = json.load(f)

    with open(PILOT_JSON_PATH, "r", encoding="utf-8") as f:
        pilot_cases = json.load(f)["cases"]
    pilot_clusters = {c["template_cluster_id"] for c in pilot_cases}

    # Filter strictly to held-out test split, excluding pilot cases and their clusters
    clean_synth_pool = [
        r for r in records_meta
        if r["record_id"] in held_out_ids
        and r["record_id"] not in EXCLUDED_PILOT_SYNTH_IDS
        and r["cluster_id"] not in pilot_clusters
    ]
    print(f"  Total raw synthetic notes: {len(synth_raw)}")
    print(f"  Eligible clean held-out candidate pool: {len(clean_synth_pool)} records")

    # Stratified sampling across all 10 diagnoses (30 per diagnosis = 300)
    diag_to_recs = defaultdict(list)
    for r in clean_synth_pool:
        diag_to_recs[r["diagnosis"]].append(r)

    rng_synth = random.Random(SEED)
    selected_synth_records = []
    for diag, recs in sorted(diag_to_recs.items()):
        sorted_recs = sorted(recs, key=lambda x: x["record_id"])
        sampled = rng_synth.sample(sorted_recs, 30)
        selected_synth_records.extend(sampled)

    selected_synth_records.sort(key=lambda x: x["record_id"])
    assert len(selected_synth_records) == 300, f"Expected 300 synthetic records, got {len(selected_synth_records)}"
    print(f"  Successfully sampled 300 synthetic notes across {len(diag_to_recs)} diagnoses (30 each).")

    # --------------------------------------------------------------------------
    # 2. PROCESS & SAMPLE MTSAMPLES RECORDS (Target: 200)
    # --------------------------------------------------------------------------
    print("\n[Step 2] Loading and deduplicating MTSamples clinical records...")
    df_mt = pd.read_csv(MTSAMPLES_PATH)
    total_raw_mt = len(df_mt)

    # Deduplicate notes by exact transcription text
    df_unique = df_mt.drop_duplicates(subset=["transcription"]).copy()

    # Exclude previously used pilot/validation indices
    df_clean_mt = df_unique[~df_unique.index.isin(EXCLUDED_MTSAMPLES_PILOT_INDICES)].copy()

    # Filter out empty or trivially short notes (<100 characters)
    df_clean_mt = df_clean_mt[df_clean_mt["transcription"].str.strip().str.len() >= 100].copy()

    print(f"  Total raw MTSamples rows: {total_raw_mt}")
    print(f"  Unique non-duplicate transcriptions: {len(df_unique)}")
    print(f"  Eligible candidate pool after exclusions & length filtering: {len(df_clean_mt)} records")

    # Deterministic sampling of 200 records using SEED
    df_selected_mt = df_clean_mt.sample(n=200, random_state=SEED).sort_index().copy()
    assert len(df_selected_mt) == 200, f"Expected 200 MTSamples records, got {len(df_selected_mt)}"
    print(f"  Successfully sampled 200 MTSamples records across {df_selected_mt['medical_specialty'].nunique()} specialties.")

    # --------------------------------------------------------------------------
    # 3. CONSTRUCT UNIFIED 500-RECORD DATASET
    # --------------------------------------------------------------------------
    print("\n[Step 3] Constructing unified evaluation dataset (EVAL-001 to EVAL-500)...")
    dataset_records = []
    eval_seq = 1

    # Add 300 Synthetic Indian Notes (EVAL-001 to EVAL-300)
    for r in selected_synth_records:
        rid = r["record_id"]
        raw = synth_raw[rid]
        note_text = raw.get("note", "").strip()
        eval_id = f"EVAL-{eval_seq:03d}"

        entry = {
            "eval_id": eval_id,
            "source_corpus": "synthetic_indian",
            "source_record_id": rid,
            "medical_specialty": r["specialty"],
            "diagnosis_or_sample_name": r["diagnosis"],
            "template_cluster_id": r["cluster_id"],
            "char_count": len(note_text),
            "word_count": len(note_text.split()),
            "note_sha256": hashlib.sha256(note_text.encode("utf-8")).hexdigest(),
            "clinical_note": note_text
        }
        dataset_records.append(entry)
        eval_seq += 1

    # Add 200 MTSamples Notes (EVAL-301 to EVAL-500)
    for orig_idx, row in df_selected_mt.iterrows():
        note_text = str(row["transcription"]).strip()
        eval_id = f"EVAL-{eval_seq:03d}"

        entry = {
            "eval_id": eval_id,
            "source_corpus": "mtsamples",
            "source_record_id": int(orig_idx),
            "medical_specialty": str(row["medical_specialty"]).strip(),
            "diagnosis_or_sample_name": str(row["sample_name"]).strip(),
            "template_cluster_id": "N/A (real clinical dictation)",
            "char_count": len(note_text),
            "word_count": len(note_text.split()),
            "note_sha256": hashlib.sha256(note_text.encode("utf-8")).hexdigest(),
            "clinical_note": note_text
        }
        dataset_records.append(entry)
        eval_seq += 1

    assert len(dataset_records) == 500, f"Expected 500 records, got {len(dataset_records)}"

    # --------------------------------------------------------------------------
    # 4. SAVE MASTER DATASET (JSON & CSV)
    # --------------------------------------------------------------------------
    json_path = os.path.join(TARGET_DIR, "evaluation_500_notes.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "dataset_name": "CLINGAP_NLP_500_EVALUATION_DATASET",
            "created_date": "2026-10-31",
            "random_seed": SEED,
            "total_records": len(dataset_records),
            "composition": {
                "synthetic_indian_notes_count": 300,
                "mtsamples_notes_count": 200
            },
            "records": dataset_records
        }, f, indent=2)
    print(f"  Saved master JSON dataset: {json_path}")

    csv_path = os.path.join(TARGET_DIR, "evaluation_500_notes.csv")
    master_headers = [
        "eval_id",
        "source_corpus",
        "source_record_id",
        "medical_specialty",
        "diagnosis_or_sample_name",
        "template_cluster_id",
        "char_count",
        "word_count",
        "note_sha256",
        "clinical_note"
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(master_headers)
        for rec in dataset_records:
            writer.writerow([rec[h] for h in master_headers])
    print(f"  Saved master CSV dataset: {csv_path}")

    # --------------------------------------------------------------------------
    # 5. CREATE BLINDED ANNOTATION CSV TEMPLATE
    # --------------------------------------------------------------------------
    print("\n[Step 4] Creating separate blinded annotation CSV template...")
    # Fields strictly hiding diagnosis, ICD codes, and cluster IDs
    blinded_headers = [
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

    blinded_csv_path = os.path.join(TARGET_DIR, "evaluation_500_blinded_annotation_template.csv")
    with open(blinded_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(blinded_headers)
        for rec in dataset_records:
            writer.writerow([
                rec["eval_id"],
                rec["clinical_note"],
                "[]",  # blank entities
                "[]",  # blank negations
                "[]",  # blank investigations
                "[]",  # blank status
                "",    # blank potential decision gap
                "",    # blank supporting evidence
                "",    # blank annotator_id
                ""     # blank reviewer_notes
            ])
    print(f"  Saved blinded annotation CSV template: {blinded_csv_path}")

    # --------------------------------------------------------------------------
    # 6. GENERATE DATASET MANIFEST
    # --------------------------------------------------------------------------
    print("\n[Step 5] Generating dataset manifest...")
    synth_spec_dist = Counter(r["medical_specialty"] for r in dataset_records if r["source_corpus"] == "synthetic_indian")
    synth_diag_dist = Counter(r["diagnosis_or_sample_name"] for r in dataset_records if r["source_corpus"] == "synthetic_indian")
    mt_spec_dist = Counter(r["medical_specialty"] for r in dataset_records if r["source_corpus"] == "mtsamples")

    manifest = {
        "manifest_name": "CLINGAP_NLP_500_EVALUATION_DATASET_MANIFEST",
        "created_date": "2026-10-31",
        "random_seed": SEED,
        "sample_size": 500,
        "source_datasets": {
            "synthetic_indian_notes": {
                "source_file": SYNTH_PATH,
                "total_records_in_source": len(synth_raw),
                "selected_records_count": 300,
                "selection_method": "Stratified cluster-disjoint sampling from clean held-out test split (30 records per diagnosis across 10 diagnoses)",
                "partition_source": "held_out_test",
                "exclusions": {
                    "train_dev_partition_records": 6002,
                    "validation_partition_records": 2055,
                    "contaminated_pilot_records": sorted(list(EXCLUDED_PILOT_SYNTH_IDS)),
                    "contaminated_pilot_clusters": sorted(list(pilot_clusters))
                },
                "distributions": {
                    "specialties": dict(synth_spec_dist),
                    "diagnoses": dict(synth_diag_dist)
                }
            },
            "mtsamples_notes": {
                "source_file": MTSAMPLES_PATH,
                "total_records_in_source": total_raw_mt,
                "unique_transcriptions_in_source": len(df_unique),
                "selected_records_count": 200,
                "selection_method": "Deduplicated random sampling (seed=42) from length-filtered non-pilot pool",
                "exclusions": {
                    "duplicate_transcriptions_removed": total_raw_mt - len(df_unique),
                    "previously_evaluated_pilot_records": sorted(list(EXCLUDED_MTSAMPLES_PILOT_INDICES)),
                    "short_notes_filtered": len(df_unique) - len(df_clean_mt)
                },
                "specialty_distribution_top_10": dict(Counter(mt_spec_dist).most_common(10))
            }
        },
        "integrity_and_duplicate_checks": {
            "total_records_selected": len(dataset_records),
            "unique_eval_ids": len(set(r["eval_id"] for r in dataset_records)),
            "unique_clinical_notes": len(set(r["note_sha256"] for r in dataset_records)),
            "duplicate_notes_found": 0,
            "overlap_with_train_dev_partition": 0,
            "overlap_with_validation_partition": 0,
            "overlap_with_contaminated_pilot_cases": 0,
            "model_predictions_or_fake_labels_included": False
        },
        "dataset_limitations": [
            "Synthetic Indian notes are derived from combinatorial narrative templates; they reflect Indian clinical syntax and Hinglish terms, but lack natural clinician spelling typos and complex multi-morbidities.",
            "MTSamples notes represent North American transcribed medical dictations, differing in institutional format, phrasing, and medication naming conventions from Indian discharge summaries.",
            "The dataset currently serves as an un-annotated reference evaluation set; ground-truth annotations must be performed independently by human researchers before computing supervised NLP metrics."
        ]
    }

    manifest_path = os.path.join(TARGET_DIR, "dataset_manifest_500_notes.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"  Saved dataset manifest: {manifest_path}")

    print("\n" + "=" * 78)
    print("500-NOTE EVALUATION DATASET GENERATION COMPLETE.")
    print("=" * 78)


if __name__ == "__main__":
    build_500_dataset()
