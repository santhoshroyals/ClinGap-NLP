from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from ..services.clinical_pipeline import ClinicalPipeline
from ..database import get_db

router = APIRouter()

class AnalyzeRequest(BaseModel):
    patient_id: Optional[int] = 1
    document_id: Optional[int] = 1
    text: Optional[str] = None

class AnalyzeResponse(BaseModel):
    entities: List[Dict[str, Any]]
    gaps: List[Dict[str, Any]]
    confidence: float
    explanation: Dict[str, Any]
    patient_id: Optional[int] = None
    document_id: Optional[int] = None
    text: Optional[str] = None
    regimens: Optional[List[Dict[str, Any]]] = None

@router.post('/api/analyze', response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest, db=Depends(get_db)):
    pipeline = ClinicalPipeline()
    result = pipeline.run(db, request.patient_id, request.document_id, text=request.text)
    result['patient_id'] = request.patient_id
    result['document_id'] = request.document_id
    result['text'] = request.text
    return AnalyzeResponse(**result)


