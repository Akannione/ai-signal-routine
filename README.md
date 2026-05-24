# AI Signal Routine

This project is now tuned as an AI Operator Intelligence routine, not a generic AI news feed. It is built to surface high-signal tools, builders, workflows, infrastructure shifts, and monetizable opportunities that create leverage for data analytics, data science, AI engineering, automation systems, freelancing, and technical product building.

It gives you a practical monitoring loop for:

- generative AI news and tooling
- data analytics and data science ideas
- open-source repo adoption signals
- Claude and Codex workflow opportunities
- builder-grade workflows and technical playbooks
- freelance, consulting, and startup opportunity signals
- noise/hype filtering for low-depth AI content
- mini-project generation for ongoing skill growth
- a memory layer for decisions and notes
- delivery digests for email and Slack
- delivery digests for iMessage text delivery
- local bash scripts for daily runs and Messages delivery
- a benchmark harness for Claude vs Codex on recurring work

It is intentionally built as a `signal system`, not a generic scraper. The goal is to help you decide what is worth learning, monitoring, building with, monetizing, or ignoring.

## What It Does

The pipeline pulls from multiple sources:

- official blogs and release feeds
- GitHub repository search
- GitHub release tracking for key workflow repos
- Hacker News discussion
- Reddit discussion across AI and analytics communities
- arXiv research feeds

Then it:

- scores items across technical depth, real-world utility, leverage potential, monetization potential, future relevance, learning value, adoption speed, difficulty to replicate, career value, and strategic edge
- ranks the strongest signals
- classifies signals into categories like Immediate Edge, Emerging Infrastructure, AI Engineering, Automation Systems, Analytics/Data Engineering, Freelance Leverage, Startup Opportunities, High-Signal Builders, Tooling Stack, Underrated Opportunities, and Noise/Hype To Ignore
- adds a structured operator intelligence layer for each major insight: why it matters to your path, who is using it, leverage created, skill gain, monetization angle, difficulty, market saturation, next step, and recommendation
- writes a Markdown briefing and JSON payload
- stores your `watch`, `test`, and `implement` decisions
- writes email and Slack digest files
- writes a short phone digest sized for iMessage delivery
- routes local phone delivery through a bash script you can automate
- creates a benchmark pack for Claude and Codex
- generates more varied mini-project ideas from both the strongest themes and the top live signals

## Quick Start

Use the WSL project path for local development:

```bash
cd "/home/tobio/Documents/New project"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/local.env.example config/local.env
chmod +x scripts/imessage.sh scripts/run_daily.sh
chmod +x scripts/install_launch_agent.sh
python3 main.py
```

Do not commit or paste values from `config/local.env`; keep real tokens, webhook URLs, phone numbers, and SMTP credentials local only.

Optional:

- Set `GITHUB_TOKEN` for higher GitHub API limits.
- Set `SLACK_WEBHOOK_URL` to send the Slack digest automatically.
- Set `SMTP_HOST`, `SMTP_FROM`, and `SMTP_TO` to send the email digest automatically.
- Set `IMESSAGE_RECIPIENT` to send the short digest through the Mac Messages app automatically.
- Use `config/local.env` for local automation settings like recipient and schedule time.

## Project Files

The AI Signal Routine project lives in these root-level files and folders:

- `main.py` - CLI entry point for building the briefing, digests, and benchmark pack.
- `dashboard.py` - Streamlit dashboard for signal review, memory updates, digests, mini-projects, and benchmarks.
- `src/ai_signal_routine/` - core collectors, scoring, reporting, digests, memory, benchmark, and mini-project logic.
- `config/sources.json` - tracked source and scoring configuration.
- `config/local.env.example` - safe template for local environment settings.
- `config/local.env` - untracked local settings file; do not expose or edit it unless you are configuring your own machine.
- `reports/` - latest generated briefing and digest outputs.
- `data/operator_memory.json` - local decision memory used by the dashboard.
- `benchmarks/` - Claude vs Codex benchmark tasks, scorecard, and result template.
- `scripts/` - local daily run, iMessage, launch agent, and publish helpers.
- `docs/operator_playbook.md` - operating guide for the daily and weekly routine.
- `tests/` - scoring and delivery behavior tests.

## Dashboard

Run the dashboard with:

```bash
AI_SIGNAL_SAMPLE_MODE=1 streamlit run dashboard.py
```

Then open the local URL Streamlit prints, usually `http://localhost:8501`.

The dashboard lets you:

- review signals visually
- inspect category, recommendation, scorecard dimensions, `why this matters`, `how it works`, and `should I implement it` guidance per signal
- review the Opportunity Radar, High-Signal Builders tracker, and Noise/Hype To Ignore list
- label items as `watch`, `test`, `implement`, or `archive`
- capture notes and next actions
- regenerate digest files from your current queue
- review the benchmark pack in one place

## Screenshots

Screenshots are not required to run the project, but they are useful for README previews, portfolio writeups, and visual QA.

Recommended local flow:

```bash
mkdir -p docs/screenshots
AI_SIGNAL_SAMPLE_MODE=1 streamlit run dashboard.py
```

Capture the main dashboard views from Streamlit and save them under `docs/screenshots/`:

- `docs/screenshots/radar.png` - main signal review view with top ranked signals and operator score details visible.
- `docs/screenshots/opportunities.png` - Opportunity Radar section showing monetizable or buildable ideas.
- `docs/screenshots/digests.png` - digest preview area showing email, Slack, and phone digest outputs without real credentials.
- `docs/screenshots/benchmark.png` - benchmark pack view showing Claude versus Codex tasks and scorecard context.

Optional:

- `docs/screenshots/memory.png` - decision queue or memory notes with safe sample data.
- `docs/screenshots/mini-projects.png` - mini-project ideas generated from current signal themes.

Before committing screenshots, confirm no real tokens, webhook URLs, phone numbers, email addresses, or private notes are visible.

Add images to this section with relative Markdown links after the files exist:

```md
![Radar tab](docs/screenshots/radar.png)
![Opportunity radar](docs/screenshots/opportunities.png)
![Digest previews](docs/screenshots/digests.png)
![Benchmark pack](docs/screenshots/benchmark.png)
```

## Output

The main run writes:

- `reports/latest_briefing.md`
- `reports/latest_briefing.json`
- `reports/latest_email_digest.md`
- `reports/latest_slack_digest.txt`
- `reports/latest_sms_digest.txt`
- `data/operator_memory.json`
- `scripts/imessage.sh`
- `scripts/run_daily.sh`
- `scripts/install_launch_agent.sh`
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
2. Check the recommendation: `Learn`, `Monitor`, `Build With`, `Monetize`, or `Ignore`.
3. In the dashboard, label each one as `watch`, `test`, `implement`, or `archive`.
4. Add one next action to the top item you care about.
5. Send or archive the digest, including iMessage if you want the top intel on your phone.

If you want the project to behave like a true daily agent, set `DAILY_RUN_HOUR` and `DAILY_RUN_MINUTE` in `config/local.env`, then install the LaunchAgent once with `scripts/install_launch_agent.sh`.

Each week:

1. Build one small project from the report, preferably from `Build With` or `Monetize`.
2. Use the benchmark pack to compare Claude and Codex on one recurring task.
3. Use Claude to pressure-test the idea and Codex to implement it.
4. Keep notes on which tools saved time, improved quality, created a sellable workflow, or were mostly hype.

The playbook for that loop is in `docs/operator_playbook.md`.

## iMessage Setup

The built-in phone-text path uses the macOS Messages app through `scripts/imessage.sh`.

1. Make sure Messages is signed in to iMessage on this Mac.
2. Confirm your recipient number in `config/local.env`.
3. Make both scripts executable once:

```bash
chmod +x scripts/imessage.sh scripts/run_daily.sh scripts/install_launch_agent.sh scripts/install_daily_agent.command
```

4. Run the local daily pipeline:

```bash
./scripts/run_daily.sh
```

5. For a direct one-off iMessage send from the latest digest:

```bash
./scripts/imessage.sh --recipient +15555550123 --file reports/latest_sms_digest.txt
```

The first time you send, macOS may ask you to allow Terminal, Python, or System Events to control Messages. Approve those prompts, then the script can send the short digest for you.

The script tries direct Messages sending first and then falls back to a UI-driven compose flow if needed. The UI fallback may require Accessibility permissions for Terminal or the app that launches the script.

The phone digest now also uses a short history window so it does not default to repeating the exact same top links or project title every morning when fresher candidates are available.

## Daily Schedule

To send the update at a designated local time every day on macOS:

1. Copy the example env file once if you have not already:

```bash
cp config/local.env.example config/local.env
```

2. Edit `config/local.env` and set:

```bash
IMESSAGE_RECIPIENT=+15555550123
DAILY_RUN_HOUR=8
DAILY_RUN_MINUTE=0
```

3. Install the LaunchAgent:

```bash
./scripts/install_launch_agent.sh
```

Or double-click `scripts/install_daily_agent.command` in Finder to install the daily schedule and trigger the first run without typing commands.

4. If you want to test it immediately after install:

```bash
./scripts/install_launch_agent.sh --start-now
```

5. If you ever want to remove the schedule:

```bash
./scripts/install_launch_agent.sh --uninstall
```

If the project lives in a protected macOS folder like `Documents`, the installer automatically stages a runnable copy under `~/.ai-signal-routine-runtime` and schedules that copy instead.

The installer writes a plist into `~/Library/LaunchAgents`, schedules `scripts/run_daily.sh`, and writes logs to either `logs/launchd.out.log` and `logs/launchd.err.log` in the project root, or the same paths under `~/.ai-signal-routine-runtime` when staging is needed.

If you change the local code after the scheduler is already installed, run `./scripts/install_launch_agent.sh --start-now` again so the staged runtime copy picks up the latest logic.

## GitHub Sync

If you want to publish the current local upgrade set back to GitHub from your own Mac session, double-click `scripts/publish_to_github.command` in Finder.

That helper will:

- add `origin` if it is missing
- set a local git name and email if they are blank
- stage only the agent-related upgrade files
- commit them on your current branch
- push the branch to GitHub
- open the compare page so you can review or create a pull request

## Daily Automation Target

If you want a single target for `launchd`, Shortcuts, or Calendar automation, point it at:

```bash
/home/tobio/Documents/New\ project/scripts/run_daily.sh
```
