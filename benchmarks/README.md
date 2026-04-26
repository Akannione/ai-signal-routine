# Benchmark Harness

This folder gives you a repeatable way to compare Claude and Codex on your own work.

## How To Run It

1. Pick one task from `benchmark_tasks.json`.
2. Run the same task in Claude and Codex with the same prompt and input context.
3. Score both tools in `benchmark_scorecard.md` or `results_template.csv`.
4. Keep the winner for that use case and update the notes with what made it better.

## What You Learn

- which tool is stronger for coding versus planning
- which tool is better for SQL, analytics, or debugging
- where explanation quality matters more than raw speed
- where your own workflow still needs templates or guardrails
