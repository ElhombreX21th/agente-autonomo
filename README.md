# Autonomous Agent

Study project for structuring a local assistant with planning, memory, and task-oriented execution flow.

Status: early-stage repository. This documentation defines the project proposal and the recommended technical direction for future development.

## Screenshots

### Console Preview

![Agent console preview](docs/screenshots/agent-console-preview.svg)

### Workflow Overview

![Agent workflow overview](docs/screenshots/agent-workflow-overview.svg)

## Objective

Build an organized foundation for an assistant that can receive a task, split it into steps, consult memory/context, and return a clear response to the user.

## Concepts Demonstrated

- Task planning
- Local context memory
- Modular organization
- Controlled decision flow
- Technical documentation for future development
- Preparation for automated tests

## Suggested Stack

- Python 3.10+
- FastAPI or Python CLI
- JSON or SQLite for local memory
- pytest for automated tests
- GitHub Actions for continuous validation

## Recommended Structure

```text
autonomous-agent/
├── app/
│   ├── agent.py
│   ├── planner.py
│   ├── memory.py
│   ├── tools.py
│   └── cli.py
├── tests/
│   └── test_agent.py
├── docs/
│   └── screenshots/
└── README.md
```

## Roadmap

- [ ] Create the base project structure
- [ ] Implement the initial CLI
- [ ] Create the planning module
- [ ] Create simple local memory
- [ ] Add automated tests
- [ ] Create a FastAPI API
- [ ] Add logs and validations
- [ ] Prepare a demonstrable portfolio version

## Future Local Execution

When the codebase is implemented, local execution should follow a flow similar to:

```bash
python -m app.cli
```

Tests:

```bash
pytest
```

## Portfolio Value

This project can demonstrate AI assistant architecture, software organization, separation of responsibilities, testing, and documentation. To make it stronger for interviews, the next step is to implement a small but complete functional MVP.

## Author

Created by ElhombreX21th.


## Runnable Python, AI automation and MedTech portfolio lab (2026)

Three independent synthetic-data demonstrations are available at [portfolio_lab](portfolio_lab/README.md): support-ticket ML triage with human review, resilient JSON API synchronization using SQLite, and MedTech event-log analysis with cited fictional runbook entries. Run `python -m portfolio_lab.demo` and `python -m unittest discover -s tests -v` from the repository root. **13 tests passed locally (2026-10-31).** These are not paid client or production implementations.
