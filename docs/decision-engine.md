# Decision Engine

## Principle
Retrieval narrows. Rules score. LLM explains.

## Candidate scoring dimensions
- Required skills match
- Preferred skills match
- Years of relevant experience
- Industry/domain relevance
- Seniority fit
- Location / work-rights / availability
- Certifications
- Evidence quality / confidence

## Rules
- Missing required skill creates hard penalty
- Direct evidence beats inferred evidence
- Years of experience only counts when role-relevant
- "Not found" does not become a negative unless the role requires it

## Retrieval
- Embed normalized candidate summaries
- Embed role requirement summary
- Retrieve top K
- Rerank with rules

## Explanation
For each candidate:
- Overall fit score
- Top strengths
- Top risks
- Missing evidence
- Suggested interview probes
