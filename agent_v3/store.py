"""Transactional storage for local deterministic workflows; no remote side effects."""

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid

from .core import execute
from .commercial import PILOT


class Conflict(Exception):
    pass


class Missing(Exception):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            if db.execute("PRAGMA user_version").fetchone()[0] > 2:
                raise ValueError("Database schema is newer than this application")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL,
                    fingerprint TEXT NOT NULL, subject TEXT NOT NULL, tool TEXT NOT NULL,
                    status TEXT NOT NULL, plan_hash TEXT NOT NULL, result TEXT,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL REFERENCES tasks(id),
                    at TEXT NOT NULL, event TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS task_scopes (
                    task_id TEXT PRIMARY KEY REFERENCES tasks(id), workspace TEXT NOT NULL
                );
                INSERT OR IGNORE INTO task_scopes SELECT id, 'local' FROM tasks;
                CREATE TABLE IF NOT EXISTS task_advice (
                    task_id TEXT PRIMARY KEY REFERENCES tasks(id),
                    suggestion_id INTEGER NOT NULL, plan TEXT NOT NULL
                );
                PRAGMA user_version = 2;
            """)
            if "actor" not in {r[1] for r in db.execute("PRAGMA table_info(events)")}:
                db.execute(
                    "ALTER TABLE events ADD COLUMN actor TEXT NOT NULL DEFAULT 'local'"
                )

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def event(db, task_id, name, actor="local"):
        db.execute(
            "INSERT INTO events(task_id, at, event, actor) VALUES (?,?,?,?)",
            (task_id, now(), name, actor),
        )

    @staticmethod
    def row(db, task_id, workspace="local"):
        row = db.execute(
            "SELECT t.* FROM tasks t JOIN task_scopes s ON t.id=s.task_id "
            "WHERE t.id=? AND s.workspace=?",
            (task_id, workspace),
        ).fetchone()
        if row is None:
            raise Missing("Task not found")
        result = dict(row)
        result.pop("request_key")
        result.pop("fingerprint")
        result["result"] = json.loads(result["result"]) if result["result"] else None
        result["events"] = [
            dict(e)
            for e in db.execute(
                "SELECT seq,at,event,actor FROM events WHERE task_id=? ORDER BY seq",
                (task_id,),
            )
        ]
        advice = db.execute(
            "SELECT suggestion_id,plan FROM task_advice WHERE task_id=?", (task_id,)
        ).fetchone()
        result["ai_suggestion"] = (
            {"id": advice["suggestion_id"], "plan": json.loads(advice["plan"])}
            if advice
            else None
        )
        result["plan"] = {
            "tool": row["tool"],
            "subject": row["subject"],
            "mode": "deterministic_local",
            "external_actions": False,
        }
        return result

    def create(
        self, subject, tool, key, workspace="local", actor="local", suggestion_id=None
    ):
        # Reuse core input validation. This call never approves or executes a tool.
        execute(subject, tool, approved=False)
        subject = subject.strip()
        if workspace != "local":
            key = workspace + ":" + key
        fingerprint = hashlib.sha256(
            json.dumps(
                [subject, tool]
                if suggestion_id is None
                else [subject, tool, suggestion_id]
            ).encode()
        ).hexdigest()
        task_id, stamp = str(uuid.uuid4()), now()
        plan_hash = hashlib.sha256(
            json.dumps([task_id, subject, tool]).encode()
        ).hexdigest()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute(
                "SELECT id,fingerprint FROM tasks WHERE request_key=?", (key,)
            ).fetchone()
            if old:
                if old["fingerprint"] != fingerprint:
                    raise Conflict("Idempotency key already used for another request")
                return self.row(db, old["id"], workspace)
            advice = None
            if suggestion_id is not None:
                advice = db.execute(
                    "SELECT plan,subject_hash FROM model_usage WHERE id=? AND workspace=? AND status=?",
                    (suggestion_id, workspace, "completed"),
                ).fetchone()
                if (
                    not advice
                    or advice["subject_hash"]
                    != hashlib.sha256(subject.encode()).hexdigest()
                    or json.loads(advice["plan"])["tool"] != tool
                ):
                    raise Conflict(
                        "AI suggestion does not match this workspace, subject and tool"
                    )
            count = db.execute(
                "SELECT count(*) FROM task_scopes WHERE workspace=?", (workspace,)
            ).fetchone()[0]
            if count >= PILOT.max_stored_tasks:
                raise Conflict("Pilot stored-task entitlement reached")
            db.execute(
                "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    task_id,
                    key,
                    fingerprint,
                    subject,
                    tool,
                    "approval_required",
                    plan_hash,
                    None,
                    stamp,
                    stamp,
                ),
            )
            db.execute("INSERT INTO task_scopes VALUES (?,?)", (task_id, workspace))
            if advice:
                db.execute(
                    "INSERT INTO task_advice VALUES (?,?,?)",
                    (task_id, suggestion_id, advice["plan"]),
                )
            self.event(db, task_id, "task_received", actor)
            self.event(db, task_id, "awaiting_approval", actor)
            return self.row(db, task_id, workspace)

    def get(self, task_id, workspace="local"):
        with self.connection() as db:
            return self.row(db, task_id, workspace)

    def list(self, workspace="local"):
        with self.connection() as db:
            return [
                self.row(db, r["id"], workspace)
                for r in db.execute(
                    "SELECT t.id FROM tasks t JOIN task_scopes s ON t.id=s.task_id "
                    "WHERE s.workspace=? ORDER BY t.created_at DESC LIMIT 100",
                    (workspace,),
                ).fetchall()
            ]

    def approve(self, task_id, plan_hash, workspace="local", actor="local"):
        # The bounded, deterministic tools run inside one transaction. A concurrent
        # approval/cancellation cannot race or leave a partially committed result.
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            task = self.row(db, task_id, workspace)
            if task["plan_hash"] != plan_hash:
                raise Conflict("Approval does not match the stored plan")
            if task["status"] == "completed":
                return task  # Replaying approval is safe and adds no duplicate events.
            if task["status"] != "approval_required":
                raise Conflict("Task cannot be approved in its current state")
            self.event(db, task_id, "human_approved", actor)
            self.event(db, task_id, "execution_started", actor)
            try:
                output = execute(task["subject"], task["tool"], approved=True).output
            except Exception:
                self.event(db, task_id, "execution_failed", actor)
                db.execute(
                    "UPDATE tasks SET status=?,updated_at=? WHERE id=?",
                    ("failed", now(), task_id),
                )
            else:
                db.execute(
                    "UPDATE tasks SET status=?,result=?,updated_at=? WHERE id=?",
                    ("completed", json.dumps(output), now(), task_id),
                )
                self.event(db, task_id, "completed", actor)
            return self.row(db, task_id, workspace)

    def cancel(self, task_id, workspace="local", actor="local"):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            task = self.row(db, task_id, workspace)
            if task["status"] == "cancelled":
                return task
            if task["status"] != "approval_required":
                raise Conflict("Only pending tasks can be cancelled")
            db.execute(
                "UPDATE tasks SET status=?,updated_at=? WHERE id=?",
                ("cancelled", now(), task_id),
            )
            self.event(db, task_id, "cancelled", actor)
            return self.row(db, task_id, workspace)

    def ready(self):
        with self.connection() as db:
            db.execute("SELECT id FROM tasks LIMIT 1").fetchall()
