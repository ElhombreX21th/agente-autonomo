# Publication-ready Upwork portfolio descriptions — 2026-10-31

These are THREE NEW independent projects using synthetic data. They should be **new portfolio cards**, not duplicate copies of the nine existing cards. Each uses a different workflow and screenshot from the complete offline package.

## 1. Field Service Dispatch Readiness & Compliance Gate

**Portfolio category:** Python automation / Medical equipment service operations

**Overview:** Built an interactive Python workflow that assesses whether a fictional technical service work order is ready for manual dispatch review. Checks authorization to access a site, technician training evidence, available spare parts, scheduling overlaps and site induction. The interface explains blocking issues and requires a human sign-off. Not a real dispatch controller.

**Skills:** Python, workflow automation, technical operations, exception handling, testing.

**Suggested screenshots:** `screenshots/dispatch-dashboard.png` and `screenshots/dispatch-blockers.png` in the downloadable package.

**What makes this different:** Proactive operational readiness checks, not a service SLA history dashboard or equipment event-log analysis.

## 2. Synthetic Laboratory Data Quality & Exception Reconciliation

**Portfolio category:** Python / Healthcare data validation

**Overview:** Developed a synthetic-data laboratory manifest QA workflow that compares expected case references to incoming result manifests. Detects unknown and missing cases, duplicate source IDs, mismatched panels and invalid record formats. Browser interface displays exceptions to be reviewed by a person. No identifiable patient data or clinical interpretation.

**Skills:** Python, CSV, data quality, validation, reconciliation, unit testing.

**Suggested screenshot:** `screenshots/lab-dashboard.png` in the downloadable package.

**What makes this different:** Controlled fictional laboratory record quality, not REST API synchronization or invoice/payment reconciliation.

## 3. Technical Pre-Sales Discovery & Follow-Up Planner

**Portfolio category:** Sales engineering / Workflow automation

**Overview:** Created a technical pre-sales qualification workspace that records fictional prospects' needs, decision-maker, budget, timeline and integration requirements. A deterministic Python rules engine suggests manual next steps and prevents outbound contact when permission is missing. No CRM writes or emails and no claims of measured conversion.

**Skills:** Python, technical sales, client discovery, customer success, workflow design.

**Suggested screenshots:** `screenshots/presales-dashboard.png` and `screenshots/presales-consent-gate.png` in the downloadable package.

**What makes this different:** B2B technical discovery, sales handoff and consent enforcement, not customer-support ticket triage.

## Reproducibility

Run `python -m unittest discover -s upwork_showcase_2026/tests -v` in the repository root. Seventeen unit tests were run locally on 2026-10-31. There is also a compact standalone [browser showcase](web/showcase.html).

**Integrity:** These are independent demonstrations, not completed client projects, revenue evidence, HIPAA compliance certifications or live medical devices. Do not add personal email addresses or off-platform contact details to Upwork cards or attachments before a contract.
