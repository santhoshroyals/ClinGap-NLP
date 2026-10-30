"""
test_evaluation_infrastructure.py - Comprehensive Unit Tests for New Evaluation Infrastructure
ClinGap-NLP Evaluation Test Suite (Tasks 1-5)

Covers:
1. Dataset Integrity & Template Clustering.
2. Leakage-Safe Cluster-Disjoint Splitting (Strict 0% Cross-Partition Leakage).
3. Annotation Schema Pydantic Validation & Invariant Checking.
4. Mathematical Correctness of Independent Evaluation Metrics (NER, Negation, Status, Gaps).
5. Academic Integrity Guard: Refusal to fabricate metrics on unverified annotations.
"""

import os
import sys
import pytest
from pydantic import ValidationError

# Ensure clinngap_nlp root is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from evaluation.dataset_analysis import identify_template_cluster, extract_diagnosis, extract_clinical_body
from evaluation.leakage_safe_splitter import perform_cluster_disjoint_split
from evaluation.annotation_schema import (
    EntitySpanAnnotation,
    NegationAnnotation,
    InvestigationStatusAnnotation,
    GuidelineActivationAnnotation,
    DecisionGapAnnotation,
    CaseAnnotation
)
from evaluation.independent_evaluator import (
    calculate_prf,
    safe_div,
    evaluate_clinical_ner,
    evaluate_negation_detection,
    evaluate_investigation_status,
    evaluate_guideline_matching,
    evaluate_decision_gap_detection,
    run_independent_evaluation_on_batch
)


# ==============================================================================
# 1. TEMPLATE CLUSTERING & ANALYSIS TESTS
# ==============================================================================

def test_template_cluster_identification_cardiology():
    sample_note = (
        "Chief Complaints: Chest pain aur saans phoolna for 5 days.\n"
        "History of Present Illness: Substernal pain on exertion, with diaphoresis.\n"
        "Past History: Hypertension since 10 years, on meds.\n"
        "Physical Examination: Heart: S1/S2 normal, no murmur.\n"
        "Investigations: ST elevation; Trop-I: Positive; Echo: EF 50%\n"
        "Diagnosis: NSTEMI (ICD: I21.4).\n"
        "Course in Hospital: Admitted to CCU. Thrombolysis kiya gaya, then angioplasty with stent.\n"
        "Advice on Discharge: Tab. Aspirin 75mg OD, Tab. Atorvastatin 40mg HS."
    )
    cid, slots = identify_template_cluster(sample_note, "cardiology")
    assert cid.startswith("cardiology_S_")
    assert len(slots) == 8
    assert -1 not in slots, "All 8 clinical slots must be identified"
    assert slots[0] == 0  # Chest pain option 0
    assert slots[5] == 0  # NSTEMI option 0


def test_template_cluster_unknown_specialty():
    cid, slots = identify_template_cluster("Some text", "unknown_spec")
    assert cid == "unknown_spec_UNKNOWN"
    assert -1 in slots


def test_extract_diagnosis_from_text():
    note = "Patient admitted.\nDiagnosis: Community-Acquired Pneumonia (ICD: J18.9).\nCourse: IV antibiotics."
    diag = extract_diagnosis(note)
    assert diag == "Community-Acquired Pneumonia (ICD: J18.9)."


def test_extract_clinical_body():
    raw = (
        "AIIMS Delhi\nDischarge Summary\nPatient: John\n"
        "Chief Complaints: Cough\n"
        "Course: Treated\n"
        "Dr. Sharma\nSignature"
    )
    body = extract_clinical_body(raw)
    assert "Chief Complaints: Cough" in body
    assert "AIIMS Delhi" not in body
    assert "Signature" not in body


# ==============================================================================
# 2. LEAKAGE-SAFE CLUSTER DISJOINT SPLIT TESTS
# ==============================================================================

def test_cluster_disjoint_splitting_guarantees(tmp_path):
    # Construct mock record-cluster mapping across 10 clusters
    mock_records = []
    rid = 1
    for c_idx in range(10):
        cid = f"cardiology_S_{c_idx}"
        for _ in range(5):
            mock_records.append({
                "record_id": rid,
                "specialty": "cardiology",
                "cluster_id": cid,
                "diagnosis": "NSTEMI" if c_idx < 5 else "AFib"
            })
            rid += 1

    import json
    map_file = tmp_path / "mock_map.json"
    with open(map_file, "w", encoding="utf-8") as f:
        json.dump(mock_records, f)

    manifest = perform_cluster_disjoint_split(
        record_cluster_map_path=str(map_file),
        output_dir=str(tmp_path),
        seed=42,
        train_dev_ratio=0.6,
        val_ratio=0.2,
        test_ratio=0.2
    )

    # Load produced cluster sets
    with open(tmp_path / "train_dev_cluster_ids.json") as f:
        train_clusters = set(json.load(f))
    with open(tmp_path / "validation_cluster_ids.json") as f:
        val_clusters = set(json.load(f))
    with open(tmp_path / "held_out_test_cluster_ids.json") as f:
        test_clusters = set(json.load(f))

    # Verify STRICT DISJOINTNESS (ZERO CROSS-SPLIT LEAKAGE)
    assert train_clusters.isdisjoint(val_clusters), "Train and Val share clusters!"
    assert train_clusters.isdisjoint(test_clusters), "Train and Test share clusters!"
    assert val_clusters.isdisjoint(test_clusters), "Val and Test share clusters!"
    assert len(train_clusters) + len(val_clusters) + len(test_clusters) == 10


# ==============================================================================
# 3. ANNOTATION SCHEMA VALIDATION TESTS
# ==============================================================================

def test_valid_case_annotation_schema():
    case = CaseAnnotation(
        record_id=101,
        specialty="cardiology",
        clinical_note="Patient has acute chest pain. CBC completed.",
        entities=[
            EntitySpanAnnotation(
                start_char=18,
                end_char=28,
                entity_text="chest pain",
                entity_type="SYMPTOM",
                normalized_value="chest pain"
            )
        ],
        negations=[
            NegationAnnotation(entity_text="chest pain", is_negated=False)
        ],
        investigations=[
            InvestigationStatusAnnotation(investigation_name="CBC", status="completed/performed")
        ],
        verification_status="AWAITING_HUMAN_VERIFICATION"
    )
    assert case.record_id == 101
    assert case.verification_status == "AWAITING_HUMAN_VERIFICATION"
    assert len(case.entities) == 1
    assert case.entities[0].entity_type == "SYMPTOM"


def test_invalid_entity_type_raises_validation_error():
    with pytest.raises(ValidationError):
        EntitySpanAnnotation(
            start_char=0,
            end_char=5,
            entity_text="cough",
            entity_type="INVALID_TYPE_FOO"
        )


def test_invalid_investigation_status_raises_validation_error():
    with pytest.raises(ValidationError):
        InvestigationStatusAnnotation(
            investigation_name="HbA1c",
            status="some_random_status"
        )


# ==============================================================================
# 4. MATHEMATICAL METRIC CALCULATION TESTS
# ==============================================================================

def test_calculate_prf_mathematics():
    # TP=8, FP=2, FN=0 -> P = 8/10 = 80%, R = 8/8 = 100%, F1 = 2*(0.8*1)/(1.8) = 88.89%
    p, r, f1 = calculate_prf(tp=8, fp=2, fn=0)
    assert p == 80.0
    assert r == 100.0
    assert f1 == 88.89


def test_calculate_prf_zero_division():
    p, r, f1 = calculate_prf(tp=0, fp=0, fn=0)
    assert p == 0.0
    assert r == 0.0
    assert f1 == 0.0


def test_evaluate_clinical_ner_metrics():
    gt = [
        {"entities": [
            {"entity_type": "DISEASE", "normalized_value": "diabetes"},
            {"entity_type": "SYMPTOM", "normalized_value": "cough"}
        ]}
    ]
    pred = [
        {"entities": [
            {"entity_type": "DISEASE", "normalized_value": "diabetes"},  # TP
            {"entity_type": "SYMPTOM", "normalized_value": "fever"}      # FP, cough is FN
        ]}
    ]
    res = evaluate_clinical_ner(gt, pred)
    # Total TP=1 (diabetes), FP=1 (fever), FN=1 (cough)
    assert res["overall_micro"]["true_positives"] == 1
    assert res["overall_micro"]["false_positives"] == 1
    assert res["overall_micro"]["false_negatives"] == 1
    assert res["overall_micro"]["precision_pct"] == 50.0
    assert res["overall_micro"]["recall_pct"] == 50.0
    assert res["overall_micro"]["f1_score_pct"] == 50.0


def test_evaluate_negation_detection_metrics():
    gt = [
        {"negations": [
            {"entity_text": "fever", "is_negated": True},
            {"entity_text": "cough", "is_negated": False}
        ]}
    ]
    pred = [
        {"entities": [
            {"entity_text": "fever", "negated": True},   # TP
            {"entity_text": "cough", "negated": False}   # TN
        ]}
    ]
    res = evaluate_negation_detection(gt, pred)
    assert res["confusion_matrix"]["tp"] == 1
    assert res["confusion_matrix"]["tn"] == 1
    assert res["confusion_matrix"]["fp"] == 0
    assert res["confusion_matrix"]["fn"] == 0
    assert res["accuracy_pct"] == 100.0
    assert res["f1_score_pct"] == 100.0


def test_evaluate_negation_missing_prediction_counts_as_fn_and_flags_not_evaluable():
    gt = [
        {
            "negations": [{"entity_text": "syncope", "is_negated": True}],
            "entities": [{"entity_text": "hypertension", "entity_type": "DISEASE"}]
        }
    ]
    # Pipeline only extracts hypertension (affirmed), completely missing syncope
    pred = [
        {
            "entities": [{"entity_text": "hypertension", "negated": False, "entity_type": "DISEASE"}]
        }
    ]
    res = evaluate_negation_detection(gt, pred)
    assert res["class_support"]["ground_truth_negated_support"] == 1
    assert res["class_support"]["matched_entities_positive_support"] == 0
    assert res["class_support"]["matched_entities_negative_support"] == 1
    assert res["confusion_matrix"]["tp"] == 0
    assert res["confusion_matrix"]["fn"] == 1  # Missing prediction counts as FN, NOT ignored
    assert res["confusion_matrix"]["tn"] == 1
    assert res["confusion_matrix"]["fp"] == 0
    assert res["matched_entities_assertion"]["is_evaluable"] is False
    assert "NOT EVALUABLE" in res["matched_entities_assertion"]["status"]


def test_evaluate_investigation_status_distinguishes_missing_from_misclassification():
    gt = [
        {
            "investigations": [
                {"investigation_name": "ecg", "status": "completed/performed"},
                {"investigation_name": "echo", "status": "completed/performed"}
            ]
        }
    ]
    # Pipeline extracts echo with status ordered, and misses ecg entirely
    pred = [
        {
            "entities": [
                {"entity_text": "echo", "entity_type": "INVESTIGATION", "status": "ordered"}
            ]
        }
    ]
    res = evaluate_investigation_status(gt, pred)
    assert res["total_evaluated_mentions"] == 2
    assert res["correctly_classified"] == 0
    assert res["accuracy_pct"] == 0.0
    bd = res["breakdown"]
    assert bd["total_reference_investigations"] == 2
    assert bd["missing_unextracted_investigations"] == 1
    assert bd["extracted_investigations_evaluated"] == 1
    assert bd["correctly_classified_on_extracted"] == 0
    assert bd["incorrectly_classified_on_extracted"] == 1
    assert bd["conditional_accuracy_on_extracted_pct"] == 0.0


def test_evaluate_gap_detection_metrics():
    gt = [
        {"expected_gap": True, "is_supported": True},
        {"expected_gap": False, "is_supported": True},
        {"expected_gap": True, "is_supported": True},
        {"expected_gap": False, "is_supported": True}
    ]
    pred = [
        {"gaps": [{"gap_type": "MISSING_INVESTIGATION"}]}, # TP
        {"gaps": []},                                      # TN
        {"gaps": []},                                      # FN
        {"gaps": [{"gap_type": "MISSING_INVESTIGATION"}]}  # FP
    ]
    res = evaluate_decision_gap_detection(gt, pred)
    cm = res["confusion_matrix"]
    assert cm["true_positives"] == 1
    assert cm["true_negatives"] == 1
    assert cm["false_positives"] == 1
    assert cm["false_negatives"] == 1
    assert res["metrics"]["accuracy_pct"] == 50.0
    assert res["metrics"]["precision_pct"] == 50.0
    assert res["metrics"]["recall_pct"] == 50.0
    assert res["metrics"]["f1_score_pct"] == 50.0


def test_evaluate_guideline_matching_dict_format():
    gt = [
        {"applicable_rule_id": "R1"},
        {"guidelines": [{"guideline_id": "R2", "is_triggered": True}]}
    ]
    pred = [
        {"explanation": {"matched_rules": [{"rule_id": "R1"}]}},
        {"explanation": {"matched_rules": [{"rule_id": "R2"}]}}
    ]
    res = evaluate_guideline_matching(gt, pred)
    assert res["confusion_counts"]["tp"] == 2
    assert res["confusion_counts"]["fp"] == 0
    assert res["confusion_counts"]["fn"] == 0
    assert res["precision_pct"] == 100.0
    assert res["recall_pct"] == 100.0
    assert res["f1_score_pct"] == 100.0


def test_evaluate_guideline_matching_string_format():
    gt = [
        {"applicable_rule_id": "R1"},
        {"guidelines": [{"guideline_id": "R2", "is_triggered": True}]}
    ]
    pred = [
        {"explanation": {"matched_rules": ["R1"]}},
        {"explanation": {"matched_rules": ["R2"]}}
    ]
    res = evaluate_guideline_matching(gt, pred)
    assert res["confusion_counts"]["tp"] == 2
    assert res["confusion_counts"]["fp"] == 0
    assert res["confusion_counts"]["fn"] == 0
    assert res["precision_pct"] == 100.0
    assert res["recall_pct"] == 100.0
    assert res["f1_score_pct"] == 100.0


def test_evaluate_guideline_matching_mixed_and_invalid_formats():
    gt = [
        {"applicable_rule_id": "R1"},
        {"guidelines": [{"guideline_id": "R2", "is_triggered": True}]},
        {"guidelines": []}
    ]
    pred = [
        {"explanation": {"matched_rules": ["R1", "", "   ", None, {}]}},
        {"explanation": {"matched_rules": [{"rule_id": "R2"}, {"rule_id": ""}, {"rule_id": None}, {"rule_id": "  "}]}},
        {"explanation": {"matched_rules": []}}
    ]
    res = evaluate_guideline_matching(gt, pred)
    assert res["confusion_counts"]["tp"] == 2
    assert res["confusion_counts"]["fp"] == 0
    assert res["confusion_counts"]["fn"] == 0
    assert res["confusion_counts"]["tn"] == 1
    assert res["precision_pct"] == 100.0
    assert res["recall_pct"] == 100.0
    assert res["f1_score_pct"] == 100.0


# ==============================================================================
# 5. ACADEMIC INTEGRITY SAFETY GUARD TEST
# ==============================================================================

def test_independent_evaluator_blocks_unverified_annotations(tmp_path):
    unverified_data = {
        "batch_id": "TEST_UNVERIFIED",
        "cases": [
            {
                "record_id": 1,
                "clinical_note": "Patient with cough.",
                "verification_status": "AWAITING_HUMAN_VERIFICATION"
            }
        ]
    }
    import json
    path = tmp_path / "test_unverified.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(unverified_data, f)

    res = run_independent_evaluation_on_batch(str(path))
    assert res["status"] == "METRICS_BLOCKED"
    assert "ZERO annotated/verified records found" in res["reason"]
