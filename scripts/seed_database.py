import os, json, sys
from pathlib import Path

# Ensure project root is on sys.path
_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from backend.database import engine, Base, SessionLocal
from backend.models.patient import Patient
from backend.models.document import Document

# Drop all and recreate (for demo)
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

session = SessionLocal()
# Insert demo patient
patient = Patient(name='John Doe')
session.add(patient)
session.commit()

# Load demo texts from data/demo folder
base_path = Path(__file__).resolve().parent.parent / 'data' / 'demo'
for txt_file in base_path.glob('*.txt'):
    with open(txt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    from datetime import datetime, timezone
    doc = Document(patient_id=patient.id, title=txt_file.stem, content=content, doc_type='note', created_at=datetime.now(timezone.utc))
    session.add(doc)

session.commit()
print('Demo database seeded.')
