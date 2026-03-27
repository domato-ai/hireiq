# HireIQ / CLAUDE.md

## Mission
Build a production-grade hiring decision workspace for SMBs and recruiters.
This is not a generic AI app.
The product must help users make better shortlist decisions quickly, with clear evidence.

## Product principles
- Evidence over vibes.
- Structured outputs over long prose.
- No fabricated candidate facts. If unknown, say "Not found".
- Deterministic scoring first, LLM explanation second.
- The first screen must be immediately useful. No landing page.
- Every screen must feel custom, intentional, and high-trust.
- Prefer compact, comparison-friendly layouts over chat-first layouts.

## UX rules
- Do not generate standard "AI SaaS" UI.
- Avoid default centered hero layouts.
- Avoid purple/indigo gradient aesthetics.
- Avoid generic cards everywhere.
- Design for dense information, excellent spacing, and strong hierarchy.
- Use typography, panel contrast, micro-motion, and evidence rails to create impact.
- The main action area should be visible without scrolling on desktop.

## Technical rules
- Frontend: Next.js (app router)
- Backend: FastAPI
- DB: PostgreSQL (Azure Flexible Server)
- File storage: Azure Blob Storage
- Auth: Microsoft Entra External ID
- Billing: Stripe
- Retrieval/search: start with pgvector in Postgres unless scale/relevance requires Azure AI Search
- Keep parsing, scoring, retrieval, and explanation as separate modules

## AI rules
- Never send all resumes to a large model.
- Parse once, structure once, embed once, reuse.
- Use LLMs only for:
  - extraction fallback
  - explanation
  - candidate comparison
  - interview question generation
  - recruiter summaries
- Always batch where possible.
- Cache structured candidate profiles and embeddings.

## Coding rules
- Plan before implementation for any non-trivial change.
- Prefer small, reviewable commits.
- Keep files focused.
- Write tests for scoring, parsing, auth guards, and billing logic.
- Never change environment or infrastructure files casually; explain why first.

## Delivery rules
For each meaningful feature:
1. Restate the goal
2. Inspect relevant files
3. Propose a short plan
4. Implement
5. Run tests/lint
6. Summarize changed files
7. Note risks / follow-ups

## Quality bar
The app should feel like a premium decision workstation, not a template.
When building UI, always apply the frontend-design skill and explain the design direction before coding.

## Cost discipline
- Never re-parse unchanged resumes
- Never regenerate embeddings for unchanged candidate records
- Cache role requirement summaries
- Retrieve top K before any expensive reasoning
- Keep prompt templates short and structured
- Prefer JSON outputs over prose
- Store normalized candidate facts and reason codes
- Use cheap models for extraction/classification where acceptable
- Use stronger models only for final comparison/explanation
