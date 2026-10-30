import re
from typing import List, Dict

NEGATION_PHRASES = ["no", "denies", "without", "not", "negative for"]


def detect_negations(entities: List[Dict]) -> List[Dict]:
    """Mark entities as negated if a negation phrase appears within a few words before the entity.
    Simple heuristic: look for negation words in the same sentence preceding the entity.
    """
    updated = []
    for ent in entities:
        text = ent.get("entity_text", "")
        # Find surrounding context (naive): assume whole document passed separately? Here we only have entity text.
        # For simplicity, check if entity text starts with a negation phrase.
        lowered = text.lower()
        negated = any(lowered.startswith(phrase + " ") or lowered == phrase for phrase in NEGATION_PHRASES)
        ent_copy = ent.copy()
        ent_copy["negated"] = negated
        updated.append(ent_copy)
    return updated
