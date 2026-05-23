from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ai_signal_routine.benchmark import BENCHMARK_PACK, write_benchmark_pack  # noqa: E402
from ai_signal_routine.digests import build_email_digest, build_slack_digest, write_digests  # noqa: E402
from ai_signal_routine.memory import (  # noqa: E402
    VALID_DECISIONS,
    VALID_PRIORITIES,
    enrich_payload_with_memory,
    ensure_memory_file,
    save_memory,
    update_signal_memory,
)


REPORT_PATH = ROOT / "reports" / "latest_briefing.json"
MEMORY_PATH = ROOT / "data" / "operator_memory.json"
SAMPLE_REPORT_PATH = ROOT / "sample_data" / "sample_briefing.json"
SAMPLE_MEMORY_PATH = ROOT / "sample_data" / "sample_operator_memory.json"
BENCHMARK_DIR = ROOT / "benchmarks"


st.set_page_config(page_title="AI Signal Routine", layout="wide")
st.markdown(
    """
<style>
    .block-container {max-width: 1400px; padding-top: 1.2rem; padding-bottom: 2rem;}
    .hero {padding: 1rem 1.1rem; border: 1px solid #204044; border-radius: 8px; background: linear-gradient(135deg, #0f1b1d, #12282c);}
    .metric-card {padding: 0.9rem 1rem; border: 1px solid #29484d; border-radius: 8px; background: #101a1c;}
    .item-card {padding: 0.9rem 1rem; border: 1px solid #24393d; border-radius: 8px; background: #11171a; margin-bottom: 0.75rem;}
    .status-pill {display: inline-block; padding: 0.15rem 0.55rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600; background: #17373d; color: #d7fbff;}
    .small-note {color: #91afb5; font-size: 0.9rem;}
</style>
""",
    unsafe_allow_html=True,
)


def main() -> None:
    st.title("AI Signal Routine")
    st.caption("Delivery, memory, and evaluation for your AI operator workflow.")

    report_path, memory_path, using_sample_data = resolve_data_paths()
    if not report_path.exists():
        st.error(
            "No briefing found yet. Run `python3 main.py` first, or run "
            "`AI_SIGNAL_SAMPLE_MODE=1 streamlit run dashboard.py` for the public-safe demo."
        )
        return

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    memory = ensure_memory_file(memory_path)
    payload = enrich_payload_with_memory(payload, memory)

    benchmark_paths = write_benchmark_pack(BENCHMARK_DIR)
    email_digest = build_email_digest(payload)
    slack_digest = build_slack_digest(payload)

    if using_sample_data:
        st.info(
            "Demo mode is using sanitized sample data from `sample_data/`. "
            "Run `python3 main.py` to generate a live briefing."
        )

    render_header(payload)

    tab_radar, tab_queue, tab_projects, tab_digests, tab_benchmark = st.tabs(
        ["Radar", "Queue", "Mini Projects", "Digests", "Benchmark"]
    )

    with tab_radar:
        render_radar(payload, memory, memory_path)

    with tab_queue:
        render_queue(payload)

    with tab_projects:
        render_projects(payload)

    with tab_digests:
        render_digests(payload, email_digest, slack_digest)

    with tab_benchmark:
        render_benchmark(benchmark_paths)


def resolve_data_paths() -> tuple[Path, Path, bool]:
    sample_mode = os.getenv("AI_SIGNAL_SAMPLE_MODE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "demo",
    }
    if sample_mode:
        return SAMPLE_REPORT_PATH, SAMPLE_MEMORY_PATH, True
    if REPORT_PATH.exists():
        return REPORT_PATH, MEMORY_PATH, False
    if SAMPLE_REPORT_PATH.exists():
        return SAMPLE_REPORT_PATH, SAMPLE_MEMORY_PATH, True
    return REPORT_PATH, MEMORY_PATH, False


def render_header(payload: dict) -> None:
    queue = payload.get("memory_summary", {})
    themes = payload.get("themes", [])
    theme_label = ", ".join(f"{item['theme']} ({item['count']})" for item in themes[:3]) or "No themes yet"
    st.markdown(
        f"""
<div class="hero">
    <div style="font-size: 1.15rem; font-weight: 700;">Your operating dashboard</div>
    <div class="small-note">Use this to decide what to watch, what to test, and what to implement while the market moves.</div>
    <div style="margin-top: 0.7rem;">Strongest themes: {theme_label}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        ("Signals", queue.get("total", 0)),
        ("Implement", queue.get("implement", 0)),
        ("Test", queue.get("test", 0)),
        ("Watch", queue.get("watch", 0)),
    ]
    for column, (label, value) in zip((col1, col2, col3, col4), metrics, strict=False):
        column.markdown(
            f"""
<div class="metric-card">
    <div class="small-note">{label}</div>
    <div style="font-size: 1.6rem; font-weight: 700;">{value}</div>
</div>
""",
            unsafe_allow_html=True,
        )


def render_radar(payload: dict, memory: dict, memory_path: Path) -> None:
    items = payload.get("items", [])
    all_sources = sorted({item["source"] for item in items})

    st.subheader("Signal Review")
    filter_col1, filter_col2, filter_col3 = st.columns([1.2, 1.2, 1.8])
    source_filter = filter_col1.multiselect("Sources", all_sources, default=all_sources)
    decision_filter = filter_col2.multiselect(
        "Decisions", VALID_DECISIONS, default=["unreviewed", "watch", "test", "implement"]
    )
    search = filter_col3.text_input("Search", placeholder="agent, analytics, codex, sql...")

    filtered = [
        item
        for item in items
        if item["source"] in source_filter
        and item.get("operator", {}).get("decision", "unreviewed") in decision_filter
        and _matches_search(item, search)
    ]
    if not filtered:
        st.info("No signals match the current filters.")
        return

    list_col, editor_col = st.columns([1.45, 1.0], gap="large")
    labels = [
        f"{item['score']:.1f} | {item['operator'].get('decision', 'unreviewed')} | {item['title']}"
        for item in filtered
    ]
    selected_label = list_col.radio("Pick a signal", labels, index=0)
    selected_index = labels.index(selected_label)
    selected_item = filtered[selected_index]

    with list_col:
        for item in filtered[:12]:
            operator = item.get("operator", {})
            st.markdown(
                f"""
<div class="item-card">
    <div style="display:flex; justify-content:space-between; gap: 0.6rem;">
        <div style="font-weight:700;">{item['title']}</div>
        <div class="status-pill">{operator.get('decision', 'unreviewed')}</div>
    </div>
    <div class="small-note" style="margin-top:0.2rem;">{item['source']} | score {item['score']:.1f}</div>
    <div style="margin-top:0.45rem;">{'; '.join(item.get('rationale', [])[:2]) or 'Relevant signal.'}</div>
</div>
""",
                unsafe_allow_html=True,
            )

    with editor_col:
        st.subheader("Decision Workspace")
        st.markdown(f"[Open source link]({selected_item['url']})")
        st.write(selected_item.get("summary") or "No summary available.")
        operator = selected_item.get("operator", {})

        with st.form("memory_form"):
            decision = st.selectbox(
                "Decision",
                VALID_DECISIONS,
                index=VALID_DECISIONS.index(operator.get("decision", "unreviewed")),
            )
            priority = st.selectbox(
                "Priority",
                VALID_PRIORITIES,
                index=VALID_PRIORITIES.index(operator.get("priority", "medium")),
            )
            next_action = st.text_input("Next action", value=operator.get("next_action", ""))
            linked_project = st.text_input("Linked project", value=operator.get("linked_project", ""))
            notes = st.text_area("Notes", value=operator.get("notes", ""), height=150)
            saved = st.form_submit_button("Save memory")

        if saved:
            update_signal_memory(
                memory,
                url=selected_item["url"],
                title=selected_item["title"],
                source=selected_item["source"],
                decision=decision,
                priority=priority,
                notes=notes,
                next_action=next_action,
                linked_project=linked_project,
            )
            save_memory(memory_path, memory)
            st.success("Memory saved.")
            st.rerun()


def render_queue(payload: dict) -> None:
    st.subheader("Action Queue")
    items = payload.get("items", [])
    grouped = {"implement": [], "test": [], "watch": []}
    for item in items:
        decision = item.get("operator", {}).get("decision", "unreviewed")
        if decision in grouped:
            grouped[decision].append(item)

    for decision in ("implement", "test", "watch"):
        st.markdown(f"### {decision.title()}")
        group = grouped[decision]
        if not group:
            st.caption("Nothing here yet.")
            continue
        for item in group:
            operator = item.get("operator", {})
            st.markdown(
                f"- [{item['title']}]({item['url']}) | {item['source']} | {operator.get('next_action') or 'No next action yet.'}"
            )


def render_projects(payload: dict) -> None:
    st.subheader("Mini Projects")
    for project in payload.get("mini_projects", []):
        with st.container(border=True):
            st.markdown(f"### {project['title']}")
            st.write(project["why_now"])
            st.markdown(f"- Build: {project['build_scope']}")
            st.markdown(f"- Stack: {project['stack']}")
            st.markdown(f"- Success: {project['success_metric']}")
            st.code(project["prompt_seed"])


def render_digests(payload: dict, email_digest: str, slack_digest: str) -> None:
    st.subheader("Delivery Layer")
    st.caption("These exports turn your current queue into something you can send or archive.")
    if st.button("Write latest digest files", use_container_width=False):
        email_path, slack_path = write_digests(email_digest, slack_digest, ROOT / "reports")
        st.success(f"Wrote {email_path.name} and {slack_path.name}.")

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("### Email Digest")
        st.text_area("Email preview", value=email_digest, height=420)
    with col2:
        st.markdown("### Slack Digest")
        st.text_area("Slack preview", value=slack_digest, height=420)

    st.caption(
        "Optional sending is available from the CLI if you set `SLACK_WEBHOOK_URL` or SMTP environment variables."
    )


def render_benchmark(benchmark_paths: dict[str, Path]) -> None:
    st.subheader("Claude vs Codex Benchmark")
    st.write(
        "Use this pack to compare both tools on recurring work like tool triage, SQL analysis, workflow refactoring, and debugging."
    )
    for task in BENCHMARK_PACK["tasks"]:
        with st.container(border=True):
            st.markdown(f"### {task['title']}")
            st.write(task["scenario"])
            st.markdown(f"- Deliverable: {task['artifact']}")
            st.markdown(f"- Timebox: {task['timebox_minutes']} minutes")
            st.markdown("- Success criteria:")
            for criterion in task["success_criteria"]:
                st.markdown(f"  - {criterion}")

    st.caption(
        "Generated files: "
        + ", ".join(str(path.relative_to(ROOT)) for path in benchmark_paths.values())
    )


def _matches_search(item: dict, search: str) -> bool:
    if not search:
        return True
    haystack = " ".join(
        [
            item.get("title", ""),
            item.get("summary", ""),
            item.get("source", ""),
            " ".join(item.get("tags", [])),
        ]
    ).lower()
    return search.lower() in haystack


if __name__ == "__main__":
    main()
