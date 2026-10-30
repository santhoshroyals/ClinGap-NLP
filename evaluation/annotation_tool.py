"""
annotation_tool.py - Researcher Annotation Workflow Assistant
ClinGap-NLP Evaluation Infrastructure (Phase 1 & 2)

Key Features:
- Eliminates manual character-offset math: Automatically locates entity spans in clinical text.
- Validates offset integrity: Asserts note[start:end] == entity_text.
- Supports physical signs and vital signs with clinical_subkind and polarity (+/-).
- Supports precise negation cue offsets, scope offsets, and mixed-language Hinglish expressions.
- Supports linking diagnostic investigation names to documented findings/results.
- Supports marking annotations as UNCERTAIN with accompanying rationale.
- Supports interactive terminal walkthrough or direct CLI command inputs.
- Finalizes cases with status RESEARCHER_ANNOTATED and annotator provenance.
- NEVER calls or pre-populates labels using ClinGap-NLP predictions.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PILOT_JSON = os.path.join(BASE_DIR, "evaluation", "pilot_10_cases", "pilot_10_cases.json")


def load_pilot_batch(file_path: str = PILOT_JSON) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_pilot_batch(batch: Dict[str, Any], file_path: str = PILOT_JSON):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(batch, f, indent=2)


def get_case_by_identifier(batch: Dict[str, Any], identifier: Any) -> Tuple[int, Dict[str, Any]]:
    cases = batch.get("cases", [])
    # Check if identifier is 1-based index (e.g. 1 to 10)
    try:
        idx = int(identifier)
        if 1 <= idx <= len(cases):
            return idx - 1, cases[idx - 1]
    except ValueError:
        pass

    # Check if identifier matches record_id
    for i, c in enumerate(cases):
        if str(c.get("record_id")) == str(identifier):
            return i, c

    raise ValueError(f"Case '{identifier}' not found in batch of {len(cases)} cases.")


def find_entity_span(
    note: str,
    entity_text: str,
    occurrence: int = 1,
    context: Optional[str] = None
) -> Tuple[int, int]:
    """
    Finds exact 0-indexed character offsets for entity_text in note.
    Occurrence: 1-indexed (e.g. 1 for first occurrence, 2 for second).
    If context is provided, searches within that context snippet first to avoid
    offset collisions on short substrings (e.g. 'no' inside 'no syncope').
    """
    clean_text = entity_text.strip()
    if context:
        ctx_clean = context.strip()
        ctx_pos = note.find(ctx_clean)
        if ctx_pos != -1:
            rel_idx = ctx_clean.find(clean_text)
            if rel_idx != -1:
                start_char = ctx_pos + rel_idx
                end_char = start_char + len(clean_text)
                assert note[start_char:end_char] == clean_text, "Context span mismatch"
                return start_char, end_char

    idx = -1
    for _ in range(occurrence):
        idx = note.find(clean_text, idx + 1)
        if idx == -1:
            break

    if idx == -1:
        # Case-insensitive fallback
        import re
        matches = [m.span() for m in re.finditer(re.escape(clean_text), note, re.IGNORECASE)]
        if matches and 1 <= occurrence <= len(matches):
            return matches[occurrence - 1]
        raise ValueError(f"Entity text '{clean_text}' not found (occurrence {occurrence}) in clinical note.")

    start_char = idx
    end_char = idx + len(clean_text)
    assert note[start_char:end_char] == clean_text, "Span mismatch assertion failed"
    return start_char, end_char


def view_case(identifier: Any, file_path: str = PILOT_JSON):
    """Displays note with line numbers and existing annotations."""
    batch = load_pilot_batch(file_path)
    idx, case = get_case_by_identifier(batch, identifier)

    print("\n" + "=" * 78)
    print(f"CASE {idx + 1} / {len(batch['cases'])} | Record ID: {case['record_id']} | Specialty: {case['specialty'].upper()}")
    print(f"Diagnosis: {case.get('diagnosis', 'UNKNOWN')}")
    print(f"Status: {case['verification_status']} | Annotator: {case['annotator_id'] or 'NONE'}")
    print("=" * 78)
    print("CLINICAL NOTE TEXT:")
    print("-" * 78)
    lines = case["clinical_note"].split("\n")
    for l_no, line in enumerate(lines, 1):
        print(f"{l_no:3d} | {line}")
    print("-" * 78)

    # Display current annotations
    print(f"Entities Tagged ({len(case.get('entities', []))}):")
    for e in case.get("entities", []):
        u_flag = " [UNCERTAIN]" if e.get("is_uncertain") else ""
        subkind = f" [subkind: {e['clinical_subkind']}]" if e.get("clinical_subkind") else ""
        pol = f" [polarity: {e['finding_polarity']}]" if e.get("finding_polarity") else ""
        print(f"  [{e['entity_type']}] \"{e['entity_text']}\" ({e['start_char']}:{e['end_char']}){subkind}{pol}{u_flag}")

    print(f"\nNegations Scoped ({len(case.get('negations', []))}):")
    for n in case.get("negations", []):
        u_flag = " [UNCERTAIN]" if n.get("is_uncertain") else ""
        cue_info = f" (cue: '{n.get('negation_cue')}' {n.get('cue_offsets') or ''})" if n.get("negation_cue") else ""
        scope_info = f" [scope: '{n.get('scope_text')}' {n.get('scope_offsets') or ''}]" if n.get("scope_text") else ""
        lang_info = f" [{n.get('language')}]" if n.get("language") and n.get("language") != "en" else ""
        norm_info = f" -> {n.get('normalized_assertion')}" if n.get("normalized_assertion") else ""
        print(f"  \"{n['entity_text']}\" -> is_negated: {n['is_negated']}{cue_info}{scope_info}{lang_info}{norm_info}{u_flag}")

    print(f"\nInvestigations Status ({len(case.get('investigations', []))}):")
    for inv in case.get("investigations", []):
        u_flag = " [UNCERTAIN]" if inv.get("is_uncertain") else ""
        finding = f" | finding: \"{inv.get('finding_result')}\" [{inv.get('finding_category') or 'unspecified'}]" if inv.get("finding_result") else ""
        ev = f" (ev: \"{inv.get('evidence_snippet')}\")" if inv.get("evidence_snippet") else ""
        print(f"  \"{inv['investigation_name']}\" -> status: {inv['status']}{finding}{ev}{u_flag}")
    print("=" * 78 + "\n")


def add_entity_to_case(
    identifier: Any,
    entity_text: str,
    entity_type: str,
    normalized_value: Optional[str] = None,
    clinical_subkind: Optional[str] = None,
    finding_polarity: Optional[str] = None,
    occurrence: int = 1,
    context: Optional[str] = None,
    is_uncertain: bool = False,
    uncertainty_note: Optional[str] = None,
    file_path: str = PILOT_JSON
):
    batch = load_pilot_batch(file_path)
    idx, case = get_case_by_identifier(batch, identifier)

    valid_types = {
        "DISEASE", "SYMPTOM", "MEDICATION", "INVESTIGATION",
        "DOSAGE", "FREQUENCY", "LAB_TEST", "PHYSICAL_SIGN", "VITAL_SIGN"
    }
    etype_clean = entity_type.strip().upper()
    if etype_clean not in valid_types:
        raise ValueError(f"Invalid entity type '{entity_type}'. Must be one of: {sorted(list(valid_types))}")

    start_char, end_char = find_entity_span(case["clinical_note"], entity_text, occurrence, context=context)

    entity_record = {
        "start_char": start_char,
        "end_char": end_char,
        "entity_text": entity_text.strip(),
        "entity_type": etype_clean,
        "clinical_subkind": clinical_subkind,
        "finding_polarity": finding_polarity,
        "normalized_value": normalized_value or entity_text.strip().lower(),
        "is_uncertain": bool(is_uncertain),
        "uncertainty_note": uncertainty_note
    }

    if "entities" not in case:
        case["entities"] = []
    case["entities"].append(entity_record)

    save_pilot_batch(batch, file_path)
    print(f"Added [{etype_clean}] '{entity_text}' [{start_char}:{end_char}] to Case {idx + 1}")


def add_negation_to_case(
    identifier: Any,
    entity_text: str,
    is_negated: bool = True,
    negation_cue: Optional[str] = None,
    scope_text: Optional[str] = None,
    language: str = "en",
    normalized_assertion: Optional[str] = None,
    is_uncertain: bool = False,
    uncertainty_note: Optional[str] = None,
    file_path: str = PILOT_JSON,
    **kwargs
):
    # Accept is_neg keyword argument for backward compatibility
    if "is_neg" in kwargs:
        is_negated = kwargs["is_neg"]

    batch = load_pilot_batch(file_path)
    idx, case = get_case_by_identifier(batch, identifier)
    note = case["clinical_note"]
    clean_ent = entity_text.strip()

    # If scope_text not provided, auto-extract the surrounding clinical clause/line
    # containing entity_text to provide localized context for cue offset discovery
    derived_scope = scope_text
    if not derived_scope:
        ent_pos = note.find(clean_ent)
        if ent_pos != -1:
            left = max(note.rfind('\n', 0, ent_pos), 0)
            right = note.find('\n', ent_pos)
            if right == -1:
                right = len(note)
            line_snippet = note[left:right].strip()
            if ": " in line_snippet:
                _, _, candidate = line_snippet.partition(": ")
                candidate = candidate.strip()
            else:
                candidate = line_snippet
            if (negation_cue and negation_cue in candidate) or not negation_cue:
                derived_scope = candidate

    cue_offsets = None
    if negation_cue:
        c_start, c_end = find_entity_span(note, negation_cue, context=derived_scope)
        cue_offsets = [c_start, c_end]

    scope_offsets = None
    if derived_scope:
        try:
            s_start, s_end = find_entity_span(note, derived_scope)
            scope_offsets = [s_start, s_end]
        except ValueError:
            pass

    neg_record = {
        "entity_text": clean_ent,
        "is_negated": bool(is_negated),
        "negation_cue": negation_cue,
        "cue_offsets": cue_offsets,
        "scope_text": derived_scope,
        "scope_offsets": scope_offsets,
        "language": language,
        "normalized_assertion": normalized_assertion,
        "is_uncertain": bool(is_uncertain),
        "uncertainty_note": uncertainty_note
    }

    if "negations" not in case:
        case["negations"] = []
    case["negations"].append(neg_record)

    save_pilot_batch(batch, file_path)
    print(f"Added Negation assertion for '{clean_ent}' (is_negated={is_negated}, cue='{negation_cue}') to Case {idx + 1}")


def update_negation_in_case(
    identifier: Any,
    entity_text: str,
    is_negated: Optional[bool] = None,
    negation_cue: Optional[str] = None,
    scope_text: Optional[str] = None,
    language: Optional[str] = None,
    normalized_assertion: Optional[str] = None,
    is_uncertain: Optional[bool] = None,
    file_path: str = PILOT_JSON,
    **kwargs
):
    if "is_neg" in kwargs and is_negated is None:
        is_negated = kwargs["is_neg"]

    batch = load_pilot_batch(file_path)
    idx, case = get_case_by_identifier(batch, identifier)
    note = case["clinical_note"]

    target_neg = None
    for n in case.get("negations", []):
        if n.get("entity_text", "").strip().lower() == entity_text.strip().lower():
            target_neg = n
            break

    if target_neg is None:
        raise ValueError(f"Negation for entity '{entity_text}' not found in Case {idx + 1}")

    if is_negated is not None:
        target_neg["is_negated"] = bool(is_negated)

    if scope_text is not None:
        target_neg["scope_text"] = scope_text
        s_start, s_end = find_entity_span(note, scope_text)
        target_neg["scope_offsets"] = [s_start, s_end]

    if negation_cue is not None:
        target_neg["negation_cue"] = negation_cue
        c_start, c_end = find_entity_span(note, negation_cue, context=target_neg.get("scope_text"))
        target_neg["cue_offsets"] = [c_start, c_end]

    if language is not None:
        target_neg["language"] = language

    if normalized_assertion is not None:
        target_neg["normalized_assertion"] = normalized_assertion

    if is_uncertain is not None:
        target_neg["is_uncertain"] = bool(is_uncertain)

    save_pilot_batch(batch, file_path)
    print(f"Updated Negation assertion for '{entity_text}' in Case {idx + 1}")


def add_investigation_to_case(
    identifier: Any,
    investigation_name: str,
    status: str,
    evidence_snippet: Optional[str] = None,
    finding_result: Optional[str] = None,
    finding_category: Optional[str] = None,
    is_uncertain: bool = False,
    uncertainty_note: Optional[str] = None,
    file_path: str = PILOT_JSON
):
    batch = load_pilot_batch(file_path)
    idx, case = get_case_by_identifier(batch, identifier)
    note = case["clinical_note"]

    valid_statuses = {"completed/performed", "ordered", "pending", "not performed/cancelled", "undocumented"}
    st_clean = status.strip().lower()
    if st_clean not in valid_statuses:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {sorted(list(valid_statuses))}")

    finding_offsets = None
    if finding_result:
        f_start, f_end = find_entity_span(note, finding_result)
        finding_offsets = [f_start, f_end]

    inv_record = {
        "investigation_name": investigation_name.strip(),
        "status": st_clean,
        "evidence_snippet": evidence_snippet,
        "finding_result": finding_result,
        "finding_offsets": finding_offsets,
        "finding_category": finding_category,
        "is_uncertain": bool(is_uncertain),
        "uncertainty_note": uncertainty_note
    }

    if "investigations" not in case:
        case["investigations"] = []
    case["investigations"].append(inv_record)

    save_pilot_batch(batch, file_path)
    print(f"Added Investigation '{investigation_name}' (status='{st_clean}') to Case {idx + 1}")


def link_investigation_finding(
    identifier: Any,
    investigation_name: str,
    finding_result: str,
    finding_category: str = "unspecified",
    evidence_snippet: Optional[str] = None,
    file_path: str = PILOT_JSON
):
    batch = load_pilot_batch(file_path)
    idx, case = get_case_by_identifier(batch, identifier)
    note = case["clinical_note"]

    target_inv = None
    for inv in case.get("investigations", []):
        if inv.get("investigation_name", "").strip().lower() == investigation_name.strip().lower():
            target_inv = inv
            break

    if target_inv is None:
        target_inv = {
            "investigation_name": investigation_name.strip(),
            "status": "completed/performed",
            "evidence_snippet": evidence_snippet or f"{investigation_name}: {finding_result}",
            "is_uncertain": False,
            "uncertainty_note": None
        }
        if "investigations" not in case:
            case["investigations"] = []
        case["investigations"].append(target_inv)

    f_start, f_end = find_entity_span(note, finding_result)
    target_inv["finding_result"] = finding_result.strip()
    target_inv["finding_offsets"] = [f_start, f_end]
    target_inv["finding_category"] = finding_category
    if evidence_snippet:
        target_inv["evidence_snippet"] = evidence_snippet

    save_pilot_batch(batch, file_path)
    print(f"Linked finding '{finding_result}' [{f_start}:{f_end}] ({finding_category}) to Investigation '{investigation_name}' in Case {idx + 1}")


def finalize_case(
    identifier: Any,
    annotator_id: str = "researcher_1",
    reviewer_notes: Optional[str] = None,
    file_path: str = PILOT_JSON
):
    batch = load_pilot_batch(file_path)
    idx, case = get_case_by_identifier(batch, identifier)

    case["verification_status"] = "RESEARCHER_ANNOTATED"
    case["annotator_id"] = annotator_id
    case["annotation_timestamp"] = datetime.now().isoformat()
    if reviewer_notes:
        case["reviewer_notes"] = reviewer_notes

    save_pilot_batch(batch, file_path)
    print(f"SUCCESS: Case {idx + 1} (Record ID: {case['record_id']}) finalized as RESEARCHER_ANNOTATED by {annotator_id}.")


def interactive_annotator(identifier: Any, file_path: str = PILOT_JSON):
    """Simple interactive CLI loop to annotate a case."""
    view_case(identifier, file_path)
    print("Interactive Annotation Mode. Type 'help' for commands or 'exit' to quit.")
    while True:
        try:
            cmd = input(f"Case {identifier} > ").strip()
            if not cmd or cmd == "exit":
                break
            parts = cmd.split(maxsplit=2)
            action = parts[0].lower()

            if action == "help":
                print("Commands:")
                print("  ent <text> <TYPE> [norm]       Add clinical entity")
                print("  neg <text> <true|false> [cue]  Add negation assertion")
                print("  inv <name> <status>            Add investigation status")
                print("  link <inv_name> <finding>      Link finding to investigation")
                print("  view                           Redisplay case")
                print("  done [annotator_id]            Finalize case as RESEARCHER_ANNOTATED")
                print("  exit                           Exit without finalizing")
            elif action == "view":
                view_case(identifier, file_path)
            elif action == "ent" and len(parts) >= 3:
                ent_text = parts[1].strip('"').strip("'")
                subparts = parts[2].split()
                etype = subparts[0]
                norm = subparts[1] if len(subparts) > 1 else None
                add_entity_to_case(identifier, ent_text, etype, norm, file_path=file_path)
            elif action == "neg" and len(parts) >= 3:
                ent_text = parts[1].strip('"').strip("'")
                subparts = parts[2].split()
                is_neg = subparts[0].lower() in {"true", "1", "yes", "y"}
                cue = subparts[1] if len(subparts) > 1 else None
                add_negation_to_case(identifier, ent_text, is_neg, cue, file_path=file_path)
            elif action == "inv" and len(parts) >= 3:
                inv_name = parts[1].strip('"').strip("'")
                status = parts[2].strip()
                add_investigation_to_case(identifier, inv_name, status, file_path=file_path)
            elif action == "link" and len(parts) >= 3:
                inv_name = parts[1].strip('"').strip("'")
                finding = parts[2].strip('"').strip("'")
                link_investigation_finding(identifier, inv_name, finding, file_path=file_path)
            elif action == "done":
                ann_id = parts[1] if len(parts) > 1 else "researcher_1"
                finalize_case(identifier, ann_id, file_path=file_path)
                break
            else:
                print(f"Unknown command: {cmd}. Type 'help' for syntax.")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Researcher Annotation Tool for ClinGap-NLP")
    parser.add_argument("--view", type=str, help="View a case by 1-based index (1-10) or record_id")
    parser.add_argument("--interactive", type=str, help="Start interactive annotation session for a case")
    parser.add_argument("--add-entity", nargs=3, metavar=("CASE", "TEXT", "TYPE"), help="Add an entity: CASE TEXT TYPE")
    parser.add_argument("--subkind", type=str, help="Clinical subkind for entity (e.g. physical_sign, vital_sign)")
    parser.add_argument("--polarity", type=str, help="Documented finding polarity (positive, negative, normal, abnormal)")
    parser.add_argument("--context", type=str, help="Context snippet to disambiguate span matching")
    parser.add_argument("--add-negation", nargs=3, metavar=("CASE", "TEXT", "IS_NEG"), help="Add negation: CASE TEXT TRUE/FALSE")
    parser.add_argument("--cue", type=str, help="Negation lexical cue phrase (e.g. 'no', 'nahi hai')")
    parser.add_argument("--scope", type=str, help="Negation scope clause/sentence")
    parser.add_argument("--language", type=str, default="en", help="Language (en, hinglish, hi)")
    parser.add_argument("--normalized", type=str, help="Normalized assertion or canonical terminology")
    parser.add_argument("--update-negation", nargs=2, metavar=("CASE", "TEXT"), help="Update existing negation: CASE TEXT")
    parser.add_argument("--add-inv", nargs=3, metavar=("CASE", "NAME", "STATUS"), help="Add investigation: CASE NAME STATUS")
    parser.add_argument("--link-finding", nargs=3, metavar=("CASE", "NAME", "FINDING"), help="Link finding to investigation: CASE NAME FINDING")
    parser.add_argument("--finding-category", type=str, default="unspecified", help="Finding category (normal, abnormal, neutral, unknown)")
    parser.add_argument("--finalize", type=str, help="Finalize case as RESEARCHER_ANNOTATED")
    parser.add_argument("--annotator", type=str, default="researcher_1", help="Annotator ID")
    parser.add_argument("--file", type=str, default=PILOT_JSON, help="Path to pilot JSON file")

    args = parser.parse_args()

    if args.view:
        view_case(args.view, args.file)
    elif args.interactive:
        interactive_annotator(args.interactive, args.file)
    elif args.add_entity:
        add_entity_to_case(
            args.add_entity[0],
            args.add_entity[1],
            args.add_entity[2],
            clinical_subkind=args.subkind,
            finding_polarity=args.polarity,
            context=args.context,
            file_path=args.file
        )
    elif args.add_negation:
        is_neg = args.add_negation[2].lower() in {"true", "1", "yes", "y"}
        add_negation_to_case(
            args.add_negation[0],
            args.add_negation[1],
            is_negated=is_neg,
            negation_cue=args.cue,
            scope_text=args.scope,
            language=args.language,
            normalized_assertion=args.normalized,
            file_path=args.file
        )
    elif args.update_negation:
        update_negation_in_case(
            args.update_negation[0],
            args.update_negation[1],
            negation_cue=args.cue,
            scope_text=args.scope,
            language=args.language,
            normalized_assertion=args.normalized,
            file_path=args.file
        )
    elif args.link_finding:
        link_investigation_finding(
            args.link_finding[0],
            args.link_finding[1],
            args.link_finding[2],
            finding_category=args.finding_category,
            file_path=args.file
        )
    elif args.add_inv:
        add_investigation_to_case(args.add_inv[0], args.add_inv[1], args.add_inv[2], file_path=args.file)
    elif args.finalize:
        finalize_case(args.finalize, args.annotator, file_path=args.file)
    else:
        parser.print_help()
