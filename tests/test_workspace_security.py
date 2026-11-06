from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import httpx
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from agent_v3.api import create_app
from agent_v3.identity import IdentityStore
from agent_v3.store import Store
from agent_v3.commercial import DisabledBilling, Entitlements


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "tasks.sqlite3"
        self.app = create_app(self.path, auth_required=True)
        self.client = TestClient(self.app, base_url="http://localhost")
        self.master, self.token = self.app.state.identities.provision(
            "Synthetic workspace A"
        )
        self.other, self.other_token = self.app.state.identities.provision(
            "Synthetic workspace B"
        )
        self.user, self.user_token = self.app.state.identities.provision(
            "A", "user", self.master.workspace
        )

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def headers(self, token=None):
        return {"Authorization": "Bearer " + (token or self.token)}

    def create(self, token=None, key="same-key"):
        return self.client.post(
            "/api/tasks",
            headers={**self.headers(token), "Idempotency-Key": key},
            json={"subject": "Synthetic urgent support request"},
        )

    def test_authentication_is_required_for_all_workspace_routes(self):
        self.assertEqual(self.client.get("/api/tasks").status_code, 401)
        self.assertEqual(self.client.get("/api/account").status_code, 401)
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.assertEqual(
            self.client.get("/api/tasks", headers=self.headers("invalid")).status_code,
            401,
        )

    def test_workspace_isolation_for_read_write_list_and_idempotency(self):
        task = self.create().json()
        other = self.create(self.other_token).json()
        self.assertNotEqual(task["id"], other["id"])
        headers = self.headers(self.other_token)
        self.assertEqual(len(self.client.get("/api/tasks", headers=headers).json()), 1)
        self.assertEqual(
            self.client.get("/api/tasks/" + task["id"], headers=headers).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                "/api/tasks/" + task["id"] + "/cancel", headers=headers
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                "/api/tasks/" + task["id"] + "/approve",
                headers=headers,
                json={"plan_hash": task["plan_hash"]},
            ).status_code,
            404,
        )

    def test_roles_and_audit_actor(self):
        task = self.create().json()
        user = self.headers(self.user_token)
        self.assertEqual(
            self.client.get("/api/tasks/" + task["id"], headers=user).status_code, 200
        )
        self.assertEqual(self.create(self.user_token, key="user-task").status_code, 200)
        self.assertEqual(
            self.client.post(
                "/api/tasks/" + task["id"] + "/approve",
                headers=user,
                json={"plan_hash": task["plan_hash"]},
            ).status_code,
            403,
        )
        administrator, token = self.app.state.identities.provision(
            "A", "administrator", self.master.workspace
        )
        done = self.client.post(
            "/api/tasks/" + task["id"] + "/approve",
            headers=self.headers(token),
            json={"plan_hash": task["plan_hash"]},
        ).json()
        self.assertEqual(done["status"], "completed")
        self.assertEqual(done["events"][0]["actor"], self.master.key_id)
        self.assertEqual(done["events"][-1]["actor"], administrator.key_id)
        self.assertNotIn(token, str(done))

    def test_revocation_and_hashed_storage(self):
        with self.app.state.store.connection() as db:
            rows = [dict(r) for r in db.execute("SELECT * FROM api_keys")]
        self.assertNotIn(self.token, str(rows))
        self.app.state.identities.revoke(self.master.key_id)
        self.assertEqual(
            self.client.get("/api/tasks", headers=self.headers()).status_code, 401
        )

    def test_legacy_data_is_not_assigned_to_new_workspace(self):
        old = self.app.state.store.create(
            "Legacy synthetic task", "checklist", "legacy"
        )
        self.assertEqual(
            self.client.get(
                "/api/tasks/" + old["id"], headers=self.headers()
            ).status_code,
            404,
        )
        Store(self.path)  # repeat migration must preserve existing tenant mappings
        self.assertEqual(self.create().status_code, 200)
        self.assertEqual(
            len(self.client.get("/api/tasks", headers=self.headers()).json()), 1
        )

    def test_pilot_entitlement_and_disabled_billing(self):
        self.create()
        with patch("agent_v3.store.PILOT", Entitlements("test", 1)):
            self.assertEqual(self.create(key="different-key").status_code, 409)
            self.assertEqual(self.create().status_code, 200)
        account = self.client.get("/api/account", headers=self.headers()).json()
        self.assertFalse(account["billing"]["charges_enabled"])
        self.assertEqual(account["role"], "master")
        with self.assertRaises(PermissionError):
            DisabledBilling().checkout(self.master.workspace)

    def test_ai_suggestion_is_bound_to_task_workspace_subject_and_tool(self):
        from agent_v3.planning import Planner

        transport = httpx.MockTransport(
            lambda req: httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "tool": "checklist",
                                        "category": "standard",
                                        "rationale": "Synthetic review",
                                        "steps": ["Review", "Approve"],
                                    }
                                )
                            }
                        }
                    ],
                    "usage": {"prompt_tokens": 40, "completion_tokens": 20},
                },
            )
        )
        provider = httpx.Client(transport=transport)
        self.addCleanup(provider.close)
        app = create_app(
            self.path,
            auth_required=True,
            planner_factory=lambda store: Planner(
                store,
                url="https://provider.example/v1/chat/completions",
                key="synthetic",
                model="test",
                budget="1",
                input_rate="1",
                output_rate="2",
                client=provider,
            ),
        )
        with TestClient(app, base_url="http://localhost") as client:
            suggested = client.post(
                "/api/interpret",
                headers=self.headers(),
                json={"subject": "Synthetic task"},
            ).json()
            self.assertIn("suggestion_id", suggested)
            payload = {
                "subject": "Synthetic task",
                "tool": "checklist",
                "suggestion_id": suggested["suggestion_id"],
            }
            other = client.post(
                "/api/tasks",
                headers={**self.headers(self.other_token), "Idempotency-Key": "ai"},
                json=payload,
            )
            self.assertEqual(other.status_code, 409)
            wrong = client.post(
                "/api/tasks",
                headers={**self.headers(), "Idempotency-Key": "wrong"},
                json={**payload, "tool": "classify"},
            )
            self.assertEqual(wrong.status_code, 409)
            created = client.post(
                "/api/tasks",
                headers={**self.headers(), "Idempotency-Key": "ai"},
                json=payload,
            ).json()
            self.assertEqual(created["ai_suggestion"]["plan"]["tool"], "checklist")
            self.assertEqual(created["status"], "approval_required")
            self.assertIsNone(created["result"])
            self.assertEqual(
                client.post(
                    "/api/interpret",
                    headers=self.headers(self.user_token),
                    json={"subject": "Synthetic task"},
                ).status_code,
                403,
            )
            self.assertEqual(
                app.state.planner.usage(self.master.workspace)["requests"], 1
            )

    def test_provider_use_not_allowed_without_workspace_credential(self):
        app = create_app(self.path, auth_required=False)
        with TestClient(app, base_url="http://localhost") as client:
            self.assertEqual(
                client.post(
                    "/api/interpret", json={"subject": "Synthetic task"}
                ).status_code,
                403,
            )

    def test_unknown_role_rejected(self):
        with self.assertRaises(ValueError):
            self.app.state.identities.provision("A", "owner")

    def test_legacy_roles_are_migrated(self):
        legacy_path = Path(self.tmp.name) / "legacy-roles.sqlite3"
        store = Store(legacy_path)
        with store.connection() as db:
            db.executescript("""
                CREATE TABLE workspaces (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL,
                    plan TEXT NOT NULL DEFAULT 'pilot'
                );
                CREATE TABLE api_keys (
                    id TEXT PRIMARY KEY, digest TEXT UNIQUE NOT NULL,
                    workspace TEXT NOT NULL REFERENCES workspaces(id),
                    role TEXT NOT NULL CHECK(role IN ('owner','operator','viewer')),
                    revoked INTEGER NOT NULL DEFAULT 0
                );
                INSERT INTO workspaces(id,name) VALUES ('w','Legacy');
                INSERT INTO api_keys(id,digest,workspace,role) VALUES
                    ('one','digest-one','w','owner'),
                    ('two','digest-two','w','operator'),
                    ('three','digest-three','w','viewer');
            """)
        IdentityStore(store)
        with store.connection() as db:
            roles = {
                row["id"]: row["role"]
                for row in db.execute("SELECT id,role FROM api_keys")
            }
        self.assertEqual(
            roles,
            {"one": "master", "two": "administrator", "three": "user"},
        )


if __name__ == "__main__":
    unittest.main()
