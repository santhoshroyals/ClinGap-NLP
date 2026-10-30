"""
test_researcher_evaluation.py - Tests for Researcher-Led NLP Evaluation Methodology
ClinGap-NLP Evaluation Test Suite (Tasks 1-5)

Covers:
1. VerificationState acceptance of RESEARCHER_ANNOTATED.
2. Independent evaluator metric computation on RESEARCHER_ANNOTATED batches.
3. Exclusion of UNCERTAIN entities, negations, and statuses from standard metric calculations.
4. Offset auto-calculation integrity in annotation_tool.py.
5. Inter-annotator agreement module behavior with single vs dual annotators.
6. Separation of exploratory educational rule engine from linguistic metrics.
"""

import os
import sys
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from evaluation.annotation_schema import (
    EntitySpanAnnotation,
    NegationAnnotation,
    InvestigationStatusAnnotation,
    CaseAnnotation
)
from evaluation.independent_evaluator import (
    evaluate_clinical_ner,
    evaluate_investigation_extraction,
    evaluate_negation_detection,
    evaluate_investigation_status,
    run_independent_evaluation_on_batch
)
from evaluation.annotation_tool import find_entity_span
from evaluation.inter_annotator_agreement import compute_inter_annotator_agreement


def test_researcher_annotated_schema_acceptance():
    case = CaseAnnotation(
        record_id=1,
        specialty="cardiology",
        clinical_note="Patient with chest pain.",
        entities=[
            EntitySpanAnnotation(
                start_char=13,
                end_char=23,
                entity_text="chest pain",
                entity_type="SYMPTOM",
                is_uncertain=False
            )
        ],
        verification_status="RESEARCHER_ANNOTATED",
        annotator_id="researcher_1"
    )
    assert case.verification_status == "RESEARCHER_ANNOTATED"
    assert case.annotator_id == "researcher_1"


def test_uncertain_entity_exclusion_from_ner():
    gt = [
        {"entities": [
            {"entity_type": "DISEASE", "normalized_value": "diabetes", "is_uncertain": False},
            {"entity_type": "SYMPTOM", "normalized_value": "malaise", "is_uncertain": True}  # UNCERTAIN
        ]}
    ]
    pred = [
        {"entities": [
            {"entity_type": "DISEASE", "normalized_value": "diabetes"},
            {"entity_type": "SYMPTOM", "normalized_value": "malaise"}
        ]}
    ]
    res = evaluate_clinical_ner(gt, pred)
    # The uncertain entity "malaise" was excluded from GT.
    # Therefore, "diabetes" is TP=1, and pred's "malaise" becomes FP=1.
    assert res["uncertain_entities_excluded"] == 1
    assert res["overall_micro"]["true_positives"] == 1
    assert res["overall_micro"]["false_positives"] == 1
    assert res["overall_micro"]["false_negatives"] == 0


def test_uncertain_negation_exclusion():
    gt = [
        {"negations": [
            {"entity_text": "fever", "is_negated": True, "is_uncertain": False},
            {"entity_text": "pain", "is_negated": False, "is_uncertain": True}  # UNCERTAIN
        ]}
    ]
    pred = [
        {"entities": [
            {"entity_text": "fever", "negated": True},
            {"entity_text": "pain", "negated": False}
        ]}
    ]
    res = evaluate_negation_detection(gt, pred)
    assert res["uncertain_negations_excluded"] == 1
    assert res["confusion_matrix"]["total"] == 1
    assert res["confusion_matrix"]["tp"] == 1


def test_find_entity_span_auto_calculation():
    note = "Discharge Summary\nPatient has severe headache and mild dizziness."
    start, end = find_entity_span(note, "severe headache")
    assert note[start:end] == "severe headache"

    start_diz, end_diz = find_entity_span(note, "mild dizziness")
    assert note[start_diz:end_diz] == "mild dizziness"


def test_find_entity_span_nonexistent_raises():
    note = "Patient has fever."
    with pytest.raises(ValueError):
        find_entity_span(note, "chest pain")


def test_inter_annotator_agreement_single_annotator_guard():
    ann1 = {"cases": [{"record_id": 1, "entities": []}]}
    res = compute_inter_annotator_agreement(ann1, ann2_data=None)
    assert res["status"] == "NOT_CALCULATED"
    assert "Single-researcher annotation" in res["reason"]


def test_inter_annotator_agreement_dual_annotators():
    ann1 = {
        "cases": [
            {
                "record_id": 1,
                "entities": [
                    {"start_char": 0, "end_char": 5, "entity_type": "SYMPTOM", "is_uncertain": False}
                ],
                "negations": [
                    {"entity_text": "fever", "is_negated": True, "is_uncertain": False}
                ]
            }
        ]
    }
    ann2 = {
        "cases": [
            {
                "record_id": 1,
                "entities": [
                    {"start_char": 0, "end_char": 5, "entity_type": "SYMPTOM", "is_uncertain": False}
                ],
                "negations": [
                    {"entity_text": "fever", "is_negated": True, "is_uncertain": False}
                ]
            }
        ]
    }
    res = compute_inter_annotator_agreement(ann1, ann2)
    assert res["status"] == "CALCULATED"
    assert res["entity_span_agreement"]["agreement_f1_pct"] == 100.0
    assert res["negation_cohens_kappa"] == 1.0


def test_independent_evaluator_accepts_researcher_annotated(tmp_path):
    import json
    data = {
        "cases": [
            {
                "record_id": 1,
                "clinical_note": "Patient presents with persistent cough.",
                "verification_status": "RESEARCHER_ANNOTATED",
                "annotator_id": "researcher_1",
                "entities": [
                    {"start_char": 24, "end_char": 39, "entity_text": "persistent cough", "entity_type": "SYMPTOM", "is_uncertain": False}
                ],
                "negations": [
                    {"entity_text": "persistent cough", "is_negated": False, "is_uncertain": False}
                ],
                "investigations": []
            }
        ]
    }
    fpath = tmp_path / "mock_researcher_annotated.json"
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f)

    res = run_independent_evaluation_on_batch(str(fpath))
    assert res["status"] == "EVALUATION_COMPLETED"
    assert res["evaluation_type"] == "SINGLE_RESEARCHER_ANNOTATED_NLP_EVALUATION"
    assert res["provenance"]["verification_status"] == "RESEARCHER_ANNOTATED"
    assert "linguistic_nlp_evaluation" in res
    assert "exploratory_educational_rule_engine" in res
