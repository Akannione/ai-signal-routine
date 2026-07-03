from __future__ import annotations

from typing import Any

from .models import MiniProject, SignalItem


PROJECT_TEMPLATES = [
    {
        "name": "Operator Intelligence Scoreboard",
        "match": ["operator", "builder", "workflow", "leverage", "automation", "mcp"],
        "why_now": "The advantage is not seeing more AI content. It is consistently turning noisy public signals into a ranked action queue.",
        "build_scope": "Extend the briefing JSON into a scoreboard that tracks category, recommendation, scorecard dimensions, source quality, and next action over time.",
        "stack": "Python, SQLite, Streamlit, pandas",
        "success_metric": "You can explain why each top signal is learn, monitor, build with, monetize, or ignore in under 10 minutes.",
        "prompt_seed": "Build an operator intelligence scoreboard that reads my briefing JSON and shows category mix, scorecard dimensions, recommendations, and stale next actions.",
    },
    {
        "name": "Freelance Automation Offer Lab",
        "match": ["freelance", "consulting", "agency", "client", "operations", "manual process", "reporting"],
        "why_now": "Small businesses are adopting AI unevenly, which leaves space for practical operators who can package dashboards, automations, and workflow cleanup as concrete services.",
        "build_scope": "Pick one recurring business pain, build a before-and-after prototype, write a one-page offer, and define the proof needed to sell it.",
        "stack": "Python, SQL, Streamlit, Zapier/n8n or lightweight API automation",
        "success_metric": "You finish with one specific client-facing offer and a demo artifact that proves time saved or reporting quality improved.",
        "prompt_seed": "Turn this AI signal into a freelance automation offer with target customer, painful workflow, prototype scope, pricing hypothesis, and demo checklist.",
    },
    {
        "name": "AI Tool Radar Dashboard",
        "match": ["mcp", "agent", "workflow", "browser"],
        "why_now": "The agent stack is moving fast, and the people who win are the ones who can separate reusable tools from flashy demos.",
        "build_scope": "Build a small dashboard that tracks tool releases, GitHub stars, and community mentions, then classifies each tool as watch, test, or ignore.",
        "stack": "Python, SQLite, Streamlit, requests",
        "success_metric": "You can review the week in under 10 minutes and immediately know which tool deserves a hands-on test.",
        "prompt_seed": "Build a Streamlit dashboard that loads my AI tool briefing JSON, shows trend cards, and lets me label tools as watch, test, or implement.",
    },
    {
        "name": "Warehouse Copilot With Guardrails",
        "match": ["sql", "analytics", "warehouse", "dashboard"],
        "why_now": "Natural-language analytics is becoming a real business workflow, but only when the output stays grounded in trusted data and safe SQL patterns.",
        "build_scope": "Create a chat-to-SQL assistant over a sample sales dataset with approved query templates, result explanations, and a chart view.",
        "stack": "Python, DuckDB, Streamlit, OpenAI or Anthropic API",
        "success_metric": "A non-technical user can answer three business questions without writing SQL and without generating unsafe queries.",
        "prompt_seed": "Build a guarded natural-language analytics app over DuckDB that explains every SQL query before execution and visualizes the result.",
    },
    {
        "name": "Coding Agent Benchmark Harness",
        "match": ["claude", "codex", "coding", "developer"],
        "why_now": "Claude and Codex are both turning into serious operators, and benchmarking them on your own recurring work is much more valuable than reading hot takes.",
        "build_scope": "Define 5 realistic tasks from your own workflow, run both tools against them, and score speed, correctness, explanation quality, and cleanup needed.",
        "stack": "Markdown rubric, Git repo fixtures, optional Python summary script",
        "success_metric": "You have a repeatable scorecard that tells you which tool to use for debugging, SQL help, automation, and project scaffolding.",
        "prompt_seed": "Create a benchmark harness with five realistic analyst and automation tasks, a scoring rubric, and a results table for Claude and Codex.",
    },
    {
        "name": "Release Notes to Action Queue",
        "match": ["openai", "anthropic", "developer", "automation", "release"],
        "why_now": "Tool updates only matter when they turn into a concrete decision: learn it, test it, or leave it alone.",
        "build_scope": "Monitor vendor release notes, summarize what changed, tag the likely business impact, and generate one mini experiment for each meaningful update.",
        "stack": "Python, Markdown reports, optional Slack or email integration",
        "success_metric": "Every meaningful model or tool release turns into a one-line decision and a next experiment inside 24 hours.",
        "prompt_seed": "Build a release monitor that reads AI vendor feeds and turns each major update into a short impact note plus a mini experiment.",
    },
    {
        "name": "Research to Notebook Lab",
        "match": ["paper", "research", "evaluation", "data science"],
        "why_now": "Reading papers is useful, but converting one good idea into a notebook or experiment is what compounds your skill.",
        "build_scope": "Take the top research items each week, extract one method or benchmark idea, and turn it into a notebook or tiny reproducible experiment.",
        "stack": "Python notebooks, pandas, scikit-learn, matplotlib",
        "success_metric": "You ship one small experiment per week and build a library of reusable patterns instead of passive notes.",
        "prompt_seed": "Create a weekly research-to-notebook workflow that turns one AI paper into a compact reproducible experiment.",
    },
    {
        "name": "LLMOps Observability Drill",
        "match": ["mlops", "observability", "evaluation", "monitoring"],
        "why_now": "As models move into real workflows, observability and evaluation become more valuable than another prompt trick.",
        "build_scope": "Build a thin evaluation dashboard that tracks prompt versions, pass rates, and failure categories for one workflow.",
        "stack": "Python, SQLite, Streamlit, pandas",
        "success_metric": "You can spot which prompt, model, or retrieval setting actually improved the workflow.",
        "prompt_seed": "Build a lightweight LLMOps dashboard that logs runs, tracks failures, and compares prompt or model versions.",
    },
    {
        "name": "Semantic Layer Experiment",
        "match": ["semantic layer", "metrics", "warehouse", "dbt"],
        "why_now": "The analytics stack keeps moving toward trusted metrics and reusable business definitions that AI can query safely.",
        "build_scope": "Model a sample business metric layer, expose it through a simple interface, and test how well an AI assistant can answer questions without breaking definitions.",
        "stack": "dbt or SQLMesh, DuckDB, Python",
        "success_metric": "Business questions return consistent answers because the metric logic lives in one trusted place.",
        "prompt_seed": "Build a small semantic-layer prototype with trusted metrics, then connect an AI question interface to it.",
    },
    {
        "name": "Agentic Browser Workflow Trial",
        "match": ["browser", "playwright", "automation", "workflow"],
        "why_now": "Browser agents are one of the clearest bridges from AI demos into measurable operations work.",
        "build_scope": "Automate one real browser workflow end to end, then log success rate, retry behavior, and time saved compared with manual execution.",
        "stack": "Python, Playwright, browser-use or similar tooling",
        "success_metric": "The workflow runs reliably enough that you would trust it for repeated internal use.",
        "prompt_seed": "Build a browser-automation proof of value for one recurring workflow and measure reliability, error handling, and time saved.",
    },
    {
        "name": "Analytics Agent Case Study Builder",
        "match": ["sales", "finance", "operations", "analysis", "forecast"],
        "why_now": "Business leverage comes from turning tooling shifts into concrete case studies, not from just collecting headlines.",
        "build_scope": "Pick one business use case, build a thin prototype around it, and document the before-and-after workflow like a real internal memo.",
        "stack": "Python, SQL, notebooks or Streamlit",
        "success_metric": "You finish with a portfolio-quality mini case study that explains the business value clearly.",
        "prompt_seed": "Build a small analytics or operations copilot, then document the problem, prototype, result, and next step like a business case study.",
    },
]


def generate_projects(
    items: list[SignalItem], limit: int = 4, history: dict[str, Any] | None = None
) -> list[MiniProject]:
    history = history or {}
    recent_titles = {title.lower() for title in history.get("recent_project_titles", []) if isinstance(title, str)}

    projects: list[MiniProject] = []
    projects.extend(_interleave_projects(_generate_item_projects(items), _generate_template_projects(items)))

    deduped: list[MiniProject] = []
    seen: set[str] = set()

    for project in projects:
        key = project.title.lower()
        if key in seen:
            continue
        if key in recent_titles and len(deduped) < limit:
            continue
        seen.add(key)
        deduped.append(project)
        if len(deduped) >= limit:
            return deduped

    if len(deduped) < limit:
        for project in projects:
            key = project.title.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(project)
            if len(deduped) >= limit:
                break
    return deduped


def _interleave_projects(
    primary: list[MiniProject], secondary: list[MiniProject]
) -> list[MiniProject]:
    combined: list[MiniProject] = []
    max_len = max(len(primary), len(secondary))
    for index in range(max_len):
        if index < len(primary):
            combined.append(primary[index])
        if index < len(secondary):
            combined.append(secondary[index])
    return combined


def _generate_template_projects(items: list[SignalItem]) -> list[MiniProject]:
    haystack = " ".join(
        [
            item.title
            + " "
            + item.summary
            + " "
            + " ".join(item.tags)
            + " "
            + str(item.metadata.get("category", ""))
            + " "
            + " ".join(item.metadata.get("operator_hits", []))
            for item in items
        ]
    ).lower()
    projects: list[MiniProject] = []

    for template in PROJECT_TEMPLATES:
        if any(term in haystack for term in template["match"]):
            projects.append(_to_project(template))

    if len(projects) < 6:
        for template in PROJECT_TEMPLATES:
            if any(project.title == template["name"] for project in projects):
                continue
            projects.append(_to_project(template))
            if len(projects) >= 6:
                break
    return projects


def _generate_item_projects(items: list[SignalItem]) -> list[MiniProject]:
    projects: list[MiniProject] = []
    for item in items[:6]:
        project = _project_from_item(item)
        if project is not None:
            projects.append(project)
        if len(projects) >= 2:
            break
    return projects


def _project_from_item(item: SignalItem) -> MiniProject | None:
    title_lower = f"{item.title} {item.summary} {' '.join(item.tags)}".lower()
    repo_name = item.title.split("/")[-1]
    repo_label = _display_name(repo_name)
    category = item.metadata.get("category", "")
    intel = item.metadata.get("operator_intelligence", {})

    if intel.get("recommendation") == "Monetize" or category in {
        "Freelance Leverage",
        "Startup Opportunities",
        "Underrated Opportunities",
    }:
        return MiniProject(
            title=f"{repo_label} Offer Probe",
            why_now=f"{item.title} has enough operator or business signal to test as a small monetizable workflow, not just a reading item.",
            build_scope="Define the target user, painful manual workflow, expected output, proof artifact, pricing hypothesis, and a 3-day prototype plan.",
            stack="Markdown offer brief, Python or SQL prototype, Streamlit demo if useful",
            success_metric="You have a specific offer-shaped experiment that can become a portfolio case study or outreach asset.",
            prompt_seed=f"Turn {item.title} into a concise freelance or startup opportunity brief with target buyer, workflow pain, prototype, proof metric, and outreach angle.",
        )

    if item.metadata.get("release_watchlist"):
        return MiniProject(
            title=f"{repo_label} Release Drill",
            why_now=f"{item.title} just shipped a tracked release, which makes it a good moment to test whether the new capability matters for your workflow.",
            build_scope=f"Review the latest release for {item.title}, pick one capability worth trying, and build a tiny before-and-after workflow demo around it.",
            stack=f"{item.metadata.get('language') or 'Python'}, Markdown notes, sample workflow fixture",
            success_metric="You can say clearly whether the release changed setup time, output quality, or workflow reliability.",
            prompt_seed=f"Create a release-evaluation drill for {item.title} that extracts the key release changes, tests one workflow, and documents whether it is worth adopting.",
        )

    if item.source_type in {"github_watchlist", "github_search"}:
        if any(term in title_lower for term in ("browser", "playwright", "automation")):
            return MiniProject(
                title=f"{repo_label} Workflow Probe",
                why_now=f"{item.title} is showing up as a practical browser or workflow tool, which makes it worth pressure-testing on a real task.",
                build_scope=f"Clone or install {item.title}, automate one recurring workflow, and record success rate, retry behavior, and time saved.",
                stack=f"{item.metadata.get('language') or 'Python'}, CLI tooling, Markdown log",
                success_metric="You finish with a real recommendation on whether this tool belongs in your operator stack.",
                prompt_seed=f"Build a proof-of-value harness for {item.title} and run it against one recurring task to measure setup cost, reliability, and business value.",
            )
        if any(term in title_lower for term in ("sql", "analytics", "warehouse", "dbt", "duckdb")):
            return MiniProject(
                title=f"{repo_label} Analytics Lab",
                why_now=f"{item.title} sits close to analytics workflows you care about, so a small lab can turn curiosity into practical judgment.",
                build_scope=f"Use {item.title} to answer one analytics question end to end, then compare the experience with your current Python and SQL workflow.",
                stack=f"{item.metadata.get('language') or 'Python'}, SQL, sample dataset",
                success_metric="You know whether the tool makes analytics work faster, safer, or easier to explain.",
                prompt_seed=f"Build a compact analytics lab around {item.title} and use it to answer one business question with reproducible steps.",
            )
        return MiniProject(
            title=f"{repo_label} Tool Trial",
            why_now=f"{item.title} is getting enough attention that it deserves a hands-on verdict rather than a note in a backlog.",
            build_scope=f"Set up {item.title}, run one contained task, and score it for setup friction, capability, and repeatability.",
            stack=f"{item.metadata.get('language') or 'Python'}, local fixture repo, Markdown scorecard",
            success_metric="You can label the tool as watch, test further, or implement with evidence.",
            prompt_seed=f"Create a compact evaluation harness for {item.title} that measures setup time, task success, and whether it is worth adopting.",
        )

    if item.group == "official":
        source_label = _display_name(item.source.replace(" News", "").replace(" Blog", ""))
        return MiniProject(
            title=f"{source_label} Workflow Memo",
            why_now=f"{item.source} is signaling a platform change that may alter what you should learn, test, or implement next.",
            build_scope=f"Turn the update into a one-page memo that explains the capability, likely business value, one hands-on test, and one follow-up question.",
            stack="Markdown memo, optional notebook or small script",
            success_metric="You can explain the update in plain business language and propose a real next step within a day.",
            prompt_seed=f"Write a release-to-decision memo for this {item.source} update, then add one small experiment that validates whether it matters.",
        )

    if item.group == "research":
        return MiniProject(
            title=f"{_paper_project_title(item.title)}",
            why_now="A research signal becomes valuable only when you turn one idea into a reproducible experiment.",
            build_scope="Extract one method, benchmark idea, or evaluation pattern from the paper and recreate a tiny version in a notebook.",
            stack="Python notebook, pandas, scikit-learn or the relevant library",
            success_metric="You finish with a runnable artifact and a plain-English note on what translated well from paper to practice.",
            prompt_seed=f"Turn the core idea from '{item.title}' into a compact reproducible experiment and write a short note on whether it has practical workflow value.",
        )

    if item.group == "discussion":
        return MiniProject(
            title=f"{_display_name(item.source)} Signal Check",
            why_now="Community signals are useful when they help you verify whether attention is backed by real workflow value.",
            build_scope="Take one repeated community claim from today's signals, test it on a small task, and document whether the claim holds up.",
            stack="Python or local CLI tooling, Markdown notes",
            success_metric="You separate hype from practical leverage with a small, evidence-backed experiment.",
            prompt_seed=f"Pick one concrete claim from today's {item.source} discussion signals and build a compact validation test around it.",
        )

    return None


def _to_project(template: dict[str, str]) -> MiniProject:
    return MiniProject(
        title=template["name"],
        why_now=template["why_now"],
        build_scope=template["build_scope"],
        stack=template["stack"],
        success_metric=template["success_metric"],
        prompt_seed=template["prompt_seed"],
    )


def _display_name(value: str) -> str:
    cleaned = value.replace("-", " ").replace("_", " ").strip()
    words = [word for word in cleaned.split() if word]
    return " ".join(word.capitalize() for word in words[:4]) or "Signal"


def _paper_project_title(title: str) -> str:
    words = [word for word in title.replace(":", " ").split() if word]
    trimmed = " ".join(words[:4]) or "Research"
    return f"{trimmed} Notebook Lab"
