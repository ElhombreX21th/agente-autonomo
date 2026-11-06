"""Sequential multi-workflow orchestration over the validated Playwright worker."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Iterable

from .browser_workflow import BrowserApproval, BrowserWorkflow, write_runner_request


@dataclass(frozen=True)
class BrowserRun:
    workflow: str
    status: str
    output_dir: str
    returncode: int


def run_batch(
    workflows: Iterable[BrowserWorkflow],
    approvals: dict[str, BrowserApproval],
    output_root: Path,
    *,
    environment: dict[str, str] | None = None,
    node_path: str = "node",
) -> list[BrowserRun]:
    """Run workflows in order and stop when a site requests human verification."""
    root = Path(__file__).resolve().parents[1]
    worker = root / "scripts" / "browser_worker.cjs"
    output_root.mkdir(parents=True, exist_ok=True)
    results = []
    for index, workflow in enumerate(workflows, start=1):
        run_dir = output_root / f"{index:03d}-{workflow.digest()[:12]}"
        run_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as temporary:
            request = Path(temporary) / "workflow.json"
            write_runner_request(
                workflow,
                request,
                approval=approvals.get(workflow.digest()),
            )
            completed = subprocess.run(
                [node_path, str(worker), str(request), str(run_dir)],
                cwd=root,
                env={**os.environ, **(environment or {})},
                check=False,
                timeout=180,
            )
        status = "failed"
        result_path = run_dir / "result.json"
        challenge_path = run_dir / "human-action-required.json"
        if completed.returncode == 0 and result_path.exists():
            status = json.loads(result_path.read_text())["status"]
        elif completed.returncode == 20 and challenge_path.exists():
            status = "human_action_required"
        results.append(
            BrowserRun(workflow.name, status, str(run_dir), completed.returncode)
        )
        if status == "human_action_required":
            break
        if status != "completed":
            break
    return results
