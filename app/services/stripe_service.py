import uuid


def create_checkout_session(
    tenant_id: str,
    price_id: str,
    success_url: str,
    cancel_url: str,
):
    """
    Mock Stripe Checkout session.

    This simulates the response we would receive from Stripe
    when creating a subscription Checkout session.
    """

    session_id = f"cs_test_mock_{uuid.uuid4().hex[:12]}"

    return {
        "id": session_id,
        "url": (
            f"http://localhost:8000/mock-checkout/"
            f"{session_id}"
            f"?success_url={success_url}"
            f"&cancel_url={cancel_url}"
        ),
        "tenant_id": tenant_id,
        "price_id": price_id,
        "mode": "subscription",
        "status": "open",
    }