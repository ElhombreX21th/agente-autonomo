"""Single-user local API. Not an authenticated or multi-tenant service."""
import json
import logging
import os
from pathlib import Path
import sqlite3
from typing import Annotated, Literal

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .store import Conflict, Missing, Store

logger = logging.getLogger('agent_v3.api')


class TaskInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    subject: str = Field(min_length=1, max_length=5000)
    tool: Literal['classify', 'summarize', 'checklist'] = 'classify'

    @field_validator('subject')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Subject must not be blank')
        return value.strip()


class Approval(BaseModel):
    model_config = ConfigDict(extra='forbid')
    plan_hash: str = Field(pattern=r'^[0-9a-f]{64}$')


def create_app(database=None):
    store = Store(database or os.getenv('AGENT_DATABASE', '.agent-v3/tasks.sqlite3'))
    app = FastAPI(title='Autonomous Agent 3.0 — Local Prototype', version='0.1.0',
                  description='Deterministic local tools. No LLM, authentication or external actions.')
    app.state.store = store
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost', '127.0.0.1', '[::1]'])

    @app.exception_handler(Conflict)
    async def conflict(request: Request, exc: Conflict):
        return JSONResponse(status_code=409, content={'detail': str(exc)})

    @app.exception_handler(Missing)
    async def missing(request: Request, exc: Missing):
        return JSONResponse(status_code=404, content={'detail': str(exc)})

    @app.exception_handler(sqlite3.Error)
    async def unavailable(request: Request, exc: sqlite3.Error):
        logger.error('storage_unavailable', extra={'error_type': type(exc).__name__})
        return JSONResponse(status_code=503, content={'detail': 'Storage unavailable'})

    @app.middleware('http')
    async def same_origin(request: Request, call_next):
        # Local services still need protection from cross-site browser writes.
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            origin = request.headers.get('origin')
            if request.headers.get('sec-fetch-site') == 'cross-site' or (
                origin is not None and origin != str(request.base_url).rstrip('/')
            ):
                return JSONResponse(status_code=403, content={'detail': 'Cross-site write rejected'})
        response = await call_next(request)
        logger.info(json.dumps({'event': 'request_completed', 'method': request.method,
                               'status': response.status_code}))
        return response

    @app.get('/health')
    def health():
        return {'status': 'ok', 'mode': 'deterministic_local_prototype'}

    @app.get('/ready')
    def ready():
        store.ready()
        return {'status': 'ready'}

    @app.get('/api/tasks')
    def tasks():
        return store.list()

    @app.post('/api/tasks')
    def create(data: TaskInput, idempotency_key: Annotated[str, Header(min_length=1, max_length=128)]):
        if not idempotency_key.strip():
            raise HTTPException(422, 'Idempotency-Key must not be blank')
        return store.create(data.subject, data.tool, idempotency_key)

    @app.get('/api/tasks/{task_id}')
    def task(task_id: str):
        return store.get(task_id)

    @app.post('/api/tasks/{task_id}/approve')
    def approve(task_id: str, data: Approval):
        return store.approve(task_id, data.plan_hash)

    @app.post('/api/tasks/{task_id}/cancel')
    def cancel(task_id: str):
        return store.cancel(task_id)

    @app.get('/')
    def workspace():
        return FileResponse(Path(__file__).parent / 'web' / 'index.html')

    return app
