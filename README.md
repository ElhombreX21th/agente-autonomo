<div align="center">

![Autonomous Agent 3.0](docs/assets/autonomous-agent-hero-v4.svg)

# Autonomous Agent 3.0

**Workflows, under control.**

A Python-first automation project evolving toward a commercial AI agent platform for technical support, service operations and business workflows.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
![Stage](https://img.shields.io/badge/stage-prototype-334155)
![Execution](https://img.shields.io/badge/execution-approval--gated-0e7490)
![Commercial](https://img.shields.io/badge/commercial-pilot%20planning-7c3aed)

**[Get started](#quick-start) · [Product vision](#product-vision) · [Explore demos](#portfolio--demos) · [Architecture](#architecture) · [Commercial pilots](#commercial-pilots)**

</div>

---

## Review the request. Approve the work. Inspect the result.

For technical support and service operations teams exploring controlled automation: validate a task, choose an allowlisted local tool, explicitly approve execution, and inspect structured results. Start with the runnable prototype below; persistent workflows and a connected operator workspace are the next delivery milestones.

| CONTROL | VISIBILITY | EXTENSIBILITY |
| :--- | :--- | :--- |
| Explicit approval before local execution | Structured results and timestamped events | Small Python modules and tested operations demos |

## Why this project?

Many teams lose time switching between tickets, spreadsheets, operational checklists and disconnected tools. Autonomous Agent explores how to orchestrate these workflows with **explicit permissions, structured results and traceability**.

> **Current maturity:** This repository contains working *prototype components* and independent synthetic-data demonstrations. The v3 core is deterministic and **does not yet use an LLM or perform external autonomous actions**. It is not production-ready.

## What exists today

| Component | Capability | Status |
| --- | --- | --- |
| **Agent v3 core** | Allowlisted actions, explicit approval, task IDs and structured outputs | Runnable prototype |
| **Command-line interface** | Run approved checklist, summary and classification flows | Runnable prototype |
| **Audit trail** | Timestamped execution events | In-memory only |
| **Portfolio lab** | Ticket triage, resilient API sync and fictional MedTech event analysis | Independent demos |
| **Operations showcase** | Dispatch readiness, lab data quality and pre-sales discovery | Independent demos |
| **Web showcase** | Read-only local demonstration interface | Demo, not SaaS |

## Quick start

Requires **Python 3.10+**. The v3 prototype uses only Python's standard library.

```bash
git clone https://github.com/ElhombreX21th/agente-autonomo.git
cd agente-autonomo
git switch upgrade/autonomous-agent-v3

# Preview a task; execution requires explicit approval
python -m agent_v3.cli --task "Review a support ticket" --tool checklist

# Run an approved local deterministic workflow
python -m agent_v3.cli --task "Review an urgent support ticket" --tool classify --approve

# Run the new v3 regression tests
python -m unittest discover -s tests -p "test_agent_v3.py" -v
```

The v3 unit tests and CLI examples are verified locally. GitHub Actions is configured to run the full suites on changes to the core, demos, tests or workflow configuration; a remote CI result is not yet confirmed.

## Architecture

![Implemented deterministic execution architecture: validated task, allowlisted tool, explicit approval, structured result and transient audit](docs/assets/execution-architecture-v4.svg)

The diagram describes the implemented local core. An unapproved call returns a preview; an approved call is a separate execution with a new task ID. There is no durable pending-task approval or resume operation yet.

**Safety by design:** no unrestricted shell tool, no automatic outbound network actions, and no silent execution in the v3 core. Persistent audit storage, authentication and multi-tenant controls are future work.

## Portfolio & demos

### Python automation lab

Explore [portfolio_lab](portfolio_lab/README.md) for three independent demonstrations using fictional/synthetic inputs:

- **Support ticket triage:** assisted categorization with human review.
- **API synchronization:** resilient JSON synchronization backed by SQLite.
- **MedTech event analysis:** fictional event logs with cited fictional runbook entries.

```bash
python -m portfolio_lab.demo
python -m unittest discover -s tests -v
```

### Operations showcase

Explore [the showcase documentation](upwork_showcase_2026/README.md), [the web interface](upwork_showcase_2026/web/showcase.html) and the workflows:

| Demo | Business question |
| --- | --- |
| [Field Service Dispatch](upwork_showcase_2026/medtech_service_desk/logic.py) | Is a visit ready for dispatch? |
| [Laboratory Data Quality](upwork_showcase_2026/healthcare_data_quality/logic.py) | Which records require review? |
| [Technical Pre-Sales](upwork_showcase_2026/technical_presales_crm/logic.py) | What is the next qualified action? |

```bash
python -m unittest discover -s upwork_showcase_2026/tests -v
python -m upwork_showcase_2026.server
```

### Real interface, synthetic data

![Actual local operations showcase captured in Chromium using fictional data](docs/screenshots/operations-showcase-v4.png)

Actual browser capture of the read-only operations showcase. It is a separate working demo, not an agent execution dashboard. The [operator workspace illustration](docs/assets/autonomous-agent-dashboard.svg) remains a **design concept**.

## Roadmap

The [delivery roadmap](docs/ROADMAP.md) separates implemented capabilities from upcoming backend, dashboard, AI and SaaS work. See the [implementation and commercialization notes](docs/UPGRADE_V3.md) for pricing hypotheses and licensing considerations.

## Commercial pilots

**Target workflows:** support ticket operations, field-service coordination, operational checklists, data-quality review and internal reporting.

**Engagement model under evaluation:** tailored pilot projects, setup/integration services and eventual monthly subscriptions. No pricing, service-level guarantees, production deployments or customer outcomes are represented as established.

Interested in evaluating a pilot? [Open a GitHub discussion via an issue](https://github.com/ElhombreX21th/agente-autonomo/issues/new) describing a workflow and its constraints. **Do not include credentials, patient information or confidential business data.**

## Brand assets

The [hero](docs/assets/autonomous-agent-hero-v4.svg), [symbol](docs/assets/autonomous-agent-mark.svg) and [execution architecture](docs/assets/execution-architecture-v4.svg) use a consistent navy, cyan and violet palette. Versioned filenames avoid reusing older GitHub image-cache paths. Legacy concept assets are retained for existing links; they are not product screenshots.

## Security, license & limitations

- Synthetic demonstration data only; not a clinical decision-support product.
- Never commit API keys, client records or sensitive operational details.
- Review dependency licenses and code ownership before commercial distribution.
- **No open-source license has been declared here.** Public visibility alone does not grant reuse or redistribution rights.
- This repository is a prototype/portfolio, not evidence of paid customers or production certification.

---

<div align="center">

**AUTONOMOUS AGENT 3.0**

*Build workflows you can inspect, approve and improve.*

Maintained by [ElhombreX21th](https://github.com/ElhombreX21th)

</div>
