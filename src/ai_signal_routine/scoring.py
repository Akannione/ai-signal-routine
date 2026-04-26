from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from .models import SignalItem
from .utils import canonicalize_url, keyword_hits


THEME_KEYWORDS = {
    "coding-agents": ["claude", "codex", "coding", "developer", "agent", "agents"],
    "workflow-automation": ["workflow", "automation", "tool use", "mcp", "browser"],
    "analytics-ai": ["analytics", "sql", "warehouse", "dashboard", "spreadsheet"],
    "data-science-systems": ["data science", "evaluation", "benchmark", "observability", "mlops"],
    "research-radar": ["research", "paper", "llm", "generative ai", "retrieval", "rag"]
}

REPO_PRIORITY_TERMS = [
    "claude",
    "codex",
    "mcp",
    "browser",
    "agent",
    "llm",
    "rag",
    "analytics",
    "data science",
    "workflow",
    "automation",
    "warehouse",
    "observability",
]


def score_items(items: list[SignalItem], config: dict[str, Any]) -> list[SignalItem]:
    profile = config["profile"]
    now = datetime.now(timezone.utc)
    for item in items:
        score_item(item, profile, now)
    return items


def score_item(item: SignalItem, profile: dict[str, Any], now: datetime) -> None:
    haystack = " ".join(
        [
            item.title,
            item.summary,
            item.source,
            " ".join(item.tags),
            str(item.metadata.get("query", "")),
        ]
    ).lower()

    topic_hits = keyword_hits(haystack, profile["topic_keywords"])
    business_hits = keyword_hits(haystack, profile["business_keywords"])
    learning_hits = keyword_hits(haystack, profile["learning_keywords"])
    age_days = item.age_days(now)

    source_score = profile["source_group_weights"].get(item.group, 0)
    topic_score = min(28, len(set(topic_hits)) * 5)
    business_score = min(16, len(set(business_hits)) * 4)
    learning_score = min(10, len(set(learning_hits)) * 3)
    recency_score = _recency_score(age_days)
    repo_score = _repo_score(item)

    tooling_boost = 0
    if any(term in haystack for term in ("claude", "codex", "mcp", "browser", "agent")):
        tooling_boost += 6
    if any(term in haystack for term in ("analytics", "sql", "dashboard", "warehouse")):
        tooling_boost += 5

    if item.metadata.get("watchlist"):
        tooling_boost += 8

    if any(term in haystack for term in ("awesome", "everything", "guide")) and not item.metadata.get("watchlist"):
        tooling_boost -= 14

    if item.source_type in {"github_search", "github_watchlist"} and not any(
        term in haystack for term in REPO_PRIORITY_TERMS
    ):
        tooling_boost -= 20

    total = source_score + topic_score + business_score + learning_score + recency_score + repo_score + tooling_boost
    if not topic_hits and item.group != "repo":
        total -= 10

    rationale: list[str] = []
    if topic_hits:
        rationale.append(f"Hits your focus: {', '.join(sorted(set(topic_hits))[:3])}")
    if business_hits:
        rationale.append(f"Business angle: {', '.join(sorted(set(business_hits))[:2])}")
    if age_days is not None and age_days <= 7:
        rationale.append("Fresh signal from the last week")
    stars = item.metadata.get("stars")
    if isinstance(stars, int) and stars >= 10000:
        rationale.append(f"Strong adoption signal: {stars:,} GitHub stars")
    if item.metadata.get("watchlist"):
        rationale.append("Curated workflow repo to keep on your radar")

    item.score = round(max(total, 0), 1)
    item.rationale = rationale[:3]
    item.metadata["topic_hits"] = sorted(set(topic_hits))
    item.metadata["business_hits"] = sorted(set(business_hits))
    item.metadata["learning_hits"] = sorted(set(learning_hits))
    item.metadata["age_days"] = age_days


def dedupe_items(items: list[SignalItem]) -> list[SignalItem]:
    seen: set[str] = set()
    unique: list[SignalItem] = []
    for item in sorted(items, key=lambda current: current.score, reverse=True):
        key = canonicalize_url(item.url) or item.title.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def select_top_items(items: list[SignalItem], config: dict[str, Any]) -> list[SignalItem]:
    max_items = config["limits"]["final_items"]
    max_per_source = config["limits"]["max_per_source_in_report"]
    selected: list[SignalItem] = []
    source_counts: Counter[str] = Counter()
    for item in sorted(items, key=lambda current: current.score, reverse=True):
        if item.score < 18:
            continue
        if source_counts[item.source] >= max_per_source:
            continue
        selected.append(item)
        source_counts[item.source] += 1
        if len(selected) >= max_items:
            break
    return selected


def split_repos(items: list[SignalItem]) -> tuple[list[SignalItem], list[SignalItem]]:
    repos = [item for item in items if item.source_type == "github_search"]
    non_repos = [item for item in items if item.source_type != "github_search"]
    return repos, non_repos


def summarize_themes(items: list[SignalItem]) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for item in items:
        haystack = " ".join([item.title, item.summary, " ".join(item.tags)]).lower()
        for theme, terms in THEME_KEYWORDS.items():
            if any(term in haystack for term in terms):
                counter[theme] += 1
    return counter.most_common(5)


def _repo_score(item: SignalItem) -> float:
    stars = item.metadata.get("stars")
    if not isinstance(stars, int) or stars <= 0:
        return 0.0
    star_component = min(18.0, math.log10(stars + 1) * 4.8)
    freshness_bonus = 0.0
    updated_at = item.metadata.get("updated_at")
    if isinstance(updated_at, str):
        parsed = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        age_days = max((datetime.now(timezone.utc) - parsed).total_seconds() / 86400, 0.0)
        if age_days <= 30:
            freshness_bonus = 4.0
    return star_component + freshness_bonus


def _recency_score(age_days: float | None) -> float:
    if age_days is None:
        return 2.0
    if age_days <= 2:
        return 18.0
    if age_days <= 7:
        return 14.0
    if age_days <= 14:
        return 10.0
    if age_days <= 30:
        return 6.0
    if age_days <= 90:
        return 3.0
    return 0.0
