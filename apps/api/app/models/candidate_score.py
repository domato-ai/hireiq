from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.role import Role


class CandidateScore(Base):
    __tablename__ = "candidate_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    overall_score: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Composite score 0.0 – 100.0"
    )
    factor_scores_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Per-factor breakdown, e.g. {skills: 85, experience: 72, ...}",
    )
    reasons_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Reasoning snippets keyed by factor",
    )
    strengths: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text),  # type: ignore[arg-type]
        nullable=True,
        comment="Top positive signals extracted from the resume",
    )
    risks: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text),  # type: ignore[arg-type]
        nullable=True,
        comment="Potential red flags or gaps",
    )
    missing_evidence: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text),  # type: ignore[arg-type]
        nullable=True,
        comment="Requirements with no supporting evidence in the resume",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ------------------------------------------------------------------ #
    # Relationships
    # ------------------------------------------------------------------ #
    candidate: Mapped[Candidate] = relationship("Candidate", back_populates="scores")
    role: Mapped[Role] = relationship("Role")

    def __repr__(self) -> str:
        return (
            f"<CandidateScore id={self.id} candidate_id={self.candidate_id} "
            f"score={self.overall_score}>"
        )
