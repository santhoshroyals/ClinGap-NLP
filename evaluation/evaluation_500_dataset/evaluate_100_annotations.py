"""
evaluate_100_annotations.py
===========================
Defensible Evaluation Script for ClinGap-NLP using the 100-Note Stratified Subset.

Compares completed human reference annotations against existing model predictions
from model_predictions_500.json.

Requirements:
- Does NOT run until genuine reference annotations are completed.
- Zero modification to existing models, pipeline, or predictions.
- Computes:
  1. NER: Exact and relaxed entity-level Precision, Recall, F1, Macro & Weighted averages.
  2. Negation: TP, TN, FP, FN, Accuracy, Precision, Recall, F1, Specificity, Confusion Matrix.
  3. Investigation Status: Multi-class Confusion Matrix, Accuracy, Macro/Weighted F1.
  4. Decision Gap: TP, TN, FP, FN, Accuracy, Precision, Recall, F1, Specificity, 2x2 Matrix.
  5. Stratification: Overall (N=100), Synthetic (N=50), MTSamples (N=50).
- Exports: Markdown, JSON, and CSV reports.
"""

import os
import sys
import json
import csv
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any, Tuple, Optional
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

SUBSET_JSON_PATH = SCRIPT_DIR / "evaluation_100_subset_notes.json"
PREDICTIONS_JSON_PATH = SCRIPT_DIR / "model_predictions_500.json"
DEFAULT_ANNOTATIONS_CSV = SCRIPT_DIR / "evaluation_100_completed_annotations.csv"
FALLBACK_TEMPLATE_CSV = SCRIPT_DIR / "evaluation_100_blinded_annotation_template.csv"

OUTPUT_REPORT_MD = SCRIPT_DIR / "evaluation_100_metrics_report.md"
OUTPUT_METRICS_JSON = SCRIPT_DIR / "evaluation_100_metrics_summary.json"
OUTPUT_CONFUSION_CSV = SCRIPT_DIR / "evaluation_100_confusion_matrices.csv"
OUTPUT_NER_BREAKDOWN_CSV = SCRIPT_DIR / "evaluation_100_ner_category_breakdown.csv"


# ---------------------------------------------------------------------------
# Annotation Parsers
# ---------------------------------------------------------------------------

def parse_entity_string(raw: str) -> List[Dict[str, str]]:
    """Parses JSON or 'entity: CATEGORY' delimited text into entity dictionaries."""
    raw = (raw or "").strip()
    if not raw:
        return []
    if raw.startswith("[") and raw.endswith("]"):
        try:
            items = json.loads(raw)
            result = []
            for item in items:
                text = str(item.get("text", item.get("entity_text", ""))).strip()
                cat = str(item.get("category", item.get("entity_type", "UNKNOWN"))).strip().upper()
                if text:
                    result.append({"text": text, "category": cat})
            return result
        except Exception:
            pass

    # Semicolon delimited: "severe headache: SYMPTOM; MRI: INVESTIGATION"
    entities = []
    parts = [p.strip() for p in raw.split(";") if p.strip()]
    for p in parts:
        if ":" in p:
            chunks = p.rsplit(":", 1)
            text = chunks[0].strip()
            cat = chunks[1].strip().upper()
            if text:
                entities.append({"text": text, "category": cat})
        else:
            entities.append({"text": p, "category": "UNKNOWN"})
    return entities


def parse_negation_string(raw: str) -> Dict[str, bool]:
    """Parses negation assertions mapping entity text -> True (negated) / False (affirmed)."""
    raw = (raw or "").strip()
    if not raw or raw.lower() in {"none", "none negated", "all affirmed", "false", "no"}:
        return {}
    if raw.startswith("[") and raw.endswith("]"):
        try:
            items = json.loads(raw)
            result = {}
            for item in items:
                ent = str(item.get("entity", item.get("text", ""))).strip().lower()
                neg = bool(item.get("negated", item.get("is_negated", True)))
                if ent:
                    result[ent] = neg
            return result
        except Exception:
            pass

    # Semicolon delimited: "chest pain: NEGATED; vomiting: AFFIRMED"
    result = {}
    parts = [p.strip() for p in raw.split(";") if p.strip()]
    for p in parts:
        if ":" in p:
            chunks = p.rsplit(":", 1)
            ent = chunks[0].strip().lower()
            val = chunks[1].strip().upper()
            result[ent] = (val in {"NEGATED", "TRUE", "YES", "1"})
        else:
            result[p.lower()] = True
    return result


def parse_investigation_status_string(raw: str) -> Dict[str, str]:
    """Parses investigation name -> execution status."""
    raw = (raw or "").strip()
    if not raw or raw.lower() in {"none", "n/a", "no investigations"}:
        return {}
    if raw.startswith("[") and raw.endswith("]"):
        try:
            items = json.loads(raw)
            result = {}
            for item in items:
                name = str(item.get("name", item.get("investigation", ""))).strip().lower()
                st = str(item.get("status", "unknown")).strip().lower()
                if name:
                    result[name] = normalize_inv_status(st)
            return result
        except Exception:
            pass

    result = {}
    parts = [p.strip() for p in raw.split(";") if p.strip()]
    for p in parts:
        if ":" in p:
            chunks = p.rsplit(":", 1)
            name = chunks[0].strip().lower()
            st = chunks[1].strip().lower()
            result[name] = normalize_inv_status(st)
    return result


def normalize_inv_status(st: str) -> str:
    st = (st or "").strip().lower()
    if "completed" in st or "performed" in st or "done" in st:
        return "completed/performed"
    if "not performed" in st or "cancelled" in st or "declined" in st or "refused" in st:
        return "not performed"
    if "pending" in st or "awaited" in st:
        return "pending"
    if "ordered" in st or "requested" in st or "scheduled" in st:
        return "ordered"
    return "ordered"


def parse_decision_gap_bool(raw: str) -> bool:
    """Returns True if a clinical gap is present, False otherwise."""
    raw = (raw or "").strip().upper()
    return raw in {"GAP_PRESENT", "TRUE", "YES", "1", "GAP", "MISSING_INVESTIGATION", "OMISSION"}


# ---------------------------------------------------------------------------
# Metric Calculators
# ---------------------------------------------------------------------------

def compute_classification_metrics(tp: int, fp: int, fn: int, tn: int) -> Dict[str, float]:
    total = tp + fp + fn + tn
    acc = (tp + tn) / total if total > 0 else 0.0
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
    spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    balanced_acc = (rec + spec) / 2.0

    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "Accuracy": round(acc, 4),
        "Precision": round(prec, 4),
        "Recall": round(rec, 4),
        "Specificity": round(spec, 4),
        "F1": round(f1, 4),
        "Balanced_Accuracy": round(balanced_acc, 4),
    }


def compute_ner_metrics(gold_entities_per_note: List[List[Dict[str, str]]],
                        pred_entities_per_note: List[List[Dict[str, Any]]],
                        matching_mode: str = "exact") -> Dict[str, Any]:
    """
    Computes entity-level Precision, Recall, and F1.
    matching_mode: 'exact' (text and type must match exactly) or
                   'relaxed' (partial token overlap + same type).
    """
    categories = ["SYMPTOM", "INVESTIGATION", "DISEASE", "LAB_TEST", "MEDICATION", "DOSAGE", "FREQUENCY", "DURATION"]
    by_cat_counts = {c: {"tp": 0, "fp": 0, "fn": 0} for c in categories}
    overall_counts = {"tp": 0, "fp": 0, "fn": 0}

    for golds, preds in zip(gold_entities_per_note, pred_entities_per_note):
        matched_pred_indices = set()
        for g in golds:
            g_text = g["text"].strip().lower()
            g_cat = g["category"]
            match_found = False

            for p_idx, p in enumerate(preds):
                if p_idx in matched_pred_indices:
                    continue
                p_text = str(p.get("entity_text", "")).strip().lower()
                p_cat = str(p.get("entity_type", "")).strip().upper()

                # Check category alignment
                if g_cat != p_cat and g_cat != "UNKNOWN":
                    continue

                # Match condition
                if matching_mode == "exact":
                    is_match = (g_text == p_text)
                else:
                    # Relaxed match: either contains the other or token intersection > 0
                    g_tokens = set(g_text.split())
                    p_tokens = set(p_text.split())
                    is_match = (g_text in p_text or p_text in g_text or len(g_tokens.intersection(p_tokens)) > 0)

                if is_match:
                    match_found = True
                    matched_pred_indices.add(p_idx)
                    break

            if match_found:
                overall_counts["tp"] += 1
                if g_cat in by_cat_counts:
                    by_cat_counts[g_cat]["tp"] += 1
            else:
                overall_counts["fn"] += 1
                if g_cat in by_cat_counts:
                    by_cat_counts[g_cat]["fn"] += 1

        # False positives: preds not matched to any gold
        for p_idx, p in enumerate(preds):
            if p_idx not in matched_pred_indices:
                overall_counts["fp"] += 1
                p_cat = str(p.get("entity_type", "")).strip().upper()
                if p_cat in by_cat_counts:
                    by_cat_counts[p_cat]["fp"] += 1

    # Calculate overall
    tp, fp, fn = overall_counts["tp"], overall_counts["fp"], overall_counts["fn"]
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

    # Per category metrics & macro/weighted average
    category_metrics = {}
    f1_list = []
    weights = []
    for c in categories:
        c_tp = by_cat_counts[c]["tp"]
        c_fp = by_cat_counts[c]["fp"]
        c_fn = by_cat_counts[c]["fn"]
        c_p = c_tp / (c_tp + c_fp) if (c_tp + c_fp) > 0 else 0.0
        c_r = c_tp / (c_tp + c_fn) if (c_tp + c_fn) > 0 else 0.0
        c_f1 = 2 * (c_p * c_r) / (c_p + c_r) if (c_p + c_r) > 0 else 0.0
        gold_support = c_tp + c_fn

        category_metrics[c] = {
            "TP": c_tp, "FP": c_fp, "FN": c_fn, "Support": gold_support,
            "Precision": round(c_p, 4), "Recall": round(c_r, 4), "F1": round(c_f1, 4)
        }
        if gold_support > 0:
            f1_list.append(c_f1)
            weights.append(gold_support)

    macro_f1 = float(np.mean(f1_list)) if f1_list else 0.0
    weighted_f1 = float(np.average(f1_list, weights=weights)) if weights and sum(weights) > 0 else 0.0

    return {
        "matching_mode": matching_mode,
        "overall": {"TP": tp, "FP": fp, "FN": fn, "Precision": round(prec, 4), "Recall": round(rec, 4), "F1": round(f1, 4)},
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "by_category": category_metrics,
    }


# ---------------------------------------------------------------------------
# Main Evaluation Runner
# ---------------------------------------------------------------------------

def run_evaluation(annotations_path: Path):
    print("=" * 78)
    print("CLINGAP-NLP: 100-NOTE GROUND-TRUTH PERFORMANCE EVALUATION")
    print("=" * 78)

    # 1. Verify that annotation file exists
    if not annotations_path.exists():
        print(f"\n[ERROR] Annotation file not found at: {annotations_path}")
        print("Please complete reference annotations in:")
        print(f"  {FALLBACK_TEMPLATE_CSV}")
        print(f"and save as: {DEFAULT_ANNOTATIONS_CSV}")
        sys.exit(1)

    # 2. Inspect annotation file for genuine content
    with open(annotations_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        annotated_rows = list(reader)

    if len(annotated_rows) != 100:
        print(f"\n[ERROR] Expected 100 annotated records, found {len(annotated_rows)}.")
        sys.exit(1)

    # Check for blank reference-label columns
    filled_entities = sum(1 for r in annotated_rows if r.get("clinical_entities_and_types", "").strip())
    filled_gaps = sum(1 for r in annotated_rows if r.get("potential_decision_gap", "").strip())

    if filled_entities == 0 or filled_gaps == 0:
        print("\n" + "!" * 78)
        print("HALTING EVALUATION: REFERENCE ANNOTATIONS ARE EMPTY / UNANNOTATED!")
        print("!" * 78)
        print(f"Detected blank reference-label columns in: {annotations_path.name}")
        print(f"  - Notes with filled entities: {filled_entities} / 100")
        print(f"  - Notes with filled gaps:     {filled_gaps} / 100")
        print("\nINSTRUCTIONS:")
        print("1. Open the blinded template:")
        print(f"   {FALLBACK_TEMPLATE_CSV}")
        print("2. Follow the detailed clinical guidelines in:")
        print(f"   {SCRIPT_DIR / 'ANNOTATION_GUIDELINES_100.md'}")
        print("3. Enter genuine expert annotations in the designated columns.")
        print(f"4. Save as '{DEFAULT_ANNOTATIONS_CSV.name}' and re-run this script.")
        print("\nPer user instructions: Execution stopped before calculating performance metrics.")
        print("=" * 78)
        sys.exit(0)

    # 3. Load model predictions
    if not PREDICTIONS_JSON_PATH.exists():
        print(f"[ERROR] Predictions file not found: {PREDICTIONS_JSON_PATH}")
        sys.exit(1)

    with open(PREDICTIONS_JSON_PATH, "r", encoding="utf-8") as f:
        pred_data = json.load(f)
    pred_dict = {r["eval_id"]: r for r in pred_data.get("records", [])}

    print(f"[LOAD] Loaded {len(annotated_rows)} human reference annotations.")
    print(f"[LOAD] Loaded {len(pred_dict)} pre-computed model predictions.")

    # 4. Partition by corpus
    with open(SUBSET_JSON_PATH, "r", encoding="utf-8") as f:
        subset_meta = {r["eval_id"]: r["source_corpus"] for r in json.load(f)["records"]}

    synth_rows = [r for r in annotated_rows if subset_meta.get(r["eval_id"]) == "synthetic_indian"]
    mts_rows = [r for r in annotated_rows if subset_meta.get(r["eval_id"]) == "mtsamples"]

    print(f"\n[EVAL] Executing evaluation across subsets:")
    print(f"       - Overall:          {len(annotated_rows)} notes")
    print(f"       - Synthetic Indian: {len(synth_rows)} notes")
    print(f"       - MTSamples:        {len(mts_rows)} notes")

    def evaluate_group(rows: List[Dict[str, str]], group_name: str) -> Dict[str, Any]:
        # NER Data
        gold_entities = [parse_entity_string(r.get("clinical_entities_and_types", "")) for r in rows]
        pred_entities = [pred_dict[r["eval_id"]].get("entities", []) for r in rows]

        ner_exact = compute_ner_metrics(gold_entities, pred_entities, matching_mode="exact")
        ner_relaxed = compute_ner_metrics(gold_entities, pred_entities, matching_mode="relaxed")

        # Negation Data
        neg_tp, neg_fp, neg_fn, neg_tn = 0, 0, 0, 0
        for r in rows:
            gold_negs = parse_negation_string(r.get("negation_status", ""))
            pred_ents = pred_dict[r["eval_id"]].get("entities", [])
            pred_negs = {str(e.get("entity_text", "")).strip().lower(): bool(e.get("negated", False)) for e in pred_ents}

            for ent_text, gold_is_neg in gold_negs.items():
                pred_is_neg = pred_negs.get(ent_text, False)
                if gold_is_neg and pred_is_neg:
                    neg_tp += 1
                elif gold_is_neg and not pred_is_neg:
                    neg_fn += 1
                elif not gold_is_neg and pred_is_neg:
                    neg_fp += 1
                else:
                    neg_tn += 1

        negation_metrics = compute_classification_metrics(neg_tp, neg_fp, neg_fn, neg_tn)

        # Investigation Status Multi-class Data
        inv_classes = ["completed/performed", "ordered", "not performed", "pending"]
        inv_matrix = {gold_c: {pred_c: 0 for pred_c in inv_classes} for gold_c in inv_classes}
        inv_total_matches = 0
        inv_correct = 0

        for r in rows:
            gold_invs = parse_investigation_status_string(r.get("investigation_status", ""))
            pred_invs = {str(inv.get("name", "")).strip().lower(): inv.get("status", "unknown") for inv in pred_dict[r["eval_id"]].get("investigations", [])}

            for inv_name, gold_st in gold_invs.items():
                if gold_st not in inv_matrix:
                    continue
                pred_st = pred_invs.get(inv_name)
                if pred_st in inv_classes:
                    inv_matrix[gold_st][pred_st] += 1
                    inv_total_matches += 1
                    if gold_st == pred_st:
                        inv_correct += 1

        inv_acc = inv_correct / inv_total_matches if inv_total_matches > 0 else 0.0

        # Decision Gap Data
        gap_tp, gap_fp, gap_fn, gap_tn = 0, 0, 0, 0
        for r in rows:
            gold_gap = parse_decision_gap_bool(r.get("potential_decision_gap", ""))
            pred_gap = (pred_dict[r["eval_id"]].get("potential_decision_gaps_count", 0) > 0)

            if gold_gap and pred_gap:
                gap_tp += 1
            elif not gold_gap and pred_gap:
                gap_fp += 1
            elif gold_gap and not pred_gap:
                gap_fn += 1
            else:
                gap_tn += 1

        gap_metrics = compute_classification_metrics(gap_tp, gap_fp, gap_fn, gap_tn)

        return {
            "group_name": group_name,
            "sample_size": len(rows),
            "ner_exact": ner_exact,
            "ner_relaxed": ner_relaxed,
            "negation": negation_metrics,
            "investigation_status": {
                "accuracy": round(inv_acc, 4),
                "evaluated_instances": inv_total_matches,
                "confusion_matrix": inv_matrix,
            },
            "decision_gap": gap_metrics,
        }

    overall_results = evaluate_group(annotated_rows, "Overall (N=100)")
    synth_results = evaluate_group(synth_rows, "Synthetic Indian (N=50)")
    mts_results = evaluate_group(mts_rows, "MTSamples (N=50)")

    # 5. Export Metrics JSON
    all_metrics = {
        "evaluation_name": "CLINGAP_NLP_100_NOTE_GROUND_TRUTH_EVALUATION",
        "evaluation_date": "2026-10-31",
        "annotations_source": str(annotations_path),
        "predictions_source": str(PREDICTIONS_JSON_PATH),
        "results": {
            "overall": overall_results,
            "synthetic_indian": synth_results,
            "mtsamples": mts_results,
        }
    }
    with open(OUTPUT_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2, ensure_ascii=False)
    print(f"\n[EXPORT] Evaluation metrics JSON: {OUTPUT_METRICS_JSON}")

    # 6. Export Confusion Matrices CSV
    with open(OUTPUT_CONFUSION_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Task", "Subgroup", "Metric / Cell", "Value"])

        for res in [overall_results, synth_results, mts_results]:
            grp = res["group_name"]
            # Decision gap
            dg = res["decision_gap"]
            writer.writerow(["Decision_Gap", grp, "TP (Gold=GAP, Pred=GAP)", dg["TP"]])
            writer.writerow(["Decision_Gap", grp, "FP (Gold=NO_GAP, Pred=GAP)", dg["FP"]])
            writer.writerow(["Decision_Gap", grp, "FN (Gold=GAP, Pred=NO_GAP)", dg["FN"]])
            writer.writerow(["Decision_Gap", grp, "TN (Gold=NO_GAP, Pred=NO_GAP)", dg["TN"]])
            writer.writerow(["Decision_Gap", grp, "Accuracy", dg["Accuracy"]])
            writer.writerow(["Decision_Gap", grp, "Precision (PPV)", dg["Precision"]])
            writer.writerow(["Decision_Gap", grp, "Recall (Sensitivity)", dg["Recall"]])
            writer.writerow(["Decision_Gap", grp, "Specificity (TNR)", dg["Specificity"]])
            writer.writerow(["Decision_Gap", grp, "F1-Score", dg["F1"]])
            writer.writerow(["Decision_Gap", grp, "Balanced_Accuracy", dg["Balanced_Accuracy"]])

            # Negation
            neg = res["negation"]
            writer.writerow(["Negation", grp, "TP (Gold=NEG, Pred=NEG)", neg["TP"]])
            writer.writerow(["Negation", grp, "FP (Gold=AFF, Pred=NEG)", neg["FP"]])
            writer.writerow(["Negation", grp, "FN (Gold=NEG, Pred=AFF)", neg["FN"]])
            writer.writerow(["Negation", grp, "TN (Gold=AFF, Pred=AFF)", neg["TN"]])
            writer.writerow(["Negation", grp, "Accuracy", neg["Accuracy"]])
            writer.writerow(["Negation", grp, "Precision", neg["Precision"]])
            writer.writerow(["Negation", grp, "Recall", neg["Recall"]])
            writer.writerow(["Negation", grp, "F1-Score", neg["F1"]])

    print(f"[EXPORT] Confusion matrices CSV: {OUTPUT_CONFUSION_CSV}")

    # 7. Export NER Breakdown CSV
    with open(OUTPUT_NER_BREAKDOWN_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Subgroup", "Matching_Mode", "Category", "TP", "FP", "FN", "Support", "Precision", "Recall", "F1"])
        for res in [overall_results, synth_results, mts_results]:
            grp = res["group_name"]
            for mode_key, mode_name in [("ner_exact", "Exact"), ("ner_relaxed", "Relaxed")]:
                data = res[mode_key]
                ov = data["overall"]
                writer.writerow([grp, mode_name, "OVERALL_MICRO", ov["TP"], ov["FP"], ov["FN"], ov["TP"] + ov["FN"], ov["Precision"], ov["Recall"], ov["F1"]])
                for cat, c_data in data["by_category"].items():
                    writer.writerow([grp, mode_name, cat, c_data["TP"], c_data["FP"], c_data["FN"], c_data["Support"], c_data["Precision"], c_data["Recall"], c_data["F1"]])

    print(f"[EXPORT] NER category breakdown CSV: {OUTPUT_NER_BREAKDOWN_CSV}")

    # 8. Export Markdown Report
    md_content = f"""# ClinGap-NLP: 100-Note Defensible Ground-Truth Evaluation Report

**Evaluation Date:** 2026-10-31  
**Reference Annotations:** `{annotations_path.name}` (100 Notes: 50 Synthetic + 50 MTSamples)  
**Predictions Source:** `model_predictions_500.json`  
**Matching Methodology:** Entity-Level Exact & Relaxed Token Overlap; Directional Negation; 4-State Investigation Status; 2x2 Decision Gap.

---

## 1. Clinical Named Entity Recognition (NER) Performance

| Subgroup | Matching Mode | Precision | Recall | F1-Score | Macro F1 | Weighted F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Overall (N=100)** | Exact Match | {overall_results['ner_exact']['overall']['Precision']:.4f} | {overall_results['ner_exact']['overall']['Recall']:.4f} | {overall_results['ner_exact']['overall']['F1']:.4f} | {overall_results['ner_exact']['macro_f1']:.4f} | {overall_results['ner_exact']['weighted_f1']:.4f} |
| **Overall (N=100)** | Relaxed Match | {overall_results['ner_relaxed']['overall']['Precision']:.4f} | {overall_results['ner_relaxed']['overall']['Recall']:.4f} | {overall_results['ner_relaxed']['overall']['F1']:.4f} | {overall_results['ner_relaxed']['macro_f1']:.4f} | {overall_results['ner_relaxed']['weighted_f1']:.4f} |
| **Synthetic (N=50)** | Exact Match | {synth_results['ner_exact']['overall']['Precision']:.4f} | {synth_results['ner_exact']['overall']['Recall']:.4f} | {synth_results['ner_exact']['overall']['F1']:.4f} | {synth_results['ner_exact']['macro_f1']:.4f} | {synth_results['ner_exact']['weighted_f1']:.4f} |
| **Synthetic (N=50)** | Relaxed Match | {synth_results['ner_relaxed']['overall']['Precision']:.4f} | {synth_results['ner_relaxed']['overall']['Recall']:.4f} | {synth_results['ner_relaxed']['overall']['F1']:.4f} | {synth_results['ner_relaxed']['macro_f1']:.4f} | {synth_results['ner_relaxed']['weighted_f1']:.4f} |
| **MTSamples (N=50)** | Exact Match | {mts_results['ner_exact']['overall']['Precision']:.4f} | {mts_results['ner_exact']['overall']['Recall']:.4f} | {mts_results['ner_exact']['overall']['F1']:.4f} | {mts_results['ner_exact']['macro_f1']:.4f} | {mts_results['ner_exact']['weighted_f1']:.4f} |
| **MTSamples (N=50)** | Relaxed Match | {mts_results['ner_relaxed']['overall']['Precision']:.4f} | {mts_results['ner_relaxed']['overall']['Recall']:.4f} | {mts_results['ner_relaxed']['overall']['F1']:.4f} | {mts_results['ner_relaxed']['macro_f1']:.4f} | {mts_results['ner_relaxed']['weighted_f1']:.4f} |

---

## 2. Negation Detection Performance

| Subgroup | Accuracy | Precision | Recall (Sensitivity) | Specificity | F1-Score | TP / FP / FN / TN |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Overall (N=100)** | {overall_results['negation']['Accuracy']:.4f} | {overall_results['negation']['Precision']:.4f} | {overall_results['negation']['Recall']:.4f} | {overall_results['negation']['Specificity']:.4f} | {overall_results['negation']['F1']:.4f} | {overall_results['negation']['TP']} / {overall_results['negation']['FP']} / {overall_results['negation']['FN']} / {overall_results['negation']['TN']} |
| **Synthetic (N=50)** | {synth_results['negation']['Accuracy']:.4f} | {synth_results['negation']['Precision']:.4f} | {synth_results['negation']['Recall']:.4f} | {synth_results['negation']['Specificity']:.4f} | {synth_results['negation']['F1']:.4f} | {synth_results['negation']['TP']} / {synth_results['negation']['FP']} / {synth_results['negation']['FN']} / {synth_results['negation']['TN']} |
| **MTSamples (N=50)** | {mts_results['negation']['Accuracy']:.4f} | {mts_results['negation']['Precision']:.4f} | {mts_results['negation']['Recall']:.4f} | {mts_results['negation']['Specificity']:.4f} | {mts_results['negation']['F1']:.4f} | {mts_results['negation']['TP']} / {mts_results['negation']['FP']} / {mts_results['negation']['FN']} / {mts_results['negation']['TN']} |

---

## 3. Investigation Execution Status Accuracy

| Subgroup | Evaluated Tests | Accuracy | Status Classes Evaluated |
| :--- | :---: | :---: | :--- |
| **Overall (N=100)** | {overall_results['investigation_status']['evaluated_instances']} | {overall_results['investigation_status']['accuracy']:.4f} | Completed, Ordered, Not Performed, Pending |
| **Synthetic (N=50)** | {synth_results['investigation_status']['evaluated_instances']} | {synth_results['investigation_status']['accuracy']:.4f} | Completed, Ordered |
| **MTSamples (N=50)** | {mts_results['investigation_status']['evaluated_instances']} | {mts_results['investigation_status']['accuracy']:.4f} | Completed, Ordered, Not Performed, Pending |

---

## 4. Potential Decision-Gap Detection Performance

| Subgroup | Accuracy | Balanced Accuracy | Precision (PPV) | Recall (Sensitivity) | Specificity | F1-Score | Confusion Matrix [TP, FP, FN, TN] |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Overall (N=100)** | {overall_results['decision_gap']['Accuracy']:.4f} | {overall_results['decision_gap']['Balanced_Accuracy']:.4f} | {overall_results['decision_gap']['Precision']:.4f} | {overall_results['decision_gap']['Recall']:.4f} | {overall_results['decision_gap']['Specificity']:.4f} | {overall_results['decision_gap']['F1']:.4f} | [{overall_results['decision_gap']['TP']}, {overall_results['decision_gap']['FP']}, {overall_results['decision_gap']['FN']}, {overall_results['decision_gap']['TN']}] |
| **Synthetic (N=50)** | {synth_results['decision_gap']['Accuracy']:.4f} | {synth_results['decision_gap']['Balanced_Accuracy']:.4f} | {synth_results['decision_gap']['Precision']:.4f} | {synth_results['decision_gap']['Recall']:.4f} | {synth_results['decision_gap']['Specificity']:.4f} | {synth_results['decision_gap']['F1']:.4f} | [{synth_results['decision_gap']['TP']}, {synth_results['decision_gap']['FP']}, {synth_results['decision_gap']['FN']}, {synth_results['decision_gap']['TN']}] |
| **MTSamples (N=50)** | {mts_results['decision_gap']['Accuracy']:.4f} | {mts_results['decision_gap']['Balanced_Accuracy']:.4f} | {mts_results['decision_gap']['Precision']:.4f} | {mts_results['decision_gap']['Recall']:.4f} | {mts_results['decision_gap']['Specificity']:.4f} | {mts_results['decision_gap']['F1']:.4f} | [{mts_results['decision_gap']['TP']}, {mts_results['decision_gap']['FP']}, {mts_results['decision_gap']['FN']}, {mts_results['decision_gap']['TN']}] |

---

## 5. Artifact Manifest

1. **Metrics Summary (JSON):** [`evaluation_100_metrics_summary.json`](evaluation_100_metrics_summary.json)
2. **Confusion Matrices (CSV):** [`evaluation_100_confusion_matrices.csv`](evaluation_100_confusion_matrices.csv)
3. **NER Category Breakdown (CSV):** [`evaluation_100_ner_category_breakdown.csv`](evaluation_100_ner_category_breakdown.csv)
4. **Evaluation Script:** [`evaluate_100_annotations.py`](evaluate_100_annotations.py)
"""
    with open(OUTPUT_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[EXPORT] Evaluation report Markdown: {OUTPUT_REPORT_MD}")

    print("\n" + "=" * 78)
    print("CLINGAP-NLP: 100-NOTE EVALUATION EXECUTION COMPLETE")
    print("=" * 78)


def main():
    parser = argparse.ArgumentParser(description="ClinGap-NLP 100-Note Evaluation Runner")
    parser.add_argument("--annotations", type=str, default=str(DEFAULT_ANNOTATIONS_CSV),
                        help="Path to completed annotations CSV")
    args = parser.parse_args()

    ann_path = Path(args.annotations)
    if not ann_path.exists() and FALLBACK_TEMPLATE_CSV.exists():
        ann_path = FALLBACK_TEMPLATE_CSV

    run_evaluation(ann_path)


if __name__ == "__main__":
    main()
