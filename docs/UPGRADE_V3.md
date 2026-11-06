# Autonomous Agent 3.0 — implementation and commercialization

## What is implemented
The original standard-library core and CLI remain intact. A local FastAPI + SQLite service and connected browser workspace now add stored tasks, plan-bound approval, idempotency, pending cancellation, result export and persistent execution events. No LLM, external action connector, authentication, tenant isolation or paid billing is implemented. See [development instructions](DEVELOPMENT.md), [roadmap](ROADMAP.md) and [architecture decision](adr/001-local-workflow.md).

## Verify
```bash
python -m unittest discover -s tests -p 'test_agent_v3.py' -v
python -m agent_v3.cli --task "Review an urgent ticket" --tool classify --approve
python -m agent_v3.cli --task "Prepare a checklist"
```

## Remaining roadmap
1. Add migration tooling and authenticated audit attribution; evaluate PostgreSQL for shared deployment.
2. Add authentication, RBAC and tenant isolation to the existing local FastAPI endpoints.
3. Add pluggable LLM providers with structured outputs, evaluation and budget limits.
4. Introduce tool permissions, secrets management, rate limiting, idempotency and human review.
5. Extend the connected local dashboard after authorization contracts; add integrations and secure deployment.
6. Pilot with real users before enabling billing.

## Commercial packaging (hypotheses)
Starter R$99/month; Professional R$299/month; Business R$999/month; Enterprise custom. These are unvalidated pricing hypotheses, not active subscriptions.

## Licensing and IP
Do not assume the public repository is open-source licensed. Choose a license and verify ownership of all contributions before selling or distributing. Keep customer data, credentials, private integrations and commercial-only code out of public commits.

## Product claims
This is a prototype. Do not market it as a production-ready autonomous AI agent, a certified healthcare solution, or a system with paying customers.
