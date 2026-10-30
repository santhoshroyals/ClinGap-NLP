"""
dataset_service.py - MTSamples dataset query and record retrieval service.
Provides indexed access and search over C:\\Desktop\\nlp project\\data\\datasets\\mtsamples_clean.csv.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

CSV_PATH = Path(r"C:\Desktop\nlp project\data\datasets\mtsamples_clean.csv")

_df_cache: Optional[pd.DataFrame] = None


def get_dataset_df() -> pd.DataFrame:
    """Loads and caches the MTSamples dataset."""
    global _df_cache
    if _df_cache is None:
        if not CSV_PATH.exists():
            raise FileNotFoundError(f"MTSamples dataset not found at {CSV_PATH}")
        df = pd.read_csv(CSV_PATH)
        # Ensure string types and fill missing
        df['medical_specialty'] = df['medical_specialty'].fillna('Unknown').astype(str).str.strip()
        df['sample_name'] = df['sample_name'].fillna('Unnamed Sample').astype(str).str.strip()
        df['description'] = df['description'].fillna('').astype(str).str.strip()
        df['transcription'] = df['transcription'].fillna('').astype(str)
        _df_cache = df
    return _df_cache


def get_specialties() -> List[str]:
    """Returns sorted unique medical specialties."""
    df = get_dataset_df()
    specs = sorted(list(df['medical_specialty'].unique()))
    return [s for s in specs if s]


def get_record_by_id(record_id: int) -> Dict[str, Any]:
    """Fetches a single MTSamples record by its 0-indexed row position."""
    df = get_dataset_df()
    if record_id < 0 or record_id >= len(df):
        raise IndexError(f"Record ID {record_id} out of range [0, {len(df) - 1}]")

    row = df.iloc[record_id]
    transcription = str(row['transcription'])
    return {
        'id': int(record_id),
        'sample_name': str(row['sample_name']),
        'medical_specialty': str(row['medical_specialty']),
        'description': str(row['description']),
        'transcription': transcription,
        'char_count': len(transcription),
        'word_count': len(transcription.split()),
        'keywords': str(row.get('keywords', '')),
    }


def search_records(
    query: Optional[str] = None,
    specialty: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Searches MTSamples records by text query and/or specialty.
    Returns paginated summaries with transcription preview.
    """
    df = get_dataset_df()
    filtered = df

    if specialty and specialty.strip() and specialty.strip().lower() != 'all':
        spec_clean = specialty.strip().lower()
        filtered = filtered[filtered['medical_specialty'].str.lower() == spec_clean]

    if query and query.strip():
        q = query.strip()
        # If query is purely numeric, check if it's a direct record ID match
        if q.isdigit():
            rec_id = int(q)
            if 0 <= rec_id < len(df):
                direct_match = df.iloc[[rec_id]]
                if specialty and specialty.strip() and specialty.strip().lower() != 'all':
                    direct_match = direct_match[direct_match['medical_specialty'].str.lower() == specialty.strip().lower()]
                if not direct_match.empty:
                    filtered = direct_match

        if not q.isdigit() or filtered.empty:
            q_lower = q.lower()
            name_match = filtered['sample_name'].str.lower().str.contains(q_lower, regex=False)
            desc_match = filtered['description'].str.lower().str.contains(q_lower, regex=False)
            spec_match = filtered['medical_specialty'].str.lower().str.contains(q_lower, regex=False)
            filtered = filtered[name_match | desc_match | spec_match]

    total_matches = len(filtered)
    paged = filtered.iloc[offset : offset + limit]

    records = []
    for idx, row in paged.iterrows():
        t = str(row['transcription'])
        preview = t[:250] + ('...' if len(t) > 250 else '')
        records.append({
            'id': int(idx),
            'sample_name': str(row['sample_name']),
            'medical_specialty': str(row['medical_specialty']),
            'description': str(row['description']),
            'char_count': len(t),
            'word_count': len(t.split()),
            'preview': preview,
        })

    return {
        'total': total_matches,
        'offset': offset,
        'limit': limit,
        'records': records,
    }
