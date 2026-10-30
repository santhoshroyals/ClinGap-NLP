"""
leakage_safe_splitter.py - Cluster-Disjoint Stratified Dataset Splitter
ClinGap-NLP Evaluation Infrastructure (Phase 2)

Key Properties:
- Reproducible pseudo-random splitting using fixed seed (default: 42).
- Groups records by underlying narrative template cluster (1,152 clusters).
- Prevents cross-split leakage: No template cluster appears in more than one partition.
- Disjoint partitions: Train/Dev (60%), Validation (20%), Held-Out Test (20%).
- Saves split manifests, ID files, and distribution reports.
- Explains structural limitations of synthetic template splits.
"""

import os
import sys
import json
import random
from collections import Counter, defaultdict
from typing import Dict, List, Any, Tuple


def perform_cluster_disjoint_split(
    record_cluster_map_path: str,
    output_dir: str,
    seed: int = 42,
    train_dev_ratio: float = 0.60,
    val_ratio: float = 0.20,
    test_ratio: float = 0.20
) -> Dict[str, Any]:
    """
    Partitions the 10,000 records strictly by their template cluster IDs.
    """
    assert abs(train_dev_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "Split ratios must sum to 1.0"

    if not os.path.exists(record_cluster_map_path):
        raise FileNotFoundError(f"Record-cluster mapping not found at {record_cluster_map_path}")

    with open(record_cluster_map_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    print(f"Loaded {len(records)} mapped records.")

    # 1. Group records by cluster_id, and track (specialty, diagnosis) of each cluster
    cluster_to_records = defaultdict(list)
    cluster_meta = {}

    for r in records:
        cid = r["cluster_id"]
        cluster_to_records[cid].append(r["record_id"])
        if cid not in cluster_meta:
            cluster_meta[cid] = {
                "specialty": r["specialty"],
                "diagnosis": r["diagnosis"]
            }

    unique_clusters = list(cluster_to_records.keys())
    print(f"Total unique clusters to partition: {len(unique_clusters)}")

    # 2. Stratify clusters by (specialty, diagnosis)
    strata = defaultdict(list)
    for cid, meta in cluster_meta.items():
        key = (meta["specialty"], meta["diagnosis"])
        strata[key].append(cid)

    rng = random.Random(seed)

    train_dev_clusters = set()
    val_clusters = set()
    test_clusters = set()

    for stratum_key, cids in sorted(strata.items()):
        # Sort cids first for deterministic ordering before random shuffle
        cids_sorted = sorted(cids)
        rng.shuffle(cids_sorted)

        n = len(cids_sorted)
        n_train = int(round(n * train_dev_ratio))
        n_val = int(round(n * val_ratio))
        # Ensure remaining go to test
        n_test = n - n_train - n_val

        # Adjust in case rounding produced 0 for any partition when n >= 3
        if n >= 3 and n_test == 0:
            n_train -= 1
            n_test = 1

        c_train = cids_sorted[:n_train]
        c_val = cids_sorted[n_train:n_train + n_val]
        c_test = cids_sorted[n_train + n_val:]

        train_dev_clusters.update(c_train)
        val_clusters.update(c_val)
        test_clusters.update(c_test)

    # 3. Assert complete cluster disjointness
    assert train_dev_clusters.isdisjoint(val_clusters), "CRITICAL LEAKAGE: train_dev and val share clusters!"
    assert train_dev_clusters.isdisjoint(test_clusters), "CRITICAL LEAKAGE: train_dev and test share clusters!"
    assert val_clusters.isdisjoint(test_clusters), "CRITICAL LEAKAGE: val and test share clusters!"
    assert len(train_dev_clusters) + len(val_clusters) + len(test_clusters) == len(unique_clusters), "Cluster count mismatch!"

    # 4. Map clusters to record IDs
    train_dev_records = []
    for cid in train_dev_clusters:
        train_dev_records.extend(cluster_to_records[cid])

    val_records = []
    for cid in val_clusters:
        val_records.extend(cluster_to_records[cid])

    test_records = []
    for cid in test_clusters:
        test_records.extend(cluster_to_records[cid])

    # Sort record IDs
    train_dev_records.sort()
    val_records.sort()
    test_records.sort()

    total_records = len(train_dev_records) + len(val_records) + len(test_records)
    assert total_records == len(records), "Record count mismatch after splitting!"

    # 5. Distribution statistics per split
    def get_split_stats(rec_ids: List[int], cluster_set: set) -> Dict[str, Any]:
        rec_set = set(rec_ids)
        split_records = [r for r in records if r["record_id"] in rec_set]
        spec_dist = Counter(r["specialty"] for r in split_records)
        diag_dist = Counter(r["diagnosis"] for r in split_records)
        return {
            "record_count": len(rec_ids),
            "record_share_pct": round((len(rec_ids) / total_records) * 100, 2),
            "cluster_count": len(cluster_set),
            "cluster_share_pct": round((len(cluster_set) / len(unique_clusters)) * 100, 2),
            "specialty_distribution": dict(spec_dist),
            "diagnosis_distribution": dict(diag_dist)
        }

    train_stats = get_split_stats(train_dev_records, train_dev_clusters)
    val_stats = get_split_stats(val_records, val_clusters)
    test_stats = get_split_stats(test_records, test_clusters)

    split_manifest = {
        "metadata": {
            "random_seed": seed,
            "split_strategy": "cluster_disjoint_stratified_by_specialty_and_diagnosis",
            "leakage_guarantee": "ZERO cross-partition template cluster sharing (0.0% overlap)",
            "limitations": (
                "While cluster disjointness prevents identical narrative templates across partitions, "
                "all synthetic notes originate from the same finite vocabulary pool in note_generator_v2.py. "
                "The test set assesses generalization across template slot combinations, NOT authentic clinical diversity."
            ),
            "total_records": total_records,
            "total_clusters": len(unique_clusters)
        },
        "partitions": {
            "train_dev": train_stats,
            "validation": val_stats,
            "held_out_test": test_stats
        }
    }

    # 6. Save manifests and ID files
    os.makedirs(output_dir, exist_ok=True)

    manifest_path = os.path.join(output_dir, "split_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(split_manifest, f, indent=2)
    print(f"Saved split manifest to {manifest_path}")

    # Save ID lists
    splits_data = {
        "train_dev_record_ids.json": train_dev_records,
        "validation_record_ids.json": val_records,
        "held_out_test_record_ids.json": test_records,
        "train_dev_cluster_ids.json": sorted(list(train_dev_clusters)),
        "validation_cluster_ids.json": sorted(list(val_clusters)),
        "held_out_test_cluster_ids.json": sorted(list(test_clusters))
    }

    for fname, id_list in splits_data.items():
        fpath = os.path.join(output_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(id_list, f, indent=2)

    print(f"Saved all 6 split ID and cluster files to {output_dir}")

    # Generate Markdown Distribution Report
    report_path = os.path.join(output_dir, "SPLIT_DISTRIBUTION_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# ClinGap-NLP: Cluster-Disjoint Dataset Split Distribution Report\n\n")
        f.write(f"- **Random Seed:** `{seed}`\n")
        f.write(f"- **Total Records:** {total_records:,}\n")
        f.write(f"- **Total Template Clusters:** {len(unique_clusters):,}\n")
        f.write("- **Cross-Partition Cluster Overlap:** **0.00% (Strictly Disjoint)**\n\n")
        f.write("## 1. Partition Overview\n\n")
        f.write("| Partition | Clusters | Cluster % | Records | Record % |\n")
        f.write("|---|:---:|:---:|:---:|:---:|\n")
        f.write(f"| **Train / Dev** | {train_stats['cluster_count']} | {train_stats['cluster_share_pct']}% | {train_stats['record_count']} | {train_stats['record_share_pct']}% |\n")
        f.write(f"| **Validation** | {val_stats['cluster_count']} | {val_stats['cluster_share_pct']}% | {val_stats['record_count']} | {val_stats['record_share_pct']}% |\n")
        f.write(f"| **Held-Out Test** | {test_stats['cluster_count']} | {test_stats['cluster_share_pct']}% | {test_stats['record_count']} | {test_stats['record_share_pct']}% |\n")
        f.write(f"| **Total** | **{len(unique_clusters)}** | **100.0%** | **{total_records}** | **100.0%** |\n\n")

        f.write("## 2. Specialty Distribution Across Partitions\n\n")
        f.write("| Specialty | Train/Dev Records | Validation Records | Test Records | Total Records |\n")
        f.write("|---|:---:|:---:|:---:|:---:|\n")
        all_specs = sorted(list(train_stats["specialty_distribution"].keys()))
        for sp in all_specs:
            tr_c = train_stats["specialty_distribution"].get(sp, 0)
            va_c = val_stats["specialty_distribution"].get(sp, 0)
            te_c = test_stats["specialty_distribution"].get(sp, 0)
            tot_c = tr_c + va_c + te_c
            f.write(f"| `{sp}` | {tr_c} | {va_c} | {te_c} | {tot_c} |\n")

        f.write("\n## 3. Methodological Limitation Statement\n\n")
        f.write("> **Academic Notice:** Although the cluster-disjoint split guarantees that no clinical narrative\n")
        f.write("> template is shared across splits, the synthetic notes are generated by combinatorial slot-filling\n")
        f.write("> from `note_generator_v2.py`. Performance on the held-out test partition measures model\n")
        f.write("> stability across unseen slot combinations, NOT clinical efficacy on real-world medical records.\n")

    print(f"Generated split distribution report at {report_path}")
    return split_manifest


if __name__ == "__main__":
    eval_dir = os.path.dirname(os.path.abspath(__file__))
    mapping_file = os.path.join(eval_dir, "record_cluster_mapping.json")
    perform_cluster_disjoint_split(mapping_file, eval_dir, seed=42)
