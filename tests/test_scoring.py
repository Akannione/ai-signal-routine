from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ai_signal_routine.benchmark import write_benchmark_pack
from ai_signal_routine.digests import (
    _resolve_imessage_script_path,
    build_email_digest,
    build_slack_digest,
    build_sms_digest,
    send_imessage_digest,
)
from ai_signal_routine.memory import (
    attach_memory_to_items,
    default_memory,
    update_signal_memory,
)
from ai_signal_routine.mini_projects import generate_projects
from ai_signal_routine.models import SignalItem
from ai_signal_routine.scoring import dedupe_items, score_items, select_noise_items, select_top_items


TEST_CONFIG = {
    "profile": {
        "topic_keywords": ["claude", "codex", "analytics", "agent", "sql"],
        "business_keywords": ["finance", "operations", "roi"],
        "learning_keywords": ["tutorial", "guide", "example"],
        "source_group_weights": {"official": 16, "repo": 15, "discussion": 8},
    },
    "limits": {"final_items": 5, "max_per_source_in_report": 2},
}


class ScoringTests(unittest.TestCase):
    def test_repo_with_stars_scores_well(self) -> None:
        item = SignalItem(
            title="openai/openai-agents-python",
            url="https://github.com/openai/openai-agents-python",
            source="GitHub Radar",
            group="repo",
            source_type="github_search",
            published_at=datetime.now(timezone.utc) - timedelta(days=1),
            summary="Agent framework for analytics workflows.",
            metadata={"stars": 21900, "updated_at": datetime.now(timezone.utc).isoformat()},
        )
        score_items([item], TEST_CONFIG)
        self.assertGreater(item.score, 40)
        self.assertTrue(any("adoption signal" in reason.lower() for reason in item.rationale))
        self.assertIn("analysis", item.metadata)
        self.assertIn("why_this_matters", item.metadata["analysis"])
        self.assertIn("operator_intelligence", item.metadata)
        self.assertIn("scorecard", item.metadata["operator_intelligence"])

    def test_hype_terms_are_categorized_as_noise(self) -> None:
        item = SignalItem(
            title="Top 10 mind-blowing AI tools to make money with AI",
            url="https://example.com/hype",
            source="Generic Feed",
            group="community",
            source_type="rss",
            published_at=datetime.now(timezone.utc),
            summary="A viral prompt hack list with no implementation detail.",
        )
        config = {
            "profile": {
                **TEST_CONFIG["profile"],
                "noise_keywords": ["top 10", "mind-blowing", "make money with ai", "prompt hack"],
                "category_keywords": {
                    "Noise/Hype To Ignore": ["top 10", "mind-blowing", "make money with ai"]
                },
            },
            "limits": TEST_CONFIG["limits"],
        }
        score_items([item], config)
        noise_items = select_noise_items([item])
        self.assertEqual(item.metadata["category"], "Noise/Hype To Ignore")
        self.assertEqual(item.metadata["operator_intelligence"]["recommendation"], "Ignore")
        self.assertEqual(noise_items, [item])

    def test_dedupe_keeps_higher_scoring_item(self) -> None:
        first = SignalItem(
            title="A",
            url="https://example.com/post?utm_source=test",
            source="OpenAI News",
            group="official",
            source_type="rss",
            published_at=datetime.now(timezone.utc),
            summary="Codex analytics guide",
            score=50,
        )
        second = SignalItem(
            title="B",
            url="https://example.com/post",
            source="OpenAI News",
            group="official",
            source_type="rss",
            published_at=datetime.now(timezone.utc),
            summary="Old post",
            score=20,
        )
        deduped = dedupe_items([second, first])
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0].title, "A")

    def test_report_selection_caps_per_source(self) -> None:
        items = []
        for index in range(4):
            items.append(
                SignalItem(
                    title=f"Item {index}",
                    url=f"https://example.com/{index}",
                    source="GitHub Radar",
                    group="repo",
                    source_type="github_search",
                    published_at=datetime.now(timezone.utc),
                    summary="Agent analytics",
                    score=50 - index,
                )
            )
        selected = select_top_items(items, TEST_CONFIG)
        self.assertEqual(len(selected), 2)

    def test_memory_attaches_operator_decision(self) -> None:
        memory = default_memory()
        update_signal_memory(
            memory,
            url="https://example.com/tool",
            title="Tool",
            source="GitHub Radar",
            decision="test",
            priority="high",
            notes="Worth a quick prototype.",
            next_action="Build a sample app.",
            linked_project="tool-radar",
        )
        item = SignalItem(
            title="Tool",
            url="https://example.com/tool",
            source="GitHub Radar",
            group="repo",
            source_type="github_search",
        )
        attach_memory_to_items([item], memory)
        operator = item.metadata["operator"]
        self.assertEqual(operator["decision"], "test")
        self.assertEqual(operator["priority"], "high")

    def test_digest_builders_include_queue_and_title(self) -> None:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "themes": [{"theme": "coding-agents", "count": 3}],
            "memory_summary": {"implement": 1, "test": 2, "watch": 3},
            "mini_projects": [{"title": "Tool Radar", "build_scope": "Build the dashboard."}],
            "items": [
                {
                    "title": "browser-use/browser-use",
                    "url": "https://github.com/browser-use/browser-use",
                    "score": 90.0,
                    "source": "GitHub Watchlist",
                    "rationale": ["Fresh signal from the last week"],
                    "operator": {"decision": "implement", "next_action": "Prototype browser workflow"},
                }
            ],
        }
        email = build_email_digest(payload)
        slack = build_slack_digest(payload)
        sms = build_sms_digest(payload)
        self.assertIn("browser-use/browser-use", email)
        self.assertIn("Implement now", email)
        self.assertIn("*Queue:*", slack)
        self.assertIn("AI OPERATOR DAILY", sms)
        self.assertIn("Themes: Coding Agents", sms)
        self.assertIn("→ Action: Implement now", sms)
        self.assertIn("Project:", sms)
        self.assertIn("browser-use/browser-use", sms)

    def test_benchmark_pack_writer_creates_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = write_benchmark_pack(Path(tmpdir))
            self.assertTrue(paths["tasks"].exists())
            self.assertTrue(paths["scorecard"].exists())
            self.assertTrue(paths["results"].exists())

    def test_sms_digest_avoids_yesterdays_top_urls_when_possible(self) -> None:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "history": {"recent_top_urls": ["https://example.com/repeat"]},
            "items": [
                {
                    "title": "Repeat Item",
                    "url": "https://example.com/repeat",
                    "score": 99.0,
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "summary": "Repeated high score item.",
                },
                {
                    "title": "Fresh One",
                    "url": "https://example.com/fresh-1",
                    "score": 90.0,
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "summary": "Fresh candidate one.",
                },
                {
                    "title": "Fresh Two",
                    "url": "https://example.com/fresh-2",
                    "score": 88.0,
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "summary": "Fresh candidate two.",
                },
                {
                    "title": "Fresh Three",
                    "url": "https://example.com/fresh-3",
                    "score": 86.0,
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "summary": "Fresh candidate three.",
                },
            ],
        }
        sms = build_sms_digest(payload)
        self.assertNotIn("Repeat Item", sms)
        self.assertIn("Fresh One", sms)
        self.assertIn("Fresh Two", sms)
        self.assertIn("Fresh Three", sms)

    def test_project_generation_mixes_signal_and_template_ideas(self) -> None:
        items = [
            SignalItem(
                title="browser-use/browser-use",
                url="https://github.com/browser-use/browser-use",
                source="GitHub Watchlist",
                group="repo",
                source_type="github_watchlist",
                summary="Browser automation for agents.",
                tags=["browser", "automation", "agent"],
                metadata={"language": "Python"},
            ),
            SignalItem(
                title="Modern evaluation patterns for agent systems",
                url="https://arxiv.org/abs/1234.5678",
                source="arXiv",
                group="research",
                source_type="arxiv",
                summary="Evaluation patterns for agent systems.",
                tags=["research", "evaluation", "agent"],
                metadata={},
            ),
        ]
        projects = generate_projects(items, history={"recent_project_titles": []})
        titles = [project.title for project in projects]
        self.assertTrue(any("Workflow Probe" in title for title in titles))
        self.assertTrue(any(title.endswith("Notebook Lab") or title == "Research to Notebook Lab" for title in titles))

    def test_imessage_script_path_uses_env_override(self) -> None:
        with patch.dict(os.environ, {"IMESSAGE_SCRIPT_PATH": "/tmp/custom-imessage.sh"}, clear=False):
            path = _resolve_imessage_script_path()
        self.assertEqual(path, Path("/tmp/custom-imessage.sh").resolve())

    def test_send_imessage_digest_calls_local_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "imessage.sh"
            script_path.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
            script_path.chmod(0o755)

            with patch.dict(
                os.environ,
                {
                    "IMESSAGE_SCRIPT_PATH": str(script_path),
                    "IMESSAGE_RECIPIENT": "+15557654321",
                },
                clear=False,
            ):
                with patch("ai_signal_routine.digests.subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stderr = ""
                    mock_run.return_value.stdout = ""
                    send_imessage_digest("hello world")
                    args, kwargs = mock_run.call_args
                    self.assertEqual(Path(args[0][0]), script_path.resolve())
                    self.assertIn("--recipient", args[0])
                    self.assertEqual(kwargs["input"], "hello world")


if __name__ == "__main__":
    unittest.main()
