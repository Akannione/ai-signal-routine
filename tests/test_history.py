from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ai_signal_routine.history import (  # noqa: E402
    build_history_snapshot,
    export_history_tables,
    record_briefing,
)


SAMPLE_PAYLOAD = {
    "generated_at": "2026-05-23T12:00:00+00:00",
    "profile": "Test AI Ops Profile",
    "themes": [
        {"theme": "workflow-automation", "count": 2},
        {"theme": "analytics-ops", "count": 1},
    ],
    "memory_summary": {
        "unreviewed": 0,
        "watch": 1,
        "test": 1,
        "implement": 1,
        "archive": 0,
        "reviewed": 3,
        "total": 3,
    },
    "items": [
        {
            "title": "Workflow automation command center",
            "url": "https://example.com/signals/workflow-automation",
            "source": "Synthetic AI Ops Radar",
            "group": "ai_operations",
            "source_type": "sample",
            "published_at": "2026-05-22T12:00:00+00:00",
            "summary": "Teams need repeatable AI workflow review loops.",
            "tags": ["ai-operations", "workflow-automation"],
            "score": 92.0,
            "operator": {
                "decision": "implement",
                "priority": "high",
                "next_action": "Build the command center view.",
                "linked_project": "AI Ops Command Center",
            },
            "metadata": {"category": "ai_operations"},
        },
        {
            "title": "SQL quality checks for weekly reports",
            "url": "https://example.com/signals/sql-quality-checks",
            "source": "Synthetic Analytics Radar",
            "group": "analytics_ops",
            "source_type": "sample",
            "published_at": "2026-05-21T12:00:00+00:00",
            "summary": "Automated checks keep KPI reports trustworthy.",
            "tags": ["sql", "data-quality"],
            "score": 88.0,
            "operator": {
                "decision": "test",
                "priority": "high",
                "next_action": "Prototype a quality gate.",
                "linked_project": "Business Operations Reporting System",
            },
            "metadata": {"category": "analytics_ops"},
        },
        {
            "title": "Human-in-the-loop CRM automation",
            "url": "https://example.com/signals/crm-automation",
            "source": "Synthetic Automation Radar",
            "group": "sales_operations",
            "source_type": "sample",
            "published_at": "2026-05-20T12:00:00+00:00",
            "summary": "Lead prioritization works best with human review.",
            "tags": ["crm", "automation"],
            "score": 80.0,
            "operator": {
                "decision": "watch",
                "priority": "medium",
                "next_action": "Track whether this belongs in the CRM demo.",
                "linked_project": "CRM Sales Pipeline Automation System",
            },
            "metadata": {"category": "sales_operations"},
        },
    ],
}


class HistoryTests(unittest.TestCase):
    def test_record_briefing_is_idempotent_by_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.sqlite"
            first = record_briefing(db_path, SAMPLE_PAYLOAD)
            second = record_briefing(db_path, SAMPLE_PAYLOAD)
            snapshot = build_history_snapshot(db_path)

            self.assertEqual(first["run_id"], second["run_id"])
            self.assertEqual(snapshot["run_count"], 1)
            self.assertEqual(snapshot["signal_count"], 3)
            self.assertEqual(snapshot["latest_run"]["implement_count"], 1)
            self.assertEqual(snapshot["latest_run"]["test_count"], 1)
            self.assertEqual(snapshot["latest_run"]["watch_count"], 1)

    def test_snapshot_exposes_decisions_sources_and_open_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.sqlite"
            record_briefing(db_path, SAMPLE_PAYLOAD)
            snapshot = build_history_snapshot(db_path)

            decisions = {row["label"]: row["count"] for row in snapshot["decision_counts"]}
            sources = {row["label"]: row["count"] for row in snapshot["source_counts"]}
            themes = {row["label"]: row["count"] for row in snapshot["theme_counts"]}

            self.assertEqual(decisions["implement"], 1)
            self.assertEqual(decisions["test"], 1)
            self.assertEqual(decisions["watch"], 1)
            self.assertEqual(sources["Synthetic AI Ops Radar"], 1)
            self.assertEqual(themes["workflow-automation"], 2)
            self.assertEqual(len(snapshot["open_actions"]), 3)

    def test_export_history_tables_writes_csvs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            db_path = root / "history.sqlite"
            outdir = root / "exports"
            record_briefing(db_path, SAMPLE_PAYLOAD)
            paths = export_history_tables(db_path, outdir)

            self.assertEqual(
                set(paths),
                {"runs", "signals", "decision_counts", "source_counts", "themes"},
            )
            for path in paths.values():
                self.assertTrue(path.exists())
                self.assertGreater(path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
