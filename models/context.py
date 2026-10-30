import os
from pathlib import Path
import json
import logging
from typing import List, Tuple

from loguru import logger

# Lazy loading for BioClinicalBERT
_bert_model = None
_bert_tokenizer = None
_fallback_vectorizer = None

def load_bert_model():
    global _bert_model, _bert_tokenizer
    if _bert_model is not None:
        return _bert_model, _bert_tokenizer
    try:
        from transformers import AutoModel, AutoTokenizer
        model_name = os.getenv('CLINGAP_NLP_CONTEXT_MODEL', 'emilyalsentzer/Bio_Clinical_BERT')
        logger.info(f"Loading BioClinicalBERT model {model_name}")
        _bert_tokenizer = AutoTokenizer.from_pretrained(model_name)
        _bert_model = AutoModel.from_pretrained(model_name)
        logger.info("BioClinicalBERT loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load BioClinicalBERT: {e}")
        _bert_model = None
        _bert_tokenizer = None
    return _bert_model, _bert_tokenizer

def load_fallback_vectorizer():
    global _fallback_vectorizer
    if _fallback_vectorizer is not None:
        return _fallback_vectorizer
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        _fallback_vectorizer = TfidfVectorizer()
    except Exception as e:
        logger.error(f"Failed to create TF-IDF fallback: {e}")
        _fallback_vectorizer = None
    return _fallback_vectorizer

def get_document_embedding(text: str):
    """Return an embedding vector for the given document.
    If BioClinicalBERT is available, use the CLS token output.
    Otherwise, use TF-IDF vector (fit on the single document for simplicity).
    """
    model, tokenizer = load_bert_model()
    if model is not None and tokenizer is not None:
        import torch
        inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        # CLS token is first token
        embedding = outputs.last_hidden_state[:, 0, :].squeeze().cpu().numpy()
        return embedding, "BioClinicalBERT"
    else:
        vectorizer = load_fallback_vectorizer()
        if vectorizer is None:
            raise RuntimeError("No context model available")
        embedding = vectorizer.fit_transform([text]).toarray()[0]
        return embedding, "TF-IDF"
