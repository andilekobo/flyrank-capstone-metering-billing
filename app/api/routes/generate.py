from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.usage_event import UsageEvent
from app.schemas.generate import GenerateRequest
from app.services.meter_service import calculate_usage
from app.services.quota_service import check_quota

router = APIRouter()


@router.post("/generate")
def generate(
    request: GenerateRequest,
    db: Session = Depends(get_db),
):
    # Check whether this idempotency key was already processed
    existing_event = db.scalar(
        select(UsageEvent).where(
            UsageEvent.idempotency_key == request.idempotency_key
        )
    )

    if existing_event:
        usage = {
            "input_tokens": existing_event.input_tokens,
            "cached_input_tokens": existing_event.cached_input_tokens,
            "reasoning_tokens": existing_event.reasoning_tokens,
            "output_tokens": existing_event.output_tokens,
            "total_billable_tokens": existing_event.total_billable_tokens,
        }

        return {
            "success": True,
            "message": "Generation completed",
            "tenant_id": existing_event.tenant_id,
            "usage": usage,
            "idempotency_key": existing_event.idempotency_key,
            "idempotent_replay": True,
        }

    # Calculate billable usage
    usage = calculate_usage(
        input_tokens=request.input_tokens,
        cached_input_tokens=request.cached_input_tokens,
        reasoning_tokens=request.reasoning_tokens,
        output_tokens=request.output_tokens,
    )

    # Get the tenant's subscription
    subscription = db.scalar(
        select(Subscription).where(
            Subscription.tenant_id == request.tenant_id
        )
    )

    if not subscription:
        raise HTTPException(
            status_code=404,
            detail="Tenant subscription not found",
        )

    # Get the plan attached to the subscription
    plan = db.scalar(
        select(Plan).where(
            Plan.id == subscription.plan_id
        )
    )

    if not plan:
        raise HTTPException(
            status_code=404,
            detail="Tenant plan not found",
        )

    # Calculate usage for the current month
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)

    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)

    api_calls_used = db.scalar(
        select(func.count(UsageEvent.id)).where(
            UsageEvent.tenant_id == request.tenant_id,
            UsageEvent.created_at >= month_start,
            UsageEvent.created_at < next_month,
        )
    ) or 0

    tokens_used = db.scalar(
        select(
            func.coalesce(
                func.sum(UsageEvent.total_billable_tokens),
                0,
            )
        ).where(
            UsageEvent.tenant_id == request.tenant_id,
            UsageEvent.created_at >= month_start,
            UsageEvent.created_at < next_month,
        )
    ) or 0

    # Check quota using the tenant's actual plan limits
    quota = check_quota(
        api_calls_used=api_calls_used,
        tokens_used=tokens_used,
        requested_tokens=usage["total_billable_tokens"],
        api_call_limit=plan.api_call_limit,
        token_limit=plan.token_limit,
    )

    if not quota["allowed"]:
        raise HTTPException(
            status_code=quota["status_code"],
            detail=quota["reason"],
        )

    # Create usage event
    event = UsageEvent(
        tenant_id=request.tenant_id,
        idempotency_key=request.idempotency_key,
        input_tokens=request.input_tokens,
        cached_input_tokens=request.cached_input_tokens,
        reasoning_tokens=request.reasoning_tokens,
        output_tokens=request.output_tokens,
        total_billable_tokens=usage["total_billable_tokens"],
    )

    db.add(event)

    try:
        db.commit()
        db.refresh(event)

    except IntegrityError:
        # Another request may have created the same idempotency key
        db.rollback()

        existing_event = db.scalar(
            select(UsageEvent).where(
                UsageEvent.idempotency_key == request.idempotency_key
            )
        )

        if not existing_event:
            raise

        usage = {
            "input_tokens": existing_event.input_tokens,
            "cached_input_tokens": existing_event.cached_input_tokens,
            "reasoning_tokens": existing_event.reasoning_tokens,
            "output_tokens": existing_event.output_tokens,
            "total_billable_tokens": existing_event.total_billable_tokens,
        }

        return {
            "success": True,
            "message": "Generation completed",
            "tenant_id": existing_event.tenant_id,
            "usage": usage,
            "idempotency_key": existing_event.idempotency_key,
            "idempotent_replay": True,
        }

    return {
        "success": True,
        "message": "Generation completed",
        "tenant_id": request.tenant_id,
        "usage": usage,
        "plan": {
            "id": plan.id,
            "name": plan.name,
            "api_call_limit": plan.api_call_limit,
            "token_limit": plan.token_limit,
        },
        "quota": quota,
        "idempotency_key": request.idempotency_key,
        "idempotent_replay": False,
    }