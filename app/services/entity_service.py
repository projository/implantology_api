# app/services/entity_service.py

import re
from typing import Dict


def extract_entities(message: str) -> Dict:

    entities = {}

    # Simple examples (you can expand later)

    city_pattern = r"\b(Mumbai|Dubai|Delhi|London|Paris)\b"
    date_pattern = r"\b(today|tomorrow|\d{4}-\d{2}-\d{2})\b"

    city_match = re.findall(city_pattern, message, re.IGNORECASE)
    if city_match:
        entities["cities"] = city_match

    date_match = re.search(date_pattern, message, re.IGNORECASE)
    if date_match:
        entities["date"] = date_match.group()

    return entities