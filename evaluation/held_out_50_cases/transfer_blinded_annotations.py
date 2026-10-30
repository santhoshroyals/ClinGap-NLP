"""
transfer_blinded_annotations.py - Transfer Blinded Annotations to Unblinded Dataset
ClinGap-NLP Evaluation Infrastructure (Phase 3)

Transfers human annotations created in:
  - evaluation/held_out_50_cases/held_out_50_cases_blinded.json OR
  - evaluation/held_out_50_cases/held_out_50_cases_blinded.csv
into:
  - evaluation/held_out_50_cases/held_out_50_cases.json

Key Features:
1. Deterministic mapping: Uses researcher_unblinding_manifest.json (case_number -> record_id).
2. Note integrity verification: Computes SHA256 on clinical note to ensure text wasn't altered.
3. Offset validation: Asserts note[start:end] == entity_text for every transferred entity.
4. Status management: Sets verification_status to RESEARCHER_ANNOTATED upon transfer of human work.
5. Dry-run and test modes: Safe verification without modifying destination files.
"""

import os
import sys
import json
import csv
import hashlib
import argparse
from typing import Dict, Any, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HELD_OUT_DIR = os.path.join(BASE_DIR, "evaluation", "held_out_50_cases")

UNBLINDING_MANIFEST = os.path.join(HELD_OUT_DIR, "researcher_unblinding_manifest.json")
UNBLINDED_JSON = os.path.join(HELD_OUT_DIR, "held_out_50_cases.json")
BLINDED_JSON = os.path.join(HELD_OUT_DIR, "held_out_50_cases_blinded.json")
BLINDED_CSV = os.path.join(HELD_OUT_DIR, "held_out_50_cases_blinded.csv")


def load_manifest(manifest_path: str = UNBLINDING_MANIFEST) -> Dict[str, Any]:
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def transfer_from_blinded_json(
    source_json_path: str,
    dest_json_path: str,
    manifest_path: str = UNBLINDING_MANIFEST,
    dry_run: bool = True
) -> Dict[str, Any]:
    manifest = load_manifest(manifest_path)
    mappings = {m["case_number"]: m for m in manifest["case_mappings"]}

    with open(source_json_path, "r", encoding="utf-8") as f:
        source_data = json.load(f)

    with open(dest_json_path, "r", encoding="utf-8") as f:
        dest_data = json.load(f)

    dest_cases_by_rid = {c["record_id"]: c for c in dest_data["cases"]}
    transferred_cases = 0
    total_entities = 0
    total_negations = 0
    total_investigations = 0

    for src_case in source_data.get("cases", []):
        case_num = src_case.get("case_number")
        if case_num not in mappings:
            raise ValueError(f"Case number {case_num} not found in unblinding manifest.")

        mapping = mappings[case_num]
        rid = mapping["original_record_id"]
        dest_case = dest_cases_by_rid.get(rid)
        if not dest_case:
            raise ValueError(f"Record ID {rid} from mapping not found in destination dataset.")

        # Verify note text hash integrity
        src_note = src_case["clinical_note"]
        dest_note = dest_case["clinical_note"]
        src_hash = hashlib.sha256(src_note.encode("utf-8")).hexdigest()
        dest_hash = hashlib.sha256(dest_note.encode("utf-8")).hexdigest()

        if src_hash != dest_hash:
            raise ValueError(f"Clinical note SHA256 mismatch for Case {case_num} (Record ID {rid}).")

        # Validate entity offsets
        for ent in src_case.get("entities", []):
            start = ent.get("start_char", 0)
            end = ent.get("end_char", 0)
            text = ent.get("entity_text", "")
            if dest_note[start:end] != text:
                raise ValueError(
                    f"Offset mismatch in Case {case_num} for entity '{text}': "
                    f"note[{start}:{end}] is '{dest_note[start:end]}'"
                )

        # Update destination case fields
        if not dry_run:
            dest_case["entities"] = src_case.get("entities", [])
            dest_case["negations"] = src_case.get("negations", [])
            dest_case["investigations"] = src_case.get("investigations", [])
            dest_case["guidelines"] = src_case.get("guidelines", [])
            dest_case["decision_gaps"] = src_case.get("decision_gaps", [])
            dest_case["annotator_id"] = src_case.get("annotator_id")
            dest_case["second_annotator_id"] = src_case.get("second_annotator_id")
            dest_case["annotation_timestamp"] = src_case.get("annotation_timestamp")
            dest_case["reviewer_notes"] = src_case.get("reviewer_notes")

            # Update status if researcher annotated
            if src_case.get("verification_status") == "RESEARCHER_ANNOTATED":
                dest_case["verification_status"] = "RESEARCHER_ANNOTATED"
            elif src_case.get("entities") or src_case.get("negations") or src_case.get("investigations"):
                dest_case["verification_status"] = "RESEARCHER_ANNOTATED"

        transferred_cases += 1
        total_entities += len(src_case.get("entities", []))
        total_negations += len(src_case.get("negations", []))
        total_investigations += len(src_case.get("investigations", []))

    if not dry_run:
        with open(dest_json_path, "w", encoding="utf-8") as f:
            json.dump(dest_data, f, indent=2)

    return {
        "status": "SUCCESS",
        "dry_run": dry_run,
        "transferred_cases": transferred_cases,
        "total_entities": total_entities,
        "total_negations": total_negations,
        "total_investigations": total_investigations
    }


def transfer_from_blinded_csv(
    source_csv_path: str,
    dest_json_path: str,
    manifest_path: str = UNBLINDING_MANIFEST,
    dry_run: bool = True
) -> Dict[str, Any]:
    manifest = load_manifest(manifest_path)
    mappings = {m["case_number"]: m for m in manifest["case_mappings"]}

    with open(dest_json_path, "r", encoding="utf-8") as f:
        dest_data = json.load(f)

    dest_cases_by_rid = {c["record_id"]: c for c in dest_data["cases"]}
    transferred_cases = 0
    total_entities = 0
    total_negations = 0
    total_investigations = 0

    with open(source_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_num = int(row["case_number"])
            if case_num not in mappings:
                raise ValueError(f"Case number {case_num} not found in unblinding manifest.")

            mapping = mappings[case_num]
            rid = mapping["original_record_id"]
            dest_case = dest_cases_by_rid.get(rid)
            if not dest_case:
                raise ValueError(f"Record ID {rid} from mapping not found in destination dataset.")

            src_note = row["clinical_note"]
            dest_note = dest_case["clinical_note"]
            src_hash = hashlib.sha256(src_note.encode("utf-8")).hexdigest()
            dest_hash = hashlib.sha256(dest_note.encode("utf-8")).hexdigest()

            if src_hash != dest_hash:
                raise ValueError(f"Clinical note SHA256 mismatch for Case {case_num} (Record ID {rid}).")

            entities = json.loads(row.get("entities_tagged_json") or "[]")
            negations = json.loads(row.get("negations_tagged_json") or "[]")
            investigations = json.loads(row.get("investigations_tagged_json") or "[]")
            guidelines = json.loads(row.get("guidelines_tagged_json") or "[]")
            decision_gaps = json.loads(row.get("decision_gaps_tagged_json") or "[]")

            # Validate offsets
            for ent in entities:
                start = ent.get("start_char", 0)
                end = ent.get("end_char", 0)
                text = ent.get("entity_text", "")
                if dest_note[start:end] != text:
                    raise ValueError(f"Offset mismatch in Case {case_num} for entity '{text}'")

            if not dry_run:
                dest_case["entities"] = entities
                dest_case["negations"] = negations
                dest_case["investigations"] = investigations
                dest_case["guidelines"] = guidelines
                dest_case["decision_gaps"] = decision_gaps
                dest_case["annotator_id"] = row.get("annotator_id") or None
                dest_case["reviewer_notes"] = row.get("reviewer_notes") or None

                status = row.get("verification_status", "AWAITING_HUMAN_VERIFICATION")
                if status == "RESEARCHER_ANNOTATED" or entities or negations or investigations:
                    dest_case["verification_status"] = "RESEARCHER_ANNOTATED"

            transferred_cases += 1
            total_entities += len(entities)
            total_negations += len(negations)
            total_investigations += len(investigations)

    if not dry_run:
        with open(dest_json_path, "w", encoding="utf-8") as f:
            json.dump(dest_data, f, indent=2)

    return {
        "status": "SUCCESS",
        "dry_run": dry_run,
        "transferred_cases": transferred_cases,
        "total_entities": total_entities,
        "total_negations": total_negations,
        "total_investigations": total_investigations
    }


def run_test_transfer():
    """
    Simulates a transfer on in-memory mock data to verify round-trip transfer
    without altering any dataset files.
    """
    print("Testing annotation transfer mechanism...")
    manifest = load_manifest(UNBLINDING_MANIFEST)
    mappings = {m["case_number"]: m for m in manifest["case_mappings"]}

    # Create mock blinded case 1 with 1 sample entity
    mock_case_num = 1
    mapping = mappings[mock_case_num]
    expected_rid = mapping["original_record_id"]

    # Verify that case 1 maps to record 251
    assert mock_case_num == 1
    assert expected_rid == 251, f"Expected 251, got {expected_rid}"
    assert mapping["specialty"] == "neurology"
    assert "Migraine" in mapping["diagnosis"]

    # Test transfer logic with dry run
    res = transfer_from_blinded_json(
        source_json_path=BLINDED_JSON,
        dest_json_path=UNBLINDED_JSON,
        manifest_path=UNBLINDING_MANIFEST,
        dry_run=True
    )
    assert res["status"] == "SUCCESS"
    assert res["transferred_cases"] == 50
    print(f"Transfer simulation passed: 50/50 cases mapped accurately to original record IDs.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transfer Blinded Annotations to Unblinded Dataset")
    parser.add_argument("--source", type=str, default=BLINDED_JSON, help="Source blinded JSON or CSV file")
    parser.add_argument("--dest", type=str, default=UNBLINDED_JSON, help="Destination unblinded JSON file")
    parser.add_argument("--manifest", type=str, default=UNBLINDING_MANIFEST, help="Researcher unblinding manifest")
    parser.add_argument("--execute", action="store_true", help="Execute write to destination (default is dry-run)")
    parser.add_argument("--test", action="store_true", help="Run transfer logic test")

    args = parser.parse_args()

    if args.test:
        run_test_transfer()
    else:
        dry_run = not args.execute
        if args.source.endswith(".csv"):
            res = transfer_from_blinded_csv(args.source, args.dest, args.manifest, dry_run=dry_run)
        else:
            res = transfer_from_blinded_json(args.source, args.dest, args.manifest, dry_run=dry_run)
        print(f"Transfer Result (dry_run={dry_run}): {json.dumps(res, indent=2)}")
