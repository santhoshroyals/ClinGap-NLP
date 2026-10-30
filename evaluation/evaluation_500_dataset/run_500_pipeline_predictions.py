"""
run_500_pipeline_predictions.py
================================
Executes the ClinGap-NLP production ClinicalPipeline on all 500 records from
evaluation/evaluation_500_dataset/evaluation_500_notes.json.

Requirements:
1. Run all 500 notes through the existing ClinicalPipeline.
2. Do not modify the model, rules, or pipeline.
3. Save predictions separately in:
   - evaluation/evaluation_500_dataset/model_predictions_500.json
   - evaluation/evaluation_500_dataset/model_predictions_500.csv
4. For every evaluation ID, save:
   - Extracted clinical entities and entity types
   - Negation status
   - Investigation names
   - Investigation execution status
   - Potential decision gaps
   - Supporting evidence and confidence, if available
5. Include processing success/failure and error messages.
6. Verify that all 500 evaluation IDs are accounted for.
7. Do not generate ground-truth labels or calculate accuracy by comparing predictions against themselves.
8. Preserve all existing dataset and annotation files.
"""

import os
import sys
import time
import json
import csv
from datetime import datetime
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any, Optional

# Setup import paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.clinical_pipeline import ClinicalPipeline
from backend.services.model_manager import ModelManager

INPUT_JSON_PATH = SCRIPT_DIR / "evaluation_500_notes.json"
OUTPUT_JSON_PATH = SCRIPT_DIR / "model_predictions_500.json"
OUTPUT_CSV_PATH = SCRIPT_DIR / "model_predictions_500.csv"
CHECKPOINT_PATH = SCRIPT_DIR / "model_predictions_500_checkpoint.json"


def load_input_dataset() -> List[Dict[str, Any]]:
    if not INPUT_JSON_PATH.exists():
        raise FileNotFoundError(f"Input evaluation dataset not found: {INPUT_JSON_PATH}")
    with open(INPUT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    records = data.get("records", [])
    if len(records) != 500:
        raise ValueError(f"Expected exactly 500 records in {INPUT_JSON_PATH}, found {len(records)}")
    return records


def load_checkpoint() -> Dict[str, Dict[str, Any]]:
    if CHECKPOINT_PATH.exists():
        try:
            with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                ckpt = json.load(f)
            print(f"[CHECKPOINT] Loaded {len(ckpt)} existing processed records from checkpoint.")
            return ckpt
        except Exception as e:
            print(f"[WARNING] Could not read checkpoint: {e}. Starting fresh.")
    return {}


def save_checkpoint(records_dict: Dict[str, Dict[str, Any]]) -> None:
    temp_path = CHECKPOINT_PATH.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(records_dict, f, indent=2, ensure_ascii=False)
    temp_path.replace(CHECKPOINT_PATH)


def process_note_record(pipeline: ClinicalPipeline, rec: Dict[str, Any]) -> Dict[str, Any]:
    eval_id = rec["eval_id"]
    source_corpus = rec["source_corpus"]
    source_record_id = rec["source_record_id"]
    medical_specialty = rec["medical_specialty"]
    diagnosis_or_sample = rec.get("diagnosis_or_sample_name", "")
    clinical_note = rec["clinical_note"]

    t_start = time.perf_counter()
    try:
        pipeline_res = pipeline.run(db=None, text=clinical_note)
        elapsed_sec = round(time.perf_counter() - t_start, 4)

        raw_entities = pipeline_res.get("entities", [])
        raw_gaps = pipeline_res.get("gaps", [])
        raw_confidence = pipeline_res.get("confidence", 0.0)
        raw_explanation = pipeline_res.get("explanation", {})
        raw_regimens = pipeline_res.get("regimens", [])
        raw_context = pipeline_res.get("context_info", {})
        ner_status = pipeline_res.get("ner_status", ModelManager.get_ner_status())

        # Clean entities & extract investigation / negation metadata
        entities_list: List[Dict[str, Any]] = []
        negated_entities_list: List[Dict[str, Any]] = []
        investigations_list: List[Dict[str, Any]] = []
        entity_types_counter = Counter()

        for ent in raw_entities:
            ent_text = ent.get("entity_text", "")
            ent_type = ent.get("entity_type", "UNKNOWN")
            norm_val = ent.get("normalized_value", ent_text.lower())
            conf = float(ent.get("confidence", 0.0))
            is_neg = bool(ent.get("negated", False))
            inv_status = ent.get("status") if ent_type == "INVESTIGATION" else None

            entity_entry = {
                "entity_text": ent_text,
                "entity_type": ent_type,
                "normalized_value": norm_val,
                "confidence": round(conf, 4),
                "source": ent.get("source", ""),
                "negated": is_neg,
                "status": inv_status,
            }
            entities_list.append(entity_entry)
            entity_types_counter[ent_type] += 1

            if is_neg:
                negated_entities_list.append({
                    "entity_text": ent_text,
                    "entity_type": ent_type,
                    "normalized_value": norm_val,
                })

            if ent_type == "INVESTIGATION":
                investigations_list.append({
                    "name": norm_val or ent_text.lower(),
                    "raw_text": ent_text,
                    "normalized_value": norm_val,
                    "status": inv_status or "unknown",
                    "negated": is_neg,
                })

        # Process potential decision gaps
        gaps_list: List[Dict[str, Any]] = []
        for g in raw_gaps:
            gaps_list.append({
                "gap_type": g.get("gap_type", "MISSING_INVESTIGATION"),
                "description": g.get("description", ""),
                "entity": g.get("entity", ""),
                "rule_id": g.get("rule_id"),
            })

        # Supporting evidence
        matched_rules = raw_explanation.get("matched_rules", [])
        gap_descriptions = [g.get("description", "") for g in gaps_list]
        supporting_evidence = {
            "matched_rules": matched_rules,
            "gap_descriptions": gap_descriptions,
            "summary": f"Matched rules: {', '.join(str(r) for r in matched_rules) if matched_rules else 'None'}. Gaps flagged: {len(gaps_list)}."
        }

        # Regimens
        regimens_list: List[Dict[str, Any]] = []
        for r in raw_regimens:
            regimens_list.append({
                "medication": r.get("medication", ""),
                "dosage": r.get("dosage", ""),
                "frequency": r.get("frequency", ""),
            })

        return {
            "eval_id": eval_id,
            "source_corpus": source_corpus,
            "source_record_id": source_record_id,
            "medical_specialty": medical_specialty,
            "diagnosis_or_sample_name": diagnosis_or_sample,
            "processing_status": "SUCCESS",
            "error_message": "",
            "processing_time_sec": elapsed_sec,
            "total_entities_count": len(entities_list),
            "entities_by_type_counts": dict(entity_types_counter),
            "entities": entities_list,
            "negated_entities_count": len(negated_entities_list),
            "negated_entities": negated_entities_list,
            "investigations_count": len(investigations_list),
            "investigations": investigations_list,
            "potential_decision_gaps_count": len(gaps_list),
            "potential_decision_gaps": gaps_list,
            "supporting_evidence": supporting_evidence,
            "pipeline_confidence": round(float(raw_confidence), 2),
            "regimens_count": len(regimens_list),
            "regimens": regimens_list,
            "context_info": raw_context,
            "ner_status": ner_status,
        }

    except Exception as exc:
        elapsed_sec = round(time.perf_counter() - t_start, 4)
        return {
            "eval_id": eval_id,
            "source_corpus": source_corpus,
            "source_record_id": source_record_id,
            "medical_specialty": medical_specialty,
            "diagnosis_or_sample_name": diagnosis_or_sample,
            "processing_status": "FAILED",
            "error_message": str(exc),
            "processing_time_sec": elapsed_sec,
            "total_entities_count": 0,
            "entities_by_type_counts": {},
            "entities": [],
            "negated_entities_count": 0,
            "negated_entities": [],
            "investigations_count": 0,
            "investigations": [],
            "potential_decision_gaps_count": 0,
            "potential_decision_gaps": [],
            "supporting_evidence": {"matched_rules": [], "gap_descriptions": [], "summary": f"Failed: {exc}"},
            "pipeline_confidence": 0.0,
            "regimens_count": 0,
            "regimens": [],
            "context_info": {},
            "ner_status": ModelManager.get_ner_status(),
        }


def format_csv_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Flattens a record dictionary into tabular CSV fields."""
    entities = rec.get("entities", [])
    negated = rec.get("negated_entities", [])
    invs = rec.get("investigations", [])
    gaps = rec.get("potential_decision_gaps", [])
    regimens = rec.get("regimens", [])
    supp_ev = rec.get("supporting_evidence", {})

    # Entity summaries
    ent_summary_parts = [f"{e['entity_text']} ({e['entity_type']})" for e in entities[:30]]
    if len(entities) > 30:
        ent_summary_parts.append(f"... (+{len(entities) - 30} more)")
    entities_summary_str = "; ".join(ent_summary_parts)

    # Negation status string
    if negated:
        neg_parts = [f"{n['entity_text']} ({n['entity_type']})" for n in negated]
        neg_str = "; ".join(neg_parts)
    else:
        neg_str = "None negated"

    # Investigation names and statuses
    inv_names = "; ".join(sorted(list({inv["name"] for inv in invs}))) if invs else "None"
    inv_statuses = "; ".join([f"{inv['name']}: {inv['status']}" for inv in invs]) if invs else "None"

    # Gaps summary
    if gaps:
        gap_parts = [f"{g['gap_type']}: {g['entity']} (rule: {g.get('rule_id') or 'direct'})" for g in gaps]
        gaps_summary_str = "; ".join(gap_parts)
    else:
        gaps_summary_str = "No gaps detected"

    # Regimens summary
    if regimens:
        reg_parts = [f"{r['medication']} ({r.get('dosage') or 'dose:unspecified'}, {r.get('frequency') or 'freq:unspecified'})" for r in regimens]
        reg_summary_str = "; ".join(reg_parts)
    else:
        reg_summary_str = "None"

    matched_rules_str = "; ".join(str(r) for r in supp_ev.get("matched_rules", [])) if supp_ev.get("matched_rules") else "None"

    return {
        "eval_id": rec["eval_id"],
        "source_corpus": rec["source_corpus"],
        "source_record_id": rec["source_record_id"],
        "medical_specialty": rec["medical_specialty"],
        "diagnosis_or_sample_name": rec.get("diagnosis_or_sample_name", ""),
        "processing_status": rec["processing_status"],
        "error_message": rec.get("error_message", ""),
        "processing_time_sec": rec["processing_time_sec"],
        "total_entities_count": rec["total_entities_count"],
        "entities_by_type_counts": json.dumps(rec.get("entities_by_type_counts", {}), ensure_ascii=False),
        "clinical_entities_summary": entities_summary_str,
        "clinical_entities_and_types": json.dumps([{"text": e["entity_text"], "type": e["entity_type"], "negated": e["negated"]} for e in entities], ensure_ascii=False),
        "negated_entities_count": rec["negated_entities_count"],
        "negated_entities": neg_str,
        "negated_entities_json": json.dumps(negated, ensure_ascii=False),
        "investigations_count": rec["investigations_count"],
        "investigation_names": inv_names,
        "investigation_execution_status": inv_statuses,
        "investigations_json": json.dumps(invs, ensure_ascii=False),
        "potential_decision_gaps_count": rec["potential_decision_gaps_count"],
        "potential_decision_gaps_summary": gaps_summary_str,
        "potential_decision_gaps_json": json.dumps(gaps, ensure_ascii=False),
        "matched_rules": matched_rules_str,
        "supporting_evidence": supp_ev.get("summary", ""),
        "pipeline_confidence": rec["pipeline_confidence"],
        "regimens_count": rec.get("regimens_count", 0),
        "regimens_summary": reg_summary_str,
        "regimens_json": json.dumps(regimens, ensure_ascii=False),
    }


def main():
    print("=" * 78)
    print("CLINGAP-NLP: 500-NOTE EVALUATION PIPELINE INFERENCE RUNNER")
    print("=" * 78)
    start_total_time = time.perf_counter()

    # 1. Load input dataset
    input_records = load_input_dataset()
    print(f"[INPUT] Loaded {len(input_records)} notes from {INPUT_JSON_PATH}")

    # 2. Initialize production pipeline
    print("[INIT] Initializing production ClinicalPipeline (Biomedical NER + Guideline Engine)...")
    pipeline = ClinicalPipeline()
    print("[INIT] Running model warmup...")
    _ = pipeline.run(db=None, text="Patient presented with mild fever. Complete blood count ordered.")
    print("[INIT] ClinicalPipeline initialized and warmed up successfully.")
    print(f"[STATUS] NER Status: {ModelManager.get_ner_status()}")

    # 3. Load checkpoint if present
    checkpoint = load_checkpoint()

    results_by_id: Dict[str, Dict[str, Any]] = dict(checkpoint)
    total_notes = len(input_records)
    newly_processed = 0

    print(f"\n[RUN] Beginning processing of {total_notes} records...")
    for idx, rec in enumerate(input_records, 1):
        eval_id = rec["eval_id"]

        if eval_id in results_by_id:
            continue

        pred = process_note_record(pipeline, rec)
        results_by_id[eval_id] = pred
        newly_processed += 1

        # Periodic checkpoint and console update
        if idx % 10 == 0 or idx == total_notes or newly_processed % 10 == 0:
            st = pred["processing_status"]
            dur = pred["processing_time_sec"]
            ent_c = pred["total_entities_count"]
            gap_c = pred["potential_decision_gaps_count"]
            print(f"[{idx:03d}/{total_notes:03d}] {eval_id} ({rec['source_corpus']}) -> {st} in {dur:.2f}s | Ents: {ent_c:2d}, Gaps: {gap_c}")

        if newly_processed % 25 == 0:
            save_checkpoint(results_by_id)

    # Save final checkpoint
    save_checkpoint(results_by_id)

    # 4. Verify all 500 evaluation IDs are accounted for
    expected_ids = [r["eval_id"] for r in input_records]
    missing_ids = [eid for eid in expected_ids if eid not in results_by_id]
    if missing_ids:
        raise RuntimeError(f"FATAL: Missing predictions for {len(missing_ids)} IDs: {missing_ids[:10]}...")

    ordered_records = [results_by_id[eid] for eid in expected_ids]

    successful_count = sum(1 for r in ordered_records if r["processing_status"] == "SUCCESS")
    failed_count = sum(1 for r in ordered_records if r["processing_status"] == "FAILED")

    total_time_elapsed = round(time.perf_counter() - start_total_time, 2)
    avg_time_per_note = round(total_time_elapsed / total_notes, 2)

    # 5. Write JSON output
    print(f"\n[EXPORT] Writing JSON predictions to {OUTPUT_JSON_PATH}...")
    json_payload = {
        "dataset_name": "CLINGAP_NLP_500_MODEL_PREDICTIONS",
        "generated_timestamp": datetime.now().isoformat(),
        "source_dataset": str(INPUT_JSON_PATH),
        "total_records": total_notes,
        "successful_records": successful_count,
        "failed_records": failed_count,
        "total_time_elapsed_seconds": total_time_elapsed,
        "average_time_per_note_seconds": avg_time_per_note,
        "evaluation_ids_range": f"{expected_ids[0]} to {expected_ids[-1]}",
        "ner_status": ModelManager.get_ner_status(),
        "records": ordered_records,
    }
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(json_payload, f, indent=2, ensure_ascii=False)
    print(f"[EXPORT] JSON export complete: {OUTPUT_JSON_PATH.stat().st_size:,} bytes")

    # 6. Write CSV output
    print(f"[EXPORT] Writing CSV predictions to {OUTPUT_CSV_PATH}...")
    csv_rows = [format_csv_record(r) for r in ordered_records]
    csv_headers = list(csv_rows[0].keys())

    with open(OUTPUT_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"[EXPORT] CSV export complete: {OUTPUT_CSV_PATH.stat().st_size:,} bytes")

    # 7. Summary Report
    print("\n" + "=" * 78)
    print("CLINGAP-NLP 500-NOTE PIPELINE INFERENCE EXECUTION SUMMARY")
    print("=" * 78)
    print(f"Total Notes Processed:       {total_notes}")
    print(f"Successful Notes:           {successful_count}")
    print(f"Failed Notes:               {failed_count}")
    print(f"Total Inference Time:       {total_time_elapsed} seconds ({total_time_elapsed / 60:.2f} minutes)")
    print(f"Average Time Per Note:      {avg_time_per_note} seconds")
    print(f"Output JSON Path:           {OUTPUT_JSON_PATH}")
    print(f"Output CSV Path:            {OUTPUT_CSV_PATH}")
    print("=" * 78)


if __name__ == "__main__":
    main()
