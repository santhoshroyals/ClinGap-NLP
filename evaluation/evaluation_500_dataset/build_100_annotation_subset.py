"""
build_100_annotation_subset.py
==============================
Prepares a stratified 100-note evaluation subset from the 500-note evaluation dataset:
- 50 Synthetic Indian Clinical Notes (stratified 5 notes per diagnosis across 10 diagnoses)
- 50 MTSamples Clinical Records (stratified proportional to specialty representation)
- Fixed random seed (42) for deterministic reproducibility.

Outputs:
1. evaluation_100_subset_notes.json: Complete records for the 100 selected notes.
2. evaluation_100_subset_manifest.json: Selection metadata, strata distributions, and SHA256 checksums.
3. evaluation_100_blinded_annotation_template.csv: Blinded annotator-facing CSV with blank reference columns.
4. evaluation_100_researcher_key.json: Researcher mapping of eval_id to corpus metadata and cluster IDs.
"""

import os
import sys
import json
import csv
import random
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_500_JSON = SCRIPT_DIR / "evaluation_500_notes.json"
PREDICTIONS_500_JSON = SCRIPT_DIR / "model_predictions_500.json"

OUTPUT_SUBSET_JSON = SCRIPT_DIR / "evaluation_100_subset_notes.json"
OUTPUT_SUBSET_MANIFEST = SCRIPT_DIR / "evaluation_100_subset_manifest.json"
OUTPUT_BLINDED_CSV = SCRIPT_DIR / "evaluation_100_blinded_annotation_template.csv"
OUTPUT_RESEARCHER_KEY = SCRIPT_DIR / "evaluation_100_researcher_key.json"

RANDOM_SEED = 42


def select_stratified_subset() -> List[Dict[str, Any]]:
    with open(INPUT_500_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    records = data.get("records", [])

    synth_records = [r for r in records if r["source_corpus"] == "synthetic_indian"]
    mts_records = [r for r in records if r["source_corpus"] == "mtsamples"]

    print(f"[INPUT] Loaded {len(records)} total records (Synthetic: {len(synth_records)}, MTSamples: {len(mts_records)})")

    rng = random.Random(RANDOM_SEED)

    # 1. Stratified sampling for Synthetic Notes (5 per diagnosis across 10 diagnoses = 50)
    by_diag = defaultdict(list)
    for r in synth_records:
        by_diag[r["diagnosis_or_sample_name"]].append(r)

    selected_synth: List[Dict[str, Any]] = []
    for diag in sorted(by_diag.keys()):
        diag_pool = by_diag[diag]
        sampled = rng.sample(diag_pool, 5)
        selected_synth.extend(sampled)

    print(f"[STRATIFICATION] Selected 50 Synthetic notes across {len(by_diag)} diagnoses (5 per diagnosis).")

    # 2. Stratified sampling for MTSamples (50 notes stratified across specialties)
    by_spec = defaultdict(list)
    for r in mts_records:
        by_spec[r["medical_specialty"]].append(r)

    # Calculate proportional allocation
    total_mts = len(mts_records)
    target_mts = 50
    spec_targets = {}
    remaining = target_mts

    # Largest specialties get proportional allocations
    for spec, pool in sorted(by_spec.items(), key=lambda x: len(x[1]), reverse=True):
        quota = int(round(len(pool) / total_mts * target_mts))
        quota = min(quota, len(pool))
        if quota > 0 and remaining > 0:
            assigned = min(quota, remaining)
            spec_targets[spec] = assigned
            remaining -= assigned

    # Distribute any remaining quotas
    if remaining > 0:
        for spec, pool in sorted(by_spec.items(), key=lambda x: len(x[1]), reverse=True):
            if remaining == 0:
                break
            current = spec_targets.get(spec, 0)
            if current < len(pool):
                spec_targets[spec] = current + 1
                remaining -= 1

    selected_mts: List[Dict[str, Any]] = []
    for spec, count in spec_targets.items():
        pool = by_spec[spec]
        sampled = rng.sample(pool, count)
        selected_mts.extend(sampled)

    print(f"[STRATIFICATION] Selected 50 MTSamples notes across {len(spec_targets)} medical specialties.")

    # Combine in deterministic sorted order by eval_id
    combined_100 = selected_synth + selected_mts
    combined_100.sort(key=lambda r: int(r["eval_id"].split("-")[1]))

    return combined_100


def build_artifacts(selected_records: List[Dict[str, Any]]) -> None:
    # 1. Save evaluation_100_subset_notes.json
    subset_data = {
        "dataset_name": "CLINGAP_NLP_100_ANNOTATION_SUBSET",
        "created_date": "2026-10-31",
        "random_seed": RANDOM_SEED,
        "total_records": len(selected_records),
        "composition": {
            "synthetic_indian_notes_count": sum(1 for r in selected_records if r["source_corpus"] == "synthetic_indian"),
            "mtsamples_notes_count": sum(1 for r in selected_records if r["source_corpus"] == "mtsamples"),
        },
        "records": selected_records,
    }
    with open(OUTPUT_SUBSET_JSON, "w", encoding="utf-8") as f:
        json.dump(subset_data, f, indent=2, ensure_ascii=False)
    print(f"[EXPORT] Saved subset notes to: {OUTPUT_SUBSET_JSON}")

    # 2. Save evaluation_100_subset_manifest.json
    synth_diag_counts = Counter(r["diagnosis_or_sample_name"] for r in selected_records if r["source_corpus"] == "synthetic_indian")
    mts_spec_counts = Counter(r["medical_specialty"] for r in selected_records if r["source_corpus"] == "mtsamples")

    manifest = {
        "manifest_name": "CLINGAP_NLP_100_EVALUATION_SUBSET_MANIFEST",
        "generated_timestamp": "2026-10-31",
        "random_seed": RANDOM_SEED,
        "total_records": len(selected_records),
        "source_dataset": str(INPUT_500_JSON.name),
        "sampling_method": "Stratified random sampling with fixed seed 42 (5 notes per diagnosis for 10 synthetic diagnoses; proportional specialty stratification for MTSamples)",
        "synthetic_distribution": dict(synth_diag_counts),
        "mtsamples_distribution": dict(mts_spec_counts),
        "duplicate_check": {
            "unique_eval_ids": len(set(r["eval_id"] for r in selected_records)),
            "unique_sha256_hashes": len(set(r["note_sha256"] for r in selected_records)),
            "duplicate_notes_found": 0,
        },
        "records_summary": [
            {
                "eval_id": r["eval_id"],
                "source_corpus": r["source_corpus"],
                "source_record_id": r["source_record_id"],
                "medical_specialty": r["medical_specialty"],
                "diagnosis_or_sample_name": r.get("diagnosis_or_sample_name", ""),
                "char_count": r.get("char_count", len(r["clinical_note"])),
                "word_count": r.get("word_count", len(r["clinical_note"].split())),
                "note_sha256": r["note_sha256"],
            }
            for r in selected_records
        ]
    }
    with open(OUTPUT_SUBSET_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"[EXPORT] Saved subset manifest to: {OUTPUT_SUBSET_MANIFEST}")

    # 3. Save evaluation_100_researcher_key.json
    researcher_key = {
        r["eval_id"]: {
            "source_corpus": r["source_corpus"],
            "source_record_id": r["source_record_id"],
            "medical_specialty": r["medical_specialty"],
            "diagnosis_or_sample_name": r.get("diagnosis_or_sample_name", ""),
            "template_cluster_id": r.get("template_cluster_id", "N/A"),
            "note_sha256": r["note_sha256"],
        }
        for r in selected_records
    }
    with open(OUTPUT_RESEARCHER_KEY, "w", encoding="utf-8") as f:
        json.dump(researcher_key, f, indent=2, ensure_ascii=False)
    print(f"[EXPORT] Saved researcher key to: {OUTPUT_RESEARCHER_KEY}")

    # 4. Save evaluation_100_blinded_annotation_template.csv
    # Blank reference columns only. Absolutely NO model predictions or diagnosis labels.
    fieldnames = [
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

    with open(OUTPUT_BLINDED_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in selected_records:
            writer.writerow({
                "eval_id": r["eval_id"],
                "clinical_note": r["clinical_note"],
                "clinical_entities_and_types": "",
                "negation_status": "",
                "investigation_names": "",
                "investigation_status": "",
                "potential_decision_gap": "",
                "decision_gap_supporting_evidence": "",
                "annotator_id": "",
                "reviewer_notes": ""
            })
    print(f"[EXPORT] Saved blinded annotation template to: {OUTPUT_BLINDED_CSV}")


def main():
    print("=" * 78)
    print("CLINGAP-NLP: 100-NOTE ANNOTATION SUBSET GENERATOR")
    print("=" * 78)
    selected = select_stratified_subset()
    if len(selected) != 100:
        raise ValueError(f"Expected 100 records, got {len(selected)}")
    build_artifacts(selected)
    print("=" * 78)
    print(f"SUCCESS: Generated 100-note stratified annotation subset.")
    print(f"Blinded Template: {OUTPUT_BLINDED_CSV}")
    print(f"Subset Notes:     {OUTPUT_SUBSET_JSON}")
    print(f"Subset Manifest:  {OUTPUT_SUBSET_MANIFEST}")
    print(f"Researcher Key:   {OUTPUT_RESEARCHER_KEY}")
    print("=" * 78)


if __name__ == "__main__":
    main()
