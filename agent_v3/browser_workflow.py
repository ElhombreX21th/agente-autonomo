"""Validated browser workflows with explicit preview and write approval boundaries."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BrowserStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal[
        "goto",
        "fill",
        "click",
        "select",
        "check",
        "wait_for",
        "extract",
        "screenshot",
        "human_challenge",
        "logout",
    ]
    selector: str | None = Field(default=None, max_length=500)
    value: str | None = Field(default=None, max_length=5000)
    secret_env: str | None = Field(default=None, pattern=r"^[A-Z][A-Z0-9_]{2,80}$")
    label: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def validate_action_fields(self):
        if self.action == "goto":
            if not self.value or self.selector or self.secret_env:
                raise ValueError("goto requires only a URL value")
        elif self.action in {"fill", "select"}:
            if not self.selector or (self.value is None) == (self.secret_env is None):
                raise ValueError(
                    f"{self.action} requires a selector and exactly one value source"
                )
        elif self.action in {"click", "check", "wait_for", "extract", "logout"}:
            if not self.selector or self.value is not None or self.secret_env:
                raise ValueError(f"{self.action} requires only a selector")
        elif self.action == "screenshot":
            if not self.value or self.selector or self.secret_env:
                raise ValueError("screenshot requires only a relative output path")
            path = Path(self.value)
            if (
                path.is_absolute()
                or ".." in path.parts
                or path.suffix.lower() != ".png"
            ):
                raise ValueError("screenshot must be a relative PNG path")
        elif self.action == "human_challenge":
            if self.selector or self.secret_env:
                raise ValueError("human_challenge accepts only an optional instruction")
        return self


class BrowserWorkflow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    allowed_hosts: list[str] = Field(min_length=1, max_length=20)
    steps: list[BrowserStep] = Field(min_length=1, max_length=100)

    @field_validator("allowed_hosts")
    @classmethod
    def valid_hosts(cls, hosts):
        clean = []
        for host in hosts:
            candidate = host.strip().lower()
            if (
                not candidate
                or "/" in candidate
                or ":" in candidate
                or candidate.startswith(".")
            ):
                raise ValueError("allowed_hosts must contain DNS hostnames only")
            clean.append(candidate)
        if len(set(clean)) != len(clean):
            raise ValueError("allowed_hosts must be unique")
        return clean

    @model_validator(mode="after")
    def validate_urls(self):
        allowed = set(self.allowed_hosts)
        for step in self.steps:
            if step.action != "goto":
                continue
            parsed = urlparse(step.value or "")
            if parsed.scheme not in {"https", "http"} or not parsed.hostname:
                raise ValueError("goto requires an HTTP(S) URL")
            if parsed.hostname.lower() not in allowed:
                raise ValueError("goto host is outside the workflow allowlist")
            if parsed.username or parsed.password:
                raise ValueError("credentials cannot be embedded in URLs")
            if parsed.scheme == "http" and parsed.hostname not in {
                "127.0.0.1",
                "localhost",
            }:
                raise ValueError("external navigation requires HTTPS")
        return self

    def canonical(self) -> str:
        return self.model_dump_json(exclude_none=True)

    def digest(self) -> str:
        return hashlib.sha256(self.canonical().encode()).hexdigest()

    def preview(self) -> dict[str, Any]:
        writes = []
        for index, step in enumerate(self.steps):
            if step.action in {"fill", "select", "check", "click", "logout"}:
                writes.append(
                    {
                        "step": index + 1,
                        "action": step.action,
                        "target": step.label or step.selector,
                        "value": "[secret]" if step.secret_env else step.value,
                    }
                )
        return {
            "workflow": self.name,
            "digest": self.digest(),
            "allowed_hosts": self.allowed_hosts,
            "steps": len(self.steps),
            "write_actions": writes,
            "human_challenge_policy": "pause_for_user",
            "approval_required": bool(writes),
        }


@dataclass(frozen=True)
class BrowserApproval:
    workflow_digest: str
    role: Literal["master", "administrator", "user"]

    def authorize(self, workflow: BrowserWorkflow):
        if self.role not in {"master", "administrator"}:
            raise PermissionError(
                "Browser writes require MASTER or ADMINISTRATOR access"
            )
        if self.workflow_digest != workflow.digest():
            raise PermissionError("Approval does not match the exact browser workflow")


def write_runner_request(
    workflow: BrowserWorkflow,
    output: Path,
    *,
    approval: BrowserApproval | None = None,
):
    preview = workflow.preview()
    if preview["approval_required"]:
        if approval is None:
            raise PermissionError("Browser write actions require preview approval")
        approval.authorize(workflow)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(workflow.model_dump(exclude_none=True), indent=2))
