from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace


class UsageEvent(Base):
    """Append-only ledger of billable / limit-tracked events."""

    __tablename__ = "usage_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment=(
            "Slug identifying the event, e.g. resume_upload | role_created "
            "| candidate_scored | shortlist_exported"
        ),
    )
    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="Number of units consumed"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # ------------------------------------------------------------------ #
    # Relationships
    # ------------------------------------------------------------------ #
    user: Mapped[User] = relationship("User", back_populates="usage_events")
    workspace: Mapped[Workspace | None] = relationship(
        "Workspace", back_populates="usage_events"
    )

    def __repr__(self) -> str:
        return (
            f"<UsageEvent id={self.id} type={self.event_type!r} "
            f"qty={self.quantity} user={self.user_id}>"
        )
