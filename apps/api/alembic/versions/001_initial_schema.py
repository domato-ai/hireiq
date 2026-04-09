"""Initial schema — users, subscriptions, usage_events, workspaces, outreach tables.

Revision ID: 001
Revises:
Create Date: 2026-04-07
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Users ──
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True,
                  comment="PBKDF2 hash for email/password auth (null for Entra ID users)"),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True, unique=True, index=True,
                  comment="Stripe customer ID for billing"),
        sa.Column("entra_id", sa.String(255), nullable=True, unique=True, index=True,
                  comment="Azure Entra ID (OID claim from the ID token)"),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free",
                  comment="Active plan slug: free | pro | team"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Workspaces ──
    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Subscriptions ──
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True, unique=True, index=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True, unique=True, index=True),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free",
                  comment="free | pro | team"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active",
                  comment="active | past_due | canceled | trialing | unpaid"),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Roles ──
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description_text", sa.Text, nullable=True),
        sa.Column("requirements_json", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Candidates ──
    op.create_table(
        "candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(500), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(100), nullable=True),
        sa.Column("structured_json", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Candidate Documents ──
    op.create_table(
        "candidate_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("filename", sa.String(500), nullable=True),
        sa.Column("blob_url", sa.String(2000), nullable=True),
        sa.Column("extracted_text", sa.Text, nullable=True),
        sa.Column("content_hash", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Candidate Scores ──
    op.create_table(
        "candidate_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("overall_score", sa.Float, nullable=True),
        sa.Column("scores_json", postgresql.JSONB, nullable=True),
        sa.Column("reason_codes", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Usage Events ──
    op.create_table(
        "usage_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("event_type", sa.String(100), nullable=False,
                  comment="Slug: resume_upload | role_created | candidate_scored | shortlist_exported | analysis | analysis:<ip>"),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1",
                  comment="Number of units consumed"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )

    # ── Outreach Contacts ──
    op.create_table(
        "outreach_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_name", sa.String(500), nullable=True),
        sa.Column("contact_name", sa.String(500), nullable=True),
        sa.Column("email", sa.String(255), nullable=True, index=True),
        sa.Column("phone", sa.String(100), nullable=True),
        sa.Column("website", sa.String(1000), nullable=True),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("role_type", sa.String(100), nullable=True),
        sa.Column("source", sa.String(100), nullable=True, server_default="manual"),
        sa.Column("status", sa.String(50), nullable=False, server_default="not_started",
                  comment="not_started|sent|delivered|bounced|failed|responded|unsubscribed"),
        sa.Column("unsubscribed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("send_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("date_contacted", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("enrich_status", sa.String(50), nullable=True,
                  comment="enriched|enriched_no_email|enrich_error"),
        sa.Column("recruiters_scraped", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Outreach Send Logs ──
    op.create_table(
        "outreach_send_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("send_type", sa.String(50), nullable=True,
                  comment="test|manual|batch"),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Outreach Clicks ──
    op.create_table(
        "outreach_clicks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=True, index=True),
        sa.Column("url", sa.String(2000), nullable=True,
                  comment="URL clicked, or '__open__' for open tracking pixel"),
        sa.Column("ip", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("outreach_clicks")
    op.drop_table("outreach_send_logs")
    op.drop_table("outreach_contacts")
    op.drop_table("usage_events")
    op.drop_table("candidate_scores")
    op.drop_table("candidate_documents")
    op.drop_table("candidates")
    op.drop_table("roles")
    op.drop_table("subscriptions")
    op.drop_table("workspaces")
    op.drop_table("users")
