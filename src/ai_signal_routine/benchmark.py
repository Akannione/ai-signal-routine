from __future__ import annotations

import csv
import json
from pathlib import Path


BENCHMARK_PACK = {
    "tools": ["Claude", "Codex"],
    "rubric": [
        {"name": "Accuracy", "description": "How correct was the final output?"},
        {"name": "Speed", "description": "How quickly did the tool get to a useful answer?"},
        {"name": "Explanation", "description": "How well did it explain the reasoning and tradeoffs?"},
        {"name": "Cleanup", "description": "How much manual cleanup did you need after the result?"},
        {"name": "Business Value", "description": "How useful was the result in a real analyst or operator workflow?"},
    ],
    "tasks": [
        {
            "id": "tool-triage-memo",
            "title": "Tool Triage Memo",
            "scenario": "Take 3 items from the latest briefing and write a short memo that labels each one watch, test, or implement.",
            "artifact": "One-page decision memo with reasoning and next step.",
            "timebox_minutes": 25,
            "success_criteria": [
                "Clear recommendation for each tool",
                "Tradeoffs explained in business language",
                "One next experiment proposed",
            ],
        },
        {
            "id": "analytics-copilot",
            "title": "Natural Language to SQL",
            "scenario": "Turn a business question about revenue, churn, or customer behavior into safe SQL plus a short interpretation.",
            "artifact": "SQL query, explanation, and one chart suggestion.",
            "timebox_minutes": 30,
            "success_criteria": [
                "Correct query logic",
                "No unsafe assumptions about the schema",
                "Clear explanation for a non-technical stakeholder",
            ],
        },
        {
            "id": "notebook-to-pipeline",
            "title": "Notebook to Repeatable Workflow",
            "scenario": "Convert a rough notebook or analysis snippet into a repeatable script or lightweight pipeline.",
            "artifact": "Runnable script plus README notes.",
            "timebox_minutes": 35,
            "success_criteria": [
                "Code is reproducible",
                "Inputs and outputs are clear",
                "Hand-off quality is strong enough for a teammate",
            ],
        },
        {
            "id": "etl-debugging",
            "title": "Data Workflow Debugging",
            "scenario": "Fix a broken transformation, parsing bug, or dashboard data issue and explain the root cause.",
            "artifact": "Patch, short root-cause note, and validation steps.",
            "timebox_minutes": 25,
            "success_criteria": [
                "Bug fixed correctly",
                "Root cause identified clearly",
                "Validation plan is credible",
            ],
        },
        {
            "id": "dashboard-extension",
            "title": "Delivery Layer Extension",
            "scenario": "Add one useful improvement to the AI Signal dashboard, such as a new filter, chart, or workflow helper.",
            "artifact": "Working enhancement and short demo note.",
            "timebox_minutes": 40,
            "success_criteria": [
                "Improvement is actually useful",
                "UI remains easy to use",
                "Change is explained clearly",
            ],
        },
    ],
}


def write_benchmark_pack(outdir: Path) -> dict[str, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    tasks_path = outdir / "benchmark_tasks.json"
    scorecard_path = outdir / "benchmark_scorecard.md"
    results_path = outdir / "results_template.csv"
    readme_path = outdir / "README.md"

    _write_if_missing(tasks_path, json.dumps(BENCHMARK_PACK, indent=2))
    _write_if_missing(scorecard_path, _build_scorecard_markdown())
    _write_if_missing(readme_path, _build_benchmark_readme())
    if not results_path.exists():
        _write_results_template(results_path)

    return {
        "tasks": tasks_path,
        "scorecard": scorecard_path,
        "results": results_path,
        "readme": readme_path,
    }


def _write_results_template(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "run_date",
                "task_id",
                "tool",
                "accuracy",
                "speed",
                "explanation",
                "cleanup",
                "business_value",
                "overall_score",
                "notes",
            ]
        )
        for task in BENCHMARK_PACK["tasks"]:
            for tool in BENCHMARK_PACK["tools"]:
                writer.writerow(["", task["id"], tool, "", "", "", "", "", "", ""])


def _build_scorecard_markdown() -> str:
    lines: list[str] = []
    lines.append("# Claude vs Codex Scorecard")
    lines.append("")
    lines.append("Score each dimension from 1 to 5 after running the task with both tools.")
    lines.append("")
    for task in BENCHMARK_PACK["tasks"]:
        lines.append(f"## {task['title']}")
        lines.append("")
        lines.append(f"- Task ID: `{task['id']}`")
        lines.append(f"- Scenario: {task['scenario']}")
        lines.append(f"- Deliverable: {task['artifact']}")
        lines.append(f"- Timebox: {task['timebox_minutes']} minutes")
        lines.append("")
        lines.append("| Tool | Accuracy | Speed | Explanation | Cleanup | Business Value | Notes |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for tool in BENCHMARK_PACK["tools"]:
            lines.append(f"| {tool} |  |  |  |  |  |  |")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _build_benchmark_readme() -> str:
    lines: list[str] = []
    lines.append("# Benchmark Harness")
    lines.append("")
    lines.append("This folder gives you a repeatable way to compare Claude and Codex on your own work.")
    lines.append("")
    lines.append("## How To Run It")
    lines.append("")
    lines.append("1. Pick one task from `benchmark_tasks.json`.")
    lines.append("2. Run the same task in Claude and Codex with the same prompt and input context.")
    lines.append("3. Score both tools in `benchmark_scorecard.md` or `results_template.csv`.")
    lines.append("4. Keep the winner for that use case and update the notes with what made it better.")
    lines.append("")
    lines.append("## What You Learn")
    lines.append("")
    lines.append("- which tool is stronger for coding versus planning")
    lines.append("- which tool is better for SQL, analytics, or debugging")
    lines.append("- where explanation quality matters more than raw speed")
    lines.append("- where your own workflow still needs templates or guardrails")
    lines.append("")
    return "\n".join(lines)


def _write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")
