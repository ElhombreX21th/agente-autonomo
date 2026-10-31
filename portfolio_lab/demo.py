"""Run all three demos offline: python -m portfolio_lab.demo"""
import json
from portfolio_lab.triage import Ticket, triage
from portfolio_lab.api_sync import connect, sync_pages
from portfolio_lab.medtech_copilot import analyze_events, retrieve_answer


def run_demo() -> dict:
    tickets = [Ticket("T-001", "Unreachable network gateway", "TCP connection refused after router restart", "partial"),
               Ticket("T-002", "Incorrect export", "CSV columns missing; duplicate rows", "none"),
               Ticket("T-003", "Unknown problem", "Please call", "stopped")]
    pages = {
        None: {"items": [{"id": "A-01", "updated_at": "2026-10-30T12:00:00Z", "amount": 10},
                         {"id": "A-02", "updated_at": "2026-10-30T12:00:00Z", "amount": 20}], "next_cursor": "page-2"},
        "page-2": {"items": [{"id": "A-02", "updated_at": "2026-10-31T12:00:00Z", "amount": 25}], "next_cursor": None},
    }
    events = [
        {"event_id": "EV-1", "asset_id": "SYNTHETIC-01", "timestamp": "2026-10-30T10:00:00Z", "code": "E-101"},
        {"event_id": "EV-2", "asset_id": "SYNTHETIC-01", "timestamp": "2026-10-30T11:00:00Z", "code": "E-101"},
        {"event_id": "EV-3", "asset_id": "SYNTHETIC-01", "timestamp": "2026-10-30T12:00:00Z", "code": "E-101"},
        {"event_id": "EV-4", "asset_id": "SYNTHETIC-02", "timestamp": "2026-10-30T12:00:00Z", "code": "E-205"},
    ]
    with connect() as conn:
        api_result = sync_pages(conn, lambda cursor: pages[cursor])
    return {"ticket_triage": [triage(t) for t in tickets],
            "api_sync": api_result,
            "medtech_log_findings": analyze_events(events),
            "medtech_runbook_answer": retrieve_answer("What does E-101 indicate?", events)}


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2, ensure_ascii=False))
