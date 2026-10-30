"""
validate_pilot_annotations.py - Validates completed pilot annotations against schema
"""
import sys, os, json
from pydantic import ValidationError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
from evaluation.annotation_schema import CaseAnnotation

def validate_file(file_path):
    print(f"Validating annotations in: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cases = data.get("cases", data if isinstance(data, list) else [])
    
    errors = 0
    for idx, c in enumerate(cases):
        try:
            # Check character span bounds
            note = c.get("clinical_note", "")
            for e in c.get("entities", []):
                start, end = e.get("start_char", 0), e.get("end_char", 0)
                if start < 0 or end > len(note) or start >= end:
                    print(f"  [ERROR] Case {c.get('record_id')}: Invalid span [{start}:{end}] for text '{e.get('entity_text')}'")
                    errors += 1
                elif note[start:end] != e.get("entity_text"):
                    print(f"  [WARNING] Case {c.get('record_id')}: Text mismatch at [{start}:{end}]. Note has '{note[start:end]}', entity specifies '{e.get('entity_text')}'")
            CaseAnnotation(**c)
        except ValidationError as ve:
            print(f"  [ERROR] Case {c.get('record_id')} schema validation failure: {ve}")
            errors += 1
            
    if errors == 0:
        print(f"SUCCESS: All {len(cases)} cases strictly conform to the evaluation schema!")
    else:
        print(f"FAILED: Found {errors} validation errors.")
    return errors == 0

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "pilot_10_cases.json")
    validate_file(target)
