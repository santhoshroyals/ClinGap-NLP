"""Pipeline orchestrator for ClinGap-NLP.
It runs the full sequence of steps for a given raw clinical note text.
"""
from typing import Dict, Any, List
from loguru import logger

from .preprocess import preprocess
from .hybrid_ner import hybrid_ner
from .negation import detect_negations
from .context_analysis import add_context_embeddings
from .prescription_parser import parse_prescription
from .investigation_extractor import extract_investigations
from .guideline_engine import match_guidelines
from .gap_detection import detect_gaps
from .confidence import compute_confidence

def run_pipeline(text: str) -> Dict[str, Any]:
    """Execute the full pipeline on the supplied text.

    Returns a dictionary containing intermediate and final results.
    """
    logger.info("Starting pipeline")
    preprocessed = preprocess(text)
    logger.debug("Preprocessed text")

    # NER
    entities = hybrid_ner(preprocessed)
    entities = detect_negations(entities)
    logger.debug(f"Extracted {len(entities)} entities after negation detection")

    # Context analysis (adds model name info)
    entities = add_context_embeddings(entities, preprocessed)

    # Prescription parsing
    prescriptions = parse_prescription(preprocessed)

    # Investigation extraction (separate from NER for demonstration)
    investigations = extract_investigations(preprocessed)

    # Guideline matching
    matched_guidelines = match_guidelines(entities)

    # Gap detection
    gaps = detect_gaps(entities, investigations, matched_guidelines)

    # Compute confidence for each gap (simple example using placeholder scores)
    for gap in gaps:
        # placeholder scores: use fixed values
        gap["confidence"] = compute_confidence(
            entity_score=0.35,
            guideline_match_score=0.30,
            context_score=0.20,
            documentation_score=0.15,
        )

    result = {
        "preprocessed": preprocessed,
        "entities": entities,
        "prescriptions": prescriptions,
        "investigations": investigations,
        "matched_guidelines": matched_guidelines,
        "gaps": gaps,
    }
    logger.info("Pipeline completed")
    return result
