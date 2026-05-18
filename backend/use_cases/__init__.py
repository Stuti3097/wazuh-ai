from rapidfuzz import fuzz

# -----------------------------------------------------------------------------
# REGISTERED USE CASES
# -----------------------------------------------------------------------------
USE_CASES = [
    {
        "name": "Dashboard Error",
        "phrases": [
            "dashboard server is not ready yet",
            "wazuh dashboard is not ready",
            "dashboard not ready",
            "dashboard cannot connect to indexer",
            "wazuh dashboard is not ready yet",
        ],
        "handler": "dashboard_error"
    },
    # add more use cases here later
]


# -----------------------------------------------------------------------------
# FUZZY MATCHER
# -----------------------------------------------------------------------------
def best_match(user_input: str):
    text       = user_input.lower()
    best       = None
    best_score = 0

    for uc in USE_CASES:
        for phrase in uc["phrases"]:
            score = fuzz.token_set_ratio(text, phrase)
            if score > best_score:
                best_score = score
                best       = uc

    return best, best_score


# -----------------------------------------------------------------------------
# MAIN ROUTER
# -----------------------------------------------------------------------------
def run_use_cases(user_input, context):

    # ---------------------------------------------------------
    # PRIORITY: if there is already an active flow in progress,
    # skip keyword matching entirely and continue that flow.
    # user_input is the user's answer to the last question.
    # ---------------------------------------------------------
    if context and context.get("stage"):
        handler = context.get("handler", "dashboard_error")

        if handler == "dashboard_error":
            from .dashboard_error import dashboard_error_flow
            return dashboard_error_flow(user_input, context)

        # add more handlers here as new use cases are built
        return None

    # ---------------------------------------------------------
    # No active flow — try to match a new use case by keyword
    # ---------------------------------------------------------
    uc, score = best_match(user_input)

    if uc and score >= 65:
        if uc["handler"] == "dashboard_error":
            from .dashboard_error import dashboard_error_flow
            result = dashboard_error_flow(None, {})
            # stamp the handler into context so follow-up messages
            # know which flow to continue
            if result and result.get("context") is not None:
                result["context"]["handler"] = "dashboard_error"
            return result

    return None
