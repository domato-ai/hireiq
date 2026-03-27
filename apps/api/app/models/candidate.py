from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.candidate_document import CandidateDocument
    from app.models.candidate_score import CandidateScore

# pgvector is an optional extension; import conditionally so unit tests
# that run without the extension can still import the model.
try:
    from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]

    _VECTOR_TYPE = Vector(1536)
except ImportError:  # pragma: no cover
    from sqlalchemy import ARRAY, Float

    _VECTOR_TYPE = ARRAY(Float)  # type: ignore[assignment]


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    raw_text: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Full plain-text extracted from resume"
    )
    structured_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Parsed resume fields (skills, experience, education, etc.)",
    )
    embedding: Mapped[Any | None] = mapped_column(
        _VECTOR_TYPE,  # type: ignore[arg-type]
        nullable=True,
        comment="1536-dim vector for semantic similarity search",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        comment="pending | parsing | parsed | scored | shortlisted | rejected",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ------------------------------------------------------------------ #
    # Relationships
    # ------------------------------------------------------------------ #
    role: Mapped[Role] = relationship("Role", back_populates="candidates")
    documents: Mapped[list[CandidateDocument]] = relationship(
        "CandidateDocument", back_populates="candidate", cascade="all, delete-orphan"
    )
    scores: Mapped[list[CandidateScore]] = relationship(
        "CandidateScore", back_populates="candidate", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Candidate id={self.id} name={self.name!r} status={self.status!r}>"
