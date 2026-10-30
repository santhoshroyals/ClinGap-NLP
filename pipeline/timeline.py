from typing import List, Dict, Optional
import datetime

def format_investigation_timeline_status(status: Optional[str], negated: bool = False) -> str:
    """Format investigation status for clinical timeline summary display."""
    raw = (status or ('not performed' if negated else 'ordered')).lower().strip()
    if raw in {'not performed', 'cancelled'} or negated:
        return 'Not performed'
    if raw == 'ordered/pending':
        return 'Ordered / Pending'
    if raw in {'pending', 'pending results'} or 'pending' in raw:
        return 'Pending Results'
    if raw in {'completed/performed', 'performed', 'completed'}:
        return 'Performed'
    return 'Ordered'


def build_timeline(entities: List[Dict], investigations: List[Dict], regimens: Optional[List[Dict]] = None) -> List[Dict]:
    """Create a simple chronological timeline based on entity order with associated regimen details."""
    timeline = []
    base_time = datetime.datetime.now()

    regimen_map = {}
    if regimens:
        for r in regimens:
            if r.get("medication"):
                regimen_map[r["medication"].lower().strip()] = r

    for i, ent in enumerate(entities):
        entry = {
            "timestamp": (base_time + datetime.timedelta(minutes=i)).isoformat(),
            "type": ent.get("entity_type", ""),
            "text": ent.get("entity_text", ""),
            "status": ent.get("status") or ("not performed" if ent.get("negated") else "ordered"),
            "negated": ent.get("negated", False),
        }
        if ent.get("entity_type") == "MEDICATION":
            reg = regimen_map.get(ent.get("entity_text", "").lower().strip())
            if reg:
                entry["dosage"] = reg.get("dosage")
                entry["frequency"] = reg.get("frequency")
        timeline.append(entry)
    for i, inv in enumerate(investigations, start=len(entities)):
        entry = {
            "timestamp": (base_time + datetime.timedelta(minutes=i)).isoformat(),
            "type": inv.get("entity_type", ""),
            "text": inv.get("entity_text", ""),
            "status": inv.get("status") or ("not performed" if inv.get("negated") else "ordered"),
            "negated": inv.get("negated", False),
        }
        timeline.append(entry)
    return timeline


def build_timeline_summary(entities: List[Dict], regimens: Optional[List[Dict]] = None) -> Dict:
    """Build summary categorization for the clinical timeline reusing reconstructed regimens.
    Ensures each medication's dosage and frequency stay associated with the correct medication.
    """
    conditions = list({
        e["entity_text"] for e in entities if e.get("entity_type") in {"DISEASE", "CONDITION"}
    })
    investigations = [
        {
            **e,
            "display_status": format_investigation_timeline_status(e.get("status"), e.get("negated", False)),
        }
        for e in entities if e.get("entity_type") == "INVESTIGATION"
    ]

    regimen_items = []
    seen_meds = set()
    if regimens:
        for r in regimens:
            med_name = r.get("medication")
            if med_name and med_name.lower().strip() not in seen_meds:
                seen_meds.add(med_name.lower().strip())
                regimen_items.append({
                    "name": med_name,
                    "dosage": r.get("dosage") or "Not specified",
                    "frequency": r.get("frequency") or "Not specified",
                })

    for e in entities:
        if e.get("entity_type") == "MEDICATION":
            med_name = e.get("entity_text")
            if med_name and med_name.lower().strip() not in seen_meds:
                seen_meds.add(med_name.lower().strip())
                regimen_items.append({
                    "name": med_name,
                    "dosage": "Not specified",
                    "frequency": "Not specified",
                })

    return {
        "conditions": conditions,
        "investigations": investigations,
        "medications": regimen_items,
    }
