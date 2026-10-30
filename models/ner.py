import spacy
from spacy.util import get_package_path
from spacy.language import Language
import os
from typing import List, Dict
from loguru import logger

# Lazy loader for scispaCy NER model
_ner_model = None

def load_ner_model(model_name: str = os.getenv('CLINGAP_NLP_NER_MODEL', 'en_ner_bc5cdr_md')) -> Language:
    global _ner_model
    if _ner_model is not None:
        return _ner_model
    try:
        logger.info(f"Loading NER model {model_name}")
        _ner_model = spacy.load(model_name)
        logger.info("NER model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load scispaCy model {model_name}: {e}")
        _ner_model = None
    return _ner_model

def extract_entities(text: str) -> List[Dict]:
    """Run the scispaCy NER model on the input text and return a list of entity dicts.
    Each dict contains the required fields. If the model is not available, returns empty list.
    """
    nlp = load_ner_model()
    if nlp is None:
        return []
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        entities.append({
            "entity_text": ent.text,
            "entity_type": ent.label_,  # scispaCy uses label like "DISEASE" etc.
            "normalized_value": None,
            "confidence": ent.kb_id_ if hasattr(ent, "kb_id_") else None,
            "negated": False,
            "source": "NER Model",
        })
    return entities
