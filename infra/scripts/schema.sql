-- =============================================================
-- RoleFitAI — PostgreSQL Database Schema
-- =============================================================
-- Requires PostgreSQL 15+ with pgvector extension.
-- Run against a fresh database:
--   psql $DATABASE_URL -f schema.sql
-- =============================================================

-- ---------------------
-- Extensions
-- ---------------------

CREATE EXTENSION IF NOT EXISTS "pgcrypto";    -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "vector";      -- pgvector for embedding columns

-- =============================================================
-- TABLES
-- =============================================================

-- ---------------------
-- users
-- ---------------------

CREATE TABLE IF NOT EXISTS users (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT        NOT NULL UNIQUE,
    name        TEXT        NOT NULL,
    entra_id    TEXT        NOT NULL UNIQUE,   -- Azure Entra ID (sub claim)
    plan        VARCHAR(16) NOT NULL DEFAULT 'free'
                            CHECK (plan IN ('free', 'pro', 'team')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  users                IS 'Authenticated application users (provisioned on first Entra ID login).';
COMMENT ON COLUMN users.entra_id       IS 'Azure Entra ID object ID (oid claim from the JWT).';
COMMENT ON COLUMN users.plan           IS 'Active billing plan; overridden by subscriptions table when paid.';

-- ---------------------
-- workspaces
-- ---------------------

CREATE TABLE IF NOT EXISTS workspaces (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT        NOT NULL,
    owner_id    UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE workspaces IS 'Organisational unit that groups roles and members.';

-- ---------------------
-- roles
-- ---------------------

CREATE TABLE IF NOT EXISTS roles (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id        UUID        NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    title               TEXT        NOT NULL,
    description         TEXT,
    requirements_json   JSONB,                  -- structured requirements extracted by LLM
    status              VARCHAR(16) NOT NULL DEFAULT 'draft'
                                    CHECK (status IN ('draft', 'active', 'closed')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  roles                   IS 'A hiring role within a workspace.';
COMMENT ON COLUMN roles.requirements_json IS 'Structured requirements extracted from the JD (must-have, nice-to-have, skills, etc.).';

-- ---------------------
-- candidate_documents
-- Note: candidate_id is nullable — the document is uploaded before the
--       candidate record is created by the parsing pipeline.
-- ---------------------

CREATE TABLE IF NOT EXISTS candidate_documents (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id        UUID,                   -- FK added below after candidates table
    role_id             UUID        NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    filename            TEXT        NOT NULL,
    blob_url            TEXT        NOT NULL,
    file_type           TEXT        NOT NULL,   -- e.g. 'application/pdf'
    size_bytes          BIGINT      NOT NULL,
    uploaded_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    processing_status   VARCHAR(24) NOT NULL DEFAULT 'pending'
                                    CHECK (processing_status IN (
                                        'pending', 'processing', 'parsed', 'failed'
                                    ))
);

COMMENT ON TABLE  candidate_documents                   IS 'Raw uploaded documents (CV, resume, cover letter).';
COMMENT ON COLUMN candidate_documents.candidate_id      IS 'Populated after the async parsing pipeline creates the candidate record.';
COMMENT ON COLUMN candidate_documents.processing_status IS 'Lifecycle state of the background parsing job.';

-- ---------------------
-- candidates
-- ---------------------

CREATE TABLE IF NOT EXISTS candidates (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id         UUID        NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    document_id     UUID        REFERENCES candidate_documents(id) ON DELETE SET NULL,
    name            TEXT        NOT NULL,
    email           TEXT,
    raw_text        TEXT,                       -- full extracted text from the document
    structured_json JSONB,                      -- parsed fields (work history, education, skills…)
    embedding       vector(1536),               -- OpenAI text-embedding-3-small
    status          VARCHAR(16) NOT NULL DEFAULT 'parsed'
                                CHECK (status IN (
                                    'pending', 'parsed', 'scored', 'shortlisted', 'rejected'
                                )),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  candidates           IS 'Parsed candidate profiles linked to a role.';
COMMENT ON COLUMN candidates.embedding IS 'OpenAI text-embedding-3-small (1536 dims) of the candidate raw_text.';

-- Now that candidates exists, add the FK from candidate_documents
ALTER TABLE candidate_documents
    ADD CONSTRAINT fk_candidate_documents_candidate_id
    FOREIGN KEY (candidate_id)
    REFERENCES candidates(id)
    ON DELETE SET NULL;

-- ---------------------
-- candidate_scores
-- ---------------------

CREATE TABLE IF NOT EXISTS candidate_scores (
    id              UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id    UUID    NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    role_id         UUID    NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    overall_score   NUMERIC(5, 2) NOT NULL CHECK (overall_score BETWEEN 0 AND 100),
    factor_scores   JSONB   NOT NULL DEFAULT '[]',  -- ScoreFactor[]
    reasons         JSONB   NOT NULL DEFAULT '{}',
    strengths       TEXT[]  NOT NULL DEFAULT '{}',
    risks           TEXT[]  NOT NULL DEFAULT '{}',
    missing_evidence TEXT[] NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  candidate_scores              IS 'LLM-generated scores for a candidate against a specific role.';
COMMENT ON COLUMN candidate_scores.factor_scores IS 'Array of {name, score, weight, reason, confidence} objects.';

-- ---------------------
-- subscriptions
-- ---------------------

CREATE TABLE IF NOT EXISTS subscriptions (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID        NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    stripe_customer_id      TEXT        UNIQUE,
    stripe_subscription_id  TEXT        UNIQUE,
    plan                    VARCHAR(16) NOT NULL DEFAULT 'free'
                                        CHECK (plan IN ('free', 'pro', 'team')),
    status                  VARCHAR(16) NOT NULL DEFAULT 'active'
                                        CHECK (status IN (
                                            'active', 'past_due', 'canceled', 'trialing'
                                        )),
    current_period_end      TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE subscriptions IS 'Stripe billing subscriptions; one row per user.';

-- ---------------------
-- usage_events
-- ---------------------

CREATE TABLE IF NOT EXISTS usage_events (
    id              UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workspace_id    UUID    REFERENCES workspaces(id) ON DELETE SET NULL,
    event_type      TEXT    NOT NULL,   -- e.g. 'document_upload', 'candidate_score', 'export'
    quantity        INT     NOT NULL DEFAULT 1 CHECK (quantity > 0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  usage_events            IS 'Append-only log of billable or rate-limited actions.';
COMMENT ON COLUMN usage_events.event_type IS 'Enum-like string: document_upload | candidate_score | export | …';

-- =============================================================
-- INDEXES
-- =============================================================

-- users
CREATE INDEX IF NOT EXISTS idx_users_entra_id      ON users(entra_id);
CREATE INDEX IF NOT EXISTS idx_users_email         ON users(email);

-- workspaces
CREATE INDEX IF NOT EXISTS idx_workspaces_owner_id ON workspaces(owner_id);

-- roles
CREATE INDEX IF NOT EXISTS idx_roles_workspace_id  ON roles(workspace_id);
CREATE INDEX IF NOT EXISTS idx_roles_status        ON roles(status);

-- candidate_documents
CREATE INDEX IF NOT EXISTS idx_candidate_docs_role_id      ON candidate_documents(role_id);
CREATE INDEX IF NOT EXISTS idx_candidate_docs_candidate_id ON candidate_documents(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_docs_status       ON candidate_documents(processing_status);

-- candidates
CREATE INDEX IF NOT EXISTS idx_candidates_role_id     ON candidates(role_id);
CREATE INDEX IF NOT EXISTS idx_candidates_document_id ON candidates(document_id);
CREATE INDEX IF NOT EXISTS idx_candidates_status      ON candidates(status);

-- pgvector IVFFlat index for approximate nearest-neighbour search
-- lists = sqrt(row_count) is a common starting point; tune for your dataset size.
CREATE INDEX IF NOT EXISTS idx_candidates_embedding
    ON candidates
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- candidate_scores
CREATE INDEX IF NOT EXISTS idx_scores_candidate_id ON candidate_scores(candidate_id);
CREATE INDEX IF NOT EXISTS idx_scores_role_id      ON candidate_scores(role_id);

-- subscriptions
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id              ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_customer_id   ON subscriptions(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_sub_id        ON subscriptions(stripe_subscription_id);

-- usage_events
CREATE INDEX IF NOT EXISTS idx_usage_events_user_id      ON usage_events(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_events_workspace_id ON usage_events(workspace_id);
CREATE INDEX IF NOT EXISTS idx_usage_events_event_type   ON usage_events(event_type);
CREATE INDEX IF NOT EXISTS idx_usage_events_created_at   ON usage_events(created_at);

-- =============================================================
-- AUTO-UPDATE updated_at via trigger
-- =============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY ARRAY[
        'users', 'workspaces', 'roles', 'candidates',
        'candidate_documents', 'subscriptions'
    ]
    LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_%I_updated_at
             BEFORE UPDATE ON %I
             FOR EACH ROW EXECUTE FUNCTION set_updated_at();',
            tbl, tbl
        );
    END LOOP;
END;
$$;
