# Local development

Use the existing checkout. Python 3.11+ is required for the API; Python 3.12 was validated. No worktree is needed. Do not use real support records or patient/customer data.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m pip check
python -m unittest discover -s tests -v
python -m unittest discover -s upwork_showcase_2026/tests -v
python scripts/check_showcase_js.py
python -m portfolio_lab.demo
```

The lock file freezes the API/test dependency resolution. requirements-api.txt and requirements-test.txt identify direct dependencies. Refresh the lock intentionally in an isolated environment and rerun tests. No provider credential is required. API tests use temporary databases, cover concurrent approvals and preserve the original demo tests.

## Local server

```bash
# Optional path override; defaults to .agent-v3/tasks.sqlite3 under the current directory
export AGENT_DATABASE=.agent-v3/tasks.sqlite3
python -m uvicorn agent_v3.api:create_app --factory --host 127.0.0.1 --port 8787
```

GET /health returns liveness. GET /ready queries storage. Open the root workspace, submit a fictional request, inspect the stored plan and approve it. /docs is interactive OpenAPI documentation; /openapi.json is the machine-readable schema. Do not bind this unauthenticated service to a public interface.

POST /api/tasks requires an Idempotency-Key header and JSON containing subject and tool (classify, summarize or checklist). GET /api/tasks returns the latest 100 tasks; GET /api/tasks/{id} includes results and ordered events. POST /api/tasks/{id}/approve requires the exact plan_hash. POST /api/tasks/{id}/cancel cancels only pending tasks. Replaying the same request/approval is safe; conflicting keys, mismatched plans and invalid transitions return 409. Invalid inputs return 422; missing tasks return 404. Cross-site browser writes return 403 and unexpected hosts return 400. Storage errors return 503 without exposing internal details.

## Browser smoke test

The smoke test requires Node.js, Playwright and Chromium. In the managed cloud environment they were already available. Elsewhere install Playwright in a temporary location, keeping its dependencies out of the Python application:

```bash
npm install --prefix /tmp/agent-browser playwright@1.62.1
# Set CHROMIUM_PATH to your installed Chromium binary if needed.
# Start the API in another terminal with a fresh temporary database first:
AGENT_DATABASE=/tmp/agent-browser.sqlite3 python -m uvicorn agent_v3.api:create_app --factory --host 127.0.0.1 --port 8787
# From the repository root:
NODE_PATH=/tmp/agent-browser/node_modules node scripts/smoke_agent_browser.cjs
```

The test creates fictional tasks, approves one, checks a result and downloaded JSON, reloads history, cancels another, and checks mobile overflow. It writes a screenshot to /tmp/agent-workspace.png. It intentionally leaves synthetic records in the selected test database. Use a temporary database, not an existing operator database. Browser requests are forwarded to the real local API through Playwright routing to accommodate managed Chromium navigation policy. It does not mock API responses. External operations and live AI providers are untested because none are enabled.

## Current limits

No authentication, tenants, PostgreSQL migrations, worker queue, LLM, usage budgets or live billing. No Docker deployment, vulnerability scan, full accessibility audit or production security certification is claimed in this increment. TestClient currently emits an upstream httpx deprecation warning; tests pass. API storage is a local prototype and must not store confidential data.
