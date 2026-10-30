"""
run_evaluation.py - Comprehensive Evaluation Runner for ClinGap-NLP
Implements Tasks 3, 4, 5, 6, 7 of the Evaluation Matrix.
Executes the real application pipeline, records actual predictions separately,
and computes gap detection, NER, and status metrics without modifying application logic.
"""

import os
import sys
import json
import csv
from typing import Dict, List, Any, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Ensure clinngap_nlp root is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.services.clinical_pipeline import ClinicalPipeline


def normalize_str(s: Any) -> str:
    if s is None:
        return ""
    return str(s).strip().lower()


def run_evaluation():
    print("=" * 70)
    print("ClinGap-NLP Evaluation Matrix: Running Automated Evaluation Pipeline")
    print("=" * 70)

    eval_dir = os.path.join(BASE_DIR, "evaluation")
    gt_path = os.path.join(eval_dir, "ground_truth.json")
    if not os.path.exists(gt_path):
        raise FileNotFoundError(f"Ground truth not found at {gt_path}")

    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth_cases = json.load(f)

    print(f"Loaded {len(ground_truth_cases)} ground-truth cases from {gt_path}")

    # Initialize the production clinical pipeline
    print("Initializing ClinicalPipeline...")
    pipeline = ClinicalPipeline()

    actual_predictions = []
    case_comparisons = []

    # Counters for binary gap evaluation (supported cases only)
    tp_gap = 0
    tn_gap = 0
    fp_gap = 0
    fn_gap = 0
    unsupported_count = 0
    supported_count = 0

    # Counters for NER evaluation
    ner_overall = {"tp": 0, "fp": 0, "fn": 0}
    ner_by_type = {}

    # Counters for Negation evaluation
    neg_tp = 0  # correctly flagged negated
    neg_tn = 0  # correctly flagged non-negated
    neg_fp = 0  # falsely flagged negated
    neg_fn = 0  # missed negation

    # Investigation status comparison
    inv_status_total = 0
    inv_status_correct = 0
    inv_status_breakdown = {}

    for case in ground_truth_cases:
        cid = case["test_case_id"]
        category = case["category"]
        is_supported = case["is_supported"]
        note = case["clinical_note"]
        expected_gap = case["expected_gap"]
        expected_ents = case.get("expected_entities", [])
        expected_negs = case.get("expected_negations", [])
        expected_invs = case.get("expected_investigations", [])

        print(f"Processing {cid} [{category}] (Supported: {is_supported})...")

        # Execute actual production pipeline
        result = pipeline.run(db=None, text=note)

        actual_ents = result.get("entities", [])
        actual_gaps = result.get("gaps", [])
        actual_regimens = result.get("regimens", [])
        actual_confidence = result.get("confidence", 0.0)

        # In ClinGap-NLP, a gap exists if actual_gaps is non-empty
        has_actual_gap = len(actual_gaps) > 0

        # Save actual predictions record
        pred_record = {
            "test_case_id": cid,
            "category": category,
            "is_supported": is_supported,
            "clinical_note": note,
            "actual_gap_detected": has_actual_gap,
            "actual_gap_count": len(actual_gaps),
            "actual_gaps": actual_gaps,
            "actual_entities_count": len(actual_ents),
            "actual_entities": actual_ents,
            "actual_regimens": actual_regimens,
            "actual_confidence": actual_confidence,
            "context_info": result.get("context_info", {}),
        }
        actual_predictions.append(pred_record)

        # Gap detection evaluation
        gap_outcome = "UNSUPPORTED"
        if is_supported:
            supported_count += 1
            if expected_gap is True and has_actual_gap is True:
                tp_gap += 1
                gap_outcome = "TP"
            elif expected_gap is False and has_actual_gap is False:
                tn_gap += 1
                gap_outcome = "TN"
            elif expected_gap is False and has_actual_gap is True:
                fp_gap += 1
                gap_outcome = "FP"
            elif expected_gap is True and has_actual_gap is False:
                fn_gap += 1
                gap_outcome = "FN"
        else:
            unsupported_count += 1

        # Case-level comparison summary
        case_comp = {
            "test_case_id": cid,
            "category": category,
            "is_supported": is_supported,
            "expected_gap": expected_gap if is_supported else "N/A",
            "actual_gap": has_actual_gap,
            "gap_outcome": gap_outcome,
            "expected_entities_count": len(expected_ents),
            "actual_entities_count": len(actual_ents),
            "actual_gap_entities": "; ".join([g.get("entity", "") for g in actual_gaps]),
            "applicable_rule_id": case.get("applicable_rule_id"),
        }
        case_comparisons.append(case_comp)

        # NER Evaluation
        # Matching tuple: (entity_type, normalized_value)
        gt_tuples = set()
        for e in expected_ents:
            etype = e["entity_type"].upper()
            val = normalize_str(e.get("normalized_value") or e.get("entity_text"))
            gt_tuples.add((etype, val))

        act_tuples = set()
        for e in actual_ents:
            etype = e["entity_type"].upper()
            val = normalize_str(e.get("normalized_value") or e.get("entity_text"))
            act_tuples.add((etype, val))

        matched_tuples = gt_tuples.intersection(act_tuples)
        fp_tuples = act_tuples - gt_tuples
        fn_tuples = gt_tuples - act_tuples

        ner_overall["tp"] += len(matched_tuples)
        ner_overall["fp"] += len(fp_tuples)
        ner_overall["fn"] += len(fn_tuples)

        # Group by entity type
        all_types = {t[0] for t in gt_tuples.union(act_tuples)}
        for t in all_types:
            if t not in ner_by_type:
                ner_by_type[t] = {"tp": 0, "fp": 0, "fn": 0}
            t_gt = {x for x in gt_tuples if x[0] == t}
            t_act = {x for x in act_tuples if x[0] == t}
            ner_by_type[t]["tp"] += len(t_gt.intersection(t_act))
            ner_by_type[t]["fp"] += len(t_act - t_gt)
            ner_by_type[t]["fn"] += len(t_gt - t_act)

        # Negation Evaluation
        for e_neg in expected_negs:
            exp_text = normalize_str(e_neg["entity_text"])
            exp_is_neg = e_neg["negated"]
            # find matching entity in actual_ents
            matching_act = [
                a for a in actual_ents
                if normalize_str(a.get("entity_text")) == exp_text
                or normalize_str(a.get("normalized_value")) == exp_text
            ]
            if matching_act:
                act_is_neg = any(a.get("negated", False) for a in matching_act)
                if exp_is_neg and act_is_neg:
                    neg_tp += 1
                elif not exp_is_neg and not act_is_neg:
                    neg_tn += 1
                elif not exp_is_neg and act_is_neg:
                    neg_fp += 1
                elif exp_is_neg and not act_is_neg:
                    neg_fn += 1

        # Investigation Status Evaluation
        for e_inv in expected_invs:
            exp_inv_text = normalize_str(e_inv["entity_text"])
            exp_status = e_inv["status"]
            if exp_status == "undocumented":
                continue  # not explicitly in text
            inv_status_total += 1
            if exp_status not in inv_status_breakdown:
                inv_status_breakdown[exp_status] = {"total": 0, "correct": 0}
            inv_status_breakdown[exp_status]["total"] += 1

            # Find matching actual investigation
            matching_act_inv = [
                a for a in actual_ents
                if a.get("entity_type") == "INVESTIGATION" and (
                    normalize_str(a.get("entity_text")) == exp_inv_text
                    or normalize_str(a.get("normalized_value")) == exp_inv_text
                )
            ]
            if matching_act_inv:
                act_status = matching_act_inv[0].get("status", "unknown")
                # Handle status synonym equivalence e.g. pending vs ORDERED/PENDING
                is_correct = False
                if exp_status == act_status:
                    is_correct = True
                elif exp_status == "pending" and act_status in {"pending", "ORDERED/PENDING"}:
                    is_correct = True
                elif exp_status == "ordered" and act_status in {"ordered", "ORDERED/PENDING"}:
                    is_correct = True
                elif exp_status == "completed/performed" and act_status == "completed/performed":
                    is_correct = True
                elif exp_status in {"not performed", "cancelled"} and act_status in {"not performed", "cancelled"}:
                    is_correct = True

                if is_correct:
                    inv_status_correct += 1
                    inv_status_breakdown[exp_status]["correct"] += 1

    # Save actual_predictions.json
    pred_json_path = os.path.join(eval_dir, "actual_predictions.json")
    with open(pred_json_path, "w", encoding="utf-8") as f:
        json.dump(actual_predictions, f, indent=2)
    print(f"Saved actual predictions to {pred_json_path}")

    # Save actual_predictions.csv
    pred_csv_path = os.path.join(eval_dir, "actual_predictions.csv")
    with open(pred_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "test_case_id", "category", "is_supported", "actual_gap_detected",
            "actual_gap_count", "actual_entities_count", "actual_confidence",
            "actual_gap_entities", "clinical_note"
        ])
        for p in actual_predictions:
            gap_ents = "; ".join([g.get("entity", "") for g in p["actual_gaps"]])
            writer.writerow([
                p["test_case_id"], p["category"], p["is_supported"],
                p["actual_gap_detected"], p["actual_gap_count"],
                p["actual_entities_count"], p["actual_confidence"],
                gap_ents, p["clinical_note"]
            ])
    print(f"Saved actual predictions CSV to {pred_csv_path}")

    # Save case_comparison.csv
    case_comp_path = os.path.join(eval_dir, "case_comparison.csv")
    with open(case_comp_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "test_case_id", "category", "is_supported", "applicable_rule_id",
            "expected_gap", "actual_gap", "gap_outcome",
            "expected_entities_count", "actual_entities_count", "actual_gap_entities"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(case_comparisons)
    print(f"Saved case comparison to {case_comp_path}")

    # Calculate Gap Detection Metrics
    total_eval = tp_gap + tn_gap + fp_gap + fn_gap
    acc_gap = (tp_gap + tn_gap) / total_eval if total_eval > 0 else 0.0
    prec_gap = tp_gap / (tp_gap + fp_gap) if (tp_gap + fp_gap) > 0 else 0.0
    rec_gap = tp_gap / (tp_gap + fn_gap) if (tp_gap + fn_gap) > 0 else 0.0
    f1_gap = (2 * prec_gap * rec_gap / (prec_gap + rec_gap)) if (prec_gap + rec_gap) > 0 else 0.0

    # Calculate NER Metrics
    ner_p = ner_overall["tp"] / (ner_overall["tp"] + ner_overall["fp"]) if (ner_overall["tp"] + ner_overall["fp"]) > 0 else 0.0
    ner_r = ner_overall["tp"] / (ner_overall["tp"] + ner_overall["fn"]) if (ner_overall["tp"] + ner_overall["fn"]) > 0 else 0.0
    ner_f1 = (2 * ner_p * ner_r / (ner_p + ner_r)) if (ner_p + ner_r) > 0 else 0.0

    ner_type_metrics = {}
    for t, counts in sorted(ner_by_type.items()):
        tp_t, fp_t, fn_t = counts["tp"], counts["fp"], counts["fn"]
        p_t = tp_t / (tp_t + fp_t) if (tp_t + fp_t) > 0 else 0.0
        r_t = tp_t / (tp_t + fn_t) if (tp_t + fn_t) > 0 else 0.0
        f1_t = (2 * p_t * r_t / (p_t + r_t)) if (p_t + r_t) > 0 else 0.0
        ner_type_metrics[t] = {
            "tp": tp_t, "fp": fp_t, "fn": fn_t,
            "precision": round(p_t * 100, 2),
            "recall": round(r_t * 100, 2),
            "f1_score": round(f1_t * 100, 2),
        }

    # Negation Metrics
    neg_total = neg_tp + neg_tn + neg_fp + neg_fn
    neg_acc = (neg_tp + neg_tn) / neg_total if neg_total > 0 else 0.0
    neg_p = neg_tp / (neg_tp + neg_fp) if (neg_tp + neg_fp) > 0 else 0.0
    neg_r = neg_tp / (neg_tp + neg_fn) if (neg_tp + neg_fn) > 0 else 0.0
    neg_f1 = (2 * neg_p * neg_r / (neg_p + neg_r)) if (neg_p + neg_r) > 0 else 0.0

    # Investigation Status Metrics
    inv_acc = (inv_status_correct / inv_status_total) if inv_status_total > 0 else 0.0

    results_summary = {
        "dataset_summary": {
            "total_test_cases": len(ground_truth_cases),
            "evaluated_supported_cases": supported_count,
            "excluded_unsupported_cases": unsupported_count,
        },
        "gap_detection": {
            "confusion_matrix": {
                "true_positives": tp_gap,
                "true_negatives": tn_gap,
                "false_positives": fp_gap,
                "false_negatives": fn_gap,
                "total_binary_evaluated": total_eval,
            },
            "metrics": {
                "accuracy_pct": round(acc_gap * 100, 2),
                "precision_pct": round(prec_gap * 100, 2),
                "recall_pct": round(rec_gap * 100, 2),
                "f1_score_pct": round(f1_gap * 100, 2),
            }
        },
        "clinical_ner": {
            "overall": {
                "true_positives": ner_overall["tp"],
                "false_positives": ner_overall["fp"],
                "false_negatives": ner_overall["fn"],
                "precision_pct": round(ner_p * 100, 2),
                "recall_pct": round(ner_r * 100, 2),
                "f1_score_pct": round(ner_f1 * 100, 2),
            },
            "by_entity_type": ner_type_metrics,
        },
        "negation_detection": {
            "true_positives": neg_tp,
            "true_negatives": neg_tn,
            "false_positives": neg_fp,
            "false_negatives": neg_fn,
            "accuracy_pct": round(neg_acc * 100, 2),
            "precision_pct": round(neg_p * 100, 2),
            "recall_pct": round(neg_r * 100, 2),
            "f1_score_pct": round(neg_f1 * 100, 2),
        },
        "investigation_status": {
            "total_evaluated_mentions": inv_status_total,
            "correctly_classified": inv_status_correct,
            "accuracy_pct": round(inv_acc * 100, 2),
            "category_breakdown": {
                k: {
                    "total": v["total"],
                    "correct": v["correct"],
                    "accuracy_pct": round((v["correct"] / v["total"]) * 100, 2) if v["total"] > 0 else 0.0
                }
                for k, v in inv_status_breakdown.items()
            }
        }
    }

    # Save evaluation_results.json
    results_json_path = os.path.join(eval_dir, "evaluation_results.json")
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)
    print(f"Saved evaluation results to {results_json_path}")

    # Generate Confusion Matrix PNG
    cm_png_path = os.path.join(eval_dir, "confusion_matrix.png")
    generate_confusion_matrix_plot(tp_gap, tn_gap, fp_gap, fn_gap, cm_png_path)
    print(f"Generated confusion matrix plot at {cm_png_path}")

    # Print summary to console
    print("\n" + "=" * 70)
    print("EVALUATION RESULTS SUMMARY")
    print("=" * 70)
    print(f"Total Test Cases: {len(ground_truth_cases)}")
    print(f"Supported Evaluated: {supported_count} | Unsupported Excluded: {unsupported_count}")
    print("\n[Gap Detection Confusion Matrix (Binary Evaluation)]")
    print(f"  TP: {tp_gap:2d}   FP: {fp_gap:2d}")
    print(f"  FN: {fn_gap:2d}   TN: {tn_gap:2d}")
    print(f"  Accuracy:  {results_summary['gap_detection']['metrics']['accuracy_pct']}%")
    print(f"  Precision: {results_summary['gap_detection']['metrics']['precision_pct']}%")
    print(f"  Recall:    {results_summary['gap_detection']['metrics']['recall_pct']}%")
    print(f"  F1-Score:  {results_summary['gap_detection']['metrics']['f1_score_pct']}%")

    print("\n[Clinical NER Overall Performance]")
    print(f"  Precision: {results_summary['clinical_ner']['overall']['precision_pct']}%")
    print(f"  Recall:    {results_summary['clinical_ner']['overall']['recall_pct']}%")
    print(f"  F1-Score:  {results_summary['clinical_ner']['overall']['f1_score_pct']}%")

    print("\n[Context & Negation Performance]")
    print(f"  Negation Accuracy:  {results_summary['negation_detection']['accuracy_pct']}%")
    print(f"  Negation F1-Score:  {results_summary['negation_detection']['f1_score_pct']}%")
    print(f"  Investigation Status Accuracy: {results_summary['investigation_status']['accuracy_pct']}%")
    print("=" * 70)

    return results_summary


def generate_confusion_matrix_plot(tp: int, tn: int, fp: int, fn: int, out_path: str):
    """Draw a clean, professional confusion matrix using matplotlib."""
    matrix = [[tp, fn], [fp, tn]]
    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)

    cax = ax.matshow([[tp, fn], [fp, tn]], cmap=plt.cm.Blues, alpha=0.85)

    for i in range(2):
        for j in range(2):
            val = matrix[i][j]
            label = ""
            if i == 0 and j == 0:
                label = f"TP\n{val}"
            elif i == 0 and j == 1:
                label = f"FN\n{val}"
            elif i == 1 and j == 0:
                label = f"FP\n{val}"
            elif i == 1 and j == 1:
                label = f"TN\n{val}"
            ax.text(j, i, label, va="center", ha="center", fontsize=14, fontweight="bold",
                    color="white" if val > (tp + tn + fp + fn) / 4 else "black")

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Actual Gap (Pos)", "Actual No-Gap (Neg)"], fontsize=11)
    ax.set_yticklabels(["Ground Truth Gap", "Ground Truth No-Gap"], fontsize=11)
    ax.set_xlabel("Predicted System Decision", fontsize=12, labelpad=10, fontweight="bold")
    ax.set_ylabel("Ground Truth Annotation", fontsize=12, labelpad=10, fontweight="bold")
    plt.title("ClinGap-NLP Gap Detection Confusion Matrix\n(Supported Guideline Rules N=26)",
              fontsize=13, fontweight="bold", pad=20)
    plt.colorbar(cax, fraction=0.046, pad=0.04)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()


if __name__ == "__main__":
    run_evaluation()
