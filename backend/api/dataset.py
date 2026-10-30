from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from ..services.dataset_service import get_specialties, get_record_by_id, search_records

router = APIRouter(prefix="/api/dataset/mtsamples", tags=["dataset"])


@router.get("/specialties", response_model=List[str])
def list_specialties():
    """Returns all 40 unique medical specialties in the MTSamples dataset."""
    try:
        return get_specialties()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/records")
def list_records(
    q: Optional[str] = Query(None, description="Search query by keyword or record ID"),
    specialty: Optional[str] = Query(None, description="Filter by medical specialty"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
):
    """Returns searchable, paginated summaries of MTSamples records."""
    try:
        return search_records(query=q, specialty=specialty, limit=limit, offset=offset)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{record_id}")
def get_record(record_id: int):
    """Fetches a specific MTSamples record with its full clinical transcription."""
    try:
        return get_record_by_id(record_id)
    except IndexError:
        raise HTTPException(status_code=404, detail=f"MTSamples record {record_id} not found.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
