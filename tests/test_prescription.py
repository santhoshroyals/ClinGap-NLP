import pytest
from backend.services.ner_service import hybrid_ner
from backend.services.prescription_service import (
    parse_prescription,
    reconstruct_regimens,
    extract_regimens,
)


def test_controlled_prescription_regimens():
    """
    Controlled regression test:
    Input:
      'The patient has hypertension and diabetes mellitus.
       The patient is prescribed metformin 500 mg twice daily and lisinopril 10 mg once daily.
       The patient should continue both medications for two weeks.'
    Expected:
      - metformin -> MEDICATION, dosage -> 500 mg, frequency -> twice daily
      - lisinopril -> MEDICATION, dosage -> 10 mg, frequency -> once daily
      - generic 'medications' MUST NOT be extracted as a medication
      - dosage extraction does not include frequency words
    """
    text = (
        "The patient has hypertension and diabetes mellitus. "
        "The patient is prescribed metformin 500 mg twice daily and lisinopril 10 mg once daily. "
        "The patient should continue both medications for two weeks."
    )

    entities = hybrid_ner(text)

    # 1. Verify entity extraction
    med_entities = [e for e in entities if e["entity_type"] == "MEDICATION"]
    med_texts = [e["entity_text"].lower() for e in med_entities]

    assert "metformin" in med_texts
    assert "lisinopril" in med_texts
    assert "medications" not in med_texts
    assert "medication" not in med_texts

    # 2. Verify dosage does not contain frequency words
    dosage_entities = [e for e in entities if e["entity_type"] == "DOSAGE"]
    dosage_texts = [e["entity_text"].lower() for e in dosage_entities]

    assert "500 mg" in dosage_texts
    assert "10 mg" in dosage_texts
    for d in dosage_texts:
        assert "daily" not in d
        assert "twice" not in d
        assert "once" not in d

    # 3. Verify frequency extraction
    freq_entities = [e for e in entities if e["entity_type"] == "FREQUENCY"]
    freq_texts = [e["entity_text"].lower() for e in freq_entities]

    assert "twice daily" in freq_texts
    assert "once daily" in freq_texts

    # 4. Verify regimen reconstruction associations
    regimens = reconstruct_regimens(text, entities=entities)
    reg_by_med = {r["medication"].lower(): r for r in regimens}

    assert "metformin" in reg_by_med
    assert reg_by_med["metformin"]["dosage"] == "500 mg"
    assert reg_by_med["metformin"]["frequency"] == "twice daily"

    assert "lisinopril" in reg_by_med
    assert reg_by_med["lisinopril"]["dosage"] == "10 mg"
    assert reg_by_med["lisinopril"]["frequency"] == "once daily"

    assert "medications" not in reg_by_med
    assert "medication" not in reg_by_med


def test_generic_medications_exclusion():
    """
    Verify that generic words like 'medications' or 'medication' are never
    extracted as a MEDICATION entity or reconstructed as a regimen.
    """
    text = "The patient should continue both medications for two weeks."
    entities = hybrid_ner(text)

    med_entities = [e for e in entities if e["entity_type"] == "MEDICATION"]
    for m in med_entities:
        assert m["entity_text"].lower() not in {"medication", "medications", "medicine", "medicines"}

    regimens = reconstruct_regimens(text, entities=entities)
    assert len(regimens) == 0


def test_dosage_does_not_contain_frequency_words():
    """
    Verify that parsing '500 mg twice daily' separates dosage from frequency cleanly:
    dosage = '500 mg'
    frequency = 'twice daily'
    """
    parsed = parse_prescription("500 mg twice daily")
    assert parsed["dosage"] == "500 mg"
    assert parsed["frequency"] == "twice daily"
