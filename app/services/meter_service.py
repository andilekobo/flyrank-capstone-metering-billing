def calculate_usage(
    input_tokens: int,
    cached_input_tokens: int,
    reasoning_tokens: int,
    output_tokens: int,
):
    billable_input_tokens = input_tokens - cached_input_tokens

    billable_output_tokens = reasoning_tokens + output_tokens

    total_billable_tokens = (
        billable_input_tokens + billable_output_tokens
    )

    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "billable_input_tokens": billable_input_tokens,
        "reasoning_tokens": reasoning_tokens,
        "output_tokens": output_tokens,
        "billable_output_tokens": billable_output_tokens,
        "total_billable_tokens": total_billable_tokens,
    }