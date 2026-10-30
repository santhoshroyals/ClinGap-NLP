from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from clinngap_nlp.pipeline.text_processor import process_clinical_text

app = FastAPI(title="ClinGap-NLP API")

class TextInput(BaseModel):
    text: str

class AnalysisResult(BaseModel):
    entities: list
    negations: list
    prescription: dict
    investigation: list
    guideline_matches: list
    decision_gaps: list
    explainability: dict

@app.post("/analyze", response_model=AnalysisResult)
async def analyze(input: TextInput):
    try:
        result = process_clinical_text(input.text)
        return AnalysisResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
