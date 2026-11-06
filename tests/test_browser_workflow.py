from pathlib import Path
import tempfile
import unittest

from pydantic import ValidationError

from agent_v3.browser_workflow import (
    BrowserApproval,
    BrowserStep,
    BrowserWorkflow,
    write_runner_request,
)


class BrowserWorkflowTests(unittest.TestCase):
    def workflow(self):
        return BrowserWorkflow(
            name="Synthetic profile update",
            allowed_hosts=["127.0.0.1"],
            steps=[
                BrowserStep(action="goto", value="http://127.0.0.1:8766/login"),
                BrowserStep(
                    action="fill",
                    selector="#email",
                    secret_env="TEST_LOGIN_EMAIL",
                    label="Email",
                ),
                BrowserStep(
                    action="fill",
                    selector="#password",
                    secret_env="TEST_LOGIN_PASSWORD",
                    label="Password",
                ),
                BrowserStep(action="click", selector="#login", label="Log in"),
                BrowserStep(
                    action="fill",
                    selector="#headline",
                    value="Improved synthetic headline",
                    label="Headline",
                ),
                BrowserStep(action="click", selector="#save", label="Save profile"),
                BrowserStep(action="logout", selector="#logout", label="Log out"),
            ],
        )

    def test_preview_redacts_secrets_and_lists_writes(self):
        preview = self.workflow().preview()
        self.assertTrue(preview["approval_required"])
        self.assertEqual(preview["write_actions"][0]["value"], "[secret]")
        self.assertNotIn("TEST_LOGIN_PASSWORD", str(preview))

    def test_exact_preview_approval_is_required(self):
        workflow = self.workflow()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "request.json"
            with self.assertRaises(PermissionError):
                write_runner_request(workflow, output)
            with self.assertRaises(PermissionError):
                write_runner_request(
                    workflow,
                    output,
                    approval=BrowserApproval("0" * 64, role="master"),
                )
            write_runner_request(
                workflow,
                output,
                approval=BrowserApproval(workflow.digest(), role="master"),
            )
            self.assertTrue(output.exists())

    def test_user_cannot_authorize_browser_writes(self):
        workflow = self.workflow()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(PermissionError):
                write_runner_request(
                    workflow,
                    Path(directory) / "request.json",
                    approval=BrowserApproval(workflow.digest(), role="user"),
                )

    def test_external_http_and_unlisted_hosts_are_rejected(self):
        with self.assertRaises(ValidationError):
            BrowserWorkflow(
                name="bad",
                allowed_hosts=["example.com"],
                steps=[BrowserStep(action="goto", value="http://example.com")],
            )
        with self.assertRaises(ValidationError):
            BrowserWorkflow(
                name="bad",
                allowed_hosts=["example.com"],
                steps=[BrowserStep(action="goto", value="https://other.example")],
            )

    def test_credentials_cannot_be_embedded_in_urls_or_plain_fill_ambiguity(self):
        with self.assertRaises(ValidationError):
            BrowserWorkflow(
                name="bad",
                allowed_hosts=["example.com"],
                steps=[
                    BrowserStep(action="goto", value="https://user:pass@example.com")
                ],
            )
        with self.assertRaises(ValidationError):
            BrowserStep(
                action="fill",
                selector="#password",
                value="plain",
                secret_env="PASSWORD",
            )

    def test_human_challenge_is_a_pause_not_a_bypass(self):
        step = BrowserStep(
            action="human_challenge", value="Complete the challenge manually"
        )
        self.assertEqual(step.action, "human_challenge")


if __name__ == "__main__":
    unittest.main()
