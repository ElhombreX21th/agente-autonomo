import unittest
from agent_v3.core import execute


class AgentV3Tests(unittest.TestCase):
    def test_approval_gate(self):
        result = execute("Prepare a report")
        self.assertEqual(result.status, "approval_required")

    def test_approved_work(self):
        result = execute("Prepare a report", approved=True)
        self.assertEqual(result.status, "completed")
        self.assertEqual(len(result.output["steps"]), 4)

    def test_invalid_tool(self):
        with self.assertRaises(ValueError):
            execute("test", tool="shell", approved=True)

    def test_blank_task(self):
        with self.assertRaises(ValueError):
            execute(" ")

    def test_classification_review(self):
        result = execute("Critical incident", tool="classify", approved=True)
        self.assertEqual(result.output["category"], "urgent")
        self.assertTrue(result.output["review_required"])


if __name__ == "__main__":
    unittest.main()
