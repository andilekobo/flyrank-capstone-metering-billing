from decimal import Decimal, ROUND_HALF_UP


# Project pricing constants
API_CALL_PRICE_CENTS = Decimal("1")

INPUT_PRICE_CENTS_PER_MILLION = Decimal("300")
CACHED_INPUT_PRICE_CENTS_PER_MILLION = Decimal("75")
OUTPUT_PRICE_CENTS_PER_MILLION = Decimal("1500")


def _calculate_token_cost(
    tokens: int,
    price_cents_per_million: Decimal,
) -> int:
    cost = (
        Decimal(tokens)
        * price_cents_per_million
        / Decimal("1000000")
    )

    return int(cost.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def calculate_cost(
    input_tokens: int,
    cached_input_tokens: int,
    reasoning_tokens: int,
    output_tokens: int,
):
    billable_input_tokens = input_tokens - cached_input_tokens
    billable_output_tokens = reasoning_tokens + output_tokens

    input_cost_cents = _calculate_token_cost(
        billable_input_tokens,
        INPUT_PRICE_CENTS_PER_MILLION,
    )

    cached_input_cost_cents = _calculate_token_cost(
        cached_input_tokens,
        CACHED_INPUT_PRICE_CENTS_PER_MILLION,
    )

    output_cost_cents = _calculate_token_cost(
        billable_output_tokens,
        OUTPUT_PRICE_CENTS_PER_MILLION,
    )

    return {
        "input_cost_cents": input_cost_cents,
        "cached_input_cost_cents": cached_input_cost_cents,
        "output_cost_cents": output_cost_cents,
        "total_cost_cents": (
            input_cost_cents
            + cached_input_cost_cents
            + output_cost_cents
        ),
    }


def calculate_total_cost(
    api_calls: int,
    input_tokens: int,
    cached_input_tokens: int,
    reasoning_tokens: int,
    output_tokens: int,
):
    token_cost = calculate_cost(
        input_tokens=input_tokens,
        cached_input_tokens=cached_input_tokens,
        reasoning_tokens=reasoning_tokens,
        output_tokens=output_tokens,
    )

    api_call_cost_cents = (
        Decimal(api_calls) * API_CALL_PRICE_CENTS
    )

    total_cost_cents = (
        token_cost["total_cost_cents"]
        + int(api_call_cost_cents)
    )

    return {
        "api_call_cost_cents": int(api_call_cost_cents),
        "input_cost_cents": token_cost["input_cost_cents"],
        "cached_input_cost_cents": token_cost["cached_input_cost_cents"],
        "output_cost_cents": token_cost["output_cost_cents"],
        "total_cost_cents": total_cost_cents,
    }
