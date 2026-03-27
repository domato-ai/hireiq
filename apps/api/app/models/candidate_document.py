from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.candidate import Candidate


class CandidateDocument(Base):
    __tablename__ = "candidate_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="Original filename provided by the uploader"
    )
    blob_url: Mapped[str] = mapped_column(
        String(2048), nullable=False, comment="Canonical Azure Blob Storage URL"
    )
    file_type: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="MIME type, e.g. application/pdf"
    )
    size_bytes: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="File size in bytes"
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ------------------------------------------------------------------ #
    # Relationships
    # ------------------------------------------------------------------ #
    candidate: Mapped[Candidate] = relationship("Candidate", back_populates="documents")

    def __repr__(self) -> str:
        return (
            f"<CandidateDocument id={self.id} filename={self.filename!r} "
            f"type={self.file_type!r}>"
        )
