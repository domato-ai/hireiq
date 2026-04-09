"""Outreach models — contacts, send logs, click/open tracking."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OutreachContact(Base):
    __tablename__ = "outreach_contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True, default="manual")
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="not_started",
        comment="not_started|sent|delivered|bounced|failed|responded|unsubscribed",
    )
    unsubscribed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    send_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    date_contacted: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    enrich_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="enriched|enriched_no_email|enrich_error",
    )
    country: Mapped[str | None] = mapped_column(
        String(2), nullable=True, index=True,
        comment="ISO 3166-1 alpha-2 country code: AU, US, GB, etc.",
    )
    recruiters_scraped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "company_name": self.company_name,
            "contact_name": self.contact_name,
            "email": self.email,
            "phone": self.phone,
            "website": self.website,
            "location": self.location,
            "industry": self.industry,
            "role_type": self.role_type,
            "source": self.source,
            "status": self.status,
            "unsubscribed": self.unsubscribed,
            "send_count": self.send_count,
            "date_contacted": self.date_contacted.isoformat() if self.date_contacted else None,
            "notes": self.notes,
            "country": self.country,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<OutreachContact id={self.id} email={self.email!r}>"


class OutreachSendLog(Base):
    __tablename__ = "outreach_send_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    send_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="test|manual|batch"
    )
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<OutreachSendLog id={self.id} email={self.email!r}>"


class OutreachClick(Base):
    __tablename__ = "outreach_clicks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    url: Mapped[str | None] = mapped_column(
        String(2000), nullable=True,
        comment="URL clicked, or '__open__' for open tracking pixel",
    )
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<OutreachClick id={self.id} email={self.email!r} url={self.url!r}>"
