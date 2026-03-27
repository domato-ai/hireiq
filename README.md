# HireIQ

A production-grade hiring decision workspace for SMBs and recruiters.

## Stack

- **Frontend**: Next.js (App Router) → Azure Static Web Apps
- **Backend**: FastAPI → Azure App Service Linux
- **Database**: PostgreSQL Flexible Server + pgvector
- **Storage**: Azure Blob Storage
- **Auth**: Microsoft Entra External ID
- **Billing**: Stripe

## Local Development

### Prerequisites
- Node.js 20+
- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- pnpm

### Setup

```bash
# Install frontend dependencies
cd apps/web && pnpm install

# Install backend dependencies
cd apps/api && pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Run database migrations
cd apps/api && alembic upgrade head

# Start frontend (port 3000)
cd apps/web && pnpm dev

# Start backend (port 8000)
cd apps/api && uvicorn app.main:app --reload
```

## Project Structure

```
├── CLAUDE.md              # AI development guidelines
├── apps/
│   ├── web/               # Next.js frontend
│   └── api/               # FastAPI backend
├── packages/
│   ├── ui/                # Shared UI components
│   ├── types/             # Shared TypeScript types
│   ├── scoring/           # Candidate scoring engine
│   └── prompts/           # LLM prompt templates
├── infra/
│   ├── bicep/             # Azure infrastructure as code
│   └── scripts/           # Deployment scripts
├── tests/
│   ├── e2e/               # Playwright end-to-end tests
│   ├── integration/       # API integration tests
│   └── unit/              # Unit tests
└── docs/                  # Product and architecture docs
```
