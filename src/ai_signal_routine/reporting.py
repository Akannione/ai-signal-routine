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
    noise_items: list[SignalItem] | None = None,
) -> dict[str, Any]:
    noise_items = noise_items or []
    top_sources = Counter(item.source for item in items).most_common(5)
    category_counts = Counter(item.metadata.get("category", "Uncategorized") for item in items)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": config["profile"]["name"],
        "top_sources": [{"source": source, "count": count} for source, count in top_sources],
        "categories": [
            {"category": category, "count": count}
            for category, count in category_counts.most_common()
        ],
        "themes": [{"theme": theme, "count": count} for theme, count in themes],
        "memory_summary": summarize_items(items),
        "items": [serialize_item(item) for item in items],
        "builder_tracker": build_builder_tracker(items),
        "opportunity_radar": build_opportunity_radar(items),
        "noise_items": [serialize_item(item) for item in noise_items],
        "mini_projects": [serialize_project(project) for project in projects],
        "errors": errors,
    }


def build_markdown_report(
    config: dict[str, Any],
    items: list[SignalItem],
    projects: list[MiniProject],
    themes: list[tuple[str, int]],
    errors: list[str],
    noise_items: list[SignalItem] | None = None,
) -> str:
    noise_items = noise_items or []
    lines: list[str] = []
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    memory_summary = summarize_items(items)
    category_counts = Counter(item.metadata.get("category", "Uncategorized") for item in items)
    builder_tracker = build_builder_tracker(items)
    opportunity_radar = build_opportunity_radar(items)

    lines.append(f"# AI Operator Intelligence Briefing")
    lines.append("")
    lines.append(f"Generated: {generated_at}")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Reviewed {len(items)} ranked operator signals for `{config['profile']['name']}`.")
    if themes:
        lines.append(
            "- Strongest themes: "
            + ", ".join(f"`{theme}` ({count})" for theme, count in themes[:4])
            + "."
        )
    if category_counts:
        lines.append(
            "- Strongest categories: "
            + ", ".join(f"`{category}` ({count})" for category, count in category_counts.most_common(4))
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
    lines.append("## Immediate Radar")
    lines.append("")
    lines.append("| Score | Category | Source | Published | Decision | Recommendation | Signal |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for item in items:
        safe_title = item.title.replace("|", "\\|")
        operator = item.metadata.get("operator", default_operator_state())
        intel = item.metadata.get("operator_intelligence", {})
        category = item.metadata.get("category", "Uncategorized")
        recommendation = intel.get("recommendation", "Monitor")
        lines.append(
            f"| {item.score:.1f} | {category} | {item.source} | {item.published_label()} | {operator.get('decision', 'unreviewed')} | {recommendation} | [{safe_title}]({item.url}) |"
        )
    lines.append("")

    lines.append("## Major Insights")
    lines.append("")
    for item in items[:8]:
        intel = item.metadata.get("operator_intelligence", {})
        if not intel:
            continue
        lines.append(f"### {intel.get('title', item.title)}")
        lines.append(f"1. TITLE: [{item.title}]({item.url})")
        lines.append(f"2. CATEGORY: {intel.get('category', item.metadata.get('category', 'Uncategorized'))}")
        lines.append(f"3. WHY IT MATTERS: {intel.get('why_it_matters', 'Relevant to your operator path.')}")
        lines.append(f"4. WHO IS USING IT: {intel.get('who_is_using_it', 'Builders and practitioners.')}")
        lines.append(f"5. LEVERAGE CREATED: {intel.get('leverage_created', 'Reusable workflow leverage.')}")
        lines.append(f"6. SKILL GAIN: {intel.get('skill_gain', 'Implementation judgment and technical fluency.')}")
        lines.append(f"7. MONETIZATION POTENTIAL: {intel.get('monetization_potential', 'Medium after validation.')}")
        lines.append(f"8. DIFFICULTY LEVEL: {intel.get('difficulty_level', 'Intermediate')}")
        lines.append(f"9. MARKET SATURATION: {intel.get('market_saturation', 'Medium')}")
        lines.append(f"10. ACTIONABLE NEXT STEP: {intel.get('actionable_next_step', 'Run one small validation task.')}")
        lines.append(f"11. WHETHER TO: {intel.get('recommendation', 'Monitor')}")
        scorecard = intel.get("scorecard", {})
        if scorecard:
            lines.append(
                f"- Signal scorecard: "
                + ", ".join(f"{key.replace('_', ' ')} {value}/10" for key, value in scorecard.items())
            )
        lines.append("")

    if opportunity_radar:
        lines.append("## Opportunity Radar")
        lines.append("")
        for opportunity in opportunity_radar[:6]:
            lines.append(
                f"- `{opportunity['recommendation']}` [{opportunity['title']}]({opportunity['url']}) | "
                f"{opportunity['category']} | {opportunity['why']}"
            )
        lines.append("")

    if builder_tracker:
        lines.append("## High-Signal Builders Tracker")
        lines.append("")
        for builder in builder_tracker[:8]:
            lines.append(
                f"- {builder['builder']} | score {builder['score']:.1f} | {builder['signal_count']} signal(s) | "
                f"{builder['why']}"
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

    if noise_items:
        lines.append("## Noise/Hype To Ignore")
        lines.append("")
        for item in noise_items[:5]:
            noise_hits = item.metadata.get("noise_hits", [])
            noise_text = ", ".join(noise_hits[:3]) if noise_hits else "low operator fit"
            lines.append(
                f"- [{item.title}]({item.url}) | score {item.score:.1f} | filter: {noise_text}"
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


def build_builder_tracker(items: list[SignalItem]) -> list[dict[str, Any]]:
    grouped: dict[str, list[SignalItem]] = {}
    for item in items:
        builder = _builder_name(item)
        if not builder:
            continue
        grouped.setdefault(builder, []).append(item)

    tracker: list[dict[str, Any]] = []
    for builder, builder_items in grouped.items():
        top_item = max(builder_items, key=lambda current: current.score)
        average_score = sum(item.score for item in builder_items) / len(builder_items)
        category = top_item.metadata.get("category", "Uncategorized")
        why = _builder_reason(top_item, category)
        tracker.append(
            {
                "builder": builder,
                "score": round(average_score, 1),
                "signal_count": len(builder_items),
                "top_signal": top_item.title,
                "top_url": top_item.url,
                "category": category,
                "why": why,
            }
        )
    return sorted(tracker, key=lambda item: (item["signal_count"], item["score"]), reverse=True)


def build_opportunity_radar(items: list[SignalItem]) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []
    for item in items:
        intel = item.metadata.get("operator_intelligence", {})
        scorecard = item.metadata.get("scorecard", {})
        recommendation = intel.get("recommendation", "Monitor")
        category = item.metadata.get("category", "Uncategorized")
        if recommendation not in {"Monetize", "Build With"} and category not in {
            "Freelance Leverage",
            "Startup Opportunities",
            "Underrated Opportunities",
            "Automation Systems",
            "Analytics/Data Engineering",
        }:
            continue
        opportunity_score = (
            scorecard.get("monetization_potential", 0)
            + scorecard.get("real_world_utility", 0)
            + scorecard.get("leverage_potential", 0)
            + scorecard.get("strategic_edge", 0)
        )
        opportunities.append(
            {
                "title": item.title,
                "url": item.url,
                "category": category,
                "recommendation": recommendation,
                "opportunity_score": opportunity_score,
                "why": intel.get("leverage_created", "Practical workflow leverage."),
                "next_step": intel.get("actionable_next_step", "Run one bounded validation."),
            }
        )
    return sorted(opportunities, key=lambda item: item["opportunity_score"], reverse=True)


def _builder_name(item: SignalItem) -> str:
    if item.source_type in {"github_search", "github_watchlist", "github_releases_watchlist"}:
        if "/" in item.title:
            return item.title.split("/", 1)[0]
        repo = item.metadata.get("repo")
        if isinstance(repo, str) and "/" in repo:
            return repo.split("/", 1)[0]
    if item.group in {"builder", "startup"}:
        return item.source
    if item.source == "Hacker News":
        return "Hacker News builders"
    if "Reddit" in item.source:
        subreddit = item.metadata.get("subreddit")
        return f"r/{subreddit}" if isinstance(subreddit, str) and subreddit else "Reddit practitioners"
    return ""


def _builder_reason(item: SignalItem, category: str) -> str:
    intel = item.metadata.get("operator_intelligence", {})
    if intel.get("who_is_using_it"):
        return str(intel["who_is_using_it"])
    if category == "High-Signal Builders":
        return "Repeated implementation detail instead of commentary."
    return f"Top related signal: {item.title}"


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
        "category": item.metadata.get("category", "Uncategorized"),
        "scorecard": item.metadata.get("scorecard", {}),
        "operator_intelligence": item.metadata.get("operator_intelligence", {}),
        "operator": item.metadata.get("operator", default_operator_state()),
        "analysis": item.metadata.get("analysis", {}),
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
