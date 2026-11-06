"""Workspace-scoped, revocable high-entropy API credentials for pilot operators."""

from dataclasses import dataclass
import hashlib
import secrets
import uuid


@dataclass(frozen=True)
class Identity:
    workspace: str
    role: str
    key_id: str


class IdentityStore:
    def __init__(self, store):
        self.store = store
        with store.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS workspaces (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL,
                    plan TEXT NOT NULL DEFAULT 'pilot'
                );
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY, digest TEXT UNIQUE NOT NULL,
                    workspace TEXT NOT NULL REFERENCES workspaces(id),
                    role TEXT NOT NULL CHECK(role IN ('owner','operator','viewer')),
                    revoked INTEGER NOT NULL DEFAULT 0
                );
            """)

    def provision(self, name, role="owner", workspace=None):
        if role not in {"owner", "operator", "viewer"}:
            raise ValueError("Unknown role")
        if not name.strip() or len(name) > 120:
            raise ValueError("Workspace name must be 1–120 characters")
        key_id, token = str(uuid.uuid4()), secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode()).hexdigest()
        with self.store.connection() as db:
            if workspace is None:
                workspace = str(uuid.uuid4())
                db.execute(
                    "INSERT INTO workspaces(id,name) VALUES (?,?)",
                    (workspace, name.strip()),
                )
            elif (
                db.execute(
                    "SELECT id FROM workspaces WHERE id=?", (workspace,)
                ).fetchone()
                is None
            ):
                raise ValueError("Workspace does not exist")
            db.execute(
                "INSERT INTO api_keys(id,digest,workspace,role) VALUES (?,?,?,?)",
                (key_id, digest, workspace, role),
            )
        return Identity(workspace, role, key_id), token

    def authenticate(self, token):
        if not token or len(token) > 256:
            return None
        with self.store.connection() as db:
            row = db.execute(
                "SELECT workspace,role,id FROM api_keys WHERE digest=? AND revoked=0",
                (hashlib.sha256(token.encode()).hexdigest(),),
            ).fetchone()
            return Identity(*row) if row else None

    def revoke(self, key_id):
        with self.store.connection() as db:
            db.execute("UPDATE api_keys SET revoked=1 WHERE id=?", (key_id,))
