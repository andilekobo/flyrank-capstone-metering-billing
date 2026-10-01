def check_quota(
    api_calls_used: int,
    tokens_used: int,
    requested_tokens: int,
    api_call_limit: int,
    token_limit: int,
):
    if api_calls_used + 1 > api_call_limit:
        return {
            "allowed": False,
            "status_code": 429,
            "reason": "API call quota exceeded",
        }

    if tokens_used + requested_tokens > token_limit:
        return {
            "allowed": False,
            "status_code": 402,
            "reason": "AI token quota exceeded",
        }

    return {
        "allowed": True,
        "status_code": 200,
        "reason": "Usage allowed",
    }