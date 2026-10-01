from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.usage_event import UsageEvent


def get_processed_request(
    db: Session,
    idempotency_key: str,
):
    return db.scalar(
        select(UsageEvent).where(
            UsageEvent.idempotency_key == idempotency_key
        )
    )


def save_processed_request(
    db: Session,
    idempotency_key: str,
    response: dict,
):
    # Idempotency is persisted by the usage_events row.
    # The response is returned from the existing event when
    # the same idempotency key is received again.
    return response