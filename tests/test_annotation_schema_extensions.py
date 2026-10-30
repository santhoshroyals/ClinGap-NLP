"""
test_annotation_schema_extensions.py - Tests for Annotation Schema Extensions
ClinGap-NLP Evaluation Infrastructure (Phase 1 & 2 Workflow Improvements)

Covers:
1. Schema support for PHYSICAL_SIGN and VITAL_SIGN entities with clinical_subkind and polarity (+/-).
2. Exact character offset validation for negation cue and scope.
3. Mixed-language Hinglish negation preservation ("koi improvement nahi hai", cue "nahi hai").
4. Investigation finding associations (qualitative and numerical results with finding categories).
5. Neutral/unknown category preservation for numerical findings (EF 46%).
6. Backward compatibility preservation with standard 7-class NER evaluation.
7. Verification that existing Case 1 annotations are fully preserved.
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
    STANDARD_SEVEN_CLASSES
)
from evaluation.annotation_tool import (
    find_entity_span,
    load_pilot_batch
)


def test_schema_accepts_physical_and_vital_signs():
    """Verify that EntitySpanAnnotation supports physical and vital sign subkinds and polarity."""
    ent_phys = EntitySpanAnnotation(
        start_char=10,
        end_char=16,
        entity_text="Pallor",
        entity_type="PHYSICAL_SIGN",
        clinical_subkind="physical_sign",
        finding_polarity="positive",
        normalized_value="pallor"
    )
    assert ent_phys.entity_type == "PHYSICAL_SIGN"
    assert ent_phys.clinical_subkind == "physical_sign"
    assert ent_phys.finding_polarity == "positive"

    ent_vital = EntitySpanAnnotation(
        start_char=20,
        end_char=36,
        entity_text="Pulse: Irregular",
        entity_type="VITAL_SIGN",
        clinical_subkind="vital_sign",
        finding_polarity="abnormal",
        normalized_value="irregular pulse"
    )
    assert ent_vital.entity_type == "VITAL_SIGN"
    assert ent_vital.clinical_subkind == "vital_sign"
    assert ent_vital.finding_polarity == "abnormal"


def test_negation_cue_and_scope_offsets():
    """Verify NegationAnnotation preserves exact cue and scope character offsets."""
    note = "History: Irregular heartbeat, no syncope observed."
    cue_start, cue_end = find_entity_span(note, "no", context="no syncope")
    scope_start, scope_end = find_entity_span(note, "Irregular heartbeat, no syncope observed.")

    neg = NegationAnnotation(
        entity_text="syncope",
        is_negated=True,
        negation_cue="no",
        cue_offsets=(cue_start, cue_end),
        scope_text="Irregular heartbeat, no syncope observed.",
        scope_offsets=(scope_start, scope_end),
        language="en",
        normalized_assertion="absence of syncope"
    )
    assert note[neg.cue_offsets[0]:neg.cue_offsets[1]] == "no"
    assert note[neg.scope_offsets[0]:neg.scope_offsets[1]] == "Irregular heartbeat, no syncope observed."
    assert neg.language == "en"


def test_hinglish_negation_representation():
    """Verify mixed-language Hinglish negation representation preserving verbatim text."""
    note = "Course in Hospital: Antiarrhythmics given. koi improvement nahi hai."
    cue_start, cue_end = find_entity_span(note, "nahi hai")
    scope_start, scope_end = find_entity_span(note, "koi improvement nahi hai.")

    neg = NegationAnnotation(
        entity_text="improvement",
        is_negated=True,
        negation_cue="nahi hai",
        cue_offsets=(cue_start, cue_end),
        scope_text="koi improvement nahi hai.",
        scope_offsets=(scope_start, scope_end),
        language="hinglish",
        normalized_assertion="lack of clinical improvement"
    )
    assert neg.language == "hinglish"
    assert neg.negation_cue == "nahi hai"
    assert note[neg.cue_offsets[0]:neg.cue_offsets[1]] == "nahi hai"
    assert note[neg.scope_offsets[0]:neg.scope_offsets[1]] == "koi improvement nahi hai."


def test_investigation_result_associations():
    """Verify linking investigation names to qualitative and numerical findings."""
    note = "Investigations: ECG: ST elevation; Echo: EF 46%."
    ecg_start, ecg_end = find_entity_span(note, "ST elevation")
    echo_start, echo_end = find_entity_span(note, "EF 46%")

    ecg_inv = InvestigationStatusAnnotation(
        investigation_name="ECG",
        status="completed/performed",
        evidence_snippet="ECG: ST elevation",
        finding_result="ST elevation",
        finding_offsets=(ecg_start, ecg_end),
        finding_category="abnormal"
    )
    assert ecg_inv.finding_category == "abnormal"
    assert note[ecg_inv.finding_offsets[0]:ecg_inv.finding_offsets[1]] == "ST elevation"

    # Numerical result EF 46% with neutral/unknown category
    echo_inv = InvestigationStatusAnnotation(
        investigation_name="Echo",
        status="completed/performed",
        evidence_snippet="Echo: EF 46%",
        finding_result="EF 46%",
        finding_offsets=(echo_start, echo_end),
        finding_category="unknown"
    )
    assert echo_inv.finding_category == "unknown"
    assert note[echo_inv.finding_offsets[0]:echo_inv.finding_offsets[1]] == "EF 46%"


def test_seven_class_ner_compatibility_preservation():
    """
    Verify that extended entities (PHYSICAL_SIGN, VITAL_SIGN) in ground truth
    do not distort standard 7-class NER metrics and are tracked in extended_entities_breakdown.
    """
    gt = [
        {"entities": [
            {"entity_type": "DISEASE", "normalized_value": "diabetes", "is_uncertain": False},
            {"entity_type": "SYMPTOM", "normalized_value": "cough", "is_uncertain": False},
            {"entity_type": "PHYSICAL_SIGN", "normalized_value": "pallor", "is_uncertain": False},
            {"entity_type": "VITAL_SIGN", "normalized_value": "irregular pulse", "is_uncertain": False}
        ]}
    ]
    pred = [
        {"entities": [
            {"entity_type": "DISEASE", "normalized_value": "diabetes"},
            {"entity_type": "SYMPTOM", "normalized_value": "cough"}
        ]}
    ]

    res = evaluate_clinical_ner(gt, pred, target_classes=STANDARD_SEVEN_CLASSES)
    # The 7-class evaluation should see TP=2, FP=0, FN=0 -> 100% precision, recall, F1
    assert res["overall_micro"]["true_positives"] == 2
    assert res["overall_micro"]["false_negatives"] == 0
    assert res["overall_micro"]["false_positives"] == 0
    assert res["overall_micro"]["f1_score_pct"] == 100.0
    # Extended entities isolated and reported separately
    assert "extended_entities_breakdown" in res
    assert res["extended_entities_breakdown"]["total_extended_entities_preserved"] == 2
    assert res["extended_entities_breakdown"]["counts_by_type"]["PHYSICAL_SIGN"] == 1
    assert res["extended_entities_breakdown"]["counts_by_type"]["VITAL_SIGN"] == 1


def test_case1_preservation_and_extensions():
    """Verify Case 1 in pilot_10_cases.json preserves original annotations and includes valid extensions."""
    batch = load_pilot_batch()
    case1 = batch["cases"][0]
    assert case1["record_id"] == 77

    # 1. Check original 14 entities are present
    orig_entity_texts = [
        "Palpitations", "dizziness", "Irregular heartbeat", "syncope",
        "Coronary artery disease", "ECG", "ST elevation", "Trop-I",
        "Positive", "Echo", "EF 46%", "Angiogram", "Atrial Fibrillation", "Antiarrhythmics"
    ]
    current_texts = [e["entity_text"] for e in case1["entities"]]
    for orig in orig_entity_texts:
        assert orig in current_texts, f"Original entity '{orig}' missing from Case 1"

    # Total entities: 14 original + 7 physical/vital signs = 21
    assert len(case1["entities"]) == 21

    # 2. Check physical signs
    phys_signs = [e for e in case1["entities"] if e["entity_type"] == "PHYSICAL_SIGN"]
    assert len(phys_signs) == 6
    polarities = {e["entity_text"]: e["finding_polarity"] for e in phys_signs}
    assert polarities["Pallor"] == "positive"
    assert polarities["Cyanosis"] == "negative"
    assert polarities["Edema"] == "negative"

    # Check vital sign
    vital_signs = [e for e in case1["entities"] if e["entity_type"] == "VITAL_SIGN"]
    assert len(vital_signs) == 1
    assert vital_signs[0]["entity_text"] == "Pulse: Irregular"
    assert vital_signs[0]["finding_polarity"] == "abnormal"

    # 3. Check negations
    assert len(case1["negations"]) == 2
    syncope_neg = next(n for n in case1["negations"] if n["entity_text"] == "syncope")
    assert syncope_neg["negation_cue"] == "no"
    assert syncope_neg["cue_offsets"] == [390, 392]

    hing_neg = next(n for n in case1["negations"] if n["entity_text"] == "improvement")
    assert hing_neg["language"] == "hinglish"
    assert hing_neg["negation_cue"] == "nahi hai"
    assert hing_neg["cue_offsets"] == [826, 834]

    # 4. Check investigations
    assert len(case1["investigations"]) == 4
    inv_map = {inv["investigation_name"]: inv for inv in case1["investigations"]}
    assert inv_map["ECG"]["finding_result"] == "ST elevation"
    assert inv_map["Trop-I"]["finding_result"] == "Positive"
    assert inv_map["Echo"]["finding_result"] == "EF 46%"
    assert inv_map["Echo"]["finding_category"] == "unknown"
    assert inv_map["Angiogram"]["finding_result"] == "77% blockage in LAD"

    # 5. Case verification status verified
    assert case1["verification_status"] in {"AWAITING_HUMAN_VERIFICATION", "RESEARCHER_ANNOTATED"}


def test_find_entity_span_context_disambiguation():
    """Verify find_entity_span disambiguates spans using context."""
    note = "File no: 12345. History: no fever."
    # Without context, 'no' matches the earlier 'no' in 'File no:'
    s1, e1 = find_entity_span(note, "no")
    assert s1 == 5
    assert note[s1:e1] == "no"

    # With context 'no fever', it targets the correct clinical negation cue
    s2, e2 = find_entity_span(note, "no", context="no fever")
    assert s2 == 25
    assert note[s2:e2] == "no"


def test_add_negation_cli_exact_command_regression(tmp_path):
    """
    Regression test for:
    python evaluation/annotation_tool.py --add-negation 2 "syncope" TRUE --cue "no"
    Verifies argument consistency (is_negated vs is_neg) and auto-derived scope/cue offsets.
    """
    import shutil
    import subprocess
    import json
    from evaluation.annotation_tool import PILOT_JSON

    mock_file = tmp_path / "mock_batch.json"
    shutil.copyfile(PILOT_JSON, mock_file)

    cmd = [
        sys.executable,
        os.path.join(BASE_DIR, "evaluation", "annotation_tool.py"),
        "--add-negation", "2", "syncope", "TRUE",
        "--cue", "no",
        "--file", str(mock_file)
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"Command failed: {proc.stderr}"
    assert "Added Negation assertion for 'syncope'" in proc.stdout

    with open(mock_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    c2 = data["cases"][1]
    assert len(c2["negations"]) >= 1
    added_neg = c2["negations"][-1]
    assert added_neg["entity_text"] == "syncope"
    assert added_neg["is_negated"] is True
    assert added_neg["negation_cue"] == "no"
    assert added_neg["cue_offsets"] == [426, 428]
    assert added_neg["scope_text"] == "Irregular heartbeat, no syncope."
    assert added_neg["scope_offsets"] == [405, 437]
