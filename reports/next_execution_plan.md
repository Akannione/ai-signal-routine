# Operator Next Execution Plan

Updated for the July 3, 2026 draft pull-request state.

## Current System State

- Daily LaunchAgent is installed and scheduled for 8:00 AM local time.
- Latest runtime report was generated at `~/.ai-signal-routine-runtime/reports/latest_briefing.md` on June 8, 2026 at 8:13 AM.
- iMessage delivery is working.
- GitHub token handling falls back cleanly if a token is rejected.
- `GITHUB_TOKEN` validation passes with the authenticated 5,000-request core limit and 30-request search limit.
- The feature branch is pushed and draft pull request [#1](https://github.com/Akannione/ai-signal-routine/pull/1) is open with the complete feature history and 0 commits behind `main`.
- The publish helper targets `Akannione/ai-signal-routine` and refuses to force-push over a divergent remote branch.

## Step 1: Review And Merge The Draft Pull Request

What you do:

1. Review the pull request and checks:

```bash
gh pr view 1 --repo Akannione/ai-signal-routine --web
gh pr checks 1 --repo Akannione/ai-signal-routine
```

The Python verification is green locally. Vercel currently reports an external deployment failure even though this repository is a Streamlit/Python application; decide whether that legacy Vercel integration should be disconnected or intentionally configured before treating it as a required check.

2. When the diff is approved, mark the PR ready and merge it:

```bash
gh pr ready 1 --repo Akannione/ai-signal-routine
gh pr merge 1 --repo Akannione/ai-signal-routine --merge --delete-branch
```

3. Sync the 8 AM runtime after the pull request is merged:

```bash
./scripts/install_launch_agent.sh
```

No token refresh is currently required. Replace `GITHUB_TOKEN` only if the validator later reports `github_token_status=invalid`.

## Step 2: Execute One Weekly Proof

Use the latest daily signal as the source of work. The June 8 digest highlighted:

- `bytechefhq/bytechef`
- `K-Dense-AI/scientific-agent-skills`
- `n8n@1.123.54`

Recommended project:

```text
Scientific Agent Skills Tool Trial
```

Project objective:

Evaluate whether an agent-skills library can improve data-science or research-style workflows enough to become a reusable AI engineering pattern, benchmark, or portfolio case study.

## Step 3: Keep Scope Small

Do not build a full product yet. Produce one evidence artifact:

- setup notes
- one working workflow or failed setup log
- friction score
- use-case fit
- monetization angle
- final verdict: ignore, monitor, build with, or monetize

## Step 4: Portfolio Output

Write a short case study:

```text
Problem:
Advanced AI-agent workflows need reusable skills, evaluation, and repeatability, not just one-off prompts.

Test:
Evaluate `K-Dense-AI/scientific-agent-skills` on one practical data-analysis or research-assistant task.

Result:
Document setup friction, capabilities, output quality, reliability, and where it fits in an AI engineering workflow.

Business angle:
Package as a small AI research/data-analysis automation demo or internal workflow audit.
```

## Commands

Check latest phone digest:

```bash
sed -n '1,80p' ~/.ai-signal-routine-runtime/reports/latest_sms_digest.txt
```

Check latest full report:

```bash
open ~/.ai-signal-routine-runtime/reports/latest_briefing.md
```

Run a manual daily test:

```bash
./scripts/install_launch_agent.sh --start-now
```
