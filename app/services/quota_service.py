FREE_API_CALL_LIMIT = 1000
FREE_TOKEN_LIMIT = 100_000


def check_quota(
    api_calls_used: int,
    tokens_used: int,
    requested_tokens: int,
):
    if api_calls_used + 1 > FREE_API_CALL_LIMIT:
        return {
            "allowed": False,
            "status_code": 429,
            "reason": "API call quota exceeded",
        }

    if tokens_used + requested_tokens > FREE_TOKEN_LIMIT:
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