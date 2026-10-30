
import json
import re
from pathlib import Path
from typing import List, Dict


# Load medication dictionary
MEDICATIONS_FILE = (
    Path(__file__).parent.parent
    / "knowledge_base"
    / "medications.json"
)

with open(MEDICATIONS_FILE, "r", encoding="utf-8") as f:
    MEDICATIONS = json.load(f)


# Extract dosage, e.g. 500 mg, 2.5 ml, 1 g
DOSAGE_PATTERN = re.compile(
    r"\b(\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml|mL|units|µg))(?!\s*/\s*(?:d[lL]|[lL]|m[lL]|u[lL]|µ[lL]|mm3|kg|min|hr|h|day)|%)\b",
    re.IGNORECASE,
)


# Extract medication frequency
FREQUENCY_PATTERN = re.compile(
    r"\b(?:"
    r"every\s+\d+\s+(?:hours?|days?|weeks?)|"
    r"once\s+daily|twice\s+daily|"
    r"three\s+times\s+daily|four\s+times\s+daily|"
    r"once\s+weekly|twice\s+weekly|once\s+monthly|"
    r"as\s+needed|"
    r"\d+\s+times?\s+(?:a|per)\s+day|"
    r"daily|weekly|monthly|"
    r"q\d+h|bid|tid|qid|od|bd|qhs|prn"
    r")\b",
    re.IGNORECASE,
)


def parse_prescription(text: str) -> List[Dict]:
    """
    Extract medication names, dosages, and frequencies.

    Each non-empty line is treated as a separate prescription.
    Returns dictionaries with medication, dosage, and frequency.
    """
    results = []

    if not isinstance(text, str) or not text.strip():
        return results

    # Check longer medication names first.
    medication_names = sorted(
        MEDICATIONS,
        key=lambda name: len(str(name)),
        reverse=True,
    )

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        medication = None

        for med_name in medication_names:
            med_name = str(med_name).strip()

            if not med_name:
                continue

            # IMPORTANT: use one backslash before each b.
            if re.search(
                rf"\b{re.escape(med_name)}\b",
                line,
                re.IGNORECASE,
            ):
                medication = med_name
                break

        if medication is None:
            continue

        dosage_match = DOSAGE_PATTERN.search(line)
        frequency_match = FREQUENCY_PATTERN.search(line)

        results.append({
            "medication": medication,
            "dosage": dosage_match.group(1) if dosage_match else None,
            "frequency": (
                frequency_match.group(0)
                if frequency_match
                else None
            ),
        })

    return results
