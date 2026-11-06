"""Transactional storage for local deterministic workflows; no remote side effects."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid

from .core import execute


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
            db.executescript('''
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
                PRAGMA user_version = 1;
            ''')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON')
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def event(db, task_id, name):
        db.execute('INSERT INTO events(task_id, at, event) VALUES (?,?,?)',
                   (task_id, now(), name))

    @staticmethod
    def row(db, task_id):
        row = db.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
        if row is None:
            raise Missing('Task not found')
        result = dict(row)
        result.pop('request_key')
        result.pop('fingerprint')
        result['result'] = json.loads(result['result']) if result['result'] else None
        result['events'] = [dict(e) for e in db.execute(
            'SELECT seq,at,event FROM events WHERE task_id=? ORDER BY seq', (task_id,))]
        result['plan'] = {'tool': row['tool'], 'subject': row['subject'],
                          'mode': 'deterministic_local', 'external_actions': False}
        return result

    def create(self, subject, tool, key):
        # Reuse core input validation. This call never approves or executes a tool.
        execute(subject, tool, approved=False)
        subject = subject.strip()
        fingerprint = hashlib.sha256(json.dumps([subject, tool]).encode()).hexdigest()
        task_id, stamp = str(uuid.uuid4()), now()
        plan_hash = hashlib.sha256(json.dumps([task_id, subject, tool]).encode()).hexdigest()
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT id,fingerprint FROM tasks WHERE request_key=?', (key,)).fetchone()
            if old:
                if old['fingerprint'] != fingerprint:
                    raise Conflict('Idempotency key already used for another request')
                return self.row(db, old['id'])
            db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?)',
                       (task_id, key, fingerprint, subject, tool, 'approval_required',
                        plan_hash, None, stamp, stamp))
            self.event(db, task_id, 'task_received')
            self.event(db, task_id, 'awaiting_approval')
            return self.row(db, task_id)

    def get(self, task_id):
        with self.connection() as db:
            return self.row(db, task_id)

    def list(self):
        with self.connection() as db:
            return [self.row(db, r['id']) for r in db.execute(
                'SELECT id FROM tasks ORDER BY created_at DESC LIMIT 100').fetchall()]

    def approve(self, task_id, plan_hash):
        # The bounded, deterministic tools run inside one transaction. A concurrent
        # approval/cancellation cannot race or leave a partially committed result.
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            task = self.row(db, task_id)
            if task['plan_hash'] != plan_hash:
                raise Conflict('Approval does not match the stored plan')
            if task['status'] == 'completed':
                return task  # Replaying approval is safe and adds no duplicate events.
            if task['status'] != 'approval_required':
                raise Conflict('Task cannot be approved in its current state')
            self.event(db, task_id, 'human_approved')
            self.event(db, task_id, 'execution_started')
            try:
                output = execute(task['subject'], task['tool'], approved=True).output
            except Exception:
                self.event(db, task_id, 'execution_failed')
                db.execute('UPDATE tasks SET status=?,updated_at=? WHERE id=?',
                           ('failed', now(), task_id))
            else:
                db.execute('UPDATE tasks SET status=?,result=?,updated_at=? WHERE id=?',
                           ('completed', json.dumps(output), now(), task_id))
                self.event(db, task_id, 'completed')
            return self.row(db, task_id)

    def cancel(self, task_id):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            task = self.row(db, task_id)
            if task['status'] == 'cancelled':
                return task
            if task['status'] != 'approval_required':
                raise Conflict('Only pending tasks can be cancelled')
            db.execute('UPDATE tasks SET status=?,updated_at=? WHERE id=?',
                       ('cancelled', now(), task_id))
            self.event(db, task_id, 'cancelled')
            return self.row(db, task_id)

    def ready(self):
        with self.connection() as db:
            db.execute('SELECT id FROM tasks LIMIT 1').fetchall()
