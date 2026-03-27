# Auth and Billing

## Authentication
Use Microsoft Entra External ID for external customer signup and login.

## Roles
- free
- pro
- team-admin
- team-member

## Free plan
- 1 active workspace
- 1 role at a time
- 20-30 resume parses per month
- No shortlist export
- No OneDrive integration
- Watermark on generated interview pack

## Pro plan
- Unlimited workspaces
- More monthly processing
- OneDrive integration
- Candidate compare
- Interview pack generation
- Export and history

## Team plan
- Shared workspaces
- Role-based access
- Usage visibility
- Admin dashboard

## Billing
Use Stripe subscriptions.
Server receives Stripe webhook events and updates entitlements.
Never trust client-side plan state.

## Notes
- Entra External ID: first 50,000 MAU at no cost
- Stripe webhook model for subscription lifecycle events
- Server-side entitlement enforcement is mandatory
