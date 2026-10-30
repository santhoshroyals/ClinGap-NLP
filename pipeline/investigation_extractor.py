import json
import os
from typing import List, Dict
from ..knowledge_base.investigations import load_investigations

# Load investigations data
INVESTIGATIONS_PATH = os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "investigations.json")
with open(INVESTIGATIONS_PATH, "r", encoding="utf-8") as f:
    INVESTIGATIONS_DATA = json.load(f)

# Build a synonym map
_SYNONYM_MAP = {}
for inv in INVESTIGATIONS_DATA:
    for syn in inv.get("synonyms", []):
        _SYNONYM_MAP[syn.lower()] = inv["name"]
    _SYNONYM_MAP[inv["name"].lower()] = inv["name"]

import re

def extract_investigations(text: str) -> List[Dict]:
    """Extract investigation mentions from text using synonyms.
    Returns list of dicts with required fields and status.
    """
    try:
        from ..backend.services.ner_service import extract_investigation_status
    except Exception:
        try:
            from backend.services.ner_service import extract_investigation_status
        except Exception:
            def extract_investigation_status(t, ent, neg=False):
                return "not performed" if neg else "ordered"

    results = []
    # Match synonyms using word boundaries
    for syn, name in _SYNONYM_MAP.items():
        if re.search(rf"\b{re.escape(syn)}\b", text, re.I):
            status = extract_investigation_status(text, syn, False)
            results.append({
                "entity_text": syn,
                "entity_type": "INVESTIGATION",
                "normalized_value": name,
                "confidence": 0.6,
                "negated": status == "not performed",
                "status": status,
                "source": "Clinical Dictionary",
            })
    return results
