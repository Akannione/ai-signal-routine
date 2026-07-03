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
    "research-radar": ["research", "paper", "llm", "generative ai", "retrieval", "rag"],
    "operator-opportunities": ["freelance", "consulting", "internal tool", "workflow", "back office"],
}

CATEGORY_ORDER = [
    "Immediate Edge",
    "Emerging Infrastructure",
    "AI Engineering",
    "Automation Systems",
    "Analytics/Data Engineering",
    "Freelance Leverage",
    "Startup Opportunities",
    "High-Signal Builders",
    "Experimental Workflows",
    "Tooling Stack",
    "Underrated Opportunities",
    "Noise/Hype To Ignore",
]

SCORE_DIMENSIONS = [
    "technical_depth",
    "real_world_utility",
    "leverage_potential",
    "monetization_potential",
    "future_relevance",
    "learning_value",
    "speed_of_adoption",
    "difficulty_to_replicate",
    "career_value",
    "strategic_edge",
]

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

IMPLEMENT_TRIGGERS = {
    "automation",
    "workflow",
    "analytics",
    "sql",
    "warehouse",
    "evaluation",
    "mlops",
}


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
    operator_hits = keyword_hits(haystack, profile.get("operator_keywords", []))
    business_hits = keyword_hits(haystack, profile["business_keywords"])
    learning_hits = keyword_hits(haystack, profile["learning_keywords"])
    monetization_hits = keyword_hits(haystack, profile.get("monetization_keywords", []))
    noise_hits = keyword_hits(haystack, profile.get("noise_keywords", []))
    age_days = item.age_days(now)
    category = _classify_category(haystack, item, profile)
    scorecard = _dimension_scorecard(
        item,
        topic_hits=sorted(set(topic_hits)),
        operator_hits=sorted(set(operator_hits)),
        business_hits=sorted(set(business_hits)),
        learning_hits=sorted(set(learning_hits)),
        monetization_hits=sorted(set(monetization_hits)),
        noise_hits=sorted(set(noise_hits)),
        age_days=age_days,
    )

    source_score = profile["source_group_weights"].get(item.group, 0)
    topic_score = min(26, len(set(topic_hits)) * 4.5)
    operator_score = min(18, len(set(operator_hits)) * 4)
    business_score = min(18, len(set(business_hits)) * 4)
    learning_score = min(10, len(set(learning_hits)) * 3)
    monetization_score = min(16, len(set(monetization_hits)) * 4)
    recency_score = _recency_score(age_days)
    repo_score = _repo_score(item)
    dimension_score = sum(scorecard.values()) * 0.95

    tooling_boost = 0
    if any(term in haystack for term in ("claude", "codex", "mcp", "browser", "agent")):
        tooling_boost += 6
    if any(term in haystack for term in ("analytics", "sql", "dashboard", "warehouse")):
        tooling_boost += 5

    if item.metadata.get("watchlist"):
        tooling_boost += 8

    if item.group == "builder":
        tooling_boost += 6

    if category in {"Immediate Edge", "Underrated Opportunities", "Freelance Leverage"}:
        tooling_boost += 5

    if any(term in haystack for term in ("awesome", "everything", "guide")) and not item.metadata.get("watchlist"):
        tooling_boost -= 14

    noise_penalty = min(34, len(set(noise_hits)) * 9)
    if category == "Noise/Hype To Ignore":
        noise_penalty += 12

    if item.source_type in {"github_search", "github_watchlist"} and not any(
        term in haystack for term in REPO_PRIORITY_TERMS
    ):
        tooling_boost -= 20

    total = (
        source_score
        + topic_score
        + operator_score
        + business_score
        + learning_score
        + monetization_score
        + recency_score
        + repo_score
        + dimension_score
        + tooling_boost
        - noise_penalty
    )
    if not topic_hits and item.group != "repo":
        total -= 10
    if not operator_hits and not business_hits and item.group not in {"repo", "official", "research"}:
        total -= 8

    rationale: list[str] = []
    if topic_hits:
        rationale.append(f"Hits your focus: {', '.join(sorted(set(topic_hits))[:3])}")
    if operator_hits:
        rationale.append(f"Operator signal: {', '.join(sorted(set(operator_hits))[:2])}")
    if business_hits:
        rationale.append(f"Business angle: {', '.join(sorted(set(business_hits))[:2])}")
    if monetization_hits:
        rationale.append(f"Monetization angle: {', '.join(sorted(set(monetization_hits))[:2])}")
    if age_days is not None and age_days <= 7:
        rationale.append("Fresh signal from the last week")
    stars = item.metadata.get("stars")
    if isinstance(stars, int) and stars >= 10000:
        rationale.append(f"Strong adoption signal: {stars:,} GitHub stars")
    if item.metadata.get("watchlist"):
        rationale.append("Curated workflow repo to keep on your radar")
    if noise_hits:
        rationale.append(f"Noise filter hit: {', '.join(sorted(set(noise_hits))[:2])}")

    item.score = round(min(max(total * 0.55, 0), 100), 1)
    item.rationale = rationale[:4]
    item.metadata["category"] = category
    item.metadata["scorecard"] = scorecard
    item.metadata["topic_hits"] = sorted(set(topic_hits))
    item.metadata["operator_hits"] = sorted(set(operator_hits))
    item.metadata["business_hits"] = sorted(set(business_hits))
    item.metadata["learning_hits"] = sorted(set(learning_hits))
    item.metadata["monetization_hits"] = sorted(set(monetization_hits))
    item.metadata["noise_hits"] = sorted(set(noise_hits))
    item.metadata["age_days"] = age_days
    analysis = _build_analysis(
        item,
        topic_hits=sorted(set(topic_hits)),
        operator_hits=sorted(set(operator_hits)),
        business_hits=sorted(set(business_hits)),
        learning_hits=sorted(set(learning_hits)),
        monetization_hits=sorted(set(monetization_hits)),
        noise_hits=sorted(set(noise_hits)),
        age_days=age_days,
        category=category,
        scorecard=scorecard,
    )
    item.metadata["analysis"] = analysis
    item.metadata["operator_intelligence"] = _build_operator_intelligence(
        item,
        analysis=analysis,
        category=category,
        scorecard=scorecard,
        topic_hits=sorted(set(topic_hits)),
        operator_hits=sorted(set(operator_hits)),
        business_hits=sorted(set(business_hits)),
        monetization_hits=sorted(set(monetization_hits)),
        noise_hits=sorted(set(noise_hits)),
    )


def _classify_category(haystack: str, item: SignalItem, profile: dict[str, Any]) -> str:
    category_keywords = profile.get("category_keywords", {})
    best_category = "AI Engineering"
    best_score = 0
    for category in CATEGORY_ORDER:
        terms = category_keywords.get(category, [])
        score = sum(1 for term in terms if term.lower() in haystack)
        if score > best_score:
            best_category = category
            best_score = score

    noise_terms = category_keywords.get("Noise/Hype To Ignore", [])
    if any(term.lower() in haystack for term in noise_terms):
        return "Noise/Hype To Ignore"

    if item.metadata.get("release_watchlist"):
        return "Immediate Edge"
    if item.source_type in {"github_search", "github_watchlist", "github_releases_watchlist"}:
        if any(term in haystack for term in ("mcp", "observability", "gateway", "runtime", "orchestration")):
            return "Emerging Infrastructure"
        if any(term in haystack for term in ("browser", "playwright", "n8n", "automation", "pipeline")):
            return "Automation Systems"
        if any(term in haystack for term in ("sql", "analytics", "warehouse", "dbt", "duckdb", "semantic layer")):
            return "Analytics/Data Engineering"
        return "Tooling Stack"
    if item.group == "research":
        return "Experimental Workflows"
    if item.group == "builder":
        return "High-Signal Builders"
    if item.group == "startup":
        return "Startup Opportunities"
    return best_category


def _dimension_scorecard(
    item: SignalItem,
    *,
    topic_hits: list[str],
    operator_hits: list[str],
    business_hits: list[str],
    learning_hits: list[str],
    monetization_hits: list[str],
    noise_hits: list[str],
    age_days: float | None,
) -> dict[str, int]:
    stars = item.metadata.get("stars")
    star_signal = math.log10(stars + 1) if isinstance(stars, int) and stars > 0 else 0.0
    fresh = age_days is not None and age_days <= 14
    very_fresh = age_days is not None and age_days <= 3
    repo_signal = item.source_type in {"github_search", "github_watchlist", "github_releases_watchlist"}
    official_or_builder = item.group in {"official", "builder", "repo"}

    scorecard = {
        "technical_depth": 3
        + min(3, len(topic_hits))
        + (2 if repo_signal or item.group == "research" else 0)
        + (1 if any(term in topic_hits for term in ("evaluation", "observability", "mlops", "mcp")) else 0),
        "real_world_utility": 3
        + min(3, len(business_hits))
        + min(2, len(operator_hits))
        + (1 if item.metadata.get("watchlist") else 0),
        "leverage_potential": 3
        + min(3, len(operator_hits))
        + (2 if any(term in topic_hits for term in ("automation", "workflow", "agent", "analytics")) else 0)
        + (1 if repo_signal else 0),
        "monetization_potential": 2
        + min(4, len(monetization_hits))
        + (2 if set(business_hits) & {"sales", "finance", "operations", "reporting"} else 0),
        "future_relevance": 3
        + min(3, len(topic_hits))
        + (2 if official_or_builder else 0)
        + (1 if fresh else 0),
        "learning_value": 2
        + min(3, len(learning_hits))
        + min(2, len(topic_hits))
        + (2 if repo_signal or item.group == "research" else 0),
        "speed_of_adoption": 2
        + (2 if very_fresh else 0)
        + (2 if isinstance(stars, int) and stars >= 1000 else 0)
        + (2 if isinstance(stars, int) and stars >= 10000 else 0),
        "difficulty_to_replicate": 2
        + (2 if any(term in topic_hits for term in ("mlops", "observability", "orchestration", "mcp")) else 0)
        + (2 if item.group == "research" else 0)
        + (1 if star_signal >= 4 else 0),
        "career_value": 3
        + min(3, len(topic_hits))
        + (2 if any(term in topic_hits for term in ("sql", "analytics", "data engineering", "codex", "claude")) else 0)
        + (1 if business_hits else 0),
        "strategic_edge": 2
        + min(3, len(operator_hits))
        + min(2, len(monetization_hits))
        + (2 if fresh else 0),
    }

    if noise_hits:
        for key in ("real_world_utility", "leverage_potential", "strategic_edge"):
            scorecard[key] -= min(4, len(noise_hits) * 2)
        scorecard["monetization_potential"] -= min(3, len(noise_hits))

    return {key: _clamp_int(scorecard.get(key, 0), 0, 10) for key in SCORE_DIMENSIONS}


def _clamp_int(value: float, low: int, high: int) -> int:
    return max(low, min(high, int(round(value))))


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


def select_noise_items(items: list[SignalItem], limit: int = 5) -> list[SignalItem]:
    ignored = [
        item
        for item in items
        if item.metadata.get("category") == "Noise/Hype To Ignore"
        or item.metadata.get("noise_hits")
        or item.score < 18
    ]
    return sorted(
        ignored,
        key=lambda item: (
            0 if item.metadata.get("category") == "Noise/Hype To Ignore" else 1,
            -len(item.metadata.get("noise_hits", [])),
            item.score,
        ),
    )[:limit]


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
        try:
            parsed = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        except ValueError:
            return star_component
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


def _build_analysis(
    item: SignalItem,
    *,
    topic_hits: list[str],
    operator_hits: list[str],
    business_hits: list[str],
    learning_hits: list[str],
    monetization_hits: list[str],
    noise_hits: list[str],
    age_days: float | None,
    category: str,
    scorecard: dict[str, int],
) -> dict[str, str]:
    suggested_decision = _suggest_decision(
        item,
        topic_hits=topic_hits,
        operator_hits=operator_hits,
        business_hits=business_hits,
        monetization_hits=monetization_hits,
        noise_hits=noise_hits,
        age_days=age_days,
        category=category,
    )
    return {
        "why_this_matters": _why_this_matters(item, topic_hits, business_hits, age_days, category),
        "how_it_works": _how_it_works(item, learning_hits),
        "should_i_implement": _implementation_summary(
            item,
            suggested_decision=suggested_decision,
            topic_hits=topic_hits,
            business_hits=business_hits,
            scorecard=scorecard,
        ),
        "suggested_decision": suggested_decision,
        "category": category,
        "score_summary": _score_summary(scorecard),
    }


def _suggest_decision(
    item: SignalItem,
    *,
    topic_hits: list[str],
    operator_hits: list[str],
    business_hits: list[str],
    monetization_hits: list[str],
    noise_hits: list[str],
    age_days: float | None,
    category: str,
) -> str:
    score = item.score
    stars = item.metadata.get("stars")

    if category == "Noise/Hype To Ignore" or len(noise_hits) >= 2:
        return "ignore"

    if (
        score >= 94
        and age_days is not None
        and age_days <= 7
        and (set(topic_hits) & IMPLEMENT_TRIGGERS or len(business_hits) >= 2 or len(operator_hits) >= 2)
        and item.group in {"official", "builder", "repo"}
    ):
        return "build_with"

    if category == "High-Signal Builders" and item.group == "builder":
        return "learn"

    if item.group == "research" and score >= 60:
        return "learn"

    if (
        len(monetization_hits) >= 2
        and business_hits
        and score >= 78
        and category
        in {
            "Freelance Leverage",
            "Startup Opportunities",
            "Underrated Opportunities",
            "Automation Systems",
            "Analytics/Data Engineering",
            "Tooling Stack",
            "Immediate Edge",
        }
    ):
        return "monetize"

    if item.metadata.get("release_watchlist") and score >= 70 and age_days is not None and age_days <= 21:
        return "build_with"

    if (
        item.source_type in {"github_watchlist", "github_search", "github_releases_watchlist"}
        and isinstance(stars, int)
        and stars >= 10000
        and score >= 70
    ):
        return "build_with"

    if item.group == "official" and score >= 68 and age_days is not None and age_days <= 14:
        return "learn"

    if category == "AI Engineering" and score >= 75:
        return "learn"

    return "monitor"


def _why_this_matters(
    item: SignalItem,
    topic_hits: list[str],
    business_hits: list[str],
    age_days: float | None,
    category: str,
) -> str:
    focus_terms = topic_hits[:2] or business_hits[:2]
    focus_text = ", ".join(focus_terms) if focus_terms else "AI workflow leverage"

    freshness = ""
    if age_days is not None and age_days <= 2:
        freshness = " It is very fresh."
    elif age_days is not None and age_days <= 7:
        freshness = " It is still moving this week."

    if item.metadata.get("release_watchlist"):
        return (
            f"This is a live release signal for a tool in your tracked stack, so it can turn into "
            f"a concrete workflow advantage quickly around {focus_text}.{freshness}"
        ).strip()

    if category == "Freelance Leverage":
        return (
            f"This points toward a serviceable business workflow around {focus_text}. For you, that matters "
            f"because small automations, dashboards, and internal tools can become portfolio proof or client offers.{freshness}"
        ).strip()

    if category == "Underrated Opportunities":
        return (
            f"This looks like the kind of unglamorous operational problem where AI can create leverage through "
            f"automation, analytics, or workflow cleanup around {focus_text}.{freshness}"
        ).strip()

    if item.source_type in {"github_watchlist", "github_search"}:
        stars = item.metadata.get("stars")
        stars_text = f"{stars:,} stars" if isinstance(stars, int) else "visible adoption"
        return (
            f"This repo is showing {stars_text} and lines up with your interests in {focus_text}, "
            f"which makes it a practical candidate for workflow evaluation rather than passive reading.{freshness}"
        ).strip()

    if item.group == "official":
        return (
            f"This is a direct vendor or platform update tied to {focus_text}, so it may change what is "
            f"worth testing, implementing, or learning next.{freshness}"
        ).strip()

    if item.group == "research":
        return (
            f"This looks useful because it could become a reusable method, benchmark, or evaluation pattern "
            f"for your work in {focus_text}.{freshness}"
        ).strip()

    return (
        f"This is a practitioner signal around {focus_text}, which helps you spot adoption, friction, and "
        f"real-world use cases before you spend time building on top of it.{freshness}"
    ).strip()


def _build_operator_intelligence(
    item: SignalItem,
    *,
    analysis: dict[str, str],
    category: str,
    scorecard: dict[str, int],
    topic_hits: list[str],
    operator_hits: list[str],
    business_hits: list[str],
    monetization_hits: list[str],
    noise_hits: list[str],
) -> dict[str, Any]:
    recommendation = _recommendation_label(analysis.get("suggested_decision", "monitor"))
    return {
        "title": item.title,
        "category": category,
        "why_it_matters": _why_user_specific(
            item,
            category=category,
            topic_hits=topic_hits,
            business_hits=business_hits,
            monetization_hits=monetization_hits,
            noise_hits=noise_hits,
        ),
        "who_is_using_it": _who_is_using_it(item),
        "leverage_created": _leverage_created(category, topic_hits, operator_hits, business_hits),
        "skill_gain": _skill_gain(category, topic_hits),
        "monetization_potential": _monetization_potential_text(scorecard, monetization_hits, business_hits),
        "difficulty_level": _difficulty_level(scorecard),
        "market_saturation": _market_saturation(item, category, noise_hits),
        "actionable_next_step": _actionable_next_step(item, recommendation, category),
        "recommendation": recommendation,
        "scorecard": scorecard,
    }


def _score_summary(scorecard: dict[str, int]) -> str:
    strongest = sorted(scorecard.items(), key=lambda pair: pair[1], reverse=True)[:3]
    return ", ".join(f"{key.replace('_', ' ')} {value}/10" for key, value in strongest)


def _recommendation_label(decision: str) -> str:
    labels = {
        "learn": "Learn",
        "ignore": "Ignore",
        "monitor": "Monitor",
        "build_with": "Build With",
        "monetize": "Monetize",
        "implement": "Build With",
        "test": "Learn",
        "watch": "Monitor",
    }
    return labels.get(decision, "Monitor")


def _why_user_specific(
    item: SignalItem,
    *,
    category: str,
    topic_hits: list[str],
    business_hits: list[str],
    monetization_hits: list[str],
    noise_hits: list[str],
) -> str:
    if noise_hits:
        return (
            "This matters mainly as a filter: it resembles low-depth AI content, so skipping it protects time for "
            "analytics, automation, and engineering work that can compound."
        )
    focus_terms = topic_hits[:2] or business_hits[:2] or monetization_hits[:2]
    focus_text = ", ".join(focus_terms) if focus_terms else "AI operator leverage"
    if category in {"Freelance Leverage", "Underrated Opportunities", "Startup Opportunities"}:
        return (
            f"It is close to {focus_text}, which can translate into a small offer, portfolio case study, or solo "
            "operator system rather than just another thing to read."
        )
    if category == "Analytics/Data Engineering":
        return (
            f"It compounds your data analytics and AI engineering lane by connecting {focus_text} to real workflows, "
            "dashboards, SQL systems, or trusted metrics."
        )
    if category == "Automation Systems":
        return (
            f"It can help you convert repeated manual work into a reliable system, which is one of the clearest "
            "ways to create career and freelance leverage."
        )
    if item.source_type in {"github_search", "github_watchlist", "github_releases_watchlist"}:
        return (
            f"It gives you a concrete tool to test around {focus_text}, so you can build evidence instead of relying "
            "on commentary."
        )
    return (
        f"It strengthens your judgment around {focus_text}, helping you decide what to learn, test, build with, or "
        "ignore while the AI stack changes."
    )


def _who_is_using_it(item: SignalItem) -> str:
    if item.source_type in {"github_search", "github_watchlist"}:
        stars = item.metadata.get("stars")
        stars_text = f" with {stars:,} GitHub stars" if isinstance(stars, int) and stars else ""
        return f"Open-source builders, maintainers, and technical operators{stars_text}."
    if item.source_type == "github_releases_watchlist":
        repo = item.metadata.get("repo") or item.title
        return f"Teams already tracking or building on `{repo}` and its surrounding ecosystem."
    if item.source == "Hacker News":
        return "Engineers, founders, and early technical adopters discussing implementation tradeoffs."
    if "Reddit" in item.source:
        subreddit = item.metadata.get("subreddit")
        if subreddit:
            return f"Practitioners in r/{subreddit} sharing field notes, friction, and adoption signals."
        return "Practitioners in technical Reddit communities."
    if item.group == "research":
        return "Researchers and early implementers who may turn the method into tooling or benchmarks."
    if item.group == "builder":
        return "Independent builders and senior practitioners who publish implementation details."
    if item.group == "startup":
        return "Product builders and early users testing new workflows before they are mature."
    return "Platform teams, engineering teams, and practitioners watching the underlying capability."


def _leverage_created(
    category: str, topic_hits: list[str], operator_hits: list[str], business_hits: list[str]
) -> str:
    terms = set(topic_hits + operator_hits + business_hits)
    if category == "Automation Systems" or terms & {"automation", "workflow", "pipeline"}:
        return "Turns repeated work into a repeatable system with measurable time savings."
    if category == "Analytics/Data Engineering" or terms & {"analytics", "sql", "warehouse", "dashboard"}:
        return "Improves decision speed by making data workflows more reliable, explainable, or reusable."
    if category == "Emerging Infrastructure" or terms & {"mcp", "observability", "evaluation", "mlops"}:
        return "Creates infrastructure judgment that helps you choose durable tools before consensus forms."
    if category in {"Freelance Leverage", "Startup Opportunities", "Underrated Opportunities"}:
        return "Can become a paid micro-offer, internal tool, or niche product experiment."
    return "Builds practical judgment and reusable patterns you can apply across AI engineering work."


def _skill_gain(category: str, topic_hits: list[str]) -> str:
    if category == "Analytics/Data Engineering":
        return "SQL, analytics engineering, data modeling, metrics design, and AI-assisted reporting."
    if category == "Automation Systems":
        return "Workflow mapping, browser/API automation, reliability checks, and operator documentation."
    if category == "Emerging Infrastructure":
        return "Agent architecture, evaluation, observability, MCP/tooling integration, and deployment tradeoffs."
    if category == "Experimental Workflows":
        return "Research translation, benchmarking, notebook experiments, and evidence-based adoption."
    if any(term in topic_hits for term in ("codex", "claude", "coding")):
        return "Advanced coding-agent usage, repo navigation, test generation, and implementation review."
    return "Technical filtering, implementation judgment, and clearer AI product instincts."


def _monetization_potential_text(
    scorecard: dict[str, int], monetization_hits: list[str], business_hits: list[str]
) -> str:
    score = scorecard.get("monetization_potential", 0)
    if score >= 8:
        angle = monetization_hits[:2] or business_hits[:2]
        angle_text = f" around {', '.join(angle)}" if angle else ""
        return f"High: test a packaged service, paid audit, internal-tool build, or dashboard automation{angle_text}."
    if score >= 5:
        return "Medium: useful for portfolio proof and may become client-facing after one validated case study."
    return "Low for now: treat it as learning or infrastructure judgment before trying to sell it."


def _difficulty_level(scorecard: dict[str, int]) -> str:
    score = scorecard.get("technical_depth", 0) + scorecard.get("difficulty_to_replicate", 0)
    if score >= 15:
        return "Advanced"
    if score >= 10:
        return "Intermediate"
    return "Beginner"


def _market_saturation(item: SignalItem, category: str, noise_hits: list[str]) -> str:
    stars = item.metadata.get("stars")
    if noise_hits or category == "Noise/Hype To Ignore":
        return "High: crowded, shallow, or attention-driven."
    if isinstance(stars, int) and stars >= 50000:
        return "Medium-high: strong adoption, but still useful if you specialize in implementation."
    if category in {"Underrated Opportunities", "Freelance Leverage"}:
        return "Low-medium: less glamorous, often underserved by technical builders."
    if item.group == "research":
        return "Low: early, but practical value still needs validation."
    return "Medium: watch for repeated builder usage before committing deeply."


def _actionable_next_step(item: SignalItem, recommendation: str, category: str) -> str:
    if recommendation == "Ignore":
        return "Archive it unless the same idea appears later from a builder with implementation details."
    if recommendation == "Monetize":
        return "Write a one-page offer: target user, painful workflow, promised output, proof artifact, and a 3-day prototype scope."
    if recommendation == "Build With":
        return "Run a 60-90 minute proof of value using a real dataset, repo, browser workflow, or reporting task."
    if recommendation == "Learn":
        return "Convert it into a small notebook, benchmark, or implementation memo within one week."
    if category == "High-Signal Builders":
        return "Follow the builder, save the source, and extract one reusable workflow pattern into your playbook."
    return "Monitor for repeated mentions from builders, GitHub releases, or practitioner failure/success reports."


def _how_it_works(item: SignalItem, learning_hits: list[str]) -> str:
    language = item.metadata.get("language")
    language_text = f" in {language}" if language else ""

    if item.metadata.get("release_watchlist"):
        tag = item.metadata.get("release_tag")
        tag_text = f" under release `{tag}`" if isinstance(tag, str) and tag else ""
        return (
            f"Treat this as a changelog-driven signal: read the release notes{tag_text}, then run one small "
            f"before/after test against your own workflow or dataset."
        )

    if item.source_type in {"github_watchlist", "github_search"}:
        return (
            f"This is an open-source workflow signal. The value usually comes from cloning the repo, reading "
            f"the README, and trying one end-to-end task with the library or CLI{language_text}."
        )

    if item.group == "official":
        return (
            "This is an official product or engineering update. Read it as a capability announcement, API shift, "
            "or implementation pattern from the builder rather than as community hype."
        )

    if item.group == "research":
        return (
            "This is a research signal. Pull out one method, benchmark idea, or evaluation technique and convert "
            "it into a notebook or small experiment before treating it as production guidance."
        )

    if learning_hits:
        return (
            "This is a hands-on learning signal. Use it to understand practical setup, tradeoffs, and edge cases, "
            "then decide whether it deserves a deeper test."
        )

    return (
        "This is a discussion signal. Use it to understand what practitioners are actually trying, where things "
        "break, and which tools are earning repeated attention."
    )


def _implementation_summary(
    item: SignalItem,
    *,
    suggested_decision: str,
    topic_hits: list[str],
    business_hits: list[str],
    scorecard: dict[str, int],
) -> str:
    focus_terms = topic_hits[:2] or business_hits[:2]
    focus_text = ", ".join(focus_terms) if focus_terms else "your current workflows"

    if suggested_decision == "ignore":
        return (
            "Ignore it for now. The signal looks more like attention capture than durable operator leverage, "
            "so it should not take time away from technical execution."
        )
    if suggested_decision == "monetize":
        return (
            f"Package this into an offer-shaped experiment. The monetization and utility scores are strong enough "
            f"to test a small client-facing workflow around {focus_text}."
        )
    if suggested_decision == "build_with":
        return (
            f"Probably yes. This is close enough to {focus_text} that you should wire up a small proof of value "
            "now instead of only reading about it."
        )
    if suggested_decision == "learn":
        return (
            f"Learn it through a bounded experiment. The career and learning scores are strong enough to turn it "
            f"into a notebook, memo, or benchmark around {focus_text}."
        )
    if scorecard.get("strategic_edge", 0) >= 7:
        return (
            f"Monitor closely. The signal has strategic edge, but it still needs clearer proof before you build "
            f"around {focus_text}."
        )
    return (
        f"Watch it for now. The signal is promising, but it still needs either clearer adoption, stronger business "
        f"evidence, or a more direct fit with {focus_text}."
    )
