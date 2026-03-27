# Architecture

## Frontend
- Next.js app
- App router
- Server actions only where appropriate
- Strong client-side upload UX
- Premium data-dense UI

## Backend
- FastAPI
- REST APIs first
- Async background jobs for parsing, embeddings, ranking
- Webhook endpoint for Stripe

## Data stores
- PostgreSQL for app data
- pgvector for initial semantic retrieval
- Blob Storage for raw files and parsed artifacts
- Optional Azure AI Search later for hybrid retrieval

## Processing pipeline
1. Ingest file
2. Extract text
3. Normalize document
4. Build candidate JSON
5. Build embeddings
6. Retrieval against role requirements
7. Deterministic scoring
8. Explanation generation
9. Persist results

## Security
- All file access server-mediated
- Signed URLs where needed
- Server-side entitlement checks
- Audit log for billing / exports / integrations
