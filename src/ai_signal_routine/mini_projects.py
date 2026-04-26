from __future__ import annotations

from .models import MiniProject, SignalItem


PROJECT_TEMPLATES = [
    {
        "name": "AI Tool Radar Dashboard",
        "match": ["mcp", "agent", "workflow", "browser"],
        "why_now": "The agent stack is moving fast, and the people who win are the ones who can separate reusable tools from flashy demos.",
        "build_scope": "Build a small dashboard that tracks tool releases, GitHub stars, and community mentions, then classifies each tool as watch, test, or ignore.",
        "stack": "Python, SQLite, Streamlit, requests",
        "success_metric": "You can review the week in under 10 minutes and immediately know which tool deserves a hands-on test.",
        "prompt_seed": "Build a Streamlit dashboard that loads my AI tool briefing JSON, shows trend cards, and lets me label tools as watch, test, or implement."
    },
    {
        "name": "Warehouse Copilot With Guardrails",
        "match": ["sql", "analytics", "warehouse", "dashboard"],
        "why_now": "Natural-language analytics is becoming a real business workflow, but only when the output stays grounded in trusted data and safe SQL patterns.",
        "build_scope": "Create a chat-to-SQL assistant over a sample sales dataset with approved query templates, result explanations, and a chart view.",
        "stack": "Python, DuckDB, Streamlit, OpenAI or Anthropic API",
        "success_metric": "A non-technical user can answer three business questions without writing SQL and without generating unsafe queries.",
        "prompt_seed": "Build a guarded natural-language analytics app over DuckDB that explains every SQL query before execution and visualizes the result."
    },
    {
        "name": "Coding Agent Benchmark Harness",
        "match": ["claude", "codex", "coding", "developer"],
        "why_now": "Claude and Codex are both turning into serious operators, and benchmarking them on your own recurring work is much more valuable than reading hot takes.",
        "build_scope": "Define 5 realistic tasks from your own workflow, run both tools against them, and score speed, correctness, explanation quality, and cleanup needed.",
        "stack": "Markdown rubric, Git repo fixtures, optional Python summary script",
        "success_metric": "You have a repeatable scorecard that tells you which tool to use for debugging, SQL help, automation, and project scaffolding.",
        "prompt_seed": "Create a benchmark harness with five realistic analyst and automation tasks, a scoring rubric, and a results table for Claude and Codex."
    },
    {
        "name": "Release Notes to Action Queue",
        "match": ["openai", "anthropic", "developer", "automation"],
        "why_now": "Tool updates only matter when they turn into a concrete decision: learn it, test it, or leave it alone.",
        "build_scope": "Monitor vendor release notes, summarize what changed, tag the likely business impact, and generate one mini experiment for each meaningful update.",
        "stack": "Python, Markdown reports, optional Slack or email integration",
        "success_metric": "Every meaningful model or tool release turns into a one-line decision and a next experiment inside 24 hours.",
        "prompt_seed": "Build a release monitor that reads AI vendor feeds and turns each major update into a short impact note plus a mini experiment."
    },
    {
        "name": "Research to Notebook Lab",
        "match": ["paper", "research", "evaluation", "data science"],
        "why_now": "Reading papers is useful, but converting one good idea into a notebook or experiment is what compounds your skill.",
        "build_scope": "Take the top research items each week, extract one method or benchmark idea, and turn it into a notebook or tiny reproducible experiment.",
        "stack": "Python notebooks, pandas, scikit-learn, matplotlib",
        "success_metric": "You ship one small experiment per week and build a library of reusable patterns instead of passive notes.",
        "prompt_seed": "Create a weekly research-to-notebook workflow that turns one AI paper into a compact reproducible experiment."
    }
]


def generate_projects(items: list[SignalItem], limit: int = 4) -> list[MiniProject]:
    haystack = " ".join(
        [item.title + " " + item.summary + " " + " ".join(item.tags) for item in items]
    ).lower()
    projects: list[MiniProject] = []
    for template in PROJECT_TEMPLATES:
        if any(term in haystack for term in template["match"]):
            projects.append(
                MiniProject(
                    title=template["name"],
                    why_now=template["why_now"],
                    build_scope=template["build_scope"],
                    stack=template["stack"],
                    success_metric=template["success_metric"],
                    prompt_seed=template["prompt_seed"],
                )
            )
        if len(projects) >= limit:
            break

    if len(projects) < limit:
        for template in PROJECT_TEMPLATES:
            if any(project.title == template["name"] for project in projects):
                continue
            projects.append(
                MiniProject(
                    title=template["name"],
                    why_now=template["why_now"],
                    build_scope=template["build_scope"],
                    stack=template["stack"],
                    success_metric=template["success_metric"],
                    prompt_seed=template["prompt_seed"],
                )
            )
            if len(projects) >= limit:
                break
    return projects
