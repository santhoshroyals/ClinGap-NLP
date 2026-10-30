import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Database configuration
DATABASE_URL = os.getenv('CLINGAP_NLP_DATABASE_URL', f"sqlite:///{BASE_DIR / 'clinngap_nlp.db'}")

# Model configuration
NER_MODEL_NAME = os.getenv('CLINGAP_NLP_NER_MODEL', 'en_ner_bc5cdr_md')
CONTEXT_MODEL_NAME = os.getenv('CLINGAP_NLP_CONTEXT_MODEL', 'emilyalsentzer/Bio_Clinical_BERT')

# Logging level
LOG_LEVEL = os.getenv('CLINGAP_NLP_LOG_LEVEL', 'INFO')
