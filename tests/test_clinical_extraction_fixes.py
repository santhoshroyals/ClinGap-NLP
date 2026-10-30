"""
test_clinical_extraction_fixes.py - Regression and validation tests for:
1. Separating medication dosages from laboratory measurements (e.g. 218 mg/dL vs 500 mg)
2. Investigation status logic (ordered, pending, completed/performed, not performed)
3. Medication and disease coverage (salbutamol, asthma)
4. Negation scope across coordinated symptoms (chest pain and dizziness)
5. Full clinical test note evaluation

NOTE: Research and automated test validation only. Does not claim medical or clinical accuracy.
"""

import pytest
import re
from backend.services.ner_service import (
    DOSAGE_PATTERN,
    hybrid_ner,
    extract_investigation_status,
    _is_lab_measurement_or_non_medication,
)
from backend.services.negation_service import detect_negations
from backend.services.prescription_service import reconstruct_regimens, DOSAGE_REGEX
from backend.services.guideline_service import GuidelineEngine
from backend.services.gap_detection import detect_gaps


class TestDosageVsLaboratoryMeasurements:
    """Verify medication dosages are separated from laboratory measurements."""

    @pytest.mark.parametrize("valid_dose", [
        "500 mg",
        "100 mcg",
        "2.5 mL",
        "2.5 ml",
        "1 g",
        "10 units",
        "50 µg",
    ])
    def test_valid_medication_strengths_extracted(self, valid_dose):
        assert DOSAGE_PATTERN.search(valid_dose) is not None, f"Expected {valid_dose} to be matched by DOSAGE_PATTERN"
        assert DOSAGE_REGEX.search(valid_dose) is not None, f"Expected {valid_dose} to be matched by DOSAGE_REGEX"

    @pytest.mark.parametrize("lab_measurement", [
        "218 mg/dL",
        "218 mg/dl",
        "14.2 g/dL",
        "1.2 mg/dl",
        "5.0 mg/L",
        "30 ng/mL",
        "random blood glucose was 218 mg/dL",
        "fasting blood glucose of 140 mg/dL",
    ])
    def test_laboratory_measurement_units_rejected(self, lab_measurement):
        m1 = DOSAGE_PATTERN.search(lab_measurement)
        assert m1 is None, f"Lab measurement '{lab_measurement}' incorrectly matched DOSAGE_PATTERN as '{m1.group(0)}'"
        m2 = DOSAGE_REGEX.search(lab_measurement)
        assert m2 is None, f"Lab measurement '{lab_measurement}' incorrectly matched DOSAGE_REGEX as '{m2.group(0)}'"

    def test_lab_measurement_not_extracted_as_medication(self):
        assert _is_lab_measurement_or_non_medication("218 mg/dL") is True
        assert _is_lab_measurement_or_non_medication("148/92 mmHg") is True
        assert _is_lab_measurement_or_non_medication("38.2°C") is True
        assert _is_lab_measurement_or_non_medication("metformin") is False
        assert _is_lab_measurement_or_non_medication("salbutamol") is False


class TestMedicationAndDiseaseCoverage:
    """Verify coverage of salbutamol and asthma."""

    def test_salbutamol_recognized(self):
        text = "The patient uses salbutamol as needed."
        ents = hybrid_ner(text)
        meds = [e['entity_text'].lower() for e in ents if e['entity_type'] == 'MEDICATION']
        assert "salbutamol" in meds

    def test_asthma_recognized(self):
        text = "Past medical history of bronchial asthma."
        ents = hybrid_ner(text)
        diseases = [e['entity_text'].lower() for e in ents if e['entity_type'] == 'DISEASE']
        assert any("asthma" in d for d in diseases)


class TestInvestigationStatusAndNegation:
    """Verify investigation status lifecycle and compound negation."""

    def test_ordered_investigation_pending_result_not_completed(self):
        text = "A complete blood count was ordered but the result is not yet available."
        status = extract_investigation_status(text, "complete blood count")
        assert status == "pending"
        assert status != "completed/performed"

    def test_requested_investigation_not_performed_not_completed(self):
        text = "Chest X-ray has been requested but has not yet been performed."
        status = extract_investigation_status(text, "Chest X-ray")
        assert status in ("not performed", "ORDERED/PENDING")
        assert status != "completed/performed"

    def test_explicitly_cancelled_investigation_not_performed(self):
        text = "Chest X-ray was not performed."
        status = extract_investigation_status(text, "Chest X-ray")
        assert status == "not performed"
        assert status != "completed/performed"

    def test_performed_investigation_completed(self):
        text = "HbA1c was performed and showed 8.1%."
        status = extract_investigation_status(text, "HbA1c")
        assert status == "completed/performed"

    def test_compound_negation_scopes_both_symptoms(self):
        text = "The patient denies chest pain and dizziness."
        entities = [
            {'entity_text': 'chest pain', 'entity_type': 'SYMPTOM'},
            {'entity_text': 'dizziness', 'entity_type': 'SYMPTOM'},
        ]
        results = detect_negations(text, entities)
        assert results[0]['negated'] is True, "Expected chest pain to be negated"
        assert results[1]['negated'] is True, "Expected dizziness to be negated"


class TestFullTestNoteIntegration:
    """Verify all requirements against the complete clinical prompt note."""

    test_note = (
        "Patient is a 58-year-old male presenting with persistent cough, fever, and shortness of breath for four days. "
        "Medical history includes type 2 diabetes mellitus and hypertension. "
        "Current medications include metformin 500 mg twice daily and amoxicillin 500 mg three times daily. "
        "The patient also uses a salbutamol inhaler 100 mcg as needed. "
        "Vital signs show a temperature of 38.2°C, blood pressure of 148/92 mmHg, heart rate of 102 beats/minute, and oxygen saturation of 92% on room air. "
        "Laboratory results show a random blood glucose level of 218 mg/dL. "
        "A complete blood count was ordered but the result is not yet available. "
        "Chest X-ray has been requested but has not yet been performed. "
        "The patient denies chest pain and dizziness."
    )

    def test_full_note_extraction_and_regimens(self):
        ents = detect_negations(self.test_note, hybrid_ner(self.test_note))

        # 1. 218 mg/dL must not be extracted as dosage
        dosages = [e['entity_text'] for e in ents if e['entity_type'] == 'DOSAGE']
        assert "218 mg" not in dosages
        assert "218 mg/dL" not in dosages
        assert "500 mg" in dosages
        assert "100 mcg" in dosages

        # 2. CBC ordered but result not available must be pending (not completed)
        cbc = next((e for e in ents if 'blood count' in e['entity_text'].lower()), None)
        assert cbc is not None
        assert cbc['status'] == 'pending'
        assert cbc['status'] != 'completed/performed'

        # 3. Chest X-ray requested but not performed must be not completed (ORDERED/PENDING)
        xray = next((e for e in ents if 'x-ray' in e['entity_text'].lower() or 'xray' in e['entity_text'].lower()), None)
        assert xray is not None
        assert xray['status'] in ('not performed', 'ORDERED/PENDING')
        assert xray['status'] != 'completed/performed'

        # 4. Denies chest pain and dizziness -> both negated
        chest_pain = next((e for e in ents if e['entity_text'].lower() == 'chest pain'), None)
        dizziness = next((e for e in ents if e['entity_text'].lower() == 'dizziness'), None)
        assert chest_pain is not None and chest_pain['negated'] is True
        assert dizziness is not None and dizziness['negated'] is True

        # 5. Non-negated symptoms preserved
        cough = next((e for e in ents if e['entity_text'].lower() == 'cough'), None)
        fever = next((e for e in ents if e['entity_text'].lower() == 'fever'), None)
        if cough:
            assert cough['negated'] is False
        if fever:
            assert fever['negated'] is False

        # 6. Regimens reconstructed for all 3 medications
        regimens = reconstruct_regimens(self.test_note, entities=ents)
        reg_meds = {r['medication'].lower(): r for r in regimens}
        assert 'metformin' in reg_meds
        assert reg_meds['metformin']['dosage'] == '500 mg'
        assert reg_meds['metformin']['frequency'] == 'twice daily'

        assert 'amoxicillin' in reg_meds
        assert reg_meds['amoxicillin']['dosage'] == '500 mg'
        assert reg_meds['amoxicillin']['frequency'] == 'three times daily'

        assert 'salbutamol' in reg_meds
        assert reg_meds['salbutamol']['dosage'] == '100 mcg'
        assert reg_meds['salbutamol']['frequency'] == 'as needed'

    def test_timeline_summary_medication_dosage_association(self):
        """Regression test: verify that the Clinical Timeline summary preserves correct
        medication, dosage, and frequency associations without arbitrary array-index pairing.
        Metformin must be 500 mg (not cross-paired), Amoxicillin must be 500 mg (not 100 mcg),
        and Salbutamol must be 100 mcg (not 500 mg).
        """
        from pipeline.timeline import build_timeline_summary

        ents = detect_negations(self.test_note, hybrid_ner(self.test_note))
        regimens = reconstruct_regimens(self.test_note, entities=ents)

        summary = build_timeline_summary(ents, regimens=regimens)
        med_summary = {m['name'].lower(): m for m in summary['medications']}

        # Verify all 3 medications are present
        assert 'metformin' in med_summary
        assert 'amoxicillin' in med_summary
        assert 'salbutamol' in med_summary

        # Verify correct associations
        assert med_summary['metformin']['dosage'] == '500 mg'
        assert med_summary['metformin']['frequency'] == 'twice daily'

        assert med_summary['amoxicillin']['dosage'] == '500 mg'
        assert med_summary['amoxicillin']['frequency'] == 'three times daily'

        assert med_summary['salbutamol']['dosage'] == '100 mcg'
        assert med_summary['salbutamol']['frequency'] == 'as needed'

        # Negative checks: verify no index-mismatches occurred
        assert med_summary['amoxicillin']['dosage'] != '100 mcg', "Amoxicillin was incorrectly assigned 100 mcg!"
        assert med_summary['salbutamol']['dosage'] != '500 mg', "Salbutamol was incorrectly assigned 500 mg!"


class TestInvestigationFalsePositiveGapsRegression:
    """Regression tests covering false-positive investigation gap detection requirements:
    1. “A urine test was ordered but has not yet been performed.”
    2. “A complete blood count was performed.”
    3. Generic wording such as “the test was not performed” without a named investigation.
    4. A genuinely unmentioned guideline-recommended investigation.
    """

    def test_urine_test_ordered_but_not_yet_performed(self):
        """'A urine test was ordered but has not yet been performed.' -> status ORDERED/PENDING, no gap."""
        text = "A urine test was ordered but has not yet been performed."
        ents = detect_negations(text, hybrid_ner(text))
        urine_ent = next((e for e in ents if 'urine' in e['entity_text'].lower()), None)
        assert urine_ent is not None, "Expected urine test to be extracted as an entity"
        assert urine_ent['entity_type'] == 'INVESTIGATION'
        assert urine_ent['status'] == 'ORDERED/PENDING'
        assert urine_ent['status'] != 'completed/performed'
        assert urine_ent['negated'] is False, "Ordered but pending test should not be negated"

        # Gap detection must NOT create a missing-investigation gap for it
        engine = GuidelineEngine()
        rules = engine.match(ents)
        gaps = detect_gaps(ents, rules)
        urine_gaps = [g for g in gaps if 'urine' in g.get('entity', '').lower() or 'urine' in g.get('description', '').lower()]
        assert len(urine_gaps) == 0, f"Expected no gap for ordered urine test, found: {urine_gaps}"

    def test_complete_blood_count_performed(self):
        """'A complete blood count was performed.' -> completed/performed, no missing gap."""
        text = "A complete blood count was performed."
        ents = detect_negations(text, hybrid_ner(text))
        cbc_ent = next((e for e in ents if 'blood count' in e['entity_text'].lower() or e.get('normalized_value') == 'cbc'), None)
        assert cbc_ent is not None, "Expected CBC to be extracted"
        assert cbc_ent['entity_type'] == 'INVESTIGATION'
        assert cbc_ent['status'] == 'completed/performed'
        assert cbc_ent['negated'] is False

        engine = GuidelineEngine()
        rules = engine.match(ents)
        gaps = detect_gaps(ents, rules)
        cbc_gaps = [g for g in gaps if g.get('entity') == 'cbc']
        assert len(cbc_gaps) == 0, f"Expected no gap for performed CBC, found: {cbc_gaps}"

    def test_generic_test_wording_not_extracted_as_entity_or_gap(self):
        """'The test was not performed.' without a named investigation must not produce a generic TEST entity or gap."""
        text = "The patient was evaluated and the test was not performed."
        ents = detect_negations(text, hybrid_ner(text))
        generic_test_ents = [
            e for e in ents
            if e.get('entity_type') == 'INVESTIGATION' and e.get('entity_text', '').strip().lower() in {'test', 'tests', 'the test'}
        ]
        assert len(generic_test_ents) == 0, f"Generic 'test' should not be extracted as standalone entity: {generic_test_ents}"

        engine = GuidelineEngine()
        rules = engine.match(ents)
        gaps = detect_gaps(ents, rules)
        test_gaps = [g for g in gaps if g.get('entity', '').lower() in {'test', 'tests'}]
        assert len(test_gaps) == 0, f"Generic 'test' gap must not be emitted: {test_gaps}"

    def test_genuinely_unmentioned_guideline_recommended_investigation_emits_gap(self):
        """Patient with diabetes where HbA1c is never mentioned -> Rule R2 must trigger MISSING_INVESTIGATION for HbA1c."""
        text = "Patient has type 2 diabetes mellitus and hypertension. A urine test was ordered but has not yet been performed."
        ents = detect_negations(text, hybrid_ner(text))
        engine = GuidelineEngine()
        rules = engine.match(ents)
        gaps = detect_gaps(ents, rules)

        hba1c_gaps = [g for g in gaps if g.get('entity') == 'hba1c']
        assert len(hba1c_gaps) == 1, f"Expected exactly 1 HbA1c guideline gap, found: {hba1c_gaps}"
        assert hba1c_gaps[0]['gap_type'] == 'MISSING_INVESTIGATION'
        assert hba1c_gaps[0]['rule_id'] == 'R2'

        # Ensure no false-positive gaps for urine test or generic test
        false_positive_gaps = [
            g for g in gaps
            if g.get('entity') in {'test', 'tests', 'urine test'}
        ]
        assert len(false_positive_gaps) == 0, f"Found false positive gaps: {false_positive_gaps}"

    @pytest.mark.parametrize("note_text,expected_status,expected_display,should_not_be_performed", [
        (
            "A urine test was ordered but has not yet been performed.",
            "ORDERED/PENDING",
            "Ordered / Pending",
            True
        ),
        (
            "A urine test was performed.",
            "completed/performed",
            "Performed",
            False
        ),
        (
            "A urine test was ordered but the result is not yet available.",
            "pending",
            "Pending Results",
            True
        ),
        (
            "A urine test was cancelled and not performed.",
            "not performed",
            "Not performed",
            True
        ),
    ])
    def test_investigation_lifecycle_status_and_timeline_display(
        self, note_text, expected_status, expected_display, should_not_be_performed
    ):
        """Verify the 4 required investigation lifecycle states:
        - 'Urine test was ordered but has not yet been performed' -> Ordered / Pending
        - 'Urine test was performed' -> Performed
        - 'Urine test was ordered but the result is not yet available' -> Pending Results
        - Explicitly cancelled/unperformed -> Not performed (never Performed)
        """
        from pipeline.timeline import build_timeline_summary, format_investigation_timeline_status

        ents = detect_negations(note_text, hybrid_ner(note_text))
        urine_ent = next((e for e in ents if 'urine' in e['entity_text'].lower()), None)
        assert urine_ent is not None, f"Expected urine test entity in '{note_text}'"
        assert urine_ent['status'] == expected_status

        if should_not_be_performed:
            assert urine_ent['status'] != 'completed/performed'
            assert format_investigation_timeline_status(urine_ent['status'], urine_ent.get('negated', False)) != 'Performed'

        display = format_investigation_timeline_status(urine_ent['status'], urine_ent.get('negated', False))
        assert display == expected_display

        summary = build_timeline_summary(ents)
        inv_summary = next((inv for inv in summary['investigations'] if 'urine' in inv.get('entity_text', '').lower()), None)
        assert inv_summary is not None
        assert inv_summary['display_status'] == expected_display
        if should_not_be_performed:
            assert inv_summary['display_status'] != 'Performed'
