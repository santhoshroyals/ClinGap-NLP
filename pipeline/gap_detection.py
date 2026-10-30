from typing import List, Dict
from loguru import logger

def detect_gaps(entities: List[Dict], investigations: List[Dict], matched_guidelines: List[Dict]) -> List[Dict]:
    """Identify decision gaps based on missing investigations or actions.
    For each matched guideline, check if its recommended investigation is present in investigations list.
    Returns list of gap dicts with type, description, confidence.
    """
    gaps = []
    inv_set = {inv["normalized_value"].lower() for inv in investigations}
    for rule in matched_guidelines:
        rec = rule.get("recommendation")
        if not rec:
            continue
        if rec.get("type") == "INVESTIGATION":
            name = rec.get("name", "").lower()
            if name not in inv_set:
                gap = {
                    "gap_type": "MISSING_INVESTIGATION",
                    "description": f"{rec['name']} was not found in the available documentation.",
                    "confidence": None,  # to be filled later
                    "rule_id": rule.get("rule_id"),
                    "recommendation": rec,
                }
                gaps.append(gap)
                logger.info(f"Detected missing investigation gap for {rec['name']}")
    return gaps
