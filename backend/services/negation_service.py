import re

NEGATION_PRE = [
    'no', 'without', 'absence of', 'denies', 'denied', 'not', 'never',
    'koi', 'kuch', 'bina', 'nahi', 'nahin', 'na'
]

def detect_negations(text: str, entities: list) -> list:
    """Mark entities as negated if preceded or followed by a negation phrase within the sentence/clause."""
    for ent in entities:
        ent['negated'] = False
        ent_text = ent.get('entity_text', '')
        if not ent_text:
            continue
        pattern_pre = re.compile(
            rf"\b(?:{'|'.join(NEGATION_PRE)})\b(?:[\s,/-]+[\w-]+){{0,8}}\s*\b{re.escape(ent_text)}\b",
            re.IGNORECASE
        )
        pattern_post = re.compile(
            rf"\b{re.escape(ent_text)}\b"
            r"(?:\s*\([^)]*\))?"          # optional parenthetical e.g. (CBC)
            r"(?:[\s,/-]+[\w-]+){0,6}\s*"
            r"\b(?:not\s+(?:yet\s+)?(?:been\s+)?(?:performed|done|indicated|taken|obtained|completed|conducted)"
            r"|was\s+not\s+(?:performed|done|indicated|taken|obtained|completed|conducted)"
            r"|has\s+not\s+been\s+(?:performed|done|indicated|taken|obtained|completed|conducted)"
            r"|negative|absent|nahi\s+hai|nahin\s+hai|nahi|nahin|na\s+hai)\b",
            re.IGNORECASE,
        )

        # Split text into sentences / clauses
        for sentence in re.split(r'[.\n;]', text):
            if re.search(rf"\b{re.escape(ent_text)}\b", sentence, re.IGNORECASE):
                if pattern_pre.search(sentence) or pattern_post.search(sentence):
                    ent['negated'] = True
                    break

        if ent.get('entity_type') == 'INVESTIGATION':
            from .ner_service import extract_investigation_status
            status = extract_investigation_status(text, ent_text, ent.get('negated', False))
            ent['status'] = status
            if status in {'ORDERED/PENDING', 'pending', 'ordered', 'completed/performed'}:
                ent['negated'] = False
            elif status in {'not performed', 'cancelled'}:
                ent['negated'] = True

    return entities

