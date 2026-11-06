"""Safe, deterministic agent MVP; no external side effects."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid

ALLOWED_TOOLS = {"summarize", "classify", "checklist"}


@dataclass
class Result:
    task_id: str
    status: str
    output: dict[str, Any]
    audit: list[dict[str, str]] = field(default_factory=list)


def execute(task: str, tool: str = "checklist", approved: bool = False) -> Result:
    if not isinstance(task, str) or not task.strip():
        raise ValueError("Task must be non-empty")
    if len(task) > 5000:
        raise ValueError("Task exceeds 5000 characters")
    if tool not in ALLOWED_TOOLS:
        raise ValueError("Tool not allowed")
    task = task.strip()
    task_id = str(uuid.uuid4())
    audit = [{"at": datetime.now(timezone.utc).isoformat(), "event": "task_received"}]
    if not approved:
        audit.append(
            {"at": datetime.now(timezone.utc).isoformat(), "event": "awaiting_approval"}
        )
        return Result(
            task_id, "approval_required", {"tool": tool, "preview": task[:160]}, audit
        )
    output: dict[str, Any]
    if tool == "summarize":
        output = {"summary": task[:300] + ("…" if len(task) > 300 else "")}
    elif tool == "classify":
        low = task.lower()
        category = (
            "urgent"
            if any(x in low for x in ("urgent", "critical", "crítico", "urgente"))
            else "standard"
        )
        output = {"category": category, "review_required": True}
    else:
        output = {
            "steps": [
                "Review the task",
                "Confirm scope and constraints",
                "Perform approved work",
                "Verify and record outcome",
            ],
            "subject": task[:160],
        }
    audit.append({"at": datetime.now(timezone.utc).isoformat(), "event": "completed"})
    return Result(task_id, "completed", output, audit)
