# AI Signal Routine

This project gives you a practical monitoring loop for:

- generative AI news and tooling
- data analytics and data science ideas
- open-source repo adoption signals
- Claude and Codex workflow opportunities
- mini-project generation for ongoing skill growth
- a memory layer for decisions and notes
- delivery digests for email and Slack
- a benchmark harness for Claude vs Codex on recurring work

It is intentionally built as a `signal system`, not a generic scraper. The goal is to help you decide what is worth learning, testing, or implementing.

## What It Does

The pipeline pulls from multiple sources:

- official blogs and release feeds
- GitHub repository search
- Hacker News discussion
- arXiv research feeds

Then it:

- scores items by relevance, business value, freshness, and learning potential
- ranks the strongest signals
- writes a Markdown briefing and JSON payload
- stores your `watch`, `test`, and `implement` decisions
- writes email and Slack digest files
- creates a benchmark pack for Claude and Codex
- generates mini-project ideas from the strongest themes

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

Optional:

- Set `GITHUB_TOKEN` for higher GitHub API limits.
- Set `SLACK_WEBHOOK_URL` to send the Slack digest automatically.
- Set `SMTP_HOST`, `SMTP_FROM`, and `SMTP_TO` to send the email digest automatically.

## Dashboard

Run the dashboard with:

```bash
streamlit run dashboard.py
```

The dashboard lets you:

- review signals visually
- label items as `watch`, `test`, `implement`, or `archive`
- capture notes and next actions
- regenerate digest files from your current queue
- review the benchmark pack in one place

## Output

The main run writes:

- `reports/latest_briefing.md`
- `reports/latest_briefing.json`
- `reports/latest_email_digest.md`
- `reports/latest_slack_digest.txt`
- `data/operator_memory.json`
- `benchmarks/benchmark_tasks.json`
- `benchmarks/benchmark_scorecard.md`
- `benchmarks/results_template.csv`

It also archives timestamped copies in `reports/archive/`.

## Customize It

Edit `config/sources.json` to:

- add or remove sources
- change keyword priorities
- tune scoring weights
- narrow the routine toward business use cases, analytics, or pure engineering

## How To Use The System

Each day:

1. Read the top 5 items.
2. In the dashboard, label each one as `watch`, `test`, `implement`, or `archive`.
3. Add one next action to the top item you care about.
4. Send or archive the digest.

Each week:

1. Build one small project from the report.
2. Use the benchmark pack to compare Claude and Codex on one recurring task.
3. Use Claude to pressure-test the idea and Codex to implement it.
4. Keep notes on which tools saved time, improved quality, or were mostly hype.

The playbook for that loop is in `docs/operator_playbook.md`.
