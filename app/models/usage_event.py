from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    tenant_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True,
        index=True,
    )

    input_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    cached_input_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    reasoning_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    output_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    total_billable_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )