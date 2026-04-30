from rapidfuzz import fuzz

# canonical phrases per use case
USE_CASES = [
    {
        "name": "Dashboard Error",
        "phrases": [
            "dashboard server is not ready yet",
            "wazuh dashboard is not ready",
            "dashboard not ready",
            "dashboard cannot connect to indexer"
        ],
        "handler": "dashboard_error"
    },
    # add more use cases here later
]


def best_match(user_input: str):
    text = user_input.lower()

    best = None
    best_score = 0

    for uc in USE_CASES:
        for phrase in uc["phrases"]:
            score = fuzz.token_set_ratio(text, phrase)
            if score > best_score:
                best_score = score
                best = uc

    return best, best_score


def run_use_cases(user_input, context):

    uc, score = best_match(user_input)

    # threshold (tune if needed)
    if uc and score >= 65:
        if uc["handler"] == "dashboard_error":
            from .dashboard_error import dashboard_error_flow
            
            if not context:
                 return dashboard_error_flow(None, {})
            else:
                 return dashboard_error_flow(user_input, context)
         
    return None
