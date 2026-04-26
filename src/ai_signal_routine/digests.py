from __future__ import annotations

import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

import requests


def build_slack_digest(payload: dict[str, Any], max_items: int = 6) -> str:
    lines: list[str] = []
    generated_at = _timestamp_label(payload.get("generated_at"))
    queue = payload.get("memory_summary", {})
    themes = payload.get("themes", [])

    lines.append(f"*AI Signal Briefing* | {generated_at}")
    if themes:
        lines.append(
            "*Top themes:* "
            + ", ".join(f"{theme['theme']} ({theme['count']})" for theme in themes[:3])
        )
    lines.append(
        "*Queue:* "
        f"implement {queue.get('implement', 0)} | "
        f"test {queue.get('test', 0)} | "
        f"watch {queue.get('watch', 0)}"
    )
    lines.append("")
    lines.append("*Top signals*")
    for item in payload.get("items", [])[:max_items]:
        operator = item.get("operator", {})
        decision = operator.get("decision", "unreviewed")
        why = "; ".join(item.get("rationale", [])[:2]) or "Relevant signal"
        lines.append(
            f"- <{item['url']}|{item['title']}> | score {item['score']:.1f} | `{decision}` | {why}"
        )

    action_items = [
        item
        for item in payload.get("items", [])
        if item.get("operator", {}).get("next_action")
    ][:4]
    if action_items:
        lines.append("")
        lines.append("*Next actions*")
        for item in action_items:
            operator = item.get("operator", {})
            lines.append(
                f"- {item['title']}: {operator.get('next_action')} ({operator.get('decision', 'unreviewed')})"
            )
    return "\n".join(lines).strip() + "\n"


def build_email_digest(payload: dict[str, Any], max_items: int = 8) -> str:
    lines: list[str] = []
    generated_at = _timestamp_label(payload.get("generated_at"))
    queue = payload.get("memory_summary", {})
    lines.append("# AI Signal Digest")
    lines.append("")
    lines.append(f"Generated: {generated_at}")
    lines.append("")
    lines.append("## Queue")
    lines.append("")
    lines.append(
        f"- Implement now: {queue.get('implement', 0)} | Test next: {queue.get('test', 0)} | Watchlist: {queue.get('watch', 0)}"
    )
    lines.append("")
    lines.append("## Priority Signals")
    lines.append("")
    for item in payload.get("items", [])[:max_items]:
        operator = item.get("operator", {})
        lines.append(f"### {item['title']}")
        lines.append(f"- Decision: `{operator.get('decision', 'unreviewed')}`")
        lines.append(f"- Source: {item['source']} | Score: {item['score']:.1f}")
        lines.append(f"- Link: {item['url']}")
        why = "; ".join(item.get("rationale", [])[:3]) or "Relevant to your focus."
        lines.append(f"- Why it matters: {why}")
        if operator.get("next_action"):
            lines.append(f"- Next action: {operator['next_action']}")
        if operator.get("notes"):
            lines.append(f"- Notes: {operator['notes']}")
        lines.append("")

    mini_projects = payload.get("mini_projects", [])[:3]
    if mini_projects:
        lines.append("## Suggested Builds")
        lines.append("")
        for project in mini_projects:
            lines.append(f"- {project['title']}: {project['build_scope']}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def write_digests(email_digest: str, slack_digest: str, outdir: Path) -> tuple[Path, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    archive_dir = outdir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    email_path = outdir / "latest_email_digest.md"
    slack_path = outdir / "latest_slack_digest.txt"
    email_path.write_text(email_digest, encoding="utf-8")
    slack_path.write_text(slack_digest, encoding="utf-8")
    (archive_dir / f"email_digest_{timestamp}.md").write_text(email_digest, encoding="utf-8")
    (archive_dir / f"slack_digest_{timestamp}.txt").write_text(slack_digest, encoding="utf-8")
    return email_path, slack_path


def send_slack_digest(slack_digest: str, webhook_url: str) -> None:
    response = requests.post(webhook_url, json={"text": slack_digest}, timeout=20)
    response.raise_for_status()


def send_email_digest(email_digest: str, subject: str) -> None:
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    username = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")
    sender = os.environ["SMTP_FROM"]
    recipients = [value.strip() for value in os.environ["SMTP_TO"].split(",") if value.strip()]

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message.set_content(email_digest)

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)


def _timestamp_label(value: str | None) -> str:
    if not value:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
