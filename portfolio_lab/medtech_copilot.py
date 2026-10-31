"""Vendor-neutral technical log review and evidence-linked runbook retrieval.

No clinical diagnosis, patient data or manufacturer-proprietary instructions.
Runbook and event records are fictional. Output needs trained human review.
"""
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import re

RUNBOOK = {
    "E-101": {
        "summary": "Synthetic example: repeated cooling-system alert.",
        "safe_next_step": "Confirm alert history and environment readings using approved procedures; refer to authorized technical support.",
        "source": "demo-runbook/E-101",
    },
    "E-205": {
        "summary": "Synthetic example: intermittent detector communication alert.",
        "safe_next_step": "Collect vendor-approved diagnostic logs and escalate for qualified technical assessment.",
        "source": "demo-runbook/E-205",
    },
    "E-330": {
        "summary": "Synthetic example: network handshake timeout.",
        "safe_next_step": "Review network event timestamps and approved connectivity checks, then escalate when unresolved.",
        "source": "demo-runbook/E-330",
    },
}


def _parse_event(event: dict) -> dict:
    for field in ("event_id", "asset_id", "timestamp", "code"):
        if not isinstance(event.get(field), str) or not event[field]:
            raise ValueError(f"Event missing {field}")
    if not re.fullmatch(r"E-\d{3}", event["code"]):
        raise ValueError("Event code must follow E-NNN pattern")
    dt = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timestamps must specify timezone")
    return {**event, "parsed_timestamp": dt.astimezone(timezone.utc)}


def analyze_events(events: list[dict], repeat_threshold: int = 3) -> dict:
    if repeat_threshold < 2:
        raise ValueError("repeat_threshold must be >=2")
    grouped = defaultdict(list)
    for raw in events:
        event = _parse_event(raw)
        grouped[(event["asset_id"], event["code"])].append(event)
    findings = []
    for (asset, code), rows in sorted(grouped.items()):
        times = sorted(row["parsed_timestamp"] for row in rows)
        recent = max((sum(t - timedelta(hours=24) <= other <= t for other in times)
                      for t in times), default=0)
        if recent >= repeat_threshold:
            reference = RUNBOOK.get(code)
            findings.append({
                "asset_id": asset, "code": code, "events_in_24h_window": recent,
                "event_ids": sorted(row["event_id"] for row in rows),
                "review_required": True,
                "evidence": reference["source"] if reference else "log-events-only",
                "interpretation": "Repeat-alert pattern; not a confirmed root cause",
            })
    return {"events_reviewed": len(events), "repeated_alert_findings": findings,
            "note": "Synthetic data only. Never use this demo for clinical or equipment safety decisions."}


def retrieve_answer(question: str, events: list[dict]) -> dict:
    """Grounded retrieval; not a generative model or a fault diagnosis."""
    if not question.strip():
        raise ValueError("Question is required")
    codes = sorted(set(re.findall(r"E-\d{3}", question.upper())))
    if not codes:
        return {"answer": "Provide an event code (for example E-101) for evidence-linked guidance.",
                "citations": [], "human_review_required": True}
    known = [code for code in codes if code in RUNBOOK]
    if not known:
        return {"answer": "No approved synthetic runbook entry for those codes.",
                "citations": [], "human_review_required": True}
    summaries = []
    citations = []
    for code in known:
        entry = RUNBOOK[code]
        count = sum(1 for item in events if item.get("code") == code)
        summaries.append(f"{code}: {entry['summary']} Seen {count} time(s) in provided events. "
                         f"Suggested review: {entry['safe_next_step']}")
        citations.append(entry["source"])
    return {"answer": " ".join(summaries), "citations": citations,
            "human_review_required": True, "generated_by": "deterministic_runbook_retrieval"}
