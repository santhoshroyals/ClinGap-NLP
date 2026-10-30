from typing import List, Dict
from loguru import logger

# Fixed weight values as per specification
WEIGHTS = {
    "entity_score": 0.35,
    "guideline_match_score": 0.30,
    "context_score": 0.20,
    "documentation_score": 0.15,
}

def compute_confidence(entity_score: float = 0.0,
                       guideline_match_score: float = 0.0,
                       context_score: float = 0.0,
                       documentation_score: float = 0.0) -> float:
    """Compute overall confidence as weighted sum (0-1) then scale to 0-100.
    Scores are expected 0-1.
    """
    total = (
        entity_score * WEIGHTS["entity_score"] +
        guideline_match_score * WEIGHTS["guideline_match_score"] +
        context_score * WEIGHTS["context_score"] +
        documentation_score * WEIGHTS["documentation_score"]
    )
    confidence_percent = round(total * 100, 2)
    logger.info(f"Computed confidence: {confidence_percent}%")
    return confidence_percent
