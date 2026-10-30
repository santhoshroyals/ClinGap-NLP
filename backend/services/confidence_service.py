def compute_confidence(entities, gaps):
    """Calculate a bounded heuristic score from 0 to 100."""
    entity_score = min(1.0, len(entities) / 20) * 0.35
    gap_score = max(0.0, 1.0 - len(gaps) / 5) * 0.30

    confidence = (entity_score + gap_score) * 100
    return round(max(0.0, min(100.0, confidence)), 2)