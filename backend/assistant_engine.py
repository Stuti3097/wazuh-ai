from use_cases import run_use_cases
def process_assistant(user_input, context=None):
    result = run_use_cases(user_input, context)

    if result:
        return {
            "type": "use_case",
            "display": result.get("display", ""),
            "ask": result.get("ask", []),
            "done": result.get("done", False),
            "context": result.get("context", {})
        }

    return {
        "type": "info",
        "message": "No matching use case found. Please give more details."
    }
