# Operator Next Execution Plan

Updated for the July 2, 2026 publish-readiness pass.

## Current System State

- Daily LaunchAgent is installed and scheduled for 8:00 AM local time.
- Latest runtime report was generated at `~/.ai-signal-routine-runtime/reports/latest_briefing.md` on June 8, 2026 at 8:13 AM.
- iMessage delivery is working.
- GitHub token handling falls back cleanly if a token is rejected.
- `GITHUB_TOKEN` validation passes with the authenticated 5,000-request core limit and 30-request search limit.
- The local feature branch now contains both the public `main` history and the prior public feature-branch tip, so GitHub can generate a normal comparison without a force-push.
- The publish helper targets `Akannione/ai-signal-routine` and refuses to force-push over a divergent remote branch.

## Step 1: Publish The Verified GitHub Coverage Fix

What you do:

1. Reconfirm the token without exposing it:

```bash
./scripts/check_github_token.sh
```

Expected result:

```text
github_token_status=valid
```

2. Publish the prepared branch:

```bash
./scripts/publish_to_github.command
```

3. Sync the 8 AM runtime after the branch is published:

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
