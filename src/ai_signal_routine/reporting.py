from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .memory import default_operator_state, summarize_items
from .models import MiniProject, SignalItem


def build_report_payload(
    config: dict[str, Any],
    items: list[SignalItem],
    projects: list[MiniProject],
    themes: list[tuple[str, int]],
    errors: list[str],
) -> dict[str, Any]:
    top_sources = Counter(item.source for item in items).most_common(5)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": config["profile"]["name"],
        "top_sources": [{"source": source, "count": count} for source, count in top_sources],
        "themes": [{"theme": theme, "count": count} for theme, count in themes],
        "memory_summary": summarize_items(items),
        "items": [serialize_item(item) for item in items],
        "mini_projects": [serialize_project(project) for project in projects],
        "errors": errors,
    }


def build_markdown_report(
    config: dict[str, Any],
    items: list[SignalItem],
    projects: list[MiniProject],
    themes: list[tuple[str, int]],
    errors: list[str],
) -> str:
    lines: list[str] = []
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    memory_summary = summarize_items(items)
    lines.append(f"# AI Signal Briefing")
    lines.append("")
    lines.append(f"Generated: {generated_at}")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Reviewed {len(items)} ranked signals for `{config['profile']['name']}`.")
    if themes:
        lines.append(
            "- Strongest themes: "
            + ", ".join(f"`{theme}` ({count})" for theme, count in themes[:4])
            + "."
        )
    lines.append(
        "- Review queue: "
        f"`implement` {memory_summary.get('implement', 0)}, "
        f"`test` {memory_summary.get('test', 0)}, "
        f"`watch` {memory_summary.get('watch', 0)}, "
        f"`unreviewed` {memory_summary.get('unreviewed', 0)}."
    )
    if items:
        lines.append(f"- Highest-priority signal: [{items[0].title}]({items[0].url}).")
    lines.append("")
    lines.append("## Top Signals")
    lines.append("")
    lines.append("| Score | Source | Published | Decision | Signal | Why it matters |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for item in items:
        why = "; ".join(item.rationale) if item.rationale else "Relevant to your focus."
        safe_title = item.title.replace("|", "\\|")
        operator = item.metadata.get("operator", default_operator_state())
        lines.append(
            f"| {item.score:.1f} | {item.source} | {item.published_label()} | {operator.get('decision', 'unreviewed')} | [{safe_title}]({item.url}) | {why} |"
        )
    lines.append("")

    repo_items = [
        item for item in items if item.metadata.get("watchlist")
    ] + [
        item for item in items if item.source_type == "github_search" and not item.metadata.get("watchlist")
    ]
    repo_items = repo_items[:6]
    if repo_items:
        lines.append("## GitHub Radar")
        lines.append("")
        for item in repo_items:
            stars = item.metadata.get("stars")
            stars_text = f"{stars:,} stars" if isinstance(stars, int) else "stars unknown"
            operator = item.metadata.get("operator", default_operator_state())
            lines.append(
                f"- [{item.title}]({item.url}) | {stars_text} | {operator.get('decision', 'unreviewed')} | {item.summary or 'Popular repo worth evaluating.'}"
            )
        lines.append("")

    action_items = [
        item
        for item in items
        if item.metadata.get("operator", {}).get("decision") in {"watch", "test", "implement"}
    ]
    if action_items:
        lines.append("## Action Queue")
        lines.append("")
        for item in action_items[:8]:
            operator = item.metadata.get("operator", default_operator_state())
            next_action = operator.get("next_action") or "Decide the next experiment."
            lines.append(
                f"- `{operator.get('decision', 'unreviewed')}` [{item.title}]({item.url}) | Next: {next_action}"
            )
        lines.append("")

    lines.append("## Mini Projects")
    lines.append("")
    for project in projects:
        lines.append(f"### {project.title}")
        lines.append(project.why_now)
        lines.append("")
        lines.append(f"- Build: {project.build_scope}")
        lines.append(f"- Stack: {project.stack}")
        lines.append(f"- Success: {project.success_metric}")
        lines.append(f"- Prompt seed: `{project.prompt_seed}`")
        lines.append("")

    if errors:
        lines.append("## Source Health")
        lines.append("")
        for error in errors:
            lines.append(f"- {error}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def write_reports(markdown: str, payload: dict[str, Any], outdir: Path) -> tuple[Path, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    archive_dir = outdir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    latest_md = outdir / "latest_briefing.md"
    latest_json = outdir / "latest_briefing.json"
    latest_md.write_text(markdown, encoding="utf-8")
    latest_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (archive_dir / f"briefing_{timestamp}.md").write_text(markdown, encoding="utf-8")
    (archive_dir / f"briefing_{timestamp}.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    return latest_md, latest_json


def serialize_item(item: SignalItem) -> dict[str, Any]:
    return {
        "title": item.title,
        "url": item.url,
        "source": item.source,
        "group": item.group,
        "source_type": item.source_type,
        "published_at": item.published_at.isoformat() if item.published_at else None,
        "summary": item.summary,
        "tags": item.tags,
        "score": item.score,
        "rationale": item.rationale,
        "operator": item.metadata.get("operator", default_operator_state()),
        "metadata": item.metadata,
    }


def serialize_project(project: MiniProject) -> dict[str, Any]:
    return {
        "title": project.title,
        "why_now": project.why_now,
        "build_scope": project.build_scope,
        "stack": project.stack,
        "success_metric": project.success_metric,
        "prompt_seed": project.prompt_seed,
    }
