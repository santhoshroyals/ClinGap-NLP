from ..services.ner_service import hybrid_ner
from ..services.negation_service import detect_negations
from ..services.model_manager import ModelManager
from ..services.context_service import ContextService
from ..services.guideline_service import GuidelineEngine
from ..services.gap_detection import detect_gaps
from ..services.confidence_service import compute_confidence
from ..services.explainability_service import build_explanation
from ..services.prescription_service import reconstruct_regimens
from sqlalchemy import text as sa_text
from typing import Optional
import numpy as np

class ClinicalPipeline:
    def __init__(self):
        self.context_service = ContextService()
        self.guideline_engine = GuidelineEngine()
    def run(self, db, patient_id: Optional[int] = None, document_id: Optional[int] = None, text: Optional[str] = None):
        content = text
        if not content and document_id is not None:
            # Retrieve document text (simplified)
            doc = db.execute(sa_text('SELECT content FROM documents WHERE id = :doc_id'), {'doc_id': document_id}).fetchone()
            content = doc[0] if doc else ''
        content = content or ''
        entities = hybrid_ner(content)
        entities = detect_negations(content, entities)
        # Compute contextual representation (Bio_ClinicalBERT → 768-dim, or TF-IDF fallback).
        # NOTE: This embedding is a numerical representation of the clinical text only.
        # It does NOT make clinical decisions; guideline matching and gap detection
        # remain fully criteria-based and are unaffected by this embedding.
        try:
            _emb = self.context_service.embed(content)
            context_info = {
                'embedding_dimension': int(len(_emb)),
                'embedding_norm': round(float(np.linalg.norm(_emb)), 6),
                'embedding_model': 'Bio_ClinicalBERT (contextual representation only — not a clinical decision)',
                'fallback_used': len(_emb) != 768,
            }
        except Exception as _ctx_err:
            import logging as _log
            _log.getLogger(__name__).warning('ContextService.embed failed: %s', _ctx_err)
            context_info = {'embedding_dimension': None, 'embedding_norm': None,
                            'embedding_model': 'unavailable', 'fallback_used': True}
        rule_matches = self.guideline_engine.match(entities)
        gaps = detect_gaps(entities, rule_matches)
        confidence = compute_confidence(entities, gaps)
        explanation = build_explanation(entities, gaps, confidence, rule_matches)
        regimens = reconstruct_regimens(content, entities=entities)
        return {
            'entities': entities,
            'gaps': gaps,
            'confidence': confidence,
            'explanation': explanation,
            'context_info': context_info,
            'regimens': regimens,
            'ner_status': ModelManager.get_ner_status(),
        }
