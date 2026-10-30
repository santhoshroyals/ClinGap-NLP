from .ner_service import INVESTIGATIONS_DICT, GENERIC_INVESTIGATION_WORDS


def _norm_inv(val: str) -> str:
    if not val:
        return ''
    cleaned = str(val).strip().rstrip('.,;:').lower()
    return INVESTIGATIONS_DICT.get(cleaned, cleaned)


def detect_gaps(entities, matched_rules):
    """Detect gaps based on guideline recommendations and negated investigations.

    - For each matched guideline rule that recommends an investigation, add a
      ``MISSING_INVESTIGATION`` gap if that investigation is not present (or is
      present but negated / cancelled) in the extracted entities.
    - Additionally, if any specific investigation entity is explicitly negated or
      cancelled in the clinical note, create a gap reflecting it was not performed.
    - Investigations that are ordered/pending, pending, ordered, or completed do NOT
      create false-positive missing gaps.
    - Generic words such as 'test' or 'investigation' never create standalone gaps.
    """
    gaps = []
    # Gaps from guideline recommendations
    for rule in matched_rules:
        rec = rule.get('recommendation')
        if not rec or rec.get('type') != 'INVESTIGATION':
            continue
        rec_name = rec.get('name', '')
        inv_name = _norm_inv(rec_name)
        # Check if investigation is present and not negated or not-performed
        found = any(
            ent.get('entity_type') == 'INVESTIGATION' and
            (_norm_inv(ent.get('normalized_value', '')) == inv_name or
             _norm_inv(ent.get('entity_text', '')) == inv_name) and
            not ent.get('negated') and
            ent.get('status') not in {'not performed', 'cancelled'}
            for ent in entities
        )
        if not found:
            gaps.append({
                'gap_type': 'MISSING_INVESTIGATION',
                'description': f"The {rec_name} investigation is missing from the record.",
                'entity': inv_name,
                'rule_id': rule.get('rule_id'),
            })
    # Gaps for explicitly negated or not performed investigations (e.g., "No CBC", "X-ray was not performed")
    for ent in entities:
        if ent.get('entity_type') == 'INVESTIGATION':
            name = ent.get('normalized_value') or ent.get('entity_text') or ''
            clean_name = name.lower().strip().rstrip('.,;:')
            raw_text = (ent.get('entity_text') or '').lower().strip().rstrip('.,;:')

            # Prevent generic words such as 'test' or 'investigation' from becoming gaps
            if clean_name in GENERIC_INVESTIGATION_WORDS or raw_text in GENERIC_INVESTIGATION_WORDS:
                continue

            status = ent.get('status')
            # Do NOT emit gaps for investigations that are ordered/pending, pending, ordered, or completed
            if status in {'ORDERED/PENDING', 'pending', 'ordered', 'completed/performed'}:
                continue

            if ent.get('negated') or status in {'not performed', 'cancelled'}:
                norm_name = _norm_inv(name)
                gaps.append({
                    'gap_type': 'MISSING_INVESTIGATION',
                    'description': f"The {name} investigation was noted as not performed.",
                    'entity': norm_name,
                    'rule_id': None,
                })
    # Deduplicate: multiple synonyms (e.g. "Complete blood count" and "CBC") that share
    # the same normalized_value must produce only one gap per (gap_type, entity).
    seen = {}
    for gap in gaps:
        key = (gap['gap_type'], gap.get('entity', ''))
        if key not in seen:
            seen[key] = gap
    return list(seen.values())
