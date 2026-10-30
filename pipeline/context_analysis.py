from typing import List, Dict
from ..models.context import get_document_embedding
from loguru import logger

def add_context_embeddings(entities: List[Dict], text: str) -> List[Dict]:
    """Attach a placeholder context embedding to each entity.
    In a real system this would compute contextual similarity; here we just add model info.
    """
    try:
        embedding, model_name = get_document_embedding(text)
        for ent in entities:
            ent["context_model"] = model_name
    except Exception as e:
        logger.error(f"Context embedding failed: {e}")
        for ent in entities:
            ent["context_model"] = "None"
    return entities
