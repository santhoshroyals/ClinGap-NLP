
"""
prescription_service.py - Prescription extraction and regimen reconstruction
for ClinGap-NLP.

Research/decision-support tool only. Not a substitute for clinical judgment.
"""

import re
from typing import List, Dict, Optional


# Dosage examples: 500 mg, 2.5 ml, 1 g, 10 units
DOSAGE_REGEX = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:mg|g|ml|mL|units|mcg|µg)(?!\s*/\s*(?:d[lL]|[lL]|m[lL]|u[lL]|µ[lL]|mm3|kg|min|hr|h|day)|%)\b",
    re.IGNORECASE,
)


# Frequency examples: twice daily, three times daily, every 8 hours, PRN
FREQ_REGEX = re.compile(
    r"\b(?:"
    r"every\s+\d+\s+(?:hours?|days?|weeks?)|"
    r"once\s+daily|twice\s+daily|"
    r"three\s+times\s+daily|four\s+times\s+daily|"
    r"once\s+weekly|twice\s+weekly|once\s+monthly|"
    r"\d+\s+times?\s+(?:a|per)\s+day|"
    r"as\s+needed|"
    r"daily|weekly|monthly|"
    r"q\d+h|bid|tid|qid|od|qd|qhs|prn"
    r")\b",
    re.IGNORECASE,
)


NOISE_MEDICATIONS = frozenset({
    "medication", "medications", "medicine", "medicines",
    "drug", "drugs", "pill", "pills", "tablet", "tablets",
})


def reconstruct_regimens(
    text: str,
    entities: Optional[List[Dict]] = None,
) -> List[Dict]:
    """
    Reconstruct medication regimens from text and optional NER entities.

    If entities are supplied, use their medication names. Otherwise,
    use the medication dictionary as a fallback.
    """
    if not isinstance(text, str) or not text.strip():
        return []

    # Obtain entities when not supplied.
    if entities is None:
        try:
            from .ner_service import hybrid_ner
            entities = hybrid_ner(text)
        except Exception:
            entities = []

    # Collect medication names from NER.
    distinct_meds = []
    seen = set()

    for entity in entities or []:
        if entity.get("entity_type") != "MEDICATION":
            continue

        name = str(entity.get("entity_text", "")).strip()

        if name and name.lower() not in NOISE_MEDICATIONS:
            if name.lower() not in seen:
                distinct_meds.append(name)
                seen.add(name.lower())

    # Fallback: detect medication names using the existing lexicon.
    if not distinct_meds:
        try:
            import json
            from pathlib import Path

            dictionary_path = (
                Path(__file__).resolve().parents[2]
                / "knowledge_base"
                / "medications.json"
            )

            with open(dictionary_path, "r", encoding="utf-8") as file:
                medication_dictionary = json.load(file)

            for name in sorted(
                medication_dictionary,
                key=lambda item: len(str(item)),
                reverse=True,
            ):
                name = str(name).strip()

                if (
                    name
                    and name.lower() not in NOISE_MEDICATIONS
                    and re.search(
                        rf"\b{re.escape(name)}\b",
                        text,
                        re.IGNORECASE,
                    )
                    and name.lower() not in seen
                ):
                    distinct_meds.append(name)
                    seen.add(name.lower())

        except (OSError, ValueError, TypeError):
            pass

    if not distinct_meds:
        return []

    # Extract dosage and frequency spans.
    dosage_spans = [
        {
            "text": match.group(0).strip(),
            "start": match.start(),
            "end": match.end(),
        }
        for match in DOSAGE_REGEX.finditer(text)
    ]

    frequency_spans = [
        {
            "text": match.group(0).strip(),
            "start": match.start(),
            "end": match.end(),
        }
        for match in FREQ_REGEX.finditer(text)
    ]

    # Find all medication occurrences.
    medication_spans = []

    for name in distinct_meds:
        for match in re.finditer(
            rf"\b{re.escape(name)}\b",
            text,
            re.IGNORECASE,
        ):
            medication_spans.append({
                "medication": name,
                "start": match.start(),
                "end": match.end(),
            })

    regimens = []

    # Associate each medication with the nearest following dosage
    # and frequency, preferring values within the same sentence.
    for name in distinct_meds:
        occurrences = [
            item for item in medication_spans
            if item["medication"].lower() == name.lower()
        ]

        best_dosage = None
        best_frequency = None
        best_dosage_distance = float("inf")
        best_frequency_distance = float("inf")

        for occurrence in occurrences:
            for dosage in dosage_spans:
                if dosage["start"] >= occurrence["end"]:
                    distance = dosage["start"] - occurrence["end"]
                else:
                    distance = (
                        occurrence["start"] - dosage["end"]
                    ) * 2

                if 0 <= distance < 120 and distance < best_dosage_distance:
                    best_dosage_distance = distance
                    best_dosage = dosage["text"]

            for frequency in frequency_spans:
                if frequency["start"] >= occurrence["end"]:
                    distance = frequency["start"] - occurrence["end"]
                else:
                    distance = (
                        occurrence["start"] - frequency["end"]
                    ) * 2

                if (
                    0 <= distance < 150
                    and distance < best_frequency_distance
                ):
                    best_frequency_distance = distance
                    best_frequency = frequency["text"]

        regimens.append({
            "medication": name,
            "dosage": best_dosage,
            "frequency": best_frequency,
        })

    return regimens


def extract_regimens(
    text: str,
    entities: Optional[List[Dict]] = None,
) -> List[Dict]:
    """Compatibility alias for reconstruct_regimens."""
    return reconstruct_regimens(text, entities)


def parse_prescription(text: str) -> dict:
    """
    Parse a prescription or clinical note.

    Preserves the existing output fields:
    dosage, frequency, regimens, and raw_text.
    """
    if not isinstance(text, str):
        text = ""

    regimens = reconstruct_regimens(text)

    dosage_match = DOSAGE_REGEX.search(text)
    frequency_match = FREQ_REGEX.search(text)

    primary_dosage = (
        regimens[0]["dosage"]
        if regimens and regimens[0]["dosage"]
        else dosage_match.group(0) if dosage_match else None
    )

    primary_frequency = (
        regimens[0]["frequency"]
        if regimens and regimens[0]["frequency"]
        else frequency_match.group(0) if frequency_match else None
    )

    return {
        "dosage": primary_dosage,
        "frequency": primary_frequency,
        "regimens": regimens,
        "raw_text": text,
    }
