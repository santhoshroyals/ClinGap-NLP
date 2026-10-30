from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
from ..services.document_parser import parse_document

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Accepts clinical notes or prescriptions in .txt, .pdf, or .docx format.
    Extracts actual document text and returns preview + text for NLP analysis.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        extracted_text, detected_fmt = parse_document(file.filename, content)

        preview = extracted_text[:300] + ("..." if len(extracted_text) > 300 else "")
        return {
            "filename": file.filename,
            "file_type": detected_fmt,
            "text": extracted_text,
            "char_count": len(extracted_text),
            "word_count": len(extracted_text.split()),
            "preview": preview,
        }
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Document parsing error: {exc}")
