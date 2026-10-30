import pytest
from backend.services.ner_service import hybrid_ner, extract_investigation_status
from backend.services.model_manager import ModelManager
from backend.services.clinical_pipeline import ClinicalPipeline


def test_administrative_ids_not_extracted_as_lab_test():
    """Regression test: Administrative IDs and numbers must not be extracted as LAB_TEST."""
    note = (
        "Patient Name: Mousumi Ghosh\n"
        "UHID: 615819763\n"
        "Admission No: ADM-20264153\n"
        "Socio-Economic Status: Class II as per modified Kuppuswamy scale.\n"
        "Condition at Discharge: Stable, afebrile.\n"
    )
    entities = hybrid_ner(note)
    lab_tests = [e['entity_text'] for e in entities if e['entity_type'] == 'LAB_TEST']

    assert "615819763" not in lab_tests, "UHID was incorrectly extracted as LAB_TEST"
    assert "ADM-20264153" not in lab_tests, "Admission number was incorrectly extracted as LAB_TEST"
    assert "Class II" not in lab_tests, "Kuppuswamy scale class was incorrectly extracted as LAB_TEST"
    assert "Stable" not in lab_tests, "Discharge condition was incorrectly extracted as LAB_TEST"


def test_section_headings_not_extracted_as_investigation():
    """Regression test: Section headings and department names must not be extracted as INVESTIGATION."""
    note = (
        "Treating Consultant: Dr. Rajesh Kumar, Cardiology\n"
        "Department of General_Medicine\n"
        "Sankara Nethralaya Chennai\n"
        "Discharge Summary - V2\n"
        "Physical Examination: Pulse: Irregular.\n"
        "Condition at Discharge: Stable.\n"
    )
    entities = hybrid_ner(note)
    investigations = [e['entity_text'].lower() for e in entities if e['entity_type'] == 'INVESTIGATION']

    assert "physical examination" not in investigations, "Section heading was incorrectly extracted as INVESTIGATION"
    assert "cardiology" not in investigations, "Department was incorrectly extracted as INVESTIGATION"
    assert "general_medicine" not in investigations, "Department was incorrectly extracted as INVESTIGATION"
    assert "condition" not in investigations, "Condition was incorrectly extracted as INVESTIGATION"
    assert "summary" not in investigations, "Summary was incorrectly extracted as INVESTIGATION"
    assert "nethralaya" not in investigations, "Hospital name was incorrectly extracted as INVESTIGATION"


def test_isolated_common_words_not_symptoms():
    """Regression test: Isolated common words and Hindi stop words must not become SYMPTOM entities."""
    note = "Patient ko bahut weakness thi. Bolne mein difficulty."
    entities = hybrid_ner(note)
    symptoms = [e['entity_text'].lower() for e in entities if e['entity_type'] == 'SYMPTOM']

    assert "bahut" not in symptoms, "Hindi stop word 'bahut' was incorrectly extracted as SYMPTOM"
    assert "difficulty" not in symptoms, "Isolated fragment 'difficulty' was incorrectly extracted as SYMPTOM"


def test_multiword_clinical_entity_extraction():
    """Regression test: Multiword clinical entities are correctly extracted."""
    note = (
        "Chief Complaints: Palpitations and irregular heartbeat.\n"
        "History of Present Illness: Productive cough, no hemoptysis.\n"
        "Neurology: Right side weakness noted.\n"
    )
    entities = hybrid_ner(note)
    extracted_texts = [e['entity_text'].lower() for e in entities]

    assert "irregular heartbeat" in extracted_texts, "Multiword entity 'irregular heartbeat' was missed"
    assert "productive cough" in extracted_texts, "Multiword entity 'productive cough' was missed"
    assert "right side weakness" in extracted_texts, "Multiword entity 'right side weakness' was missed"
    assert "hemoptysis" in extracted_texts, "Entity 'hemoptysis' was missed"


def test_investigation_extraction_and_status_classification():
    """Regression test: Colon-delimited findings and status classifications."""
    note = (
        "Investigations: ECG: ST elevation; Trop-I: Positive; Echo: EF 46%; "
        "Angiogram: 77% blockage in LAD; CBC: WBC high; X-ray: Pneumonia."
    )
    entities = hybrid_ner(note)
    inv_map = {e['entity_text'].lower(): e for e in entities if e['entity_type'] == 'INVESTIGATION'}

    assert "ecg" in inv_map, "ECG was not extracted"
    assert "trop-i" in inv_map, "Trop-I was not extracted"
    assert "echo" in inv_map, "Echo was not extracted"
    assert "angiogram" in inv_map, "Angiogram was not extracted"
    assert "cbc" in inv_map, "CBC was not extracted"
    assert "x-ray" in inv_map, "X-ray was not extracted"

    assert inv_map["ecg"]["status"] == "completed/performed"
    assert inv_map["echo"]["status"] == "completed/performed"
    assert inv_map["angiogram"]["status"] == "completed/performed"

    # Status function direct unit checks
    assert extract_investigation_status("CT was ordered, pending results", "CT") == "ORDERED/PENDING"
    assert extract_investigation_status("MRI scheduled for next week", "MRI") == "ordered"
    assert extract_investigation_status("Biopsy was not performed due to refusal", "Biopsy") == "not performed"


def test_model_fallback_status_reporting():
    """Regression test: System explicitly reports biomedical model or fallback status."""
    status = ModelManager.get_ner_status()
    assert isinstance(status, str)
    assert len(status) > 0
    # Must explicitly state whether biomedical model or fallback is active
    assert "Biomedical model active" in status or "Fallback active" in status

    pipeline = ClinicalPipeline()
    result = pipeline.run(db=None, text="Patient has fever.")
    assert "ner_status" in result, "Pipeline output missing ner_status"
    assert isinstance(result["ner_status"], str)
