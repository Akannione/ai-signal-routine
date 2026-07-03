from __future__ import annotations

import os
import smtplib
import subprocess
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

import requests

from .utils import canonicalize_url


def build_sms_digest(payload: dict[str, Any], max_items: int = 3) -> str:
    lines: list[str] = []
    items = _select_daily_items(payload.get("items", []), payload.get("history", {}), max_items)

    lines.append("AI OPERATOR DAILY")
    lines.append("")

    themes = payload.get("themes", [])
    if themes:
        clean = ", ".join(_titleize_theme(str(theme["theme"])) for theme in themes[:3])
        lines.append(f"Themes: {clean}")
        lines.append("")

    lines.append("Top Signals:")
    for index, item in enumerate(items, start=1):
        summary = " ".join((item.get("summary") or "").split())
        action = _daily_action_label(item)
        intel = _operator_intel(item)
        category = item.get("category") or intel.get("category", "Signal")
        short_summary = _truncate(summary, 110) if summary else "Relevant AI workflow signal"

        lines.append(f"{index}) {item['title']}")
        lines.append(f"{category}: {short_summary}")
        lines.append(f"→ Action: {action}")
        lines.append(item["url"])
        lines.append("")

    project = _select_daily_project(payload.get("mini_projects", []), payload.get("history", {}))
    if project:
        lines.append("Project:")
        lines.append(_truncate(project["title"], 80))

    message = "\n".join(lines).strip() + "\n"
    return message[:1400]


def build_slack_digest(payload: dict[str, Any], max_items: int = 6) -> str:
    lines: list[str] = []
    generated_at = _timestamp_label(payload.get("generated_at"))
    queue = payload.get("memory_summary", {})
    themes = payload.get("themes", [])

    lines.append(f"*AI Operator Intelligence* | {generated_at}")
    if themes:
        lines.append(
            "*Top themes:* "
            + ", ".join(f"{theme['theme']} ({theme['count']})" for theme in themes[:3])
        )
    categories = payload.get("categories", [])
    if categories:
        lines.append(
            "*Top categories:* "
            + ", ".join(f"{item['category']} ({item['count']})" for item in categories[:3])
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
        intel = _operator_intel(item)
        recommendation = intel.get("recommendation", "Monitor")
        category = item.get("category") or intel.get("category", "Signal")
        why = "; ".join(item.get("rationale", [])[:2]) or "Relevant signal"
        lines.append(
            f"- <{item['url']}|{item['title']}> | {category} | score {item['score']:.1f} | `{decision}` | {recommendation} | {why}"
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
    lines.append("# AI Operator Intelligence Digest")
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
        analysis = item.get("analysis") or item.get("metadata", {}).get("analysis", {})
        intel = _operator_intel(item)
        lines.append(f"### {item['title']}")
        lines.append(f"- Category: {item.get('category') or intel.get('category', 'Uncategorized')}")
        lines.append(f"- Decision: `{operator.get('decision', 'unreviewed')}`")
        lines.append(f"- Recommendation: `{intel.get('recommendation', 'Monitor')}`")
        lines.append(f"- Source: {item['source']} | Score: {item['score']:.1f}")
        lines.append(f"- Link: {item['url']}")
        why = intel.get("why_it_matters") or "; ".join(item.get("rationale", [])[:3]) or "Relevant to your focus."
        lines.append(f"- Why it matters: {why}")
        if intel.get("leverage_created"):
            lines.append(f"- Leverage created: {intel['leverage_created']}")
        if intel.get("skill_gain"):
            lines.append(f"- Skill gain: {intel['skill_gain']}")
        if intel.get("monetization_potential"):
            lines.append(f"- Monetization: {intel['monetization_potential']}")
        if intel.get("actionable_next_step"):
            lines.append(f"- Next operator step: {intel['actionable_next_step']}")
        if analysis.get("how_it_works"):
            lines.append(f"- How it works: {analysis['how_it_works']}")
        if analysis.get("should_i_implement"):
            lines.append(f"- Should you implement it: {analysis['should_i_implement']}")
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


def write_digests(
    email_digest: str, slack_digest: str, sms_digest: str, outdir: Path
) -> tuple[Path, Path, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    archive_dir = outdir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    email_path = outdir / "latest_email_digest.md"
    slack_path = outdir / "latest_slack_digest.txt"
    sms_path = outdir / "latest_sms_digest.txt"
    email_path.write_text(email_digest, encoding="utf-8")
    slack_path.write_text(slack_digest, encoding="utf-8")
    sms_path.write_text(sms_digest, encoding="utf-8")
    (archive_dir / f"email_digest_{timestamp}.md").write_text(email_digest, encoding="utf-8")
    (archive_dir / f"slack_digest_{timestamp}.txt").write_text(slack_digest, encoding="utf-8")
    (archive_dir / f"sms_digest_{timestamp}.txt").write_text(sms_digest, encoding="utf-8")
    return email_path, slack_path, sms_path


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


def send_imessage_digest(sms_digest: str) -> None:
    recipient = os.environ["IMESSAGE_RECIPIENT"]
    script_path = _resolve_imessage_script_path()
    if not script_path.exists():
        raise RuntimeError(
            f"iMessage script not found at {script_path}. Create it or set `IMESSAGE_SCRIPT_PATH`."
        )
    if not os.access(script_path, os.X_OK):
        raise RuntimeError(
            f"iMessage script is not executable: {script_path}. Run `chmod +x {script_path}`."
        )

    completed = subprocess.run(
        [str(script_path), "--recipient", recipient],
        check=False,
        input=sms_digest,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        error_text = completed.stderr.strip() or completed.stdout.strip() or "Unknown AppleScript error"
        if 'Can’t get application "Messages"' in error_text or "Connection invalid" in error_text:
            raise RuntimeError(
                "Messages app automation is unavailable in this execution environment. "
                "Run the same command from the Mac Terminal while signed into iMessage and allow automation access."
            )
        raise RuntimeError(error_text)


def _timestamp_label(value: str | None) -> str:
    if not value:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _titleize_theme(value: str) -> str:
    return value.replace("-", " ").title()


def _operator_intel(item: dict[str, Any]) -> dict[str, Any]:
    intel = item.get("operator_intelligence")
    if isinstance(intel, dict):
        return intel
    metadata = item.get("metadata", {})
    if isinstance(metadata, dict):
        nested = metadata.get("operator_intelligence")
        if isinstance(nested, dict):
            return nested
    return {}


def _daily_action_label(item: dict[str, Any]) -> str:
    operator = item.get("operator", {})
    decision = operator.get("decision", "unreviewed")
    if decision == "implement":
        return "Implement now"
    if decision == "test":
        return "Test this week"
    recommendation = _operator_intel(item).get("recommendation")
    if recommendation == "Monetize":
        return "Package offer"
    if recommendation == "Build With":
        return "Build proof"
    if recommendation == "Learn":
        return "Study by building"
    if recommendation == "Ignore":
        return "Ignore"
    if item.get("score", 0) >= 85:
        return "Test this week"
    return "Review"


def _select_daily_items(
    items: list[dict[str, Any]], history: dict[str, Any], max_items: int
) -> list[dict[str, Any]]:
    recent_top_urls = {
        canonicalize_url(url)
        for url in history.get("recent_top_urls", [])
        if isinstance(url, str) and url
    }
    ranked = sorted(items, key=lambda item: _daily_item_sort_key(item, recent_top_urls))
    return ranked[:max_items]


def _select_daily_project(
    projects: list[dict[str, Any]], history: dict[str, Any]
) -> dict[str, Any] | None:
    if not projects:
        return None
    recent_titles = {
        str(title).lower().strip()
        for title in history.get("recent_project_titles", [])
        if isinstance(title, str) and title
    }
    for project in projects:
        title = str(project.get("title", "")).lower().strip()
        if title and title not in recent_titles:
            return project
    return projects[0]


def _daily_item_sort_key(item: dict[str, Any], recent_top_urls: set[str]) -> tuple[int, float, float]:
    canonical_url = canonicalize_url(str(item.get("url", "")))
    repeated = 1 if canonical_url in recent_top_urls else 0
    published_at = _parse_payload_datetime(item.get("published_at"))
    published_rank = -published_at.timestamp() if published_at else 0.0
    score_rank = -float(item.get("score", 0.0))
    return (repeated, published_rank, score_rank)


def _parse_payload_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _resolve_imessage_script_path() -> Path:
    configured = os.environ.get("IMESSAGE_SCRIPT_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / "scripts" / "imessage.sh"
