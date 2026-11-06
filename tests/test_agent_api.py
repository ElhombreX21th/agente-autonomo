"""API lifecycle, durable storage and authorization-boundary regression tests."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from agent_v3.api import create_app
from agent_v3.store import Store


class WorkflowApiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "tasks.sqlite3"
        self.client = TestClient(create_app(self.path), base_url="http://localhost")

    def tearDown(self):
        self.client.close()
        self.directory.cleanup()

    def create(self, key="request-1", **values):
        return self.client.post(
            "/api/tasks",
            headers={"Idempotency-Key": key},
            json={"subject": "Synthetic urgent support incident", **values},
        )

    def approve(self, task, **values):
        return self.client.post(
            "/api/tasks/" + task["id"] + "/approve",
            json={"plan_hash": task["plan_hash"], **values},
        )

    def test_end_to_end_and_restart(self):
        task = self.create().json()
        self.assertEqual(task["status"], "approval_required")
        self.assertIsNone(task["result"])
        self.assertEqual(task["plan"]["mode"], "deterministic_local")
        done = self.approve(task).json()
        self.assertEqual(done["status"], "completed")
        self.assertEqual(done["id"], task["id"])
        self.assertEqual(done["result"]["category"], "urgent")
        with TestClient(
            create_app(self.path), base_url="http://localhost"
        ) as restarted:
            restored = restarted.get("/api/tasks/" + task["id"]).json()
            self.assertEqual(done, restored)
            self.assertEqual(len(restarted.get("/api/tasks").json()), 1)
        self.assertEqual(
            [e["event"] for e in done["events"]],
            [
                "task_received",
                "awaiting_approval",
                "human_approved",
                "execution_started",
                "completed",
            ],
        )

    def test_idempotency_conflict_and_replay(self):
        first = self.create().json()
        self.assertEqual(self.create().json(), first)
        self.assertEqual(self.create(subject="A different request").status_code, 409)
        done = self.approve(first).json()
        self.assertEqual(self.approve(first).json(), done)
        self.assertEqual(self.create().json(), done)

    def test_wrong_plan_does_not_execute(self):
        task = self.create().json()
        self.assertEqual(self.approve(task, plan_hash="0" * 64).status_code, 409)
        self.assertIsNone(self.client.get("/api/tasks/" + task["id"]).json()["result"])

    def test_approval_for_another_task_rejected(self):
        a, b = self.create().json(), self.create(key="request-2").json()
        self.assertEqual(self.approve(b, plan_hash=a["plan_hash"]).status_code, 409)

    def test_cancelled_task_cannot_execute(self):
        task = self.create().json()
        path = "/api/tasks/" + task["id"] + "/cancel"
        cancelled = self.client.post(path).json()
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(self.client.post(path).json(), cancelled)
        self.assertEqual(self.approve(task).status_code, 409)

    def test_completed_task_cannot_be_cancelled(self):
        task = self.create().json()
        self.approve(task)
        self.assertEqual(
            self.client.post("/api/tasks/" + task["id"] + "/cancel").status_code, 409
        )

    def test_validation(self):
        for subject in ["", "   ", "a" * 5001]:
            self.assertEqual(self.create(subject=subject).status_code, 422)
        self.assertEqual(self.create(tool="shell").status_code, 422)
        self.assertEqual(self.create(approved=True).status_code, 422)
        self.assertEqual(
            self.client.post("/api/tasks", json={"subject": "valid"}).status_code, 422
        )
        self.assertEqual(self.create(key=" ").status_code, 422)
        self.assertEqual(self.client.get("/api/tasks/not-found").status_code, 404)

    def test_untrusted_host_rejected(self):
        self.assertEqual(
            self.client.get(
                "/health", headers={"Host": "untrusted.example"}
            ).status_code,
            400,
        )

    def test_browser_cross_site_writes_rejected(self):
        for headers in [
            {"Origin": "https://untrusted.example"},
            {"Sec-Fetch-Site": "cross-site"},
        ]:
            self.assertEqual(
                self.client.post(
                    "/api/tasks",
                    headers={"Idempotency-Key": "cross-site", **headers},
                    json={"subject": "valid"},
                ).status_code,
                403,
            )
        self.assertEqual(self.client.get("/api/tasks").json(), [])

    def test_concurrent_approvals_execute_once(self):
        task = self.create().json()
        store = Store(self.path)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(
                pool.map(
                    lambda _: store.approve(task["id"], task["plan_hash"]), range(4)
                )
            )
        self.assertTrue(all(r == results[0] for r in results))
        self.assertEqual(len(results[0]["events"]), 5)

    def test_tool_failure_is_persisted_without_exception_details(self):
        task = self.create().json()
        with patch(
            "agent_v3.store.execute", side_effect=RuntimeError("sensitive exception")
        ):
            failed = self.approve(task).json()
        self.assertEqual(failed["status"], "failed")
        self.assertIsNone(failed["result"])
        self.assertNotIn("sensitive exception", str(failed))
        self.assertEqual(self.approve(task).status_code, 409)

    def test_health_readiness_and_openapi(self):
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.assertEqual(self.client.get("/ready").status_code, 200)
        self.assertIn("/api/tasks", self.client.get("/openapi.json").json()["paths"])
        self.assertIn("Local Workspace", self.client.get("/").text)


if __name__ == "__main__":
    unittest.main()
