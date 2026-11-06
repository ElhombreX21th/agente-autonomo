# Commercial pilot boundary

## Demonstration acceptance criteria

Use fictional support requests in two workspaces. An authenticated operator submits a task, optionally requests an AI suggestion, reviews the stored plan and approves one permitted local tool. A viewer inspects results but cannot approve. A second workspace cannot read, cancel or approve the first workspace's task. Results, actor identifiers and events survive restart and export as JSON. Revoked credentials fail immediately. These boundaries are covered by automated tests.

AI suggestions require an explicitly configured HTTPS provider, model, credential, positive token rates and workspace budget. The provider response must match the restricted plan schema. Suggestions cannot execute actions. They bind to the workspace, subject and tool when a task is created. Failed or ambiguous requests retain their conservative reservation and are not silently retried. Provider billing accuracy and tokenization are external contracts: validate configured rates and reconcile real invoices before a paid pilot.

## Commercial hypotheses

Starter R$99/month; Professional R$299/month; Business R$999/month; Enterprise by agreement. These are hypotheses, not active offers or subscriptions. Current entitlements are the pilot's 1,000 stored tasks per workspace. The billing interface is disabled; checkout raises an error and cannot create a charge.

## Public and proprietary boundaries

Keep the educational core, fictional fixtures and demonstration documentation free of customer/private integration data. Isolate customer connectors, deployment secrets, support contracts and any proprietary service component from the public repository. No unrelated project or private customer information belongs here. Review contributor ownership before distribution. No repository license grant is invented by this change.

Dependency metadata is inventoried in DEPENDENCY_LICENSES.md. Metadata inspection is not a legal opinion: assess attribution, redistribution and hosted-service obligations for the actual distribution. Production readiness still requires customer identity lifecycle/SSO, infrastructure hardening, migration/backup testing, retention policy, rate limiting and operational support. This local pilot foundation is not a clinical system, production certification or evidence of paying customers.
