# Autonomous Agent 3.0 — implementation

The standard-library core, CLI and independent demos are preserved. The FastAPI + SQLite service and connected browser workspace now provide persistent tasks, approval, idempotency, pending cancellation, exports and audit events. Workspace credentials add scoped access, revocation and MASTER/ADMINISTRATOR/USER roles. An optional HTTPS provider adds structured AI suggestions with persisted provenance, token/cost estimates and conservative spending reservations. The browser worker supports ordered multi-task workflows, login/logout, common form controls, extraction and screenshots, with exact-preview approval and mandatory human pause for CAPTCHA or anti-bot challenges. Billing remains disabled.

See [development instructions](DEVELOPMENT.md), [delivery status](ROADMAP.md), [commercial pilot](COMMERCIAL_PILOT.md), [delivery evidence](DELIVERY.md) and [the original architecture decision](adr/001-local-workflow.md). The original ADR records the first local increment; the current access/AI additions are described in ADR 002.

Live model validation, production deployment hardening, customer SSO, PostgreSQL migration and legal licensing remain separate from implemented/tested pilot capabilities. No production certification, paid customer outcome or active subscription is claimed.
