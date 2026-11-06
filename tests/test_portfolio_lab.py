"""Safety, correctness and regression tests; only generated synthetic records."""

import unittest
import json
import tempfile
from pathlib import Path
from portfolio_lab.triage import Ticket, NaiveBayesClassifier, triage
from portfolio_lab.api_sync import (
    connect,
    current_cursor,
    sync_pages,
    http_json_page_fetcher,
)
from portfolio_lab.medtech_copilot import analyze_events, retrieve_answer
from portfolio_lab.demo import run_demo


class TicketTriageTests(unittest.TestCase):
    def test_classifier_recognizes_example(self):
        label, score = NaiveBayesClassifier().predict(
            "CSV columns and duplicate spreadsheet rows"
        )
        self.assertEqual(label, "data")
        self.assertGreater(score, 0.5)

    def test_critical_impact_requires_review(self):
        result = triage(Ticket("X", "Device error", "not working", "stopped"))
        self.assertEqual(result["priority"], "P1")
        self.assertTrue(result["human_review_required"])

    def test_unknown_text_requires_review(self):
        result = triage(Ticket("X", "zxcv", "qwerty", "none"))
        self.assertEqual(result["model_score_uncalibrated"], 0.0)
        self.assertTrue(result["human_review_required"])

    def test_invalid_impact_rejected(self):
        with self.assertRaises(ValueError):
            triage(Ticket("X", "issue", "body", "severe"))


class ApiSyncTests(unittest.TestCase):
    def test_dedup_and_newest_record(self):
        pages = {
            None: {
                "items": [
                    {"id": "1", "updated_at": "2026-01-01T00:00:00Z", "amount": 10}
                ],
                "next_cursor": "two",
            },
            "two": {
                "items": [
                    {"id": "1", "updated_at": "2026-01-02T00:00:00Z", "amount": 20}
                ],
                "next_cursor": None,
            },
        }
        with connect() as conn:
            out = sync_pages(conn, lambda c: pages[c])
            self.assertEqual(out["unique_records_in_db"], 1)
            row = conn.execute("SELECT payload FROM records WHERE id='1'").fetchone()
            self.assertEqual(json.loads(row[0])["amount"], 20)

    def test_resume_after_failure(self):
        with tempfile.TemporaryDirectory() as d:
            path = str(Path(d) / "checkpoint.db")
            with connect(path) as conn:
                sync_pages(
                    conn,
                    lambda c: {
                        "items": [{"id": "A", "updated_at": "2026-01-01Z"}],
                        "next_cursor": "next",
                    },
                    max_pages=1,
                )
            with connect(path) as conn:
                self.assertEqual(current_cursor(conn), "next")
                result = sync_pages(
                    conn,
                    lambda c: {
                        "items": [{"id": "B", "updated_at": "2026-01-02Z"}],
                        "next_cursor": None,
                    },
                )
                self.assertTrue(result["finished"])
                self.assertEqual(result["unique_records_in_db"], 2)

    def test_validation_prevents_partial_page_commit(self):
        with connect() as conn:
            with self.assertRaises(ValueError):
                sync_pages(
                    conn,
                    lambda c: {
                        "items": [
                            {"id": "valid", "updated_at": "2026-01-01Z"},
                            {"id": "invalid"},
                        ],
                        "next_cursor": None,
                    },
                )
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM records").fetchone()[0], 0
            )

    def test_rejects_cleartext_remote_api(self):
        with self.assertRaises(ValueError):
            http_json_page_fetcher("http://example.com/api")


class MedTechTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {
                "event_id": f"E{i}",
                "asset_id": "SYNTHETIC-01",
                "timestamp": f"2026-10-30T1{i}:00:00Z",
                "code": "E-101",
            }
            for i in range(3)
        ]

    def test_repeat_alert_and_evidence(self):
        report = analyze_events(self.rows)
        self.assertEqual(report["events_reviewed"], 3)
        self.assertEqual(len(report["repeated_alert_findings"]), 1)
        self.assertEqual(
            report["repeated_alert_findings"][0]["evidence"], "demo-runbook/E-101"
        )

    def test_safe_retrieval_cites_entry(self):
        ans = retrieve_answer("Explain E-101", self.rows)
        self.assertIn("demo-runbook/E-101", ans["citations"])
        self.assertTrue(ans["human_review_required"])

    def test_unknown_code_not_invented(self):
        ans = retrieve_answer("Explain E-999", self.rows)
        self.assertEqual(ans["citations"], [])
        self.assertIn("No approved", ans["answer"])

    def test_timezone_required(self):
        with self.assertRaises(ValueError):
            analyze_events(
                [
                    {
                        "event_id": "1",
                        "asset_id": "x",
                        "timestamp": "2026-10-30T12:00:00",
                        "code": "E-101",
                    }
                ]
            )

    def test_all_demos_execute(self):
        result = run_demo()
        self.assertEqual(result["api_sync"]["unique_records_in_db"], 2)
        self.assertEqual(len(result["ticket_triage"]), 3)


if __name__ == "__main__":
    unittest.main()
