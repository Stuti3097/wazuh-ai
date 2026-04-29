from use_cases import run_use_cases

def process_assistant(user_input):

    result = run_use_cases(user_input)

    if result:
        return {
            "type": "use_case",
            "name": result.get("name", "Unknown"),
            "steps": result.get("steps", [])
        }

    return {
        "type": "info",
        "message": "No matching use case found. Please give more details."
    }
