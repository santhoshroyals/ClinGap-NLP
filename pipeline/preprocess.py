import re
from typing import List, Dict


def preprocess(text: str) -> str:
    """Basic preprocessing: normalize whitespace and strip."""
    return " ".join(text.split()).strip()
