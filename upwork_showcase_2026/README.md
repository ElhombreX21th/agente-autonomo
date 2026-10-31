# MedTech Operations — Three Independent Portfolio Projects

**Status:** Runnable independent demonstrations, built 2026-10-31. All data are fictional. None is a paid customer deployment, production medical software, medical diagnosis, HIPAA-certified solution or automated contacting system.

## Three distinct, nonduplicate projects

1. **Field Service Dispatch Readiness & Compliance Gate** — checks technician readiness, training, site access, available parts, and scheduling conflicts before a human dispatch decision. [Python rules](medtech_service_desk/logic.py). Different from the existing service SLA dashboard and log analyzer: operational authorization checks, not historical reporting or device diagnosis.
2. **Synthetic Laboratory Data Quality & Exception Reconciliation** — validates fictional report manifests, detects duplicate source references, incorrect panels, unknown IDs and missing reports. [Python rules](healthcare_data_quality/logic.py). Different from API sync and payment reconciliation: domain-specific controlled schema and laboratory exception rules.
3. **Technical Pre-Sales Discovery & Follow-Up Planner** — scores completeness of technical discovery (problem, decision maker, budget, timing, constraints) and blocks outreach without permission. [Python rules](technical_presales_crm/logic.py). Different from support-ticket triage: sales discovery and consent checks, not incident management.

## Local project bundle

A complete local project bundle contains browser-based interfaces, screenshots, read-only API server and **17 passing unit tests**, available as a ZIP attachment through the conversation. Those interface/screenshots are not yet mirrored to GitHub or Upwork.

Run from the directory above the project:
```bash
python -m unittest discover -s upwork_showcase_2026/tests -v
python -m upwork_showcase_2026.server
```

Only synthetic examples. No real patients, private device logs, proprietary customer information, production access or customer outcome claims.
