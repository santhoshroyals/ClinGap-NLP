import re
from typing import List, Dict


def extract_entities(text: str) -> List[Dict]:
    # Simple regex for medication names (example list)
    meds = ["aspirin", "metformin", "lisinopril", "atorvastatin", "insulin"]
    entities = []
    for med in meds:
        for match in re.finditer(r"\b" + re.escape(med) + r"\b", text, flags=re.IGNORECASE):
            entities.append({"type": "Medication", "text": match.group(), "start": match.start(), "end": match.end()})
    return entities


def detect_negations(text: str) -> List[Dict]:
    neg_words = ["no", "not", "denies", "without", "absence of"]
    negations = []
    for neg in neg_words:
        for match in re.finditer(r"\b" + re.escape(neg) + r"\b", text, flags=re.IGNORECASE):
            negations.append({"text": match.group(), "start": match.start(), "end": match.end()})
    return negations


def parse_prescriptions(text: str) -> Dict:
    # Prescription extraction: look for pattern '<med> <dose> mg' excluding lab units like mg/dL
    prescription = {}
    pattern = re.compile(
        r"(\w+)\s+(\d+)\s*mg(?!\s*/\s*(?:d[lL]|[lL]|m[lL]|u[lL]|µ[lL]|mm3|kg|min|hr|h|day)|%)",
        re.IGNORECASE
    )
    for match in pattern.finditer(text):
        med = match.group(1).lower()
        dose = int(match.group(2))
        prescription[med] = dose
    return prescription


def extract_investigations(text: str) -> List[Dict]:
    investigations = []
    keywords = ["CT scan", "MRI", "X-ray", "ultrasound", "blood test"]
    for kw in keywords:
        for match in re.finditer(re.escape(kw), text, flags=re.IGNORECASE):
            investigations.append({"type": kw, "start": match.start(), "end": match.end()})
    return investigations


def match_guidelines(entities: List[Dict]) -> List[Dict]:
    # Stub: return empty list
    return []


def detect_decision_gaps(entities: List[Dict], guidelines: List[Dict]) -> List[Dict]:
    # Stub: return empty list
    return []


def explainability(result: Dict) -> Dict:
    # Stub: return a simple explanation dict
    return {"explanation": "Analysis performed using simple regex-based pipeline."}


def process_clinical_text(text: str) -> Dict:
    entities = extract_entities(text)
    negations = detect_negations(text)
    prescription = parse_prescriptions(text)
    investigations = extract_investigations(text)
    guidelines = match_guidelines(entities)
    decision_gaps = detect_decision_gaps(entities, guidelines)
    explain = explainability({})
    return {
        "entities": entities,
        "negations": negations,
        "prescription": prescription,
        "investigation": investigations,
        "guideline_matches": guidelines,
        "decision_gaps": decision_gaps,
        "explainability": explain,
    }
