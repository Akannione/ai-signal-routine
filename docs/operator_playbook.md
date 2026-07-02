# AI Operator Playbook

This project is built around a simple idea: you do not become hard to replace by reading the most news. You become hard to replace by building a repeatable loop that turns new information into judgment, experiments, and portfolio evidence.

## Your Edge

Your background is strong for this path because it already spans business administration, computer information systems, Python, SQL, AWS, analytics, and infrastructure basics. That combination matters. The market is filling up with people who can prompt and people who can code, but there are still far fewer people who can:

- translate model and tooling changes into business decisions
- decide what is worth implementing versus what is hype
- prototype analytics and automation workflows quickly
- explain the tradeoffs in plain business language

That is the lane this routine is designed for.

## What To Watch

Use the automation to cover four lanes:

1. Official product and engineering updates.
   Track OpenAI, Anthropic, Hugging Face, AWS, GitHub, and similar builder ecosystems first. This is where high-quality release notes, APIs, and platform shifts show up.

2. Open-source adoption signals.
   Track GitHub repositories, not just articles. Stars are not everything, but strong repo adoption plus recent activity is often a better signal than social hype.

3. Practitioner discussion.
   Hacker News, issue threads, and engineering blog posts help you see where tools break, where they shine, and where real users are spending time.

4. Research with implementation potential.
   Papers matter most when they produce a method you can test in a notebook, dashboard, evaluation harness, or workflow.

## Current Signals

As of April 25, 2026, the current open-source and product landscape suggests a few strong areas to monitor closely:

- `browser-use/browser-use` is showing major adoption for browser automation workflows and AI agents. GitHub's public repo page snippet showed roughly 88k stars in April 2026.
  Source: [browser-use/browser-use](https://github.com/browser-use/browser-use)

- `modelcontextprotocol/servers` has become one of the clearest infrastructure signals for agent tooling. GitHub's public repo page snippet showed about 83.8k stars.
  Source: [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)

- `All-Hands-AI/OpenHands` is one of the strongest signals in open agentic development tooling. GitHub's public repo page snippet showed roughly 71.4k stars.
  Source: [All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands)

- Crawl4AI's own stats page reported 60,904 GitHub stars on February 24, 2026, with strong download growth. That makes it one of the clearest signals for web-to-LLM extraction pipelines.
  Source: [Crawl4AI stats](https://docs.crawl4ai.com/stats/)

- `Aider-AI/aider` remains a serious practical repo for coding workflow improvement, with GitHub snippets showing about 43.5k stars in April 2026.
  Source: [Aider-AI/aider](https://github.com/Aider-AI/aider)

- `microsoft/playwright-mcp` is a strong signal for browser automation plus MCP-based workflows, with GitHub snippets showing about 31k stars.
  Source: [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)

- `openai/openai-agents-python` is a major workflow repo for multi-agent orchestration, with GitHub snippets showing about 21.9k stars in April 2026.
  Source: [openai/openai-agents-python](https://github.com/openai/openai-agents-python)

- `simonw/llm` remains a practical command-line and experimentation tool with GitHub snippets showing about 11.6k stars.
  Source: [simonw/llm](https://github.com/simonw/llm)

## Claude And Codex Use Cases Worth Studying

The strongest signal is that both tools are moving beyond assistant behavior into operating-system behavior for real work.

OpenAI has published that Codex is being used internally across security, product engineering, frontend, API, infrastructure, and performance teams for code understanding, performance work, test generation, staying in flow, and ideation.
Source: [How OpenAI uses Codex](https://openai.com/business/guides-and-resources/how-openai-uses-codex/)

OpenAI also published a work-focused set of Codex use cases on April 23, 2026, including a daily chief of staff, weekly summary, draft slide decks, research-to-decision memo, spreadsheet consolidation, book of business prioritization, month-end financial review, and workflow audit.
Source: [Top 10 uses for Codex at work](https://openai.com/academy/top-10-use-cases-codex-for-work)

Anthropic's Claude Code product page says Claude Code is now used broadly enough at Anthropic that the majority of code is written by Claude Code. Their public customer examples are especially relevant for you:

- Ramp reported an 80% reduction in incident investigation time, and said non-engineering teams across sales, risk, and finance query their warehouse in natural language.
- Ramp also shared that Claude can help turn exploratory notebook work into Metaflow pipelines, saving one to two days per model.
- Stripe reportedly deployed Claude Code to 1,370 engineers, including a 10,000-line Scala-to-Java migration completed in four days.
- Wiz reported migrating a 50,000-line Python library to Go in about 20 hours of active development.
- Rakuten reported reducing average feature delivery from 24 working days to 5.
- Intercom described using Claude Code to build internal applications like AI labeling tools and ROI calculators.

Source: [Anthropic Claude Code](https://www.anthropic.com/product/claude-code)

## How To Use This System Weekly

Run the script daily in the morning or early evening. Let it give you a ranked briefing, then do this:

1. Read the top 5 signals.
2. Pick 1 item to explain to yourself in business terms.
3. Pick 1 item to test in code.
4. Capture 1 sentence on whether it is `watch`, `test`, or `implement`.
5. Add one next action in the memory file or dashboard.

Once a week:

1. Pick the highest-scoring mini project.
2. Run one benchmark task with Claude and Codex using the benchmark harness.
3. Use Claude or Codex to scaffold the best mini project fast.
4. Finish something small enough to demo in a week.
5. Write a short note on what worked, what broke, and where the business value is.

## Delivery And Memory Layer

The new layer matters because raw discovery is not enough. You need a system that remembers what you already saw, what you decided, and what still deserves action.

The project now includes:

- `data/operator_memory.json` for your running decisions, notes, and next actions
- `dashboard.py` for visual review and queue management in Streamlit
- `reports/latest_email_digest.md` and `reports/latest_slack_digest.txt` for delivery
- `benchmarks/` for Claude versus Codex comparisons on recurring work

This turns the project from a reading system into an operating system.

## Recommended Daily Workflow

1. Run `python3 main.py`.
2. Open the dashboard with `streamlit run dashboard.py`.
3. Move at least one item into `test` or `implement`.
4. Write one next action.
5. Send or save the digest.

## Recommended Weekly Workflow

1. Review what is still in `watch`.
2. Pick one benchmark task from `benchmarks/benchmark_tasks.json`.
3. Run the same task with Claude and Codex.
4. Score both tools in `benchmarks/benchmark_scorecard.md` or `benchmarks/results_template.csv`.
5. Update your notes with where each tool is strongest.

## Best Roles For Claude And Codex

Use Claude for:

- turning messy ideas into structured plans
- comparing tools and tradeoffs
- turning notebooks, notes, and requirements into clearer workflows
- generating business-facing explanations and implementation memos

Use Codex for:

- building and refining the project itself
- exploring codebases and repos quickly
- generating or fixing tests
- wiring together scripts, dashboards, data apps, and automation tasks

The powerful pattern is not Claude versus Codex. It is Claude for framing and synthesis, then Codex for implementation and verification.
