import os
import json
import re
from typing import List, Dict
from loguru import logger
from ..models.ner import extract_entities as model_entities

# Load local clinical dictionaries
DICTIONARY_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
with open(os.path.join(DICTIONARY_DIR, "medications.json"), "r", encoding="utf-8") as f:
    MEDICATIONS = json.load(f)

# Simple regex patterns for other entity types (example placeholders)
DISEASE_PATTERN = re.compile(r"\b(?:diabetes|hypertension|infection|cancer)\b", re.IGNORECASE)
SYMPTOM_PATTERN = re.compile(r"\b(?:fever|cough|pain|fatigue)\b", re.IGNORECASE)
INVESTIGATION_PATTERN = re.compile(r"\b(?:cbc|x-ray|mri|ct scan)\b", re.IGNORECASE)

def extract_local_entities(text: str) -> List[Dict]:
    entities = []
    for match in DISEASE_PATTERN.finditer(text):
        entities.append({
            "entity_text": match.group(0),
            "entity_type": "DISEASE",
            "normalized_value": None,
            "confidence": 0.5,
            "negated": False,
            "source": "Clinical Dictionary",
        })
    for match in SYMPTOM_PATTERN.finditer(text):
        entities.append({
            "entity_text": match.group(0),
            "entity_type": "SYMPTOM",
            "normalized_value": None,
            "confidence": 0.5,
            "negated": False,
            "source": "Clinical Dictionary",
        })
    for match in INVESTIGATION_PATTERN.finditer(text):
        entities.append({
            "entity_text": match.group(0),
            "entity_type": "INVESTIGATION",
            "normalized_value": None,
            "confidence": 0.5,
            "negated": False,
            "source": "Clinical Dictionary",
        })
    # Medication detection from list
    for med in MEDICATIONS:
        if re.search(rf"\\b{re.escape(med)}\\b", text, re.IGNORECASE):
            entities.append({
                "entity_text": med,
                "entity_type": "MEDICATION",
                "normalized_value": None,
                "confidence": 0.6,
                "negated": False,
                "source": "Clinical Dictionary",
            })
    return entities

def hybrid_ner(text: str) -> List[Dict]:
    """Combine model-based NER with local dictionary/pattern extraction.
    Returns a unified list of entity dictionaries with required fields.
    """
    logger.info("Running hybrid NER")
    model_ents = model_entities(text)
    local_ents = extract_local_entities(text)
    # Simple deduplication by entity text and type
    combined = { (e["entity_text"].lower(), e["entity_type"]) : e for e in model_ents + local_ents }
    return list(combined.values())
