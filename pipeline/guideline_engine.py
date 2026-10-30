import json
import os
from typing import List, Dict, Any
from loguru import logger

# Load guidelines
GUIDELINES_PATH = os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "guidelines.json")
with open(GUIDELINES_PATH, "r", encoding="utf-8") as f:
    GUIDELINES = json.load(f)

def match_guidelines(entities: List[Dict]) -> List[Dict]:
    """Match guideline rules based on extracted entities.
    Simple deterministic matching: if all required entity types are present, rule matches.
    Returns list of matched guideline dicts with rule metadata.
    """
    entity_types = {e["entity_type"] for e in entities if not e.get("negated", False)}
    matches = []
    for rule in GUIDELINES:
        criteria = rule.get("criteria", {})
        required = set(criteria.get("entities", []))
        if required.issubset(entity_types):
            matches.append(rule)
    logger.info(f"Matched {len(matches)} guidelines")
    return matches
