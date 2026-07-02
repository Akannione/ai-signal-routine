from __future__ import annotations

import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ai_signal_routine.history import (  # noqa: E402
    build_history_snapshot,
    build_trend_deltas,
    build_weekly_summary,
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

    def test_weekly_summary_is_stakeholder_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.sqlite"
            record_briefing(db_path, SAMPLE_PAYLOAD)
            rows = build_weekly_summary(db_path)

            self.assertEqual(len(rows), 1)
            summary = rows[0]
            self.assertEqual(summary["signals"], 3)
            self.assertEqual(summary["reviewed"], 3)
            self.assertEqual(summary["review_rate"], 1.0)
            self.assertEqual(summary["open_actions"], 3)
            self.assertEqual(summary["top_theme"], "workflow-automation")
            self.assertEqual(summary["top_source"], "Synthetic AI Ops Radar")
            self.assertIn("open actions", summary["stakeholder_summary"])

    def test_trend_deltas_compare_latest_run_to_previous_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.sqlite"
            later_payload = deepcopy(SAMPLE_PAYLOAD)
            later_payload["generated_at"] = "2026-05-30T12:00:00+00:00"
            later_payload["items"][0]["score"] = 96.0
            later_payload["items"][2]["operator"]["decision"] = "archive"
            later_payload["memory_summary"].update({"watch": 0, "archive": 1})

            record_briefing(db_path, SAMPLE_PAYLOAD)
            record_briefing(db_path, later_payload)
            rows = build_trend_deltas(db_path)

            self.assertEqual(len(rows), 2)
            latest = rows[0]
            previous = rows[1]
            self.assertEqual(latest["generated_at"], "2026-05-30T12:00:00+00:00")
            self.assertEqual(latest["open_actions"], 2)
            self.assertEqual(latest["open_actions_delta"], -1)
            self.assertEqual(latest["avg_score_delta"], 1.3)
            self.assertEqual(latest["review_rate_delta"], 0.0)
            self.assertEqual(latest["comparison"], "Compared with previous run")
            self.assertEqual(previous["comparison"], "No previous run")

    def test_export_history_tables_writes_csvs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            db_path = root / "history.sqlite"
            outdir = root / "exports"
            record_briefing(db_path, SAMPLE_PAYLOAD)
            paths = export_history_tables(db_path, outdir)

            self.assertEqual(
                set(paths),
                {
                    "runs",
                    "signals",
                    "decision_counts",
                    "source_counts",
                    "themes",
                    "weekly_summary",
                    "trend_deltas",
                },
            )
            self.assertEqual(paths["weekly_summary"].name, "ai_signal_weekly_summary.csv")
            self.assertEqual(paths["trend_deltas"].name, "ai_signal_trend_deltas.csv")
            for path in paths.values():
                self.assertTrue(path.exists())
                self.assertGreater(path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
