"""
independent_evaluator.py - Rigorous, Independent Evaluation Engine for ClinGap-NLP
ClinGap-NLP Evaluation Infrastructure (Researcher-Led NLP Evaluation)

Implements rigorous metric calculations for:
1. Clinical Named Entity Recognition (NER) - Micro & Macro P, R, F1 per entity type
2. Negation Detection - P, R, F1, Specificity, Confusion Matrix
3. Diagnostic Investigation Extraction - P, R, F1 specifically on investigations
4. Investigation Status Classification - P, R, F1 per status class
5. Exploratory Guideline Matching & Decision Gap Testing (Separated as Educational Software Logic)

ACADEMIC INTEGRITY POLICY:
1. Evaluates only against manually annotated reference labels (RESEARCHER_ANNOTATED or EXPERT_VERIFIED).
2. Programmatically blocks metrics if all records are marked 'AWAITING_HUMAN_VERIFICATION'.
3. Excludes UNCERTAIN annotations from standard metric calculations and reports their counts separately.
4. Does NOT calculate inter-annotator agreement unless a second annotator is present.
5. Educational rules are kept strictly separate as exploratory software logic, NOT clinical validation.
"""

import os
import sys
import json
from typing import Dict, List, Any, Tuple, Optional, Set
from collections import defaultdict, Counter


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division preventing ZeroDivisionError."""
    if denominator == 0.0:
        return default
    return numerator / denominator


def calculate_prf(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    """Calculates precision, recall, and F1-score as percentages."""
    p = safe_div(float(tp), float(tp + fp))
    r = safe_div(float(tp), float(tp + fn))
    f1 = safe_div(2.0 * p * r, p + r)
    return round(p * 100.0, 2), round(r * 100.0, 2), round(f1 * 100.0, 2)


STANDARD_SEVEN_CLASSES: Set[str] = {
    "DISEASE",
    "SYMPTOM",
    "MEDICATION",
    "INVESTIGATION",
    "DOSAGE",
    "FREQUENCY",
    "LAB_TEST"
}


# ==============================================================================
# 1. CLINICAL NER EVALUATION (Excludes UNCERTAIN annotations)
# ==============================================================================

def evaluate_clinical_ner(
    ground_truth_cases: List[Dict[str, Any]],
    predicted_cases: List[Dict[str, Any]],
    matching_mode: str = "normalized_or_text",
    target_classes: Optional[Set[str]] = None
) -> Dict[str, Any]:
    """
    Evaluates NER performance.
    Matches tuples of (entity_type, identifier) between GT and predictions.
    Excludes entities marked is_uncertain=True and reports count separately.
    When target_classes is set (e.g. STANDARD_SEVEN_CLASSES), extended categories
    (such as PHYSICAL_SIGN, VITAL_SIGN) are preserved in an extended breakdown
    and do not penalize standard 7-class evaluation.
    """
    overall_counts = {"tp": 0, "fp": 0, "fn": 0}
    by_type_counts = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    uncertain_excluded = 0
    extended_entities_isolated = 0
    extended_by_type = defaultdict(int)

    for gt_case, pred_case in zip(ground_truth_cases, predicted_cases):
        raw_gt_ents = gt_case.get("entities", [])
        pred_ents = pred_case.get("entities", [])

        # Filter out UNCERTAIN entities; isolate extended non-target types if target_classes specified
        gt_ents = []
        if isinstance(raw_gt_ents, list):
            for e in raw_gt_ents:
                if not isinstance(e, dict):
                    continue
                if e.get("is_uncertain", False):
                    uncertain_excluded += 1
                elif target_classes is not None and str(e.get("entity_type", "")).upper() not in target_classes:
                    extended_entities_isolated += 1
                    extended_by_type[str(e.get("entity_type", "")).upper()] += 1
                else:
                    gt_ents.append(e)

        def to_tuples(ents):
            res = set()
            if isinstance(ents, list):
                for e in ents:
                    if not isinstance(e, dict):
                        continue
                    etype = str(e.get("entity_type", "")).upper()
                    if target_classes is not None and etype not in target_classes:
                        continue
                    norm = str(e.get("normalized_value") or e.get("entity_text") or "").strip().lower()
                    if etype and norm:
                        res.add((etype, norm))
            return res

        gt_set = to_tuples(gt_ents)
        pred_set = to_tuples(pred_ents)

        matched = gt_set.intersection(pred_set)
        fps = pred_set - gt_set
        fns = gt_set - pred_set

        overall_counts["tp"] += len(matched)
        overall_counts["fp"] += len(fps)
        overall_counts["fn"] += len(fns)

        all_types = {t[0] for t in gt_set.union(pred_set)}
        for t in all_types:
            t_gt = {x for x in gt_set if x[0] == t}
            t_pred = {x for x in pred_set if x[0] == t}
            by_type_counts[t]["tp"] += len(t_gt.intersection(t_pred))
            by_type_counts[t]["fp"] += len(t_pred - t_gt)
            by_type_counts[t]["fn"] += len(t_gt - t_pred)

    overall_p, overall_r, overall_f1 = calculate_prf(
        overall_counts["tp"], overall_counts["fp"], overall_counts["fn"]
    )

    per_type_metrics = {}
    f1_list = []
    for t, c in sorted(by_type_counts.items()):
        p, r, f1 = calculate_prf(c["tp"], c["fp"], c["fn"])
        per_type_metrics[t] = {
            "true_positives": c["tp"],
            "false_positives": c["fp"],
            "false_negatives": c["fn"],
            "precision_pct": p,
            "recall_pct": r,
            "f1_score_pct": f1
        }
        if (c["tp"] + c["fn"]) > 0:  # Only average types present in GT
            f1_list.append(f1)

    macro_f1 = round(sum(f1_list) / len(f1_list), 2) if f1_list else 0.0

    result = {
        "overall_micro": {
            "true_positives": overall_counts["tp"],
            "false_positives": overall_counts["fp"],
            "false_negatives": overall_counts["fn"],
            "precision_pct": overall_p,
            "recall_pct": overall_r,
            "f1_score_pct": overall_f1
        },
        "macro_f1_pct": macro_f1,
        "by_entity_type": per_type_metrics,
        "per_type_metrics": per_type_metrics,
        "uncertain_entities_excluded": uncertain_excluded,
        "evaluation_standard": "7_CLASS_STANDARD" if target_classes == STANDARD_SEVEN_CLASSES else "ALL_CLASSES"
    }
    if extended_entities_isolated > 0:
        result["extended_entities_breakdown"] = {
            "total_extended_entities_preserved": extended_entities_isolated,
            "counts_by_type": dict(extended_by_type)
        }
    return result


# ==============================================================================
# 2. INVESTIGATION EXTRACTION EVALUATION (Dedicated Sub-Metric)
# ==============================================================================

def evaluate_investigation_extraction(
    ground_truth_cases: List[Dict[str, Any]],
    predicted_cases: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Evaluates extraction specifically for INVESTIGATION entities.
    Excludes UNCERTAIN mentions and reports count separately.
    """
    tp = 0
    fp = 0
    fn = 0
    uncertain_excluded = 0

    for gt_case, pred_case in zip(ground_truth_cases, predicted_cases):
        gt_invs = set()
        raw_gt_ents = gt_case.get("entities", []) if isinstance(gt_case, dict) else []
        if isinstance(raw_gt_ents, list):
            for e in raw_gt_ents:
                if not isinstance(e, dict):
                    continue
                if str(e.get("entity_type", "")).upper() == "INVESTIGATION":
                    if e.get("is_uncertain", False):
                        uncertain_excluded += 1
                        continue
                    norm = str(e.get("normalized_value") or e.get("entity_text") or "").strip().lower()
                    if norm:
                        gt_invs.add(norm)

        pred_invs = set()
        raw_pred_ents = pred_case.get("entities", []) if isinstance(pred_case, dict) else []
        if isinstance(raw_pred_ents, list):
            for e in raw_pred_ents:
                if not isinstance(e, dict):
                    continue
                if str(e.get("entity_type", "")).upper() == "INVESTIGATION":
                    norm = str(e.get("normalized_value") or e.get("entity_text") or "").strip().lower()
                    if norm:
                        pred_invs.add(norm)

        matched = gt_invs.intersection(pred_invs)
        tp += len(matched)
        fp += len(pred_invs - gt_invs)
        fn += len(gt_invs - pred_invs)

    p, r, f1 = calculate_prf(tp, fp, fn)

    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision_pct": p,
        "recall_pct": r,
        "f1_score_pct": f1,
        "uncertain_investigations_excluded": uncertain_excluded
    }


# ==============================================================================
# 3. NEGATION DETECTION EVALUATION (Excludes UNCERTAIN annotations)
# ==============================================================================

def evaluate_negation_detection(
    ground_truth_cases: List[Dict[str, Any]],
    predicted_cases: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Evaluates clinical assertion/negation classification on clinical entities.
    Excludes annotations marked is_uncertain=True.
    Distinguishes end-to-end extraction+assertion from conditional assertion on matched entities.
    Reports positive and negative class support and confusion matrices.
    Flags matched-entity evaluation as NOT EVALUABLE when positive-class support among extracted entities is zero.
    """
    tp = 0  # GT negated, Pred negated
    tn = 0  # GT affirmed, Pred affirmed (on matched entities)
    fp = 0  # GT affirmed, Pred negated
    fn = 0  # GT negated, Pred affirmed OR missing prediction (missing predictions not counted as correct)

    matched_tp = 0
    matched_tn = 0
    matched_fp = 0
    matched_fn = 0

    gt_neg_count = 0
    gt_aff_count = 0
    pred_neg_count = 0
    pred_aff_count = 0
    uncertain_excluded = 0

    for gt_case, pred_case in zip(ground_truth_cases, predicted_cases):
        raw_gt_negs = gt_case.get("negations", []) if isinstance(gt_case, dict) else []
        case_gt_assertions = {}

        if isinstance(raw_gt_negs, list):
            for e in raw_gt_negs:
                if not isinstance(e, dict):
                    continue
                if e.get("is_uncertain", False):
                    uncertain_excluded += 1
                    continue
                text = str(e.get("entity_text", "")).strip().lower()
                if text:
                    case_gt_assertions[text] = bool(e.get("is_negated", False))

        # Check entities for affirmed findings or entities without separate negation records
        if isinstance(gt_case, dict) and "entities" in gt_case:
            raw_gt_ents = gt_case.get("entities", [])
            if isinstance(raw_gt_ents, list):
                for e in raw_gt_ents:
                    if not isinstance(e, dict):
                        continue
                    if e.get("is_uncertain", False):
                        uncertain_excluded += 1
                        continue
                    text = str(e.get("entity_text", "")).strip().lower()
                    if text and text not in case_gt_assertions:
                        case_gt_assertions[text] = bool(e.get("negated", False))

        for is_neg in case_gt_assertions.values():
            if is_neg:
                gt_neg_count += 1
            else:
                gt_aff_count += 1

        pred_negs = {}
        raw_pred_ents = pred_case.get("entities", []) if isinstance(pred_case, dict) else []
        if isinstance(raw_pred_ents, list):
            for e in raw_pred_ents:
                if isinstance(e, dict):
                    text = str(e.get("entity_text", "")).strip().lower()
                    if text:
                        is_pneg = bool(e.get("negated", False))
                        pred_negs[text] = is_pneg
                        if is_pneg:
                            pred_neg_count += 1
                        else:
                            pred_aff_count += 1

        for ent_name, gt_is_neg in case_gt_assertions.items():
            in_pred = ent_name in pred_negs
            pred_is_neg = pred_negs.get(ent_name, False)

            if gt_is_neg:
                # Positive class (negated finding)
                if in_pred and pred_is_neg:
                    tp += 1
                    matched_tp += 1
                elif in_pred and not pred_is_neg:
                    fn += 1
                    matched_fn += 1
                else:
                    # Missing prediction: unextracted negated finding counts as FN (do not count missing as correct)
                    fn += 1
            else:
                # Negative class (affirmed finding)
                if in_pred and pred_is_neg:
                    fp += 1
                    matched_fp += 1
                elif in_pred and not pred_is_neg:
                    tn += 1
                    matched_tn += 1
                else:
                    # Unextracted affirmed finding -> not counted as TN (do not count missing as correct)
                    pass

    total_matched = matched_tp + matched_tn + matched_fp + matched_fn
    matched_pos_support = matched_tp + matched_fn
    is_evaluable_on_matched = matched_pos_support > 0

    total = tp + tn + fp + fn
    accuracy = safe_div(float(tp + tn), float(total)) * 100.0
    precision, recall, f1 = calculate_prf(tp, fp, fn)
    specificity = safe_div(float(tn), float(tn + fp)) * 100.0

    result = {
        "evaluation_mode": "END_TO_END_ASSERTION_AND_MATCHED_ASSERTION",
        "class_support": {
            "ground_truth_negated_support": gt_neg_count,
            "ground_truth_affirmed_support": gt_aff_count,
            "predicted_negated_count": pred_neg_count,
            "predicted_affirmed_count": pred_aff_count,
            "matched_entities_positive_support": matched_pos_support,
            "matched_entities_negative_support": matched_tn + matched_fp
        },
        "matched_entities_assertion": {
            "is_evaluable": is_evaluable_on_matched,
            "status": "EVALUABLE" if is_evaluable_on_matched else "NOT EVALUABLE (Zero positive-class support among extracted entities)",
            "confusion_matrix": {"tp": matched_tp, "tn": matched_tn, "fp": matched_fp, "fn": matched_fn, "total": total_matched},
            "precision_pct": round(safe_div(float(matched_tp), float(matched_tp + matched_fp)) * 100.0, 2) if is_evaluable_on_matched else None,
            "recall_pct": round(safe_div(float(matched_tp), float(matched_tp + matched_fn)) * 100.0, 2) if is_evaluable_on_matched else None,
            "f1_score_pct": round(safe_div(2.0 * matched_tp, 2.0 * matched_tp + matched_fp + matched_fn) * 100.0, 2) if is_evaluable_on_matched else None
        },
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn, "total": total},
        "accuracy_pct": round(accuracy, 2),
        "precision_pct": precision,
        "recall_pct": recall,
        "f1_score_pct": f1,
        "specificity_pct": round(specificity, 2),
        "uncertain_negations_excluded": uncertain_excluded
    }
    if not is_evaluable_on_matched and gt_neg_count > 0:
        result["evaluation_notice"] = (
            "NOT EVALUABLE ON MATCHED ENTITIES: Zero ground-truth negated concepts were extracted by the upstream NER pipeline. "
            "End-to-end evaluation records unextracted negated entities as False Negatives (FN)."
        )
    return result


# ==============================================================================
# 4. INVESTIGATION STATUS EVALUATION (Excludes UNCERTAIN annotations)
# ==============================================================================

def evaluate_investigation_status(
    ground_truth_cases: List[Dict[str, Any]],
    predicted_cases: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Evaluates multi-class classification of diagnostic investigation statuses.
    Excludes statuses marked is_uncertain=True.
    Distinguishes extraction omissions (missing predictions) from status classification errors.
    """
    status_classes = ["completed/performed", "ordered", "pending", "not performed/cancelled"]
    per_class_counts = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    total_evaluated = 0
    total_correct = 0
    uncertain_excluded = 0

    missing_unextracted = 0
    extracted_evaluated = 0
    correctly_classified_extracted = 0
    incorrectly_classified_extracted = 0

    for gt_case, pred_case in zip(ground_truth_cases, predicted_cases):
        gt_invs = {}
        raw_gt_invs = gt_case.get("investigations", []) if isinstance(gt_case, dict) else []
        if isinstance(raw_gt_invs, list):
            for e in raw_gt_invs:
                if not isinstance(e, dict):
                    continue
                if e.get("is_uncertain", False):
                    uncertain_excluded += 1
                    continue
                name = str(e.get("investigation_name") or e.get("entity_text", "")).strip().lower()
                st = str(e.get("status", "")).lower()
                if name and st:
                    gt_invs[name] = st

        pred_invs = {}
        raw_pred_ents = pred_case.get("entities", []) if isinstance(pred_case, dict) else []
        if isinstance(raw_pred_ents, list):
            for e in raw_pred_ents:
                if isinstance(e, dict) and str(e.get("entity_type", "")).upper() == "INVESTIGATION":
                    name = str(e.get("entity_text") or e.get("normalized_value", "")).strip().lower()
                    st = str(e.get("status", "")).lower()
                    if name:
                        pred_invs[name] = st

        for inv_name, gt_st in gt_invs.items():
            if not gt_st or gt_st == "undocumented":
                continue
            total_evaluated += 1
            is_extracted = inv_name in pred_invs
            pred_st = pred_invs.get(inv_name, "unknown")

            # Map status synonyms
            if pred_st in {"order", "ordered/pending"}:
                pred_st_norm = "ordered"
            elif pred_st in {"done", "completed"}:
                pred_st_norm = "completed/performed"
            elif pred_st in {"not done", "cancelled", "not performed"}:
                pred_st_norm = "not performed/cancelled"
            else:
                pred_st_norm = pred_st

            if gt_st in {"order", "ordered/pending"}:
                gt_st_norm = "ordered"
            elif gt_st in {"done", "completed"}:
                gt_st_norm = "completed/performed"
            elif gt_st in {"not done", "cancelled", "not performed"}:
                gt_st_norm = "not performed/cancelled"
            else:
                gt_st_norm = gt_st

            if not is_extracted:
                missing_unextracted += 1
            else:
                extracted_evaluated += 1
                if gt_st_norm == pred_st_norm:
                    correctly_classified_extracted += 1
                else:
                    incorrectly_classified_extracted += 1

            if gt_st_norm == pred_st_norm:
                total_correct += 1
                per_class_counts[gt_st_norm]["tp"] += 1
            else:
                per_class_counts[gt_st_norm]["fn"] += 1
                per_class_counts[pred_st_norm]["fp"] += 1

    class_metrics = {}
    f1_list = []
    for sc in status_classes:
        c = per_class_counts[sc]
        p, r, f1 = calculate_prf(c["tp"], c["fp"], c["fn"])
        class_metrics[sc] = {
            "tp": c["tp"], "fp": c["fp"], "fn": c["fn"],
            "precision_pct": p, "recall_pct": r, "f1_score_pct": f1
        }
        if (c["tp"] + c["fn"]) > 0:
            f1_list.append(f1)

    overall_acc = safe_div(float(total_correct), float(total_evaluated)) * 100.0
    macro_f1 = round(sum(f1_list) / len(f1_list), 2) if f1_list else 0.0

    return {
        "total_evaluated_mentions": total_evaluated,
        "correctly_classified": total_correct,
        "accuracy_pct": round(overall_acc, 2),
        "macro_f1_pct": macro_f1,
        "by_class": class_metrics,
        "breakdown": {
            "total_reference_investigations": total_evaluated,
            "missing_unextracted_investigations": missing_unextracted,
            "extracted_investigations_evaluated": extracted_evaluated,
            "correctly_classified_on_extracted": correctly_classified_extracted,
            "incorrectly_classified_on_extracted": incorrectly_classified_extracted,
            "conditional_accuracy_on_extracted_pct": round(safe_div(float(correctly_classified_extracted), float(extracted_evaluated)) * 100.0, 2)
        },
        "uncertain_statuses_excluded": uncertain_excluded
    }


# ==============================================================================
# 5. EXPLORATORY GUIDELINE MATCHING & GAP TESTING (Educational Logic Verification)
# ==============================================================================

def _extract_rule_id(rule_item: Any) -> Optional[str]:
    """
    Extracts a normalized rule ID from either a dictionary or string representation.
    Returns uppercase stripped string ID, or None if invalid or empty.
    Robust to:
    - Dict: {"rule_id": "R1"}, {"id": "R1"}, {"name": "R1"}
    - String: "R1"
    - Other types / empty / whitespace / None -> returns None
    """
    if isinstance(rule_item, bool) or rule_item is None:
        return None
    raw_id = None
    if isinstance(rule_item, dict):
        raw_id = rule_item.get("rule_id")
        if raw_id is None:
            raw_id = rule_item.get("id")
        if raw_id is None:
            raw_id = rule_item.get("name")
    elif isinstance(rule_item, (str, int, float)):
        raw_id = rule_item
    else:
        return None

    if raw_id is None or isinstance(raw_id, bool):
        return None
    cleaned = str(raw_id).strip()
    return cleaned.upper() if cleaned else None


def evaluate_guideline_matching(
    ground_truth_cases: List[Dict[str, Any]],
    predicted_cases: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Evaluates whether configured guideline rules were triggered.
    EXPLORATORY SOFTWARE BEHAVIOR: Rules are educational heuristics, not clinical validity.
    Robust to both dictionary ({"rule_id": "R1"}) and string ("R1") pipeline outputs.
    """
    tp = 0
    fp = 0
    fn = 0
    tn = 0

    for gt_case, pred_case in zip(ground_truth_cases, predicted_cases):
        if not isinstance(gt_case, dict) or not isinstance(pred_case, dict):
            continue

        gt_rules = set()
        raw_guidelines = gt_case.get("guidelines", [])
        if isinstance(raw_guidelines, list):
            for g in raw_guidelines:
                if isinstance(g, dict):
                    if g.get("is_triggered", False):
                        rid = _extract_rule_id(g.get("guideline_id")) or _extract_rule_id(g)
                        if rid:
                            gt_rules.add(rid)
                else:
                    rid = _extract_rule_id(g)
                    if rid:
                        gt_rules.add(rid)
        elif isinstance(raw_guidelines, (str, dict)):
            rid = _extract_rule_id(raw_guidelines)
            if rid:
                gt_rules.add(rid)

        if not gt_rules and gt_case.get("applicable_rule_id"):
            rid = _extract_rule_id(gt_case.get("applicable_rule_id"))
            if rid:
                gt_rules.add(rid)

        pred_rules = set()
        raw_explanation = pred_case.get("explanation", {})
        matched_items = []
        if isinstance(raw_explanation, dict):
            matched_items = raw_explanation.get("matched_rules", [])
        elif isinstance(raw_explanation, list):
            matched_items = raw_explanation
        elif isinstance(raw_explanation, str):
            matched_items = [raw_explanation]

        if not matched_items and isinstance(pred_case.get("matched_rules"), list):
            matched_items = pred_case.get("matched_rules", [])

        if isinstance(matched_items, list):
            for item in matched_items:
                rid = _extract_rule_id(item)
                if rid:
                    pred_rules.add(rid)
        elif isinstance(matched_items, (str, dict)):
            rid = _extract_rule_id(matched_items)
            if rid:
                pred_rules.add(rid)

        matched = gt_rules.intersection(pred_rules)
        fps = pred_rules - gt_rules
        fns = gt_rules - pred_rules

        tp += len(matched)
        fp += len(fps)
        fn += len(fns)
        if len(gt_rules) == 0 and len(pred_rules) == 0:
            tn += 1

    p, r, f1 = calculate_prf(tp, fp, fn)

    return {
        "confusion_counts": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "precision_pct": p,
        "recall_pct": r,
        "f1_score_pct": f1
    }


def evaluate_decision_gap_detection(
    ground_truth_cases: List[Dict[str, Any]],
    predicted_cases: List[Dict[str, Any]],
    supported_only: bool = True
) -> Dict[str, Any]:
    """
    Evaluates gap detection logic.
    EXPLORATORY SOFTWARE BEHAVIOR: Reflects prototype rule firing, not verified clinical omissions.
    """
    tp = 0
    tn = 0
    fp = 0
    fn = 0
    evaluated_count = 0
    excluded_count = 0

    for gt_case, pred_case in zip(ground_truth_cases, predicted_cases):
        if not isinstance(gt_case, dict) or not isinstance(pred_case, dict):
            continue
        if supported_only and gt_case.get("is_supported") is False:
            excluded_count += 1
            continue

        gt_has_gap = False
        if "expected_gap" in gt_case:
            gt_has_gap = bool(gt_case["expected_gap"])
        elif "decision_gaps" in gt_case:
            raw_gaps = gt_case.get("decision_gaps", [])
            if isinstance(raw_gaps, list):
                gt_has_gap = any(
                    isinstance(g, dict) and g.get("is_actionable_gap", False)
                    for g in raw_gaps
                )
            else:
                gt_has_gap = bool(raw_gaps)

        pred_gaps = pred_case.get("gaps", []) if isinstance(pred_case, dict) else []
        if isinstance(pred_gaps, list):
            pred_has_gap = len(pred_gaps) > 0
        else:
            pred_has_gap = bool(pred_gaps)

        evaluated_count += 1
        if gt_has_gap and pred_has_gap:
            tp += 1
        elif not gt_has_gap and not pred_has_gap:
            tn += 1
        elif not gt_has_gap and pred_has_gap:
            fp += 1
        elif gt_has_gap and not pred_has_gap:
            fn += 1

    total = tp + tn + fp + fn
    accuracy = safe_div(float(tp + tn), float(total)) * 100.0
    precision, recall, f1 = calculate_prf(tp, fp, fn)
    specificity = safe_div(float(tn), float(tn + fp)) * 100.0
    balanced_acc = safe_div((safe_div(float(tp), float(tp + fn)) + safe_div(float(tn), float(tn + fp))), 2.0) * 100.0

    return {
        "evaluation_summary": {
            "total_evaluated_cases": evaluated_count,
            "excluded_unsupported_cases": excluded_count
        },
        "confusion_matrix": {
            "true_positives": tp,
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "total": total
        },
        "metrics": {
            "accuracy_pct": round(accuracy, 2),
            "precision_pct": precision,
            "recall_pct": recall,
            "f1_score_pct": f1,
            "specificity_pct": round(specificity, 2),
            "balanced_accuracy_pct": round(balanced_acc, 2)
        }
    }


# ==============================================================================
# 6. PIPELINE EXECUTION AUDITOR
# ==============================================================================

def run_independent_evaluation_on_batch(
    annotation_file_path: str,
    pipeline_instance=None
) -> Dict[str, Any]:
    """
    Loads an annotation document and audits its verification status.
    Refuses to calculate model metrics if records are unverified.
    Accepts RESEARCHER_ANNOTATED and EXPERT_VERIFIED reference annotations.
    """
    if not os.path.exists(annotation_file_path):
        raise FileNotFoundError(f"Annotation file not found: {annotation_file_path}")

    with open(annotation_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cases = data.get("cases", data if isinstance(data, list) else [])
    if not cases:
        return {"status": "EMPTY_BATCH", "message": "No cases in annotation file."}

    # Audit verification status
    statuses = Counter(c.get("verification_status", "UNKNOWN") for c in cases)
    valid_statuses = {"RESEARCHER_ANNOTATED", "RESEARCHER_CONSENSUS", "EXPERT_VERIFIED"}
    valid_cases = [c for c in cases if c.get("verification_status") in valid_statuses]

    if len(valid_cases) == 0:
        return {
            "status": "METRICS_BLOCKED",
            "reason": (
                "ZERO annotated/verified records found in batch. "
                "In strict accordance with academic integrity, performance metrics (P, R, F1) "
                "cannot be calculated on unverified template files. "
                "Please annotate cases and set verification_status to 'RESEARCHER_ANNOTATED'."
            ),
            "verification_status_breakdown": dict(statuses),
            "total_cases_audited": len(cases),
            "next_steps": "Complete manual annotation in pilot_10_cases.json and update verification_status to RESEARCHER_ANNOTATED."
        }

    # Extract annotator provenance
    primary_annotators = list({c.get("annotator_id") for c in valid_cases if c.get("annotator_id")})
    second_annotators = list({c.get("second_annotator_id") for c in valid_cases if c.get("second_annotator_id")})
    primary_status = "RESEARCHER_ANNOTATED" if any(c.get("verification_status") == "RESEARCHER_ANNOTATED" for c in valid_cases) else "EXPERT_VERIFIED"

    # If valid records exist, run actual pipeline
    if pipeline_instance is None:
        from backend.services.clinical_pipeline import ClinicalPipeline
        pipeline_instance = ClinicalPipeline()

    predicted_cases = []
    for c in valid_cases:
        text = c.get("clinical_note", "")
        res = pipeline_instance.run(db=None, text=text)
        predicted_cases.append(res)

    # Compute linguistic components (evaluates 7 standard classes against 7-class pipeline)
    ner_metrics = evaluate_clinical_ner(valid_cases, predicted_cases, target_classes=STANDARD_SEVEN_CLASSES)
    inv_extraction_metrics = evaluate_investigation_extraction(valid_cases, predicted_cases)
    neg_metrics = evaluate_negation_detection(valid_cases, predicted_cases)
    status_metrics = evaluate_investigation_status(valid_cases, predicted_cases)

    # Compute exploratory rule components
    rule_metrics = evaluate_guideline_matching(valid_cases, predicted_cases)
    gap_metrics = evaluate_decision_gap_detection(valid_cases, predicted_cases)

    total_uncertain = (
        ner_metrics.get("uncertain_entities_excluded", 0) +
        inv_extraction_metrics.get("uncertain_investigations_excluded", 0) +
        neg_metrics.get("uncertain_negations_excluded", 0) +
        status_metrics.get("uncertain_statuses_excluded", 0)
    )

    return {
        "status": "EVALUATION_COMPLETED",
        "evaluation_type": "SINGLE_RESEARCHER_ANNOTATED_NLP_EVALUATION" if not second_annotators else "DUAL_RESEARCHER_ANNOTATED_NLP_EVALUATION",
        "provenance": {
            "verification_status": primary_status,
            "primary_annotator_ids": primary_annotators or ["researcher_1"],
            "second_annotator_ids": second_annotators or [],
            "inter_annotator_agreement": (
                "NOT_CALCULATED (Single-researcher annotation; no second annotator provided)"
                if not second_annotators else "AVAILABLE"
            ),
            "academic_notice": (
                "Linguistic Information Extraction Evaluation Only. "
                "Evaluated against researcher-annotated ground truth. "
                "NOT clinically validated by licensed medical doctors."
            )
        },
        "evaluated_records_count": len(valid_cases),
        "uncertainty_audit": {
            "total_uncertain_annotations_excluded": total_uncertain,
            "uncertain_entities_excluded": ner_metrics.get("uncertain_entities_excluded", 0),
            "uncertain_investigations_excluded": inv_extraction_metrics.get("uncertain_investigations_excluded", 0),
            "uncertain_negations_excluded": neg_metrics.get("uncertain_negations_excluded", 0),
            "uncertain_statuses_excluded": status_metrics.get("uncertain_statuses_excluded", 0)
        },
        "linguistic_nlp_evaluation": {
            "clinical_ner": ner_metrics,
            "investigation_extraction": inv_extraction_metrics,
            "negation_detection": neg_metrics,
            "investigation_status_classification": status_metrics
        },
        "exploratory_educational_rule_engine": {
            "disclaimer": (
                "EXPLORATORY SOFTWARE BEHAVIOR: Rules R1 and R2 are educational demonstration heuristics. "
                "Rule activations and gap detection results reflect software logic verification only "
                "and do NOT denote medical correctness or clinical validity."
            ),
            "guideline_matching": rule_metrics,
            "decision_gap_detection": gap_metrics
        }
    }
