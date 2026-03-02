# app/services/entity_service.py

import re
from typing import Dict


def extract_entities(message: str) -> Dict:

    entities = {}

    # Doctor name
    doctor_pattern = r"\bDr\.?\s?[A-Z][a-z]+\b"
    doctor_match = re.findall(doctor_pattern, message)
    if doctor_match:
        entities["doctor_name"] = doctor_match[0]

    # Date
    date_pattern = r"\b(today|tomorrow|\d{4}-\d{2}-\d{2})\b"
    date_match = re.search(date_pattern, message, re.IGNORECASE)
    if date_match:
        entities["appointment_date"] = date_match.group()

    # Time
    time_pattern = r"\b(\d{1,2}\s?(AM|PM|am|pm))\b"
    time_match = re.search(time_pattern, message)
    if time_match:
        entities["appointment_time"] = time_match.group()

    # Department
    department_pattern = r"\b(cardiology|neurology|orthopedics|pediatrics)\b"
    department_match = re.search(department_pattern, message, re.IGNORECASE)
    if department_match:
        entities["department"] = department_match.group()

    return entities