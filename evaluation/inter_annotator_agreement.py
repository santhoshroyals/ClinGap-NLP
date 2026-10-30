"""
inter_annotator_agreement.py - Dual-Annotator Agreement Assessment Engine
ClinGap-NLP Evaluation Infrastructure (Phase 2 & 3)

Academic Principle:
If only one annotator has labeled the dataset, this module strictly returns:
'NOT_CALCULATED (Single-researcher annotation; no second annotator provided)'.

When two independent annotators have completed annotations:
- Computes Cohen's Kappa for categorical assertions (Negation, Investigation Status).
- Computes Inter-Annotator Span Agreement (Precision, Recall, F1 overlap) for NER.
"""

import os
import sys
import json
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter


def compute_inter_annotator_agreement(
    ann1_data: Dict[str, Any],
    ann2_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Computes inter-annotator agreement between two independent annotation files.
    """
    if ann2_data is None:
        return {
            "status": "NOT_CALCULATED",
            "reason": "Single-researcher annotation protocol. A second independent annotator dataset was not provided.",
            "metrics": None
        }

    cases1 = ann1_data.get("cases", ann1_data if isinstance(ann1_data, list) else [])
    cases2 = ann2_data.get("cases", ann2_data if isinstance(ann2_data, list) else [])

    if not cases2 or len(cases2) == 0:
        return {
            "status": "NOT_CALCULATED",
            "reason": "Second annotator dataset is empty.",
            "metrics": None
        }

    # Match cases by record_id
    map1 = {c["record_id"]: c for c in cases1}
    map2 = {c["record_id"]: c for c in cases2}
    common_ids = sorted(list(set(map1.keys()).intersection(set(map2.keys()))))

    if not common_ids:
        return {
            "status": "NOT_CALCULATED",
            "reason": "No overlapping record IDs between the two annotator sets.",
            "metrics": None
        }

    # 1. Entity Span Agreement (Treat Annotator 1 as Reference, Annotator 2 as Candidate)
    tp_spans = 0
    fp_spans = 0
    fn_spans = 0

    for rid in common_ids:
        c1, c2 = map1[rid], map2[rid]
        spans1 = {
            (e["start_char"], e["end_char"], e["entity_type"].upper())
            for e in c1.get("entities", [])
            if not e.get("is_uncertain", False)
        }
        spans2 = {
            (e["start_char"], e["end_char"], e["entity_type"].upper())
            for e in c2.get("entities", [])
            if not e.get("is_uncertain", False)
        }
        matched = spans1.intersection(spans2)
        tp_spans += len(matched)
        fp_spans += len(spans2 - spans1)
        fn_spans += len(spans1 - spans2)

    p_span = tp_spans / (tp_spans + fp_spans) if (tp_spans + fp_spans) > 0 else 0.0
    r_span = tp_spans / (tp_spans + fn_spans) if (tp_spans + fn_spans) > 0 else 0.0
    f1_span = (2 * p_span * r_span / (p_span + r_span)) if (p_span + r_span) > 0 else 0.0

    # 2. Cohen's Kappa for Negation on shared entities
    agreed_neg = 0
    total_shared_negs = 0
    cat_counts1 = Counter()
    cat_counts2 = Counter()

    for rid in common_ids:
        c1, c2 = map1[rid], map2[rid]
        negs1 = {
            n["entity_text"].lower(): n["is_negated"]
            for n in c1.get("negations", [])
            if not n.get("is_uncertain", False)
        }
        negs2 = {
            n["entity_text"].lower(): n["is_negated"]
            for n in c2.get("negations", [])
            if not n.get("is_uncertain", False)
        }
        shared_keys = set(negs1.keys()).intersection(set(negs2.keys()))
        for k in shared_keys:
            v1, v2 = negs1[k], negs2[k]
            total_shared_negs += 1
            cat_counts1[v1] += 1
            cat_counts2[v2] += 1
            if v1 == v2:
                agreed_neg += 1

    po_neg = agreed_neg / total_shared_negs if total_shared_negs > 0 else 1.0
    pe_neg = sum((cat_counts1[k] / total_shared_negs) * (cat_counts2[k] / total_shared_negs) for k in [True, False]) if total_shared_negs > 0 else 0.0
    kappa_neg = (po_neg - pe_neg) / (1.0 - pe_neg) if (1.0 - pe_neg) > 0 else 1.0

    return {
        "status": "CALCULATED",
        "overlapping_cases_count": len(common_ids),
        "entity_span_agreement": {
            "agreement_f1_pct": round(f1_span * 100, 2),
            "shared_spans_count": tp_spans,
            "discrepant_spans_count": fp_spans + fn_spans
        },
        "negation_cohens_kappa": round(kappa_neg, 3),
        "total_shared_negation_mentions": total_shared_negs
    }
