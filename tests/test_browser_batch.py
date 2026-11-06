from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent_v3.browser_batch import run_batch
from agent_v3.browser_workflow import BrowserApproval, BrowserStep, BrowserWorkflow


class BrowserBatchTests(unittest.TestCase):
    def workflow(self, name):
        return BrowserWorkflow(
            name=name,
            allowed_hosts=["127.0.0.1"],
            steps=[BrowserStep(action="goto", value="http://127.0.0.1:9999")],
        )

    @patch("agent_v3.browser_batch.subprocess.run")
    def test_runs_multiple_read_only_tasks_in_order(self, run):
        def complete(args, **kwargs):
            output = Path(args[-1])
            (output / "result.json").write_text('{"status":"completed"}')
            return type("Completed", (), {"returncode": 0})()

        run.side_effect = complete
        workflows = [self.workflow("one"), self.workflow("two")]
        with tempfile.TemporaryDirectory() as directory:
            results = run_batch(workflows, {}, Path(directory))
        self.assertEqual([result.workflow for result in results], ["one", "two"])
        self.assertTrue(all(result.status == "completed" for result in results))

    @patch("agent_v3.browser_batch.subprocess.run")
    def test_stops_batch_for_human_challenge(self, run):
        def challenge(args, **kwargs):
            output = Path(args[-1])
            (output / "human-action-required.json").write_text(
                '{"status":"human_action_required"}'
            )
            return type("Completed", (), {"returncode": 20})()

        run.side_effect = challenge
        workflows = [self.workflow("challenge"), self.workflow("must-not-run")]
        with tempfile.TemporaryDirectory() as directory:
            results = run_batch(workflows, {}, Path(directory))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, "human_action_required")

    def test_write_task_requires_master_or_administrator_approval(self):
        workflow = BrowserWorkflow(
            name="write",
            allowed_hosts=["127.0.0.1"],
            steps=[
                BrowserStep(action="goto", value="http://127.0.0.1:9999"),
                BrowserStep(action="click", selector="#save"),
            ],
        )
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(PermissionError):
                run_batch([workflow], {}, Path(directory))
            with self.assertRaises(PermissionError):
                run_batch(
                    [workflow],
                    {
                        workflow.digest(): BrowserApproval(
                            workflow.digest(), role="user"
                        )
                    },
                    Path(directory),
                )


if __name__ == "__main__":
    unittest.main()
