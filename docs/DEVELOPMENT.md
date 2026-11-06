# Development and pilot access

Use the existing checkout. Python 3.11+ is required; Python 3.12 was validated. The CLI and original portfolio demos remain compatible. Use fictional data only.

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

Direct dependencies are listed in requirements-api.txt/requirements-test.txt; requirements-lock.txt freezes the tested runtime/test resolution. Quality tools are separate in requirements-quality.txt. No secret is required for deterministic demos or the automated provider contract tests.

## Authenticated local pilot

```bash
# Provision an owner credential locally; it is shown once. Store it securely.
python -m agent_v3.manage provision --name "Synthetic Pilot"
# Then require credentials for workspace APIs:
AGENT_AUTH_REQUIRED=1 python -m uvicorn agent_v3.api:create_app --factory --host 127.0.0.1 --port 8787
```

Open the root workspace and enter the generated credential in Connect workspace. It stays in page memory, never browser persistent storage, and must be re-entered after reload. Do not share credentials. The offline management CLI is an administrator operation on the database; there is no public unauthenticated registration endpoint.

Use `python -m agent_v3.manage provision --name "Synthetic Pilot" --workspace WORKSPACE_ID --role viewer` to issue read-only access to an existing workspace, or `--role operator` to permit task creation/approval. Owner and operator both have workflow permissions; owner identity is reserved for future administration. Use `python -m agent_v3.manage revoke --key-id KEY_ID` to revoke immediately. Only a SHA-256 digest of each random 256-bit credential is stored. Events record public credential IDs, not raw credentials.

AGENT_DATABASE optionally selects the SQLite path (default .agent-v3/tasks.sqlite3). All commands must use the same path. Legacy tasks remain in the local demo workspace; they are not assigned to a new authenticated workspace. Omitting AGENT_AUTH_REQUIRED=1 intentionally enables the original unauthenticated loopback demo. Never use demo mode on a shared network.

## API

GET /health reports process liveness; GET /ready queries storage. /docs and /openapi.json include bearer authentication. /api/account reports workspace, role, entitlements, provider budget/usage and disabled billing state. /api/tasks returns the latest 100 scoped tasks. Creation requires an Idempotency-Key header and a subject/tool JSON body. Approval requires the exact stored plan_hash. Pending tasks can be cancelled. Task details and JSON exports include results, optional AI provenance and ordered events. Cross-workspace identifiers return 404; viewer writes return 403; revoked/missing required credentials return 401. Host/origin protections remain enabled.

## Optional real AI provider

Configure AGENT_LLM_URL to a trusted HTTPS OpenAI-compatible chat-completions endpoint, AGENT_LLM_MODEL, AGENT_LLM_API_KEY, AGENT_LLM_BUDGET_USD, AGENT_LLM_INPUT_USD_PER_MILLION and AGENT_LLM_OUTPUT_USD_PER_MILLION. Set secrets securely in environment settings; do not commit .env files or paste keys in chat. The app does not automatically read .env files. Values in .env.example are configuration names, not working credentials or validated pricing.

The AI button appears only for a writable authenticated credential with a fully configured provider. /api/interpret returns a restricted structured suggestion and stores usage/provenance. Task creation can bind suggestion_id to the same workspace, request text and tool. Suggestions do not execute actions. Every tool still needs approval of the stored task plan.

Spend accounting reserves a conservative serialized-input/output estimate before the network request. Reservations are workspace-scoped and transactional. Failures and ambiguous requests retain the reservation; there are no automatic paid retries. Reported input/output tokens and estimated USD cost are stored separately. Rates must match the selected provider/model. HTTP uses TLS verification, inherited proxy trust, no redirects and bounded connect/read timeouts. Only the known local tool names pass schema validation. Live-provider validation is unrun because no provider credential was configured in this environment. MockTransport tests verify the real adapter contract and rejection/budget paths without claiming paid inference.

## Browser, quality and security checks

```bash
python -m pip install -r requirements-quality.txt
ruff check --select E9,F63,F7,F82 agent_v3 tests scripts
mypy --check-untyped-defs --ignore-missing-imports agent_v3
pip-audit -r requirements-lock.txt --disable-pip --no-deps --progress-spinner off
# Install browser tooling separately if it is not already present:
npm install --prefix /tmp/agent-browser playwright@1.62.1
# Use CHROMIUM_PATH for a system Chromium, or install Playwright Chromium:
/tmp/agent-browser/node_modules/.bin/playwright install chromium
NODE_PATH=/tmp/agent-browser/node_modules python -m scripts.run_browser_smoke
```

The browser runner creates a temporary authenticated workspace/database and service, verifies submit → approve → result → JSON download → reconnect after reload → history → cancellation plus mobile overflow, then stops the service. Credentials remain in test-process memory and are not printed. Browser requests are forwarded to the real local HTTP server to accommodate managed Chromium navigation policy, without mocked API responses. GitHub Actions includes Python, quality and authenticated browser jobs; remote outcomes are separate from local results.

## Docker

```bash
docker compose up --build -d
docker compose exec agent python -m agent_v3.manage provision --name "Synthetic Pilot"
docker compose down
```

Compose binds only to loopback, requires credentials, drops capabilities and stores SQLite in a named volume. The image runs as UID 10001 and its Python base image is pinned by digest. In this managed cloud environment, build using `docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt -t autonomous-agent:v3 .` so pip trusts the session proxy without disabling TLS. On a standard host no custom CA secret is required. Live processes restart; volume data persists. Backups, migrations to PostgreSQL and multi-instance deployment still require dedicated validation.

## Limits

Workspace API credentials are a pilot identity foundation, not customer SSO or full account lifecycle. No live billing, external action connector, worker queue, in-flight interruption, automatic retries or production certification. Pending cancellation only. SQLite version-2 schema initialization is idempotent and rejects newer schema versions; a full migration/rollback framework is not implemented. Local audit rows are not tamper-proof. No full accessibility or penetration-test certification is claimed. The upstream Starlette/httpx TestClient deprecation warning remains; tests pass.
