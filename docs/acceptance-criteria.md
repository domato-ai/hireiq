# Acceptance Criteria

## Role ingestion
- User can paste JD text or upload file
- System extracts role requirements
- User can edit extracted requirements before scoring begins

## Resume ingestion
- User can upload many files at once
- Duplicate files are detected
- Unsupported files fail gracefully
- Extracted text is reviewable for each candidate

## Shortlisting
- Role shows ranked candidate list
- Each score has factor breakdown
- User can sort/filter by factors
- User can compare selected candidates side-by-side

## Reliability
- Failures in one resume do not fail whole batch
- Retries are supported for parsing/embedding
- Every background job is traceable

## Billing
- Free-tier limits are enforced
- Upgrade path works
- Downgraded users lose premium actions without losing their data
