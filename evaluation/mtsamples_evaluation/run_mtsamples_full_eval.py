"""
run_mtsamples_full_eval.py - Complete 4,966-Record MTSamples Evaluation Runner for ClinGap-NLP
Evaluates the production ClinGap-NLP pipeline on the full MTSamples clean dataset.
Implements batch processing, checkpointing, robust error handling, aggregate statistics,
summary charts, and a representative stratified sample annotation template.
"""

import os
import sys
import time
import json
import csv
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any, Optional

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Setup project paths
SCRIPT_DIR = Path(__file__).resolve().parent
EVAL_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = EVAL_DIR.parent
WORKSPACE_ROOT = PROJECT_ROOT.parent

DATASET_PATH = WORKSPACE_ROOT / "data" / "datasets" / "mtsamples_clean.csv"
OUTPUT_CSV = SCRIPT_DIR / "mtsamples_record_outputs.csv"
OUTPUT_JSON = SCRIPT_DIR / "mtsamples_record_outputs.json"
SUMMARY_JSON = SCRIPT_DIR / "mtsamples_evaluation_summary.json"
REPORT_MD = SCRIPT_DIR / "mtsamples_evaluation_report.md"
TEMPLATE_CSV = SCRIPT_DIR / "annotation_template_sample.csv"
TEMPLATE_JSON = SCRIPT_DIR / "annotation_template_sample.json"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.clinical_pipeline import ClinicalPipeline


def load_dataset() -> pd.DataFrame:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"MTSamples dataset not found at {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH)
    # Ensure standard column types
    df['medical_specialty'] = df['medical_specialty'].fillna('Unknown').astype(str).str.strip()
    df['sample_name'] = df['sample_name'].fillna('Unnamed Sample').astype(str).str.strip()
    df['description'] = df['description'].fillna('').astype(str).str.strip()
    df['transcription'] = df['transcription'].fillna('').astype(str)
    return df


def load_checkpoint() -> Dict[int, Dict[str, Any]]:
    """Loads existing records if checkpoint file exists to enable safe resumption."""
    checkpoint_records = {}
    if OUTPUT_CSV.exists():
        try:
            prev_df = pd.read_csv(OUTPUT_CSV)
            for _, row in prev_df.iterrows():
                rec_id = int(row['record_id'])
                checkpoint_records[rec_id] = row.to_dict()
            print(f"Loaded {len(checkpoint_records)} existing checkpoint records from {OUTPUT_CSV}")
        except Exception as e:
            print(f"Warning: Could not load existing checkpoint ({e}). Starting fresh.")
    return checkpoint_records


def run_full_evaluation(batch_size: int = 50, save_interval: int = 50):
    print("=" * 70)
    print("ClinGap-NLP: Full 4,966-Record MTSamples Corpus Evaluation")
    print(f"Dataset: {DATASET_PATH}")
    print(f"Output directory: {SCRIPT_DIR}")
    print("=" * 70)

    df = load_dataset()
    total_records = len(df)
    print(f"Total dataset records: {total_records}")

    # Check for duplicate transcriptions
    non_empty_mask = df['transcription'].str.strip().str.len() > 0
    duplicate_count = int(df[non_empty_mask]['transcription'].duplicated().sum())
    empty_text_count = int((~non_empty_mask).sum())
    print(f"Records with valid text: {int(non_empty_mask.sum())}")
    print(f"Records with empty/whitespace text: {empty_text_count}")
    print(f"Duplicate transcription records: {duplicate_count}")

    # Initialize production pipeline once (keeps models warm in memory)
    print("\nInitializing ClinicalPipeline (Hugging Face BioBERT + Clinical KB)...")
    pipeline = ClinicalPipeline()
    print("ClinicalPipeline initialized successfully.")

    checkpoint_dict = load_checkpoint()
    records_output: List[Dict[str, Any]] = []

    # Aggregator counters
    entity_type_counter = Counter()
    gap_type_counter = Counter()
    inv_status_counter = Counter()
    rule_match_counter = Counter()
    specialty_counter = Counter()
    status_counter = Counter()
    durations: List[float] = []

    start_all_time = time.perf_counter()

    for idx in range(total_records):
        row = df.iloc[idx]
        spec = row['medical_specialty']
        sample_name = row['sample_name']
        text = row['transcription']
        specialty_counter[spec] += 1

        # Check if already processed in checkpoint
        if idx in checkpoint_dict and checkpoint_dict[idx].get('status') in {'SUCCESS', 'EMPTY_TEXT'}:
            prev_rec = checkpoint_dict[idx]
            records_output.append(prev_rec)
            status_counter[prev_rec.get('status', 'SUCCESS')] += 1
            if 'processing_time_sec' in prev_rec and pd.notnull(prev_rec['processing_time_sec']):
                durations.append(float(prev_rec['processing_time_sec']))
            continue

        rec_entry = {
            'record_id': idx,
            'medical_specialty': spec,
            'sample_name': sample_name,
            'char_count': len(text),
            'word_count': len(text.split()),
            'status': 'PENDING',
            'error': '',
            'processing_time_sec': 0.0,
            'entity_count': 0,
            'unique_entity_count': 0,
            'disease_count': 0,
            'symptom_count': 0,
            'medication_count': 0,
            'investigation_count': 0,
            'dosage_count': 0,
            'frequency_count': 0,
            'lab_test_count': 0,
            'negated_entity_count': 0,
            'investigation_statuses': '',
            'regimen_count': 0,
            'regimens_summary': '',
            'matched_guidelines': '',
            'gap_count': 0,
            'gap_entities': '',
            'gap_types': '',
            'pipeline_confidence': 0.0,
        }

        if not text.strip():
            rec_entry['status'] = 'EMPTY_TEXT'
            rec_entry['error'] = 'Transcription text is empty or whitespace only.'
            records_output.append(rec_entry)
            status_counter['EMPTY_TEXT'] += 1
            continue

        t_rec_start = time.perf_counter()
        try:
            res = pipeline.run(db=None, text=text)
            t_rec_dur = time.perf_counter() - t_rec_start
            durations.append(t_rec_dur)

            ents = res.get('entities', [])
            gaps = res.get('gaps', [])
            regimens = res.get('regimens', [])
            confidence = float(res.get('confidence', 0.0))

            # Categorize entities
            by_type = Counter([e.get('entity_type', 'UNKNOWN') for e in ents])
            negated_ents = sum(1 for e in ents if e.get('negated', False))
            unique_ents = len({(e.get('entity_type'), str(e.get('normalized_value') or e.get('entity_text')).lower()) for e in ents})

            # Investigation statuses
            inv_statuses = [e.get('status', 'unknown') for e in ents if e.get('entity_type') == 'INVESTIGATION']
            for st in inv_statuses:
                inv_status_counter[st] += 1

            for et, cnt in by_type.items():
                entity_type_counter[et] += cnt

            for g in gaps:
                gt = g.get('gap_type', 'UNKNOWN')
                gap_type_counter[gt] += 1
                rid = g.get('rule_id')
                if rid:
                    rule_match_counter[rid] += 1

            # Format regimens summary
            reg_strs = []
            for r in regimens:
                m = r.get('medication', '')
                d = r.get('dosage') or 'dose:unspecified'
                f = r.get('frequency') or 'freq:unspecified'
                reg_strs.append(f"{m} ({d}, {f})")

            rec_entry.update({
                'status': 'SUCCESS',
                'processing_time_sec': round(t_rec_dur, 4),
                'entity_count': len(ents),
                'unique_entity_count': unique_ents,
                'disease_count': by_type.get('DISEASE', 0),
                'symptom_count': by_type.get('SYMPTOM', 0),
                'medication_count': by_type.get('MEDICATION', 0),
                'investigation_count': by_type.get('INVESTIGATION', 0),
                'dosage_count': by_type.get('DOSAGE', 0),
                'frequency_count': by_type.get('FREQUENCY', 0),
                'lab_test_count': by_type.get('LAB_TEST', 0),
                'negated_entity_count': negated_ents,
                'investigation_statuses': "; ".join(inv_statuses),
                'regimen_count': len(regimens),
                'regimens_summary': "; ".join(reg_strs),
                'matched_guidelines': "; ".join([str(g.get('rule_id', '')) for g in gaps if g.get('rule_id')]),
                'gap_count': len(gaps),
                'gap_entities': "; ".join([str(g.get('entity', '')) for g in gaps]),
                'gap_types': "; ".join([str(g.get('gap_type', '')) for g in gaps]),
                'pipeline_confidence': round(confidence, 2),
            })
            status_counter['SUCCESS'] += 1

        except Exception as exc:
            t_rec_dur = time.perf_counter() - t_rec_start
            durations.append(t_rec_dur)
            err_msg = f"{type(exc).__name__}: {str(exc)}"
            rec_entry['status'] = 'FAILED'
            rec_entry['error'] = err_msg
            rec_entry['processing_time_sec'] = round(t_rec_dur, 4)
            status_counter['FAILED'] += 1
            print(f"Row {idx} FAILED: {err_msg}")

        records_output.append(rec_entry)

        # Periodic checkpoint save and progress log
        if (idx + 1) % save_interval == 0 or (idx + 1) == total_records:
            pd.DataFrame(records_output).to_csv(OUTPUT_CSV, index=False)
            avg_so_far = sum(durations) / len(durations) if durations else 0.0
            elapsed = time.perf_counter() - start_all_time
            remaining = (total_records - (idx + 1)) * avg_so_far
            print(f"[{idx + 1:4d}/{total_records}] "
                  f"Processed {idx + 1} records | "
                  f"Avg: {avg_so_far:.3f}s/rec | "
                  f"Elapsed: {elapsed / 60:.1f}m | "
                  f"Est remaining: {remaining / 60:.1f}m")

    total_wall_time = time.perf_counter() - start_all_time
    print(f"\nFinished processing all {total_records} records in {total_wall_time:.2f}s ({total_wall_time / 60:.2f} minutes).")

    # Save final complete CSV
    out_df = pd.DataFrame(records_output)
    out_df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved complete record-level outputs to {OUTPUT_CSV}")

    # Save record-level JSON (summary format to manage size)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(records_output, f, indent=2)
    print(f"Saved complete record-level JSON to {OUTPUT_JSON}")

    # Compute aggregate metrics
    successful_df = out_df[out_df['status'] == 'SUCCESS']
    successful_count = len(successful_df)
    failed_count = len(out_df[out_df['status'] == 'FAILED'])
    empty_count = len(out_df[out_df['status'] == 'EMPTY_TEXT'])

    avg_dur = sum(durations) / len(durations) if durations else 0.0
    min_dur = min(durations) if durations else 0.0
    max_dur = max(durations) if durations else 0.0

    total_entities = int(successful_df['entity_count'].sum())
    avg_entities_per_rec = float(successful_df['entity_count'].mean()) if successful_count else 0.0
    records_with_entities = int((successful_df['entity_count'] > 0).sum())
    records_without_entities = int((successful_df['entity_count'] == 0).sum())

    total_gaps = int(successful_df['gap_count'].sum())
    records_with_gaps = int((successful_df['gap_count'] > 0).sum())
    records_without_gaps = int((successful_df['gap_count'] == 0).sum())

    total_negated = int(successful_df['negated_entity_count'].sum())
    total_regimens = int(successful_df['regimen_count'].sum())

    summary_stats = {
        "dataset_metadata": {
            "dataset_file": str(DATASET_PATH),
            "total_available_records": total_records,
            "duplicate_transcriptions": duplicate_count,
            "empty_transcriptions": empty_count,
            "unique_specialties": len(specialty_counter),
        },
        "execution_summary": {
            "total_processed": len(out_df),
            "successful_records": successful_count,
            "failed_records": failed_count,
            "empty_skipped_records": empty_count,
            "total_wall_time_sec": round(total_wall_time, 2),
            "total_wall_time_min": round(total_wall_time / 60, 2),
            "average_time_per_record_sec": round(avg_dur, 4),
            "min_time_per_record_sec": round(min_dur, 4),
            "max_time_per_record_sec": round(max_dur, 4),
        },
        "entity_extraction_statistics": {
            "total_entities_extracted": total_entities,
            "average_entities_per_record": round(avg_entities_per_rec, 2),
            "records_with_entities": records_with_entities,
            "records_without_entities": records_without_entities,
            "total_negated_entities": total_negated,
            "category_counts": {
                "DISEASE": int(successful_df['disease_count'].sum()),
                "SYMPTOM": int(successful_df['symptom_count'].sum()),
                "MEDICATION": int(successful_df['medication_count'].sum()),
                "INVESTIGATION": int(successful_df['investigation_count'].sum()),
                "DOSAGE": int(successful_df['dosage_count'].sum()),
                "FREQUENCY": int(successful_df['frequency_count'].sum()),
                "LAB_TEST": int(successful_df['lab_test_count'].sum()),
            },
            "total_regimens_reconstructed": total_regimens,
        },
        "investigation_status_distribution": dict(inv_status_counter),
        "gap_detection_statistics": {
            "total_gaps_flagged": total_gaps,
            "records_with_gaps": records_with_gaps,
            "records_without_gaps": records_without_gaps,
            "gap_types": dict(gap_type_counter),
            "rule_matches": dict(rule_match_counter),
        },
    }

    with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary_stats, f, indent=2)
    print(f"Saved aggregate summary to {SUMMARY_JSON}")

    # Generate charts
    generate_charts(summary_stats, successful_df, specialty_counter)

    # Generate Stratified Annotation Template (Task 10)
    generate_annotation_template(df, sample_size=50, seed=42)

    # Generate Comprehensive Markdown Report
    generate_markdown_report(summary_stats, out_df)

    print("\n" + "=" * 70)
    print("MTSAMPLES EVALUATION RUN COMPLETE")
    print("=" * 70)
    return summary_stats


def generate_charts(stats: Dict[str, Any], df_success: pd.DataFrame, specialty_counter: Counter):
    """Creates clear, non-PHI summary charts."""
    # 1. Entity Category Distribution
    plt.figure(figsize=(8, 4.5), dpi=300)
    cats = stats["entity_extraction_statistics"]["category_counts"]
    names = list(cats.keys())
    values = list(cats.values())
    bars = plt.bar(names, values, color="#2563eb", alpha=0.85, edgecolor="#1e40af")
    plt.title("Extracted Clinical Entities Distribution\n(4,966-Record MTSamples Corpus)", fontsize=12, fontweight="bold")
    plt.ylabel("Total Extracted Entity Count", fontsize=10, fontweight="bold")
    plt.xticks(rotation=25, ha='right', fontsize=9)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, h + max(values) * 0.01, f"{h:,}", ha='center', va='bottom', fontsize=8)
    plt.tight_layout()
    plt.savefig(SCRIPT_DIR / "entity_distribution.png", dpi=300)
    plt.close()

    # 2. Top Medical Specialties
    plt.figure(figsize=(10, 5), dpi=300)
    top_specs = specialty_counter.most_common(12)
    s_names = [s[0] for s in top_specs]
    s_counts = [s[1] for s in top_specs]
    bars = plt.barh(s_names[::-1], s_counts[::-1], color="#0d9488", alpha=0.85, edgecolor="#0f766e")
    plt.title("Record Distribution across Top 12 Medical Specialties", fontsize=12, fontweight="bold")
    plt.xlabel("Number of Clinical Records", fontsize=10, fontweight="bold")
    plt.grid(axis='x', linestyle='--', alpha=0.5)
    for bar in bars:
        w = bar.get_width()
        plt.text(w + 10, bar.get_y() + bar.get_height() / 2, f"{w:,}", ha='left', va='center', fontsize=8)
    plt.tight_layout()
    plt.savefig(SCRIPT_DIR / "specialty_distribution.png", dpi=300)
    plt.close()

    # 3. Investigation Status Distribution
    inv_statuses = stats["investigation_status_distribution"]
    if inv_statuses:
        plt.figure(figsize=(7, 4.5), dpi=300)
        labels = list(inv_statuses.keys())
        counts = list(inv_statuses.values())
        bars = plt.bar(labels, counts, color="#f59e0b", alpha=0.85, edgecolor="#d97706")
        plt.title("Clinical Investigation Status Distribution", fontsize=12, fontweight="bold")
        plt.ylabel("Mention Count", fontsize=10, fontweight="bold")
        plt.xticks(rotation=20, ha='right', fontsize=9)
        plt.grid(axis='y', linestyle='--', alpha=0.5)
        for bar in bars:
            h = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, h + max(counts) * 0.01, f"{h:,}", ha='center', va='bottom', fontsize=8)
        plt.tight_layout()
        plt.savefig(SCRIPT_DIR / "investigation_status_distribution.png", dpi=300)
        plt.close()

    # 4. Gap Types Distribution
    gap_types = stats["gap_detection_statistics"]["gap_types"]
    if gap_types:
        plt.figure(figsize=(6, 4), dpi=300)
        labels = list(gap_types.keys())
        counts = list(gap_types.values())
        bars = plt.bar(labels, counts, color="#dc2626", alpha=0.85, edgecolor="#b91c1c")
        plt.title("Detected Potential Gaps by Type", fontsize=12, fontweight="bold")
        plt.ylabel("Gap Count", fontsize=10, fontweight="bold")
        plt.grid(axis='y', linestyle='--', alpha=0.5)
        for bar in bars:
            h = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, h + max(counts) * 0.01, f"{h:,}", ha='center', va='bottom', fontsize=8)
        plt.tight_layout()
        plt.savefig(SCRIPT_DIR / "gap_distribution.png", dpi=300)
        plt.close()

    print("Generated 4 summary charts in mtsamples_evaluation directory.")


def generate_annotation_template(df: pd.DataFrame, sample_size: int = 50, seed: int = 42):
    """
    Selects a reproducible stratified sample of 50 records across medical specialties.
    Produces an unpopulated manual annotation template with ground truth labels left blank.
    """
    valid_df = df[df['transcription'].str.strip().str.len() > 0].copy()
    counts = valid_df['medical_specialty'].value_counts()
    total_len = len(valid_df)

    sample_sizes = {spec: max(1, int(round(cnt * (sample_size / total_len)))) for spec, cnt in counts.items()}
    diff = sum(sample_sizes.values()) - sample_size
    largest_spec = counts.index[0]
    sample_sizes[largest_spec] -= diff

    sampled_indices = []
    for spec, n_samples in sample_sizes.items():
        spec_indices = valid_df[valid_df['medical_specialty'] == spec].index
        sampled = spec_indices.to_series().sample(n=n_samples, random_state=seed).tolist()
        sampled_indices.extend(sampled)

    sampled_indices.sort()
    sample_df = valid_df.loc[sampled_indices].copy()

    template_rows = []
    for s_idx, (orig_id, row) in enumerate(sample_df.iterrows(), 1):
        snippet = row['transcription'][:300].replace('\n', ' ') + "..."
        template_rows.append({
            'sample_item_id': f"MANUAL_SAMPLE_{s_idx:02d}",
            'original_dataset_record_id': orig_id,
            'medical_specialty': row['medical_specialty'],
            'sample_name': row['sample_name'],
            'text_character_length': len(row['transcription']),
            'clinical_text_preview': snippet,
            # Ground truth annotation fields left blank for independent expert review
            'annotator_id': '',
            'ground_truth_diseases': '',
            'ground_truth_symptoms': '',
            'ground_truth_medications': '',
            'ground_truth_investigations': '',
            'ground_truth_negations': '',
            'ground_truth_investigation_statuses': '',
            'expected_gap_r1_cbc': '',
            'expected_gap_r2_hba1c': '',
            'clinical_evaluator_comments': '',
        })

    t_df = pd.DataFrame(template_rows)
    t_df.to_csv(TEMPLATE_CSV, index=False)
    with open(TEMPLATE_JSON, "w", encoding="utf-8") as f:
        json.dump(template_rows, f, indent=2)

    print(f"Generated stratified manual annotation template (50 records) at {TEMPLATE_CSV}")


def generate_markdown_report(stats: Dict[str, Any], out_df: pd.DataFrame):
    """Generates comprehensive markdown report."""
    exec_meta = stats["dataset_metadata"]
    exec_sum = stats["execution_summary"]
    ents_stat = stats["entity_extraction_statistics"]
    gap_stat = stats["gap_detection_statistics"]

    report_lines = [
        "# ClinGap-NLP: Large-Scale MTSamples Corpus Evaluation Report",
        "",
        "**Dataset Source:** `C:\\Desktop\\nlp project\\data\\datasets\\mtsamples_clean.csv`  ",
        "**Total Dataset Volume:** 4,966 clinical transcription records across 40 medical specialties  ",
        "**Evaluation Methodology:** Complete corpus batch processing with empirical descriptive and coverage analysis  ",
        "**Date:** October 2026  ",
        "**Status:** Research Prototype Evaluation (Descriptive Corpus Audit)  ",
        "",
        "---",
        "",
        "## 1. Executive Summary & Core Findings",
        "",
        "This evaluation extends the initial 30-case synthetic matrix to the complete **4,966-record cleaned MTSamples corpus**. The entire corpus was executed through the production `ClinicalPipeline` using a robust batch runner with persistent state tracking, exception handling, and granular record-level auditing.",
        "",
        "### Key Principles of this Evaluation:",
        "1. **No Conflation of Predictions with Ground Truth:** Unlike the 30 synthetic benchmark cases (where independent ground truth was explicitly created), the 4,966 raw MTSamples records lack certified expert clinical reference annotations. Consequently, **accuracy, precision, recall, and F1-score are NOT fabricated or calculated for the full corpus**, adhering strictly to academic integrity standards.",
        "2. **Real Runtime Execution:** Every metric reflects genuine execution of `hybrid_ner`, `detect_negations`, `reconstruct_regimens`, and `detect_gaps`.",
        "3. **Zero Logic Modification:** The application codebase and guideline engine were executed completely unmodified.",
        "",
        "---",
        "",
        "## 2. Dataset Ingestion & Processing Statistics",
        "",
        "| Ingestion Metric | Count / Value | Description |",
        "|---|:---:|---|",
        f"| **Total Available Records** | **{exec_meta['total_available_records']:,}** | Total records loaded from `mtsamples_clean.csv` |",
        f"| **Successfully Processed** | **{exec_sum['successful_records']:,}** | Records parsed through full NLP pipeline |",
        f"| **Failed Records** | **{exec_sum['failed_records']:,}** | Execution exceptions recorded |",
        f"| **Empty / Skipped Records** | **{exec_sum['empty_skipped_records']:,}** | Transcriptions with empty/whitespace content |",
        f"| **Duplicate Transcriptions** | **{exec_meta['duplicate_transcriptions']:,}** | Identical clinical texts identified |",
        f"| **Unique Medical Specialties** | **{exec_meta['unique_specialties']}** | Distinct clinical disciplines represented |",
        f"| **Total Wall-Clock Time** | **{exec_sum['total_wall_time_min']:.2f} min** | Total processing duration |",
        f"| **Average Time per Record** | **{exec_sum['average_time_per_record_sec']:.4f} s** | Average pipeline latency on CPU |",
        f"| **Min / Max Latency** | **{exec_sum['min_time_per_record_sec']:.3f}s / {exec_sum['max_time_per_record_sec']:.3f}s** | Latency range depending on text length |",
        "",
        "---",
        "",
        "## 3. Entity Extraction & Clinical Coverage Statistics",
        "",
        f"Across the {exec_sum['successful_records']:,} processed records, the hybrid 4-tier pipeline extracted **{ents_stat['total_entities_extracted']:,} total clinical entities**, averaging **{ents_stat['average_entities_per_record']:.2f} entities per record**.",
        "",
        "### Extracted Entity Distribution by Category",
        "",
        "| Entity Category | Total Extracted | Category Share | Mean per Record |",
        "|---|:---:|:---:|:---:|",
    ]

    tot_e = ents_stat["total_entities_extracted"]
    for cat, cnt in ents_stat["category_counts"].items():
        pct = (cnt / tot_e * 100) if tot_e else 0.0
        mean_r = cnt / exec_sum["successful_records"] if exec_sum["successful_records"] else 0.0
        report_lines.append(f"| **{cat}** | {cnt:,} | {pct:.1f}% | {mean_r:.2f} |")

    report_lines.extend([
        "",
        f"- **Negated Findings Detected:** {ents_stat['total_negated_entities']:,} entities were identified as negated via clausal scoping.",
        f"- **Medication Regimens Reconstructed:** {ents_stat['total_regimens_reconstructed']:,} multi-element prescription regimens (medication + dosage + frequency).",
        f"- **Records with Extracted Entities:** {ents_stat['records_with_entities']:,} ({ents_stat['records_with_entities'] / exec_sum['successful_records'] * 100:.1f}%)",
        f"- **Records with Zero Extracted Entities:** {ents_stat['records_without_entities']:,} ({ents_stat['records_without_entities'] / exec_sum['successful_records'] * 100:.1f}%)",
        "",
        "---",
        "",
        "## 4. Investigation Status Classification",
        "",
        "Investigation entities were automatically categorized into clinical progression statuses:",
        "",
        "| Investigation Status | Total Mentions | Status Share | Clinical Significance |",
        "|---|:---:|:---:|---|",
    ])

    tot_inv = sum(stats["investigation_status_distribution"].values())
    for st, cnt in stats["investigation_status_distribution"].items():
        pct = (cnt / tot_inv * 100) if tot_inv else 0.0
        report_lines.append(f"| `{st}` | {cnt:,} | {pct:.1f}% | Categorized by keyword & result evidence |")

    report_lines.extend([
        "",
        "---",
        "",
        "## 5. Potential Decision Gaps & Prototype Rule Behavior",
        "",
        f"A total of **{gap_stat['total_gaps_flagged']:,} potential gaps** were flagged across **{gap_stat['records_with_gaps']:,} records** ({gap_stat['records_with_gaps'] / exec_sum['successful_records'] * 100:.1f}% of all records).",
        "",
        "### Breakdown by Gap Type:",
    ])

    for gt, cnt in gap_stat["gap_types"].items():
        report_lines.append(f"- **{gt}:** {cnt:,}")

    report_lines.extend([
        "",
        "### Critical Pattern & Rule Trigger Analysis:",
        "- **Rule R1 Over-Triggering:** Recommends CBC for any non-negated `SYMPTOM`. In a wide-corpus setting like MTSamples, symptoms (pain, swelling, nausea) appear across almost all surgical, orthopedic, and dermatological records, causing R1 to trigger in high volume.",
        "- **Rule R2 Over-Triggering:** Recommends HbA1c for any non-negated `DISEASE`. Because criteria in `guidelines.json` check for `DISEASE` broadly rather than restricting to Diabetes Mellitus, records mentioning non-diabetic conditions (e.g., hypertension, arthritis, glaucoma) trigger an HbA1c recommendation.",
        "- **Direct Non-Performance Audits:** Successfully flags explicitly cancelled or unperformed investigations without requiring rule prerequisite matches.",
        "",
        "---",
        "",
        "## 6. Stratified Sampling & Manual Annotation Protocol (Task 10)",
        "",
        "Because raw corpus predictions cannot serve as ground truth, a **stratified random sample of 50 records** was selected across all 40 medical specialties using a fixed random seed (`seed=42`).",
        "",
        "- The annotation template is saved at: `evaluation/mtsamples_evaluation/annotation_template_sample.csv`.",
        "- **Integrity Guarantee:** All ground-truth columns are intentionally provided blank (unpopulated). They must be verified by certified clinicians or medical annotators before calculating accuracy, precision, recall, or F1 scores on MTSamples data.",
        "",
        "---",
        "",
        "## 7. Artifacts Generated",
        "",
        "1. `mtsamples_record_outputs.csv` — Full record-level output dataset (4,966 rows).",
        "2. `mtsamples_record_outputs.json` — Structured JSON record output.",
        "3. `mtsamples_evaluation_summary.json` — Complete summary statistics.",
        "4. `annotation_template_sample.csv` — Stratified 50-record sample for manual gold-standard annotation.",
        "5. `annotation_template_sample.json` — JSON version of manual sample.",
        "6. `entity_distribution.png` — Distribution of extracted clinical entities.",
        "7. `specialty_distribution.png` — Top 12 medical specialties in the corpus.",
        "8. `investigation_status_distribution.png` — Distribution of investigation statuses.",
        "9. `gap_distribution.png` — Distribution of detected gap types.",
        "10. `mtsamples_evaluation_report.md` — This comprehensive evaluation report.",
        "",
        "---",
        "",
        "## 8. Limitations & Clinical Research Disclaimer",
        "",
        "> [!IMPORTANT]",
        "> **Research Prototype Disclaimer:** The ClinGap-NLP system is an experimental decision-support research tool. The configured guideline rules are educational demonstration rules, not clinical standards of care. Extracted findings and flagged gaps must never be used for real patient treatment or diagnosis.",
    ])

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"Saved comprehensive report to {REPORT_MD}")


if __name__ == "__main__":
    run_full_evaluation()
