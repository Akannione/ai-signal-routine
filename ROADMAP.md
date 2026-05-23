# Roadmap: AI Ops Command Center

This roadmap turns AI Signal Routine from a signal-monitoring script into a stronger portfolio flagship for analytics, automation, AI operations, and solutions engineering roles.

The next version should answer one question clearly:

> How do I turn AI/tooling noise into decisions, experiments, and portfolio evidence?

## Current Version

AI Signal Routine already provides:

- source monitoring for AI, analytics, and automation signals
- scoring and ranking logic
- Markdown and JSON briefings
- digest outputs
- a lightweight operator memory layer
- Streamlit review workflow
- benchmark files for comparing Claude and Codex on recurring work
- mini-project generation from high-signal themes
- a public-safe sample data path for demoing the dashboard without private credentials
- a real Streamlit screenshot captured from the sample workflow

This is enough to show a working AI operations loop. The next phase should make the system stronger as an analytics product, not just an automation demo.

## Version 1: Public-Safe Proof Layer

Goal: make the project immediately understandable to a recruiter, hiring manager, or technical reviewer.

Completed:

- Added a sanitized sample briefing JSON file.
- Added a sanitized sample operator memory file.
- Added a small `sample_data/` folder so the app can run without private local files or API keys.
- Added a dashboard demo mode with `AI_SIGNAL_SAMPLE_MODE=1 streamlit run dashboard.py`.
- Added README documentation explaining the sample workflow from signal to decision.
- Added a public-safe Streamlit screenshot from sample data.

Success criteria:

- A reviewer can open the repo and understand the workflow without running live API calls.
- The README shows a real dashboard screenshot, not only a static mockup.
- The sample output does not expose personal config, local paths, tokens, private notes, or unpublished data.

## Version 2: AI Ops Command Center

Goal: turn the dashboard into a compact command center for AI operations and analytics automation.

Planned dashboard tabs:

- `Signal Queue`: ranked signals with score, source, category, recommendation, and decision status.
- `Benchmarks`: Claude/Codex task results, scores, notes, and best-use recommendations.
- `Project Backlog`: generated mini-project ideas grouped by career value and build scope.
- `Automation Opportunities`: recurring workflows that could become scripts, dashboards, or client offers.
- `Weekly Brief`: executive summary of what changed, what matters, and what to build next.

Success criteria:

- The dashboard supports a weekly review workflow.
- Each signal can be moved toward `watch`, `test`, `implement`, or `archive`.
- The project backlog connects signals to concrete portfolio builds.
- The weekly brief is usable as a decision memo.

## Version 3: Analytics And Reporting Layer

Goal: make the project stronger for data analytics and BI roles.

Planned work:

- Store signal history in SQLite.
- Add trend views by source, category, recommendation, and theme.
- Add freshness and stale-action tracking.
- Add CSV exports for signal history, decision queue, and benchmark results.
- Add a weekly summary table that can be opened in Excel or Power BI.

Success criteria:

- The project demonstrates more than automation; it also shows analytics modeling and reporting.
- A reviewer can see how raw signal data becomes structured decision data.
- Exports support downstream dashboarding or stakeholder reporting.

## Version 4: Workflow Reliability Layer

Goal: show stronger engineering judgment around repeatable automation.

Planned work:

- Add tests for scoring, category assignment, sample data loading, and dashboard data transforms.
- Add clear error handling for missing API tokens or rate-limited sources.
- Add a public-safe config example.
- Add a simple health check for source availability.
- Add a `make demo` or equivalent command for running the sample workflow.

Success criteria:

- The demo path works without private credentials.
- Failure states are understandable.
- The repo feels reliable enough for a technical reviewer to trust.

## Version 5: Solutions Engineering Packaging

Goal: package the project as a practical workflow someone could adapt for a team.

Planned work:

- Add a one-page implementation brief.
- Add a sample weekly operating review template.
- Add examples of business questions the system answers.
- Add a short architecture diagram.
- Add a comparison section: manual research process vs. AI Ops Command Center process.

Success criteria:

- The repo tells a clear before/after story.
- The project can be explained as an internal tool, analyst workflow, or lightweight AI operations system.
- The value is visible to non-technical stakeholders.

## Career Positioning

This roadmap is designed to support four role lanes:

- Data analytics: structured data, dashboards, trend analysis, reporting exports.
- Automation: recurring source monitoring, scoring, queue management, digest generation.
- AI operations: filtering noisy AI signals into decisions and experiments.
- Solutions engineering: clear workflow demo, stakeholder-ready summary, practical implementation story.

## Immediate Next Build

Version 1 is now complete enough for portfolio review.

The highest-leverage next task is Version 3: add a lightweight SQLite trend layer so the project shows historical signal tracking, stale-action reporting, and exportable analytics tables. That will make the repo stronger for analytics, BI, AI operations, and solutions engineering roles at the same time.
