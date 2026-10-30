import pytest
import json
from backend.services.clinical_pipeline import ClinicalPipeline
from backend.database import SessionLocal
from sqlalchemy import text
import scripts.seed_database as seed_db

def test_case1_gap_detection():
    # Seed DB with case1 text (already done by seed script)
    db = SessionLocal()
    # Find document id for case1
    doc = db.execute(text('SELECT id FROM documents WHERE title = :title'), {'title': 'case1'}).fetchone()
    assert doc is not None
    doc_id = doc[0]
    pipeline = ClinicalPipeline()
    result = pipeline.run(db, patient_id=1, document_id=doc_id)
    # Expect a missing investigation gap for CBC
    gap_types = [g['gap_type'] for g in result['gaps']]
    assert 'MISSING_INVESTIGATION' in gap_types
    # Confidence should be between 0 and 100
    assert 0 <= result['confidence'] <= 100
