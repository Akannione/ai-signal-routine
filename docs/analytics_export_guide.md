# Analytics Export Guide

This guide explains how the SQLite history layer and CSV exports can support analytics, BI, AI operations, and solutions engineering review workflows.

## Goal

AI Signal Routine does more than create a latest briefing. It records each run into SQLite and exports lightweight tables that can be opened in Excel, loaded into Power BI, or connected to Looker Studio after converting the CSVs to a supported source.

The main review question is:

> Which signals changed, which actions are open, and what should be tested or implemented next?

## Visual Mockup

![BI export dashboard mockup](../assets/screenshots/ai_signal_bi_export_mockup.svg)

This mockup shows how the exported CSV files can become an executive analytics view with review rate, open actions, decision mix, source quality, theme trend, and stakeholder summary.

## Export Files

Run the normal workflow:

```bash
python3 main.py
```

Or export from the Streamlit `Trends` tab after running:

```bash
AI_SIGNAL_SAMPLE_MODE=1 streamlit run dashboard.py
```

The export folder is:

```text
reports/history_exports/
```

Generated files:

- `ai_signal_weekly_summary.csv`: stakeholder-ready weekly operating summary.
- `signal_history_runs.csv`: one row per briefing run.
- `signal_history_signals.csv`: one row per signal per run.
- `signal_history_decision_counts.csv`: decision distribution by run.
- `signal_history_source_counts.csv`: source distribution and average score by run.
- `signal_history_themes.csv`: theme counts by run.

Generated SQLite database:

```text
data/signal_history.sqlite
```

The demo dashboard uses:

```text
data/sample_signal_history.sqlite
```

SQLite databases and history export folders are ignored by git because they are generated artifacts.

## Suggested Dashboard Pages

### Executive Summary

Use `ai_signal_weekly_summary.csv`.

Recommended cards:

- Signals reviewed
- Review rate
- Open actions
- Average score
- Top theme
- Top source

Recommended table:

- `generated_at`
- `signals`
- `review_rate`
- `open_actions`
- `top_theme`
- `top_source`
- `stakeholder_summary`

### Signal Queue

Use `signal_history_signals.csv`.

Recommended filters:

- Decision
- Priority
- Source
- Linked project
- Theme hint

Recommended table:

- Title
- Source
- Score
- Decision
- Priority
- Linked project
- Next action

### Source Quality

Use `signal_history_source_counts.csv`.

Recommended visuals:

- Count by source
- Average score by source
- Source trend by run

### Decision Mix

Use `signal_history_decision_counts.csv`.

Recommended visuals:

- Implement, test, watch, archive, and unreviewed counts
- Review completion rate by run
- Open actions over time

### Theme Radar

Use `signal_history_themes.csv`.

Recommended visuals:

- Top themes by run
- Theme count trend
- Theme mix for the latest run

## Suggested Data Model

Join on `run_id` when combining the detailed tables:

```text
signal_history_runs.run_id
  -> signal_history_signals.run_id
  -> signal_history_decision_counts.run_id
  -> signal_history_source_counts.run_id
  -> signal_history_themes.run_id
```

Use `ai_signal_weekly_summary.csv` as the easiest standalone table for an executive view.

## Portfolio Talking Points

This export layer demonstrates:

- durable data modeling with SQLite
- operational metrics from an AI workflow
- stakeholder-ready CSV outputs
- dashboard-ready decision, source, and theme dimensions
- a practical bridge from automation to BI reporting

That makes the project relevant for data analytics, automation, AI operations, and solutions engineering roles.
