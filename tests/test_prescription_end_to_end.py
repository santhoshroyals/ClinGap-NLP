import pytest
import json
from backend.services.prescription_service import reconstruct_regimens, parse_prescription
from backend.services.clinical_pipeline import ClinicalPipeline
from backend.services.ner_service import hybrid_ner

def test_case_1_amoxicillin_three_times_daily():
    text = "The patient is prescribed amoxicillin 500 mg three times daily."
    regimens = reconstruct_regimens(text)
    assert len(regimens) == 1
    assert regimens[0]['medication'].lower() == 'amoxicillin'
    assert regimens[0]['dosage'] == '500 mg'
    assert regimens[0]['frequency'] == 'three times daily'

def test_case_2_metformin_twice_daily():
    text = "The patient is prescribed metformin 500 mg twice daily."
    regimens = reconstruct_regimens(text)
    assert len(regimens) == 1
    assert regimens[0]['medication'].lower() == 'metformin'
    assert regimens[0]['dosage'] == '500 mg'
    assert regimens[0]['frequency'] == 'twice daily'

def test_case_3_every_8_hours():
    text = "Prescribe ibuprofen 400 mg every 8 hours."
    regimens = reconstruct_regimens(text)
    assert len(regimens) == 1
    assert regimens[0]['medication'].lower() == 'ibuprofen'
    assert regimens[0]['dosage'] == '400 mg'
    assert regimens[0]['frequency'] == 'every 8 hours'

def test_case_4_as_needed():
    text = "Take paracetamol 500 mg as needed for fever."
    regimens = reconstruct_regimens(text)
    assert len(regimens) == 1
    assert regimens[0]['medication'].lower() == 'paracetamol'
    assert regimens[0]['dosage'] == '500 mg'
    assert regimens[0]['frequency'] == 'as needed'

def test_case_5_dosage_without_frequency():
    text = "Patient was given amoxicillin 250 mg for infection."
    regimens = reconstruct_regimens(text)
    assert len(regimens) == 1
    assert regimens[0]['medication'].lower() == 'amoxicillin'
    assert regimens[0]['dosage'] == '250 mg'
    assert regimens[0]['frequency'] is None

def test_case_6_frequency_without_dosage():
    text = "Patient instructed to take metformin once daily with breakfast."
    regimens = reconstruct_regimens(text)
    assert len(regimens) == 1
    assert regimens[0]['medication'].lower() == 'metformin'
    assert regimens[0]['dosage'] is None
    assert regimens[0]['frequency'] == 'once daily'

def test_case_7_multiple_medications_different_frequencies():
    text = (
        "Prescribed metformin 500 mg twice daily for glycemic control, "
        "and lisinopril 10 mg once daily for blood pressure."
    )
    regimens = reconstruct_regimens(text)
    assert len(regimens) == 2
    med_map = {r['medication'].lower(): r for r in regimens}
    assert 'metformin' in med_map
    assert med_map['metformin']['dosage'] == '500 mg'
    assert med_map['metformin']['frequency'] == 'twice daily'

    assert 'lisinopril' in med_map
    assert med_map['lisinopril']['dosage'] == '10 mg'
    assert med_map['lisinopril']['frequency'] == 'once daily'

def test_case_8_no_medications():
    text = "Patient complains of headache and fatigue. CBC was performed with normal results."
    regimens = reconstruct_regimens(text)
    assert len(regimens) == 0

def test_case_9_medication_absent_from_dictionary():
    # Synthetic / unlisted drug name that NER model identifies or text supplies with entities
    custom_entities = [
        {'entity_text': 'Zilucoplan', 'entity_type': 'MEDICATION', 'confidence': 0.95}
    ]
    text = "Started on Zilucoplan 16.6 mg once daily subcutaneously."
    regimens = reconstruct_regimens(text, entities=custom_entities)
    assert len(regimens) == 1
    assert regimens[0]['medication'] == 'Zilucoplan'
    assert regimens[0]['dosage'] == '16.6 mg'
    assert regimens[0]['frequency'] == 'once daily'

def test_case_10_pipeline_run_returns_regimens_and_frequencies():
    pipeline = ClinicalPipeline()
    text = "The patient is prescribed amoxicillin 500 mg three times daily."
    result = pipeline.run(None, text=text)
    
    assert 'regimens' in result
    assert len(result['regimens']) == 1
    reg = result['regimens'][0]
    assert reg['medication'].lower() == 'amoxicillin'
    assert reg['dosage'] == '500 mg'
    assert reg['frequency'] == 'three times daily'
    
    # Check that entities contains both DOSAGE and FREQUENCY
    freq_entities = [e for e in result['entities'] if e['entity_type'] == 'FREQUENCY']
    assert len(freq_entities) >= 1
    assert any(fe['entity_text'] == 'three times daily' for fe in freq_entities)
