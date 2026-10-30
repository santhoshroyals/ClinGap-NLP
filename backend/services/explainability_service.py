def build_explanation(entities, gaps, confidence, rule_matches):
    return {
        'entities': entities,
        'gaps': gaps,
        'confidence': confidence,
        'matched_rules': [r.get('rule_id', r.get('id')) for r in rule_matches]
    }
