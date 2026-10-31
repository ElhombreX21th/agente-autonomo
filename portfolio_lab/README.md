# Python, AI automation and MedTech — three runnable demonstrations

> **Status:** Independent demonstration only. No paid customer deployment, clinical use, confirmed maintenance diagnosis or measured business return is claimed. All sample data and event codes are fictional. The ML classifier uses only 12 synthetic training examples; its numerical score is not a calibrated correctness probability.

**Reproduce locally** from the root of this repository with Python 3.10+ (no external package needed):

```bash
python -m portfolio_lab.demo
python -m unittest discover -s tests -v
```

| Demo | Problem addressed | Evidence in code |
|---|---|---|
| [AI-Assisted Support Ticket Triage](triage.py) | Inconsistent support queue routing | Offline Naive Bayes classification, P1/P2/P3 priority, human review for low confidence or critical impact |
| [Resumable REST API Data Sync](api_sync.py) | Duplicates and lost progress in paginated feeds | SQLite atomic checkpoint per page, idempotent upsert, input checks, optional authorized HTTPS adapter |
| [MedTech Event Log Analytics](medtech_copilot.py) | Hard-to-review recurring technical events | Fictional event analysis, 24h repeat detection, source-linked synthetic runbook, human-review-only next steps |

**Runnable output:** [demo.py](demo.py). **Automated checks:** [tests/test_portfolio_lab.py](../tests/test_portfolio_lab.py) (13 tests passed locally on October 31, 2026). **Upwork-ready writeups:** [UPWORK_PORTFOLIO.md](UPWORK_PORTFOLIO.md).

## Key limitations

- Naive Bayes demo trained on a tiny synthetic dataset: not evaluated on real data, not ready for production.
- API HTTPS adapter is opt-in and has not been exercised against a third-party API. Date ordering assumes comparable normalized timestamp strings.
- The MedTech runbook is fictional and retrieval-based, **not generative AI**. It cannot verify failures, diagnose equipment or recommend unapproved interventions.
- Never upload patient data, confidential employer/customer logs, access tokens or proprietary repair instructions.

**Positioning:** Python automation and practical AI-assisted workflows supported by 13+ years of real field-service/MedTech troubleshooting, with software demonstrations accurately identified as independent projects.
