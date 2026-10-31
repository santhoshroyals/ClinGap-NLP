"""
generate_diverse_evaluation_dataset.py
======================================
Generates a defensible, large-scale (N=800: 200 Dev, 600 Held-Out Test),
diverse, clinically plausible synthetic evaluation dataset for ClinGap-NLP.

Requirements:
- Independent ground truth established by clinical logic (not model predictions).
- Balanced Gap vs. No-Gap distribution (~50/50).
- Stratification across 10 medical specialties.
- Broad spectrum of 10 clinical scenario categories:
  1. Missing required investigation for acute presentation (Gap=True)
  2. Missing required monitoring for chronic metabolic condition (Gap=True)
  3. Explicitly unperformed / cancelled / refused investigations (Gap=True)
  4. Partially satisfied guideline recommendations (Gap=True)
  5. Multi-condition complex presentations with omissions (Gap=True)
  6. Complete guideline compliance with documented completed results (Gap=False)
  7. Ordered / pending investigations actively awaiting results (Gap=False)
  8. Clausal and coordinated negations of clinical findings (Gap=False)
  9. Historical or resolved conditions vs active presentation (Gap=False)
  10. Non-target conditions without indication for CBC/HbA1c (Gap=False)
  11. Contradictory / ambiguous mentions (Gap=False)
  12. Boundary cases with lab measurements & generic procedure terms (Gap=False)

Reproducibility: SEED = 42
"""

import os
import sys
import json
import random
from typing import List, Dict, Any

SEED = 42
random.seed(SEED)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "evaluation", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

SPECIALTIES = [
    "Internal Medicine",
    "Cardiology",
    "Pulmonology",
    "Endocrinology",
    "Gastroenterology",
    "Neurology",
    "Nephrology",
    "Pediatrics",
    "Geriatrics",
    "Oncology",
]

# Vocabulary & clinical templates pools
SYMPTOMS_POOL = [
    ("fever", "fever"),
    ("persistent cough", "cough"),
    ("productive cough", "cough"),
    ("chest pain", "chest pain"),
    ("substernal chest pain", "chest pain"),
    ("severe headache", "headache"),
    ("dizziness", "dizziness"),
    ("generalized fatigue", "fatigue"),
    ("severe weakness", "weakness"),
    ("shortness of breath", "dyspnea"),
    ("abdominal pain", "abdominal pain"),
    ("vomiting", "vomiting"),
    ("palpitations", "palpitations"),
]

DISEASES_POOL = [
    ("type 2 diabetes mellitus", "diabetes mellitus", True),   # Needs HbA1c
    ("diabetes mellitus", "diabetes mellitus", True),          # Needs HbA1c
    ("uncontrolled diabetes", "diabetes mellitus", True),      # Needs HbA1c
    ("essential hypertension", "hypertension", False),         # Non-target
    ("hypertension", "hypertension", False),                  # Non-target
    ("bronchial asthma", "asthma", False),                    # Non-target
    ("coronary artery disease", "coronary artery disease", False), # Non-target
    ("acute gastritis", "gastritis", False),                  # Non-target
    ("migraine", "migraine", False),                          # Non-target
    ("epilepsy", "epilepsy", False),                          # Non-target
    ("chronic kidney disease stage 3", "chronic kidney disease", False), # Non-target
    ("osteoarthritis", "osteoarthritis", False),              # Non-target
]

MEDICATIONS_POOL = [
    ("metformin", "500 mg", "twice daily"),
    ("metformin", "850 mg", "twice daily"),
    ("aspirin", "75 mg", "once daily"),
    ("aspirin", "150 mg", "once daily"),
    ("lisinopril", "10 mg", "once daily"),
    ("lisinopril", "20 mg", "once daily"),
    ("amoxicillin", "500 mg", "three times daily"),
    ("amoxicillin", "250 mg", "three times daily"),
    ("ibuprofen", "400 mg", "as needed"),
    ("salbutamol", "100 mcg", "as needed"),
    ("atorvastatin", "40 mg", "at bedtime"),
    ("clopidogrel", "75 mg", "once daily"),
    ("pantoprazole", "40 mg", "once daily"),
]

INVESTIGATIONS_POOL = [
    ("complete blood count", "cbc"),
    ("CBC", "cbc"),
    ("HbA1c", "hba1c"),
    ("glycated hemoglobin", "hba1c"),
    ("chest X-ray", "x-ray"),
    ("chest xray", "x-ray"),
    ("electrocardiogram", "ecg"),
    ("ECG", "ecg"),
    ("troponin-I", "trop-i"),
    ("echocardiogram", "echo"),
    ("endoscopy", "endoscopy"),
    ("ultrasound abdomen", "ultrasound"),
]

COMPLETED_PHRASES = [
    "was performed and results were within normal limits.",
    "completed with unremarkable findings.",
    "showed normal parameters.",
    "was conducted today and confirmed stable status.",
    "revealed no acute abnormality.",
    "result was documented in the medical chart.",
]

PENDING_PHRASES = [
    "was ordered and results are currently pending from the laboratory.",
    "has been requisitioned and is awaiting technician review.",
    "ordered today, final laboratory report awaited.",
    "has been requested and is currently in progress.",
    "was sent for analysis; results pending.",
]

UNPERFORMED_PHRASES = [
    "was not performed due to patient refusal.",
    "was cancelled due to hemolyzed laboratory sample.",
    "was omitted because of machine calibration downtime.",
    "was declined by the patient after informed consent discussion.",
    "was deferred and not done during this visit.",
    "was not completed owing to technical difficulties.",
]


def create_case(case_id: str, specialty: str, category_idx: int, split: str) -> Dict[str, Any]:
    """Generates a single diverse clinical case with independent ground truth."""
    expected_entities = []
    expected_negations = []
    expected_investigations = []
    expected_medications = []
    expected_gap_entities = []
    expected_gap = False
    rationale = ""
    note_text = ""

    # Category 0: Missing required investigation for acute presentation (Gap = True)
    if category_idx == 0:
        sym_text, sym_norm = random.choice(SYMPTOMS_POOL)
        dur = random.randint(2, 7)
        age = random.randint(22, 74)
        gender = random.choice(["male", "female"])
        note_text = (
            f"A {age}-year-old {gender} presented to {specialty} complaining of {sym_text} for {dur} days. "
            f"Vital signs are recorded and general physical exam was conducted. No diagnostic laboratory tests were ordered or documented."
        )
        expected_entities.append({"entity_text": sym_text, "entity_type": "SYMPTOM", "normalized_value": sym_norm, "negated": False})
        expected_negations.append({"entity_text": sym_text, "negated": False})
        expected_investigations.append({"entity_text": "CBC", "status": "undocumented", "negated": False})
        expected_gap = True
        expected_gap_entities = ["cbc"]
        rationale = f"Acute symptom presentation ({sym_text}) indicates CBC evaluation. CBC is undocumented in the note."

    # Category 1: Missing monitoring for chronic metabolic condition (Gap = True)
    elif category_idx == 1:
        dis_text, dis_norm, _ = random.choice([d for d in DISEASES_POOL if d[2]])
        age = random.randint(45, 80)
        gender = random.choice(["male", "female"])
        med_name, med_dose, med_freq = random.choice(MEDICATIONS_POOL[:4])
        note_text = (
            f"Follow-up visit in {specialty} clinic for a {age}-year-old {gender} with established {dis_text}. "
            f"Current regimen includes {med_name} {med_dose} {med_freq}. "
            f"Blood pressure is stable. No glycemic monitoring or HbA1c testing is documented in this encounter."
        )
        expected_entities.append({"entity_text": dis_text, "entity_type": "DISEASE", "normalized_value": dis_norm, "negated": False})
        expected_entities.append({"entity_text": med_name, "entity_type": "MEDICATION", "normalized_value": med_name, "negated": False})
        expected_entities.append({"entity_text": med_dose, "entity_type": "DOSAGE", "normalized_value": med_dose, "negated": False})
        expected_entities.append({"entity_text": med_freq, "entity_type": "FREQUENCY", "normalized_value": med_freq, "negated": False})
        expected_negations.append({"entity_text": dis_text, "negated": False})
        expected_investigations.append({"entity_text": "HbA1c", "status": "undocumented", "negated": False})
        expected_medications.append({"name": med_name, "dosage": med_dose, "frequency": med_freq})
        expected_gap = True
        expected_gap_entities = ["hba1c"]
        rationale = f"Patient with {dis_text} requires periodic HbA1c assessment. No HbA1c is documented."

    # Category 2: Explicitly unperformed / cancelled / refused investigation (Gap = True)
    elif category_idx == 2:
        inv_text, inv_norm = random.choice(INVESTIGATIONS_POOL[:6])
        unperf_phrase = random.choice(UNPERFORMED_PHRASES)
        age = random.randint(30, 75)
        gender = random.choice(["male", "female"])
        note_text = (
            f"Clinical encounter at {specialty} department for a {age}-year-old {gender}. "
            f"Routine physical examination completed. {inv_text} {unperf_phrase} "
            f"Plan discussed with patient regarding rescheduling."
        )
        expected_entities.append({"entity_text": inv_text, "entity_type": "INVESTIGATION", "normalized_value": inv_norm, "negated": True})
        expected_negations.append({"entity_text": inv_text, "negated": True})
        expected_investigations.append({"entity_text": inv_text, "status": "not performed", "negated": True})
        expected_gap = True
        expected_gap_entities = [inv_norm]
        rationale = f"{inv_text} was explicitly not performed / cancelled, constituting an unperformed gap."

    # Category 3: Partially satisfied guideline recommendations (Gap = True)
    elif category_idx == 3:
        sym_text, sym_norm = random.choice(SYMPTOMS_POOL[:6])
        dis_text, dis_norm, _ = random.choice([d for d in DISEASES_POOL if d[2]])
        comp_phrase = random.choice(COMPLETED_PHRASES)
        note_text = (
            f"Patient with {dis_text} presents with new {sym_text}. "
            f"Complete blood count {comp_phrase} However, routine HbA1c was not documented or ordered."
        )
        expected_entities.append({"entity_text": dis_text, "entity_type": "DISEASE", "normalized_value": dis_norm, "negated": False})
        expected_entities.append({"entity_text": sym_text, "entity_type": "SYMPTOM", "normalized_value": sym_norm, "negated": False})
        expected_entities.append({"entity_text": "complete blood count", "entity_type": "INVESTIGATION", "normalized_value": "cbc", "negated": False})
        expected_negations.append({"entity_text": dis_text, "negated": False})
        expected_negations.append({"entity_text": sym_text, "negated": False})
        expected_negations.append({"entity_text": "complete blood count", "negated": False})
        expected_investigations.append({"entity_text": "complete blood count", "status": "completed/performed", "negated": False})
        expected_investigations.append({"entity_text": "HbA1c", "status": "undocumented", "negated": False})
        expected_gap = True
        expected_gap_entities = ["hba1c"]
        rationale = f"CBC satisfied acute presentation; however, HbA1c for {dis_text} remains undocumented."

    # Category 4: Multi-condition complex presentation with unperformed investigation (Gap = True)
    elif category_idx == 4:
        sym_text, sym_norm = random.choice(SYMPTOMS_POOL[6:])
        unperf_phrase = random.choice(UNPERFORMED_PHRASES)
        note_text = (
            f"A patient attended {specialty} with complaint of {sym_text}. "
            f"ECG was performed showing normal sinus rhythm. Chest X-ray {unperf_phrase} "
            f"Patient advised bed rest and symptomatic relief."
        )
        expected_entities.append({"entity_text": sym_text, "entity_type": "SYMPTOM", "normalized_value": sym_norm, "negated": False})
        expected_entities.append({"entity_text": "ECG", "entity_type": "INVESTIGATION", "normalized_value": "ecg", "negated": False})
        expected_entities.append({"entity_text": "Chest X-ray", "entity_type": "INVESTIGATION", "normalized_value": "x-ray", "negated": True})
        expected_negations.append({"entity_text": sym_text, "negated": False})
        expected_negations.append({"entity_text": "ECG", "negated": False})
        expected_negations.append({"entity_text": "Chest X-ray", "negated": True})
        expected_investigations.append({"entity_text": "ECG", "status": "completed/performed", "negated": False})
        expected_investigations.append({"entity_text": "Chest X-ray", "status": "not performed", "negated": True})
        expected_gap = True
        expected_gap_entities = ["cbc", "x-ray"]
        rationale = f"Chest X-ray was explicitly not performed and symptom {sym_text} lacks CBC."

    # Category 5: Complete compliance with documented completed results (Gap = False)
    elif category_idx == 5:
        sym_text, sym_norm = random.choice(SYMPTOMS_POOL[:6])
        comp_phrase = random.choice(COMPLETED_PHRASES)
        note_text = (
            f"Patient evaluated in {specialty} for {sym_text}. "
            f"Complete blood count {comp_phrase} Vitals are within normal limits. Discharge on supportive care."
        )
        expected_entities.append({"entity_text": sym_text, "entity_type": "SYMPTOM", "normalized_value": sym_norm, "negated": False})
        expected_entities.append({"entity_text": "complete blood count", "entity_type": "INVESTIGATION", "normalized_value": "cbc", "negated": False})
        expected_negations.append({"entity_text": sym_text, "negated": False})
        expected_negations.append({"entity_text": "complete blood count", "negated": False})
        expected_investigations.append({"entity_text": "complete blood count", "status": "completed/performed", "negated": False})
        expected_gap = False
        expected_gap_entities = []
        rationale = "Required investigation (CBC) was performed and documented with normal findings; no gap exists."

    # Category 6: Ordered or pending investigations actively awaiting results (Gap = False)
    elif category_idx == 6:
        sym_text, sym_norm = random.choice(SYMPTOMS_POOL[:6])
        pend_phrase = random.choice(PENDING_PHRASES)
        note_text = (
            f"Clinical encounter at {specialty} clinic. Patient reports {sym_text}. "
            f"CBC {pend_phrase} Patient instructed to return once results are ready."
        )
        expected_entities.append({"entity_text": sym_text, "entity_type": "SYMPTOM", "normalized_value": sym_norm, "negated": False})
        expected_entities.append({"entity_text": "CBC", "entity_type": "INVESTIGATION", "normalized_value": "cbc", "negated": False})
        expected_negations.append({"entity_text": sym_text, "negated": False})
        expected_negations.append({"entity_text": "CBC", "negated": False})
        expected_investigations.append({"entity_text": "CBC", "status": "pending", "negated": False})
        expected_gap = False
        expected_gap_entities = []
        rationale = "Investigation is actively ordered/pending; guidelines treat pending orders as compliant, no gap."

    # Category 7: Clausal and coordinated negations of clinical findings (Gap = False)
    elif category_idx == 7:
        sym1, norm1 = random.choice(SYMPTOMS_POOL[:4])
        sym2, norm2 = random.choice(SYMPTOMS_POOL[4:8])
        dis_cand = [d for d in DISEASES_POOL if d[2]]
        dis_text, dis_norm, _ = random.choice(dis_cand)
        note_text = (
            f"Routine health checkup in {specialty}. Patient denies {sym1} and denies {sym2}. "
            f"No history of {dis_text}. General physical exam is unremarkable."
        )
        expected_entities.append({"entity_text": sym1, "entity_type": "SYMPTOM", "normalized_value": norm1, "negated": True})
        expected_entities.append({"entity_text": sym2, "entity_type": "SYMPTOM", "normalized_value": norm2, "negated": True})
        expected_entities.append({"entity_text": dis_text, "entity_type": "DISEASE", "normalized_value": dis_norm, "negated": True})
        expected_negations.append({"entity_text": sym1, "negated": True})
        expected_negations.append({"entity_text": sym2, "negated": True})
        expected_negations.append({"entity_text": dis_text, "negated": True})
        expected_gap = False
        expected_gap_entities = []
        rationale = "All symptoms and diseases are negated; no guideline rules trigger, no gap."

    # Category 8: Historical or resolved conditions vs active presentation (Gap = False)
    elif category_idx == 8:
        dis_text, dis_norm, _ = random.choice([d for d in DISEASES_POOL if d[2]])
        yrs = random.randint(5, 15)
        note_text = (
            f"Patient seen for annual wellness review in {specialty}. "
            f"Remote history of {dis_text} {yrs} years ago, fully resolved with lifestyle modification and currently normal blood sugars. "
            f"No current symptoms, no current medications."
        )
        expected_entities.append({"entity_text": dis_text, "entity_type": "DISEASE", "normalized_value": dis_norm, "negated": False})
        expected_negations.append({"entity_text": dis_text, "negated": False})
        expected_gap = False
        expected_gap_entities = []
        rationale = f"Historical resolved {dis_text} without active disease; clinically no gap."

    # Category 9: Non-target conditions without indication for CBC/HbA1c (Gap = False)
    # NOTE: In ClinGap-NLP's coarse rule R2, DISEASE -> HbA1c will over-trigger here!
    # Establishing independent Ground Truth = False gives a genuine, realistic benchmark for FP detection!
    elif category_idx == 9:
        non_target_diseases = [d for d in DISEASES_POOL if not d[2]]
        dis_text, dis_norm, _ = random.choice(non_target_diseases)
        med_name, med_dose, med_freq = random.choice(MEDICATIONS_POOL[2:])
        note_text = (
            f"Follow-up visit in {specialty} for {dis_text}. Patient is stable on {med_name} {med_dose} {med_freq}. "
            f"Blood pressure and vitals stable. No complaints of dizziness or pain."
        )
        expected_entities.append({"entity_text": dis_text, "entity_type": "DISEASE", "normalized_value": dis_norm, "negated": False})
        expected_entities.append({"entity_text": med_name, "entity_type": "MEDICATION", "normalized_value": med_name, "negated": False})
        expected_entities.append({"entity_text": med_dose, "entity_type": "DOSAGE", "normalized_value": med_dose, "negated": False})
        expected_entities.append({"entity_text": med_freq, "entity_type": "FREQUENCY", "normalized_value": med_freq, "negated": False})
        expected_negations.append({"entity_text": dis_text, "negated": False})
        expected_medications.append({"name": med_name, "dosage": med_dose, "frequency": med_freq})
        expected_gap = False
        expected_gap_entities = []
        rationale = f"Patient has {dis_text} which does not clinically require HbA1c or CBC. Independent ground truth is No Gap."

    # Category 10: Contradictory / ambiguous mentions (Gap = False)
    elif category_idx == 10:
        sym_text, sym_norm = random.choice(SYMPTOMS_POOL[:4])
        note_text = (
            f"Consultation in {specialty}. Family reported possible {sym_text} yesterday at home, "
            f"but patient is currently afebrile, denies any discomfort, and physical examination is entirely normal. "
            f"No investigations indicated at present."
        )
        expected_entities.append({"entity_text": sym_text, "entity_type": "SYMPTOM", "normalized_value": sym_norm, "negated": True})
        expected_negations.append({"entity_text": sym_text, "negated": True})
        expected_gap = False
        expected_gap_entities = []
        rationale = f"Reported {sym_text} was resolved/contradicted by clinical exam; no gap exists."

    # Category 11: Boundary cases with lab measurements and generic procedure words (Gap = False)
    else:
        dis_text, dis_norm, _ = random.choice([d for d in DISEASES_POOL if d[2]])
        lab_val = random.randint(110, 165)
        comp_phrase = random.choice(COMPLETED_PHRASES)
        note_text = (
            f"Review visit in {specialty} for {dis_text}. "
            f"Fasting blood glucose was {lab_val} mg/dL and HbA1c {comp_phrase} "
            f"Routine diagnostic workup and laboratory investigations were reviewed. No further testing needed."
        )
        expected_entities.append({"entity_text": dis_text, "entity_type": "DISEASE", "normalized_value": dis_norm, "negated": False})
        expected_entities.append({"entity_text": "HbA1c", "entity_type": "INVESTIGATION", "normalized_value": "hba1c", "negated": False})
        expected_negations.append({"entity_text": dis_text, "negated": False})
        expected_negations.append({"entity_text": "HbA1c", "negated": False})
        expected_investigations.append({"entity_text": "HbA1c", "status": "completed/performed", "negated": False})
        expected_gap = False
        expected_gap_entities = []
        rationale = "HbA1c completed with documented glucose level; generic procedure tokens should not trigger gaps."

    return {
        "test_case_id": case_id,
        "split": split,
        "specialty": specialty,
        "category_id": category_idx,
        "category_name": [
            "Missing Investigation (Acute)",
            "Missing Monitoring (Chronic)",
            "Unperformed / Cancelled Investigation",
            "Partially Satisfied Guideline",
            "Multi-Condition Presentation",
            "Documented Completed Results",
            "Ordered / Pending Investigation",
            "Negated Clinical Findings",
            "Historical / Resolved Condition",
            "Non-Target Disease Presentation",
            "Contradictory / Discrepant Presentation",
            "Boundary Lab Measurements & Generic Tokens",
        ][category_idx],
        "is_gap_expected": expected_gap,
        "expected_gap_entities": expected_gap_entities,
        "clinical_note": note_text,
        "expected_entities": expected_entities,
        "expected_negations": expected_negations,
        "expected_investigations": expected_investigations,
        "expected_medications": expected_medications,
        "clinical_rationale": rationale,
    }


def generate_all_datasets():
    print("=" * 70)
    print("GENERATING INDEPENDENT CLINICAL EVALUATION DATASET")
    print(f"Seed: {SEED} | Target: 200 Dev Cases, 600 Final Held-Out Test Cases")
    print("=" * 70)

    # 1. Generate Dev Set (200 cases: 20 cases per specialty, evenly split across categories)
    dev_cases = []
    case_idx = 1
    for spec in SPECIALTIES:
        for i in range(20):
            cat_idx = i % 12
            cid = f"DEV-{case_idx:03d}"
            dev_cases.append(create_case(cid, spec, cat_idx, "dev"))
            case_idx += 1

    # 2. Generate Final Test Set (600 cases: 60 cases per specialty, 5 of each of 12 categories)
    test_cases = []
    case_idx = 1
    for spec in SPECIALTIES:
        for i in range(60):
            cat_idx = i % 12
            cid = f"TEST-{case_idx:03d}"
            test_cases.append(create_case(cid, spec, cat_idx, "test"))
            case_idx += 1

    # Shuffle deterministically within splits
    random.Random(SEED + 1).shuffle(dev_cases)
    random.Random(SEED + 2).shuffle(test_cases)

    # Save Dev Set
    dev_path = os.path.join(RESULTS_DIR, "evaluation_dev_dataset.json")
    with open(dev_path, "w", encoding="utf-8") as f:
        json.dump(dev_cases, f, indent=2)
    print(f"Saved {len(dev_cases)} development cases to {dev_path}")

    # Save Test Set
    test_path = os.path.join(RESULTS_DIR, "evaluation_test_dataset_with_ground_truth.json")
    with open(test_path, "w", encoding="utf-8") as f:
        json.dump(test_cases, f, indent=2)
    print(f"Saved {len(test_cases)} test cases to {test_path}")

    # Calculate distributions
    dev_gap_cnt = sum(1 for c in dev_cases if c["is_gap_expected"])
    test_gap_cnt = sum(1 for c in test_cases if c["is_gap_expected"])

    print("\n--- DATASET DISTRIBUTION SUMMARY ---")
    print(f"Dev Set:  Total={len(dev_cases)}, Gap={dev_gap_cnt} ({dev_gap_cnt/len(dev_cases)*100:.1f}%), No-Gap={len(dev_cases)-dev_gap_cnt} ({(len(dev_cases)-dev_gap_cnt)/len(dev_cases)*100:.1f}%)")
    print(f"Test Set: Total={len(test_cases)}, Gap={test_gap_cnt} ({test_gap_cnt/len(test_cases)*100:.1f}%), No-Gap={len(test_cases)-test_gap_cnt} ({(len(test_cases)-test_gap_cnt)/len(test_cases)*100:.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    generate_all_datasets()
