# app/services/flow_service.py

def handle_multi_turn(intent, session):

    required = intent.get("required_entities", [])
    collected = session.get("collected_entities", {})

    for entity in required:
        if entity not in collected:
            return f"Please provide {entity}."

    return None