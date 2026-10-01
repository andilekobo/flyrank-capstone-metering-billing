from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.usage_event import UsageEvent
from app.services.billing_service import calculate_total_cost

router = APIRouter()


@router.get("/usage/{tenant_id}")
def get_usage(
    tenant_id: str,
    db: Session = Depends(get_db),
):
    # Current month window
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)

    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)

    # Get tenant subscription
    subscription = db.scalar(
        select(Subscription).where(
            Subscription.tenant_id == tenant_id
        )
    )

    if not subscription:
        return {
            "tenant_id": tenant_id,
            "error": "Tenant subscription not found",
        }

    # Get current plan
    plan = db.scalar(
        select(Plan).where(
            Plan.id == subscription.plan_id
        )
    )

    if not plan:
        return {
            "tenant_id": tenant_id,
            "error": "Tenant plan not found",
        }

    # Get current month's usage
    events = db.scalars(
        select(UsageEvent).where(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.created_at >= month_start,
            UsageEvent.created_at < next_month,
        )
    ).all()

    api_calls = len(events)

    input_tokens = sum(
        event.input_tokens for event in events
    )

    cached_input_tokens = sum(
        event.cached_input_tokens for event in events
    )

    reasoning_tokens = sum(
        event.reasoning_tokens for event in events
    )

    output_tokens = sum(
        event.output_tokens for event in events
    )

    total_billable_tokens = sum(
        event.total_billable_tokens for event in events
    )

    cost = calculate_total_cost(
        api_calls=api_calls,
        input_tokens=input_tokens,
        cached_input_tokens=cached_input_tokens,
        reasoning_tokens=reasoning_tokens,
        output_tokens=output_tokens,
    )

    return {
        "tenant_id": tenant_id,
        "billing_period": {
            "start": month_start.isoformat(),
            "end": next_month.isoformat(),
        },
        "subscription": {
            "status": subscription.status,
            "plan": {
                "id": plan.id,
                "name": plan.name,
                "api_call_limit": plan.api_call_limit,
                "token_limit": plan.token_limit,
            },
        },
        "usage": {
            "api_calls": api_calls,
            "api_call_limit": plan.api_call_limit,
            "tokens": {
                "input_tokens": input_tokens,
                "cached_input_tokens": cached_input_tokens,
                "reasoning_tokens": reasoning_tokens,
                "output_tokens": output_tokens,
                "total_billable_tokens": total_billable_tokens,
            },
            "token_limit": plan.token_limit,
        },
        "cost": cost,
    }