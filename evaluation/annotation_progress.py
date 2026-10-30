"""
annotation_progress.py - Annotation Progress & Review Audit Tracker
ClinGap-NLP Evaluation Infrastructure (Phase 3 & 4)

Tracks annotation progress across batches:
- Counts pending (AWAITING_HUMAN_VERIFICATION) vs. completed (EXPERT_VERIFIED) records.
- Audits annotator contributions and verification provenance.
- Reports component annotation density (entities, negations, statuses, guidelines, gaps).
- Assesses readiness for empirical metric calculation.
"""

import os
import sys
import json
import csv
from collections import Counter, defaultdict
from typing import Dict, List, Any


def audit_annotation_progress(file_path: str) -> Dict[str, Any]:
    """
    Scans an annotation JSON or CSV file and generates an academic progress report.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Annotation file not found: {file_path}")

    cases = []
    batch_metadata = {}

    if file_path.endswith(".json"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            batch_metadata = {k: v for k, v in data.items() if k != "cases"}
            cases = data.get("cases", [])
        elif isinstance(data, list):
            cases = data
    elif file_path.endswith(".csv"):
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cases = list(reader)
    else:
        raise ValueError(f"Unsupported file format: {file_path}. Must be .json or .csv")

    total_cases = len(cases)
    if total_cases == 0:
        return {"status": "EMPTY_FILE", "total_records": 0}

    status_counter = Counter()
    specialty_counter = Counter()
    annotator_counter = Counter()

    total_entities = 0
    total_negations = 0
    total_investigations = 0
    total_guidelines = 0
    total_decision_gaps = 0
    total_uncertain = 0

    for c in cases:
        v_status = c.get("verification_status") or "AWAITING_HUMAN_VERIFICATION"
        status_counter[v_status] += 1

        spec = c.get("specialty") or "UNKNOWN"
        specialty_counter[spec] += 1

        annotator = c.get("annotator_id") or "UNASSIGNED"
        annotator_counter[annotator] += 1

        # Count annotations and track uncertainty
        ents = c.get("entities", [])
        if isinstance(ents, str):
            try: ents = json.loads(ents)
            except: ents = []
        total_entities += len(ents)
        total_uncertain += sum(1 for e in ents if e.get("is_uncertain", False))

        negs = c.get("negations", [])
        if isinstance(negs, str):
            try: negs = json.loads(negs)
            except: negs = []
        total_negations += len(negs)
        total_uncertain += sum(1 for e in negs if e.get("is_uncertain", False))

        invs = c.get("investigations", [])
        if isinstance(invs, str):
            try: invs = json.loads(invs)
            except: invs = []
        total_investigations += len(invs)
        total_uncertain += sum(1 for e in invs if e.get("is_uncertain", False))

        gls = c.get("guidelines", [])
        if isinstance(gls, str):
            try: gls = json.loads(gls)
            except: gls = []
        total_guidelines += len(gls)

        gaps = c.get("decision_gaps", [])
        if isinstance(gaps, str):
            try: gaps = json.loads(gaps)
            except: gaps = []
        total_decision_gaps += len(gaps)

    researcher_annotated_count = status_counter.get("RESEARCHER_ANNOTATED", 0)
    expert_verified_count = status_counter.get("EXPERT_VERIFIED", 0)
    pending_count = status_counter.get("AWAITING_HUMAN_VERIFICATION", 0)
    flagged_count = status_counter.get("FLAGGED_DISCREPANCY", 0)
    rejected_count = status_counter.get("REJECTED_UNSUITABLE", 0)

    total_valid = researcher_annotated_count + expert_verified_count
    completion_rate_pct = round((total_valid / total_cases) * 100, 2)
    if total_valid == total_cases:
        readiness = "READY (All records researcher-annotated or expert-verified)"
    elif total_valid > 0:
        readiness = f"IN_PROGRESS ({total_valid}/{total_cases} records verified)"
    else:
        readiness = "BLOCKED (Pending manual annotation)"

    cases_overview = []
    for idx, c in enumerate(cases):
        ents = c.get("entities", [])
        if isinstance(ents, str):
            try: ents = json.loads(ents)
            except: ents = []
        negs = c.get("negations", [])
        if isinstance(negs, str):
            try: negs = json.loads(negs)
            except: negs = []
        invs = c.get("investigations", [])
        if isinstance(invs, str):
            try: invs = json.loads(invs)
            except: invs = []
        cases_overview.append({
            "case_index": idx + 1,
            "record_id": c.get("record_id"),
            "specialty": c.get("specialty", "UNKNOWN"),
            "verification_status": c.get("verification_status") or "AWAITING_HUMAN_VERIFICATION",
            "annotator_id": c.get("annotator_id") or "UNASSIGNED",
            "entities": len(ents),
            "negations": len(negs),
            "investigations": len(invs)
        })

    progress_summary = {
        "file_audited": os.path.abspath(file_path),
        "total_records": total_cases,
        "verification_breakdown": {
            "pending_review": pending_count,
            "researcher_annotated": researcher_annotated_count,
            "expert_verified": expert_verified_count,
            "flagged_discrepancy": flagged_count,
            "rejected_unsuitable": rejected_count
        },
        "completion_rate_pct": completion_rate_pct,
        "evaluation_readiness": readiness,
        "annotator_distribution": dict(annotator_counter),
        "specialty_distribution": dict(specialty_counter),
        "uncertainty_count": total_uncertain,
        "annotation_density": {
            "total_entities_tagged": total_entities,
            "total_negations_scoped": total_negations,
            "total_investigations_classified": total_investigations,
            "total_guidelines_judged": total_guidelines,
            "total_decision_gaps_judged": total_decision_gaps,
            "mean_entities_per_record": round(total_entities / total_cases, 2)
        },
        "cases_overview": cases_overview
    }

    return progress_summary


def print_progress_report(file_path: str):
    """Prints a clean human-readable CLI progress table."""
    summary = audit_annotation_progress(file_path)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        rel_path = os.path.relpath(summary["file_audited"], base_dir)
    except ValueError:
        rel_path = summary["file_audited"]

    print("\n" + "=" * 70)
    print("ClinGap-NLP: Annotation Progress & Verification Audit")
    print("=" * 70)
    print(f"File Audited: {rel_path}")
    print(f"Full Path:    {summary['file_audited']}")
    print(f"Total Records in Batch: {summary['total_records']}")
    print("-" * 70)
    print(f"  [Pending Verification]     {summary['verification_breakdown']['pending_review']:4d} (Awaiting manual annotation)")
    print(f"  [Researcher Annotated]     {summary['verification_breakdown']['researcher_annotated']:4d} (Researcher-led ground truth)")
    print(f"  [Expert Verified]          {summary['verification_breakdown']['expert_verified']:4d} (Clinical expert verified)")
    print(f"  [Flagged Discrepancies]    {summary['verification_breakdown']['flagged_discrepancy']:4d} (Awaiting consensus adjudication)")
    print(f"  [Rejected / Unsuitable]    {summary['verification_breakdown']['rejected_unsuitable']:4d}")
    print("-" * 70)
    print(f"Overall Completion Rate:     {summary['completion_rate_pct']}%")
    print(f"Metric Calculation State:    {summary['evaluation_readiness']}")
    print(f"Uncertain Mentions Count:    {summary['uncertainty_count']} (Excluded from metrics)")
    print("-" * 70)
    print("Tagged Content Density:")
    print(f"  Entities: {summary['annotation_density']['total_entities_tagged']} | Negations: {summary['annotation_density']['total_negations_scoped']} | Statuses: {summary['annotation_density']['total_investigations_classified']}")
    print(f"  Guidelines: {summary['annotation_density']['total_guidelines_judged']} | Decision Gaps: {summary['annotation_density']['total_decision_gaps_judged']}")
    print("-" * 70)
    print("Per-Case Progress Status:")
    for c in summary.get("cases_overview", []):
        v_tag = f"[{c['verification_status']}]"
        print(f"  Case {c['case_index']:2d} (ID: {c['record_id']:3d}, {c['specialty']:16s}): {v_tag:30s} -> {c['entities']:2d} ents, {c['negations']:2d} negs, {c['investigations']:2d} invs")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    default_pilot = os.path.join(os.path.dirname(__file__), "pilot_10_cases", "pilot_10_cases.json")
    target = sys.argv[1] if len(sys.argv) > 1 else default_pilot
    print_progress_report(target)
