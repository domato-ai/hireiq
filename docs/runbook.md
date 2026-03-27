# Runbook

## Local development
- Web runs on localhost:3000
- API runs on localhost:8000
- Use Azurite or real dev storage account
- Use local Postgres; keep schema aligned with Azure Postgres

## Environments
- dev
- test
- prod

## Deployment rules
- Infra via Bicep
- App config via environment variables
- Secrets only in Azure Key Vault / platform config
- No manual prod schema changes

## Incident basics
- Check API health endpoint
- Check worker backlog
- Check storage access
- Check Stripe webhook health
- Check auth provider state
