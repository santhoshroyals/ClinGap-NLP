import os, logging
from typing import Optional

log = logging.getLogger(__name__)

class ModelManager:
    _ner_model = None
    _context_model = None
    _ner_model_name = os.getenv('NER_MODEL_NAME', 'en_ner_bc5cdr_md')
    _context_model_name = os.getenv('CONTEXT_MODEL_NAME', 'emilyalsentzer/Bio_ClinicalBERT')
    _ner_load_attempted: bool = False
    _ner_load_error: Optional[str] = None

    @classmethod
    def load_ner(cls):
        if cls._ner_model is not None:
            return cls._ner_model
        if cls._ner_load_attempted:
            return cls._ner_model
        cls._ner_load_attempted = True
        try:
            import spacy
            log.info('Loading configured biomedical NER model: %s', cls._ner_model_name)
            cls._ner_model = spacy.load(cls._ner_model_name)
            cls._ner_load_error = None
        except Exception as e:
            cls._ner_load_error = str(e)
            log.warning(
                'Biomedical NER model (%s) unavailable: %s. '
                'Active pipeline: Dictionary-based NER fallback.',
                cls._ner_model_name, e
            )
            cls._ner_model = None
        return cls._ner_model

    @classmethod
    def load_context(cls):
        if cls._context_model is not None:
            return cls._context_model
        try:
            from transformers import AutoTokenizer, AutoModel
            log.info('Loading context model %s', cls._context_model_name)
            tokenizer = AutoTokenizer.from_pretrained(cls._context_model_name)
            model = AutoModel.from_pretrained(cls._context_model_name)
            cls._context_model = (tokenizer, model)
        except Exception as e:
            log.warning('Failed to load context model (%s): %s. Falling back to TF‑IDF.', cls._context_model_name, e)
            cls._context_model = None
        return cls._context_model

    @classmethod
    def get_ner_status(cls) -> str:
        """
        Explicitly report whether the biomedical NER model is active,
        or if dictionary fallback is active (including the reason).
        """
        if cls._ner_model is not None:
            return f"Biomedical model active ({cls._ner_model_name})"
        if cls._ner_load_error:
            return f"Fallback active: Dictionary-based NER (configured biomedical model '{cls._ner_model_name}' unavailable: {cls._ner_load_error})"
        return f"Fallback active: Dictionary-based NER (configured biomedical model '{cls._ner_model_name}' not loaded)"

    @classmethod
    def is_biomedical_model_loaded(cls) -> bool:
        return cls._ner_model is not None

    @classmethod
    def get_context_status(cls):
        return 'Loaded' if cls._context_model else 'Fallback (TF‑IDF)'

