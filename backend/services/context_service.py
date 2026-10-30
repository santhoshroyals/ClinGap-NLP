import logging, os, torch
from .model_manager import ModelManager
from sklearn.feature_extraction.text import TfidfVectorizer

log = logging.getLogger(__name__ )

class ContextService:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = None
    def embed(self, text: str):
        model = ModelManager.load_context()
        if model:
            tokenizer, mdl = model
            inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
            with torch.no_grad():
                embeddings = mdl(**inputs).last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
            return embeddings
        else:
            # TF‑IDF fallback
            if self.tfidf_matrix is None:
                self.tfidf_matrix = self.vectorizer.fit_transform([text])
                return self.tfidf_matrix.toarray()[0]
            else:
                return self.vectorizer.transform([text]).toarray()[0]
