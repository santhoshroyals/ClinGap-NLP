import json, os

KB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'knowledge_base', 'guidelines.json')

class GuidelineEngine:
    def __init__(self):
        with open(KB_PATH) as f:
            self.rules = json.load(f)
    def match(self, entities: list) -> list:
        """Match guidelines based on extracted entities.
        Returns only rules whose required entity types are present (non‑negated).
        """
        entity_types = {e["entity_type"] for e in entities if not e.get("negated", False)}
        matches = []
        for rule in self.rules:
            criteria = rule.get("criteria", {})
            required = set(criteria.get("entities", []))
            if required and required.issubset(entity_types) and rule.get("recommendation"):
                matches.append(rule)
        return matches
