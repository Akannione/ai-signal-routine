from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .benchmark import write_benchmark_pack
from .agent_briefing import create_agent_briefing
from .digests import (
    build_email_digest,
    build_slack_digest,
    send_email_digest,
    send_slack_digest,
    write_digests,
)
from .history import export_history_tables, record_briefing
from .memory import attach_memory_to_items, ensure_memory_file
from .mini_projects import generate_projects
from .reporting import build_markdown_report, build_report_payload, write_reports
from .scoring import dedupe_items, score_items, select_top_items, summarize_themes
from .sources import SourceCollector


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build an AI and analytics research briefing.")
    parser.add_argument(
        "--config",
        default="config/sources.json",
        help="Path to the sources config JSON file.",
    )
    parser.add_argument(
        "--outdir",
        default="reports",
        help="Directory where the markdown and JSON reports will be written.",
    )
    parser.add_argument(
        "--memory",
        default="data/operator_memory.json",
        help="Path to the operator memory JSON file.",
    )
    parser.add_argument(
        "--history-db",
        default="data/signal_history.sqlite",
        help="Path to the SQLite history database for trend reporting.",
    )
    parser.add_argument(
        "--history-export-dir",
        default="reports/history_exports",
        help="Directory where history CSV exports will be written.",
    )
    parser.add_argument(
        "--skip-history",
        action="store_true",
        help="Skip writing the SQLite history database and CSV exports.",
    )
    parser.add_argument(
        "--benchmark-dir",
        default="benchmarks",
        help="Directory where the benchmark pack will be written.",
    )
    parser.add_argument(
        "--skip-digests",
        action="store_true",
        help="Skip writing email and Slack digest files.",
    )
    parser.add_argument(
        "--send-digests",
        action="store_true",
        help="Send digests if `SLACK_WEBHOOK_URL` or SMTP settings are available.",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    outdir = Path(args.outdir)
    memory_path = Path(args.memory)
    history_db = Path(args.history_db)
    history_export_dir = Path(args.history_export_dir)
    benchmark_dir = Path(args.benchmark_dir)
    config = load_config(config_path)

    collector = SourceCollector()
    result = collector.fetch_all(config)
    scored = score_items(result.items, config)
    deduped = dedupe_items(scored)
    selected = select_top_items(deduped, config)
    memory = ensure_memory_file(memory_path)
    selected = attach_memory_to_items(selected, memory)
    themes = summarize_themes(selected)
    projects = generate_projects(selected)

    payload = build_report_payload(config, selected, projects, themes, result.errors)
    markdown = build_markdown_report(config, selected, projects, themes, result.errors)
    latest_md, latest_json = write_reports(markdown, payload, outdir)

    print(f"Wrote {len(selected)} ranked items to {latest_md}")
    print(f"Wrote JSON payload to {latest_json}")

    if not args.skip_history:
        history_result = record_briefing(history_db, payload)
        export_paths = export_history_tables(history_db, history_export_dir)
        print(
            "Wrote SQLite history to "
            f"{history_db} ({history_result['items_recorded']} signals in run {history_result['run_id']})"
        )
        if export_paths:
            print(f"Wrote history CSV exports to {history_export_dir}")

    if not args.skip_digests:
        email_digest = build_email_digest(payload)
        raw_slack_digest = build_slack_digest(payload)

        try:
            slack_digest = create_agent_briefing(raw_slack_digest)
        except Exception as error:
            print(f"Agent briefing failed, using normal digest: {error}")
            slack_digest = raw_slack_digest

        email_path, slack_path = write_digests(email_digest, slack_digest, outdir)
        print(f"Wrote email digest to {email_path}")
        print(f"Wrote Slack digest to {slack_path}")
        if args.send_digests:
            _send_digests_if_configured(email_digest, slack_digest)

    benchmark_paths = write_benchmark_pack(benchmark_dir)
    print(f"Wrote benchmark pack to {benchmark_paths['readme'].parent}")

    if result.errors:
        print("Some sources failed:")
        for error in result.errors:
            print(f"- {error}")
    return 0


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _send_digests_if_configured(email_digest: str, slack_digest: str) -> None:
    slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if slack_webhook:
        send_slack_digest(slack_digest, slack_webhook)
        print("Sent Slack digest.")
    else:
        print("Skipped Slack send. `SLACK_WEBHOOK_URL` is not set.")

    required_email_env = {"SMTP_HOST", "SMTP_FROM", "SMTP_TO"}
    if required_email_env.issubset(os.environ):
        send_email_digest(email_digest, "AI Signal Digest")
        print("Sent email digest.")
    else:
        print("Skipped email send. SMTP settings are incomplete.")
