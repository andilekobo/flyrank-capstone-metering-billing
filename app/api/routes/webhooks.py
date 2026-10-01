import hashlib
import hmac
import json
import os
import time

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.plan import Plan
from app.models.stripe_event import StripeEvent
from app.models.subscription import Subscription

router = APIRouter()

MOCK_WEBHOOK_SECRET = os.getenv(
    "MOCK_WEBHOOK_SECRET",
    "mock_webhook_secret"
)


def verify_mock_signature(
    payload: bytes,
    signature: str,
) -> bool:
    """
    Verify a mock Stripe-style webhook signature.

    Format:
    t=<timestamp>,v1=<signature>
    """

    try:
        parts = dict(
            item.split("=", 1)
            for item in signature.split(",")
        )

        timestamp = parts["t"]
        received_signature = parts["v1"]

        signed_payload = f"{timestamp}.".encode() + payload

        expected_signature = hmac.new(
            MOCK_WEBHOOK_SECRET.encode(),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(
            received_signature,
            expected_signature,
        )

    except (KeyError, ValueError):
        return False


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()

    signature = request.headers.get("stripe-signature")

    if not signature:
        raise HTTPException(
            status_code=400,
            detail="Missing Stripe signature",
        )

    if not verify_mock_signature(payload, signature):
        raise HTTPException(
            status_code=400,
            detail="Invalid Stripe signature",
        )

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook payload",
        )

    event_id = event.get("id")
    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})

    if not event_id or not event_type:
        raise HTTPException(
            status_code=400,
            detail="Invalid event",
        )

    db: Session = SessionLocal()

    try:
        existing_event = db.scalar(
            select(StripeEvent).where(
                StripeEvent.stripe_event_id == event_id
            )
        )

        if existing_event:
            return {
                "received": True,
                "duplicate": True,
                "event_id": event_id,
            }

        stripe_event = StripeEvent(
            stripe_event_id=event_id,
            event_type=event_type,
        )

        db.add(stripe_event)

        if event_type == "checkout.session.completed":
            tenant_id = data.get("metadata", {}).get("tenant_id")
            subscription_id = data.get("subscription")

            if tenant_id and subscription_id:
                subscription = db.scalar(
                    select(Subscription).where(
                        Subscription.tenant_id == tenant_id
                    )
                )

                if subscription:
                    pro_plan = db.scalar(
                        select(Plan).where(
                            Plan.id == "pro"
                        )
                    )

                    if pro_plan:
                        subscription.plan_id = pro_plan.id

                    subscription.status = "active"
                    subscription.stripe_subscription_id = (
                        subscription_id
                    )

        elif event_type == "customer.subscription.updated":
            stripe_subscription_id = data.get("id")
            status = data.get("status")

            subscription = db.scalar(
                select(Subscription).where(
                    Subscription.stripe_subscription_id
                    == stripe_subscription_id
                )
            )

            if subscription and status:
                subscription.status = status

        elif event_type == "customer.subscription.deleted":
            stripe_subscription_id = data.get("id")

            subscription = db.scalar(
                select(Subscription).where(
                    Subscription.stripe_subscription_id
                    == stripe_subscription_id
                )
            )

            if subscription:
                subscription.status = "canceled"

                free_plan = db.scalar(
                    select(Plan).where(
                        Plan.id == "free"
                    )
                )

                if free_plan:
                    subscription.plan_id = free_plan.id

        db.commit()

        return {
            "received": True,
            "duplicate": False,
            "event_id": event_id,
            "event_type": event_type,
        }

    finally:
        db.close()
