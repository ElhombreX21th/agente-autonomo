"""Local/pilot API with optional workspace credentials and scoped planning."""

import json
import logging
import os
from pathlib import Path
import sqlite3
from typing import Annotated, Literal

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .commercial import PILOT, DisabledBilling
from .planning import Planner, ProviderUnavailable
from .identity import Identity, IdentityStore
from .store import Conflict, Missing, Store

logger = logging.getLogger("agent_v3.api")


class TaskInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: str = Field(min_length=1, max_length=5000)
    tool: Literal["classify", "summarize", "checklist"] = "classify"
    suggestion_id: int | None = Field(default=None, ge=1, strict=True)

    @field_validator("subject")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Subject must not be blank")
        return value.strip()


class Approval(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


def create_app(database=None, auth_required=None, planner_factory=Planner):
    store = Store(database or os.getenv("AGENT_DATABASE", ".agent-v3/tasks.sqlite3"))
    identities = IdentityStore(store)
    planner = planner_factory(store)
    require_auth = (
        os.getenv("AGENT_AUTH_REQUIRED", "0") == "1"
        if auth_required is None
        else auth_required
    )
    app = FastAPI(
        title="Autonomous Agent 3.0 — Local Prototype",
        version="0.1.0",
        description="Scoped pilot workflows with optional structured AI suggestions. No external action tools or live billing.",
    )
    app.state.store = store
    app.state.identities = identities
    app.state.planner = planner
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "[::1]"]
    )

    @app.exception_handler(ProviderUnavailable)
    async def provider_unavailable(request: Request, exc: ProviderUnavailable):
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(Conflict)
    async def conflict(request: Request, exc: Conflict):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(Missing)
    async def missing(request: Request, exc: Missing):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(sqlite3.Error)
    async def unavailable(request: Request, exc: sqlite3.Error):
        logger.error("storage_unavailable", extra={"error_type": type(exc).__name__})
        return JSONResponse(status_code=503, content={"detail": "Storage unavailable"})

    @app.middleware("http")
    async def same_origin(request: Request, call_next):
        if request.url.path.startswith("/api/"):
            header = request.headers.get("authorization", "")
            identity = (
                identities.authenticate(header[7:])
                if header.startswith("Bearer ")
                else None
            )
            if identity is None and (require_auth or header):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Valid workspace credential required"},
                )
            request.state.identity = identity or Identity("local", "master", "local")
        # Local services still need protection from cross-site browser writes.
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            origin = request.headers.get("origin")
            if request.headers.get("sec-fetch-site") == "cross-site" or (
                origin is not None and origin != str(request.base_url).rstrip("/")
            ):
                return JSONResponse(
                    status_code=403, content={"detail": "Cross-site write rejected"}
                )
        response = await call_next(request)
        logger.info(
            json.dumps(
                {
                    "event": "request_completed",
                    "method": request.method,
                    "status": response.status_code,
                }
            )
        )
        return response

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": "controlled_pilot_prototype"}

    @app.get("/ready")
    def ready():
        store.ready()
        return {"status": "ready"}

    @app.get("/api/account")
    def account(request: Request):
        identity = request.state.identity
        return {
            "workspace": identity.workspace,
            "role": identity.role,
            "authentication_required": bool(require_auth),
            "entitlements": {
                "plan": PILOT.plan,
                "max_stored_tasks": PILOT.max_stored_tasks,
            },
            "usage": planner.usage(identity.workspace),
            "billing": DisabledBilling().status(identity.workspace),
        }

    @app.post("/api/interpret")
    def interpret(data: TaskInput, request: Request):
        # Provider use always requires an authenticated, writable workspace credential,
        # even when the rest of the app is in local demo mode.
        if request.state.identity.key_id == "local":
            raise HTTPException(
                403, "Provider use requires an authenticated workspace credential"
            )
        if request.state.identity.role not in {"master", "administrator"}:
            raise HTTPException(
                403, "AI planning requires MASTER or ADMINISTRATOR access"
            )
        return planner.suggest(data.subject, request.state.identity.workspace)

    @app.get("/api/tasks")
    def tasks(request: Request):
        return store.list(request.state.identity.workspace)

    @app.post("/api/tasks")
    def create(
        request: Request,
        data: TaskInput,
        idempotency_key: Annotated[str, Header(min_length=1, max_length=128)],
    ):
        if not idempotency_key.strip():
            raise HTTPException(422, "Idempotency-Key must not be blank")
        return store.create(
            data.subject,
            data.tool,
            idempotency_key,
            request.state.identity.workspace,
            request.state.identity.key_id,
            data.suggestion_id,
        )

    @app.get("/api/tasks/{task_id}")
    def task(task_id: str, request: Request):
        return store.get(task_id, request.state.identity.workspace)

    @app.post("/api/tasks/{task_id}/approve")
    def approve(task_id: str, data: Approval, request: Request):
        if request.state.identity.role not in {"master", "administrator"}:
            raise HTTPException(403, "Approval requires MASTER or ADMINISTRATOR access")
        return store.approve(
            task_id,
            data.plan_hash,
            request.state.identity.workspace,
            request.state.identity.key_id,
        )

    @app.post("/api/tasks/{task_id}/cancel")
    def cancel(task_id: str, request: Request):
        if request.state.identity.role not in {"master", "administrator"}:
            raise HTTPException(
                403, "Cancellation requires MASTER or ADMINISTRATOR access"
            )
        return store.cancel(
            task_id, request.state.identity.workspace, request.state.identity.key_id
        )

    @app.get("/")
    def workspace():
        return FileResponse(Path(__file__).parent / "web" / "index.html")

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})[
        "WorkspaceCredential"
    ] = {
        "type": "http",
        "scheme": "bearer",
        "description": "Revocable workspace credential; required when AGENT_AUTH_REQUIRED=1. Always required for AI suggestions.",
    }
    for path, methods in schema["paths"].items():
        if path.startswith("/api/"):
            for operation in methods.values():
                operation["security"] = [{"WorkspaceCredential": []}]
    app.openapi_schema = schema
    return app
