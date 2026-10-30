import pytest
from backend.services.ner_service import hybrid_ner
from backend.services.negation_service import detect_negations
from backend.services.guideline_service import GuidelineEngine
from backend.services.gap_detection import detect_gaps


def test_hybrid_ner_basic():
    text = 'Patient takes aspirin and needs a CBC. No headache reported.'
    ents = hybrid_ner(text)
    types = {e['entity_type'] for e in ents}
    assert 'MEDICATION' in types
    assert 'INVESTIGATION' in types
    assert 'SYMPTOM' in types
    # Dosage/frequency not present, ensure no false positives
    assert not any(e['entity_type'] == 'DOSAGE' for e in ents)


def test_demo_clinical_note():
    text = (
        "The patient has diabetes mellitus.\n"
        "CBC was not performed.\n"
        "HbA1c was performed and the result was 8.2%.\n"
        "The patient is taking metformin 500 mg twice daily."
    )
    ents = hybrid_ner(text)
    ents = detect_negations(text, ents)
    by_text = {e['entity_text']: e for e in ents}

    assert 'diabetes mellitus' in by_text
    assert by_text['diabetes mellitus']['entity_type'] == 'DISEASE'

    assert 'CBC' in by_text
    assert by_text['CBC']['entity_type'] == 'INVESTIGATION'
    assert by_text['CBC']['negated'] is True

    assert 'HbA1c' in by_text
    assert by_text['HbA1c']['entity_type'] == 'INVESTIGATION'
    assert by_text['HbA1c']['negated'] is False
    assert by_text['HbA1c']['normalized_value'] == 'hba1c'

    assert 'metformin' in by_text
    assert by_text['metformin']['entity_type'] == 'MEDICATION'

    assert '500 mg' in by_text
    assert by_text['500 mg']['entity_type'] == 'DOSAGE'

    assert 'twice daily' in by_text
    assert by_text['twice daily']['entity_type'] == 'FREQUENCY'


def test_hba1c_classification_and_variants():
    """Verify that HbA1c and its synonym/casing variants normalize to INVESTIGATION / hba1c."""
    variants = [
        "HbA1c was performed.",
        "HBA1C was performed.",
        "hba1c was performed.",
        "Hemoglobin A1c was performed.",
        "glycated hemoglobin was performed.",
        "glycosylated hemoglobin was performed.",
    ]
    for sent in variants:
        ents = hybrid_ner(sent)
        inv_ents = [e for e in ents if e['entity_type'] == 'INVESTIGATION']
        assert any(e['normalized_value'] == 'hba1c' for e in inv_ents), f"Failed for variant: {sent}"
        # Ensure it is not classified as MEDICATION
        assert not any(e['entity_type'] == 'MEDICATION' and 'hba1c' in e['entity_text'].lower() for e in ents)


def test_guideline_r2_hba1c_performed_no_gap():
    """When diabetes is present and HbA1c was performed, R2 should NOT emit a missing investigation gap."""
    text = (
        "Patient presents with hypertension and diabetes mellitus. "
        "HbA1c was performed. CBC was not performed."
    )
    ents = hybrid_ner(text)
    ents = detect_negations(text, ents)

    hba1c_ent = next((e for e in ents if e['normalized_value'] == 'hba1c'), None)
    assert hba1c_ent is not None
    assert hba1c_ent['entity_type'] == 'INVESTIGATION'
    assert hba1c_ent['negated'] is False

    engine = GuidelineEngine()
    rules = engine.match(ents)
    rule_ids = [r['rule_id'] for r in rules]
    assert 'R2' in rule_ids

    gaps = detect_gaps(ents, rules)
    gap_entities = [g['entity'] for g in gaps]
    # CBC was not performed -> missing CBC gap
    assert 'cbc' in gap_entities
    # HbA1c was performed -> NO missing HbA1c gap
    assert 'hba1c' not in gap_entities


def test_guideline_r2_hba1c_not_performed_emits_gap():
    """When diabetes is present and HbA1c was not performed, a missing investigation gap MUST be emitted."""
    text = (
        "Patient presents with hypertension and diabetes mellitus. "
        "HbA1c was not performed."
    )
    ents = hybrid_ner(text)
    ents = detect_negations(text, ents)

    hba1c_ent = next((e for e in ents if e['normalized_value'] == 'hba1c'), None)
    assert hba1c_ent is not None
    assert hba1c_ent['entity_type'] == 'INVESTIGATION'
    assert hba1c_ent['negated'] is True

    engine = GuidelineEngine()
    rules = engine.match(ents)
    gaps = detect_gaps(ents, rules)
    gap_entities = [g['entity'] for g in gaps]
    assert 'hba1c' in gap_entities


def test_hyper_fragment_suppression():
    """'hyper' must not be extracted as a symptom when only 'hypertension' is present."""
    text = "Patient presents with hypertension and diabetes mellitus."
    ents = hybrid_ner(text)
    ent_texts = [e['entity_text'].lower() for e in ents]
    assert 'hypertension' in ent_texts
    assert 'hyper' not in ent_texts


def test_nested_entity_deduplication():
    """Shorter entity inside longer entity is suppressed if 100% nested, but kept if distinct occurrence exists."""
    # Case 1: 100% nested
    text1 = "Patient presents with hypertension and diabetes mellitus."
    ents1 = hybrid_ner(text1)
    texts1 = [e['entity_text'].lower() for e in ents1]
    assert 'diabetes mellitus' in texts1
    assert 'diabetes' not in texts1

    # Case 2: Separate occurrence exists
    text2 = "Patient has diabetes mellitus. Family history of diabetes."
    ents2 = hybrid_ner(text2)
    texts2 = [e['entity_text'].lower() for e in ents2]
    assert 'diabetes mellitus' in texts2
    assert 'diabetes' in texts2


def test_noise_token_filtering():
    """Header and document noise tokens like ClinGap, NLP Test, Clinical Note must not be extracted."""
    text = "ClinGap - NLP Test - Clinical Note. Patient has headache."
    ents = hybrid_ner(text)
    texts = [e['entity_text'].lower() for e in ents]
    assert 'clingap' not in texts
    assert 'nlp test' not in texts
    assert 'clinical note' not in texts
    assert 'headache' in texts


def test_full_verified_clinical_note_pipeline():
    """End-to-end verification of the exact clinical note described in the user prompt."""
    text = (
        "Patient presents with hypertension and diabetes mellitus.\n"
        "The patient reports headache and fatigue.\n"
        "The patient is prescribed metformin 500 mg twice daily and lisinopril 10 mg once daily.\n"
        "HbA1c was performed.\n"
        "CBC was not performed.\n"
        "The patient denies dizziness."
    )
    ents = hybrid_ner(text)
    ents = detect_negations(text, ents)

    by_norm = {e['normalized_value']: e for e in ents}
    by_text = {e['entity_text'].lower(): e for e in ents}

    # Verify entities
    assert 'hypertension' in by_text
    assert 'diabetes mellitus' in by_text
    assert 'diabetes' not in by_text  # nested duplicate suppressed
    assert 'hyper' not in by_text      # fragment suppressed

    assert 'hba1c' in by_norm
    assert by_norm['hba1c']['entity_type'] == 'INVESTIGATION'
    assert by_norm['hba1c']['negated'] is False

    assert 'cbc' in by_norm
    assert by_norm['cbc']['entity_type'] == 'INVESTIGATION'
    assert by_norm['cbc']['negated'] is True

    assert 'dizziness' in by_text
    assert by_text['dizziness']['negated'] is True

    # Guideline & Gap Detection
    engine = GuidelineEngine()
    rules = engine.match(ents)
    gaps = detect_gaps(ents, rules)

    gap_entities = [g['entity'] for g in gaps]
    assert 'cbc' in gap_entities
    assert 'hba1c' not in gap_entities  # HbA1c was performed, so no gap!
