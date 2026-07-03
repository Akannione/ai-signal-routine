# Operator Next Execution Plan

Updated for the July 3, 2026 merged and installed runtime state.

## Current System State

- Daily LaunchAgent is installed and scheduled for 8:00 AM local time.
- Latest runtime report was generated at `~/.ai-signal-routine-runtime/reports/latest_briefing.md` on June 8, 2026 at 8:13 AM.
- iMessage delivery is working.
- GitHub token handling falls back cleanly if a token is rejected.
- `GITHUB_TOKEN` validation passes with the authenticated 5,000-request core limit and 30-request search limit.
- Coverage and runtime follow-up pull requests #1 through #6 are merged into `main`.
- The publish helper targets `Akannione/ai-signal-routine` and refuses to force-push over a divergent remote branch.
- The stale Vercel project is removed; it had no successful deployment or custom domain.
- The 8:00 AM LaunchAgent is installed from a scoped 344 MB runtime that excludes unrelated workspace projects and preserves live reports and data.

## Step 1: Verify The Next Scheduled Run

What you do:

After the next 8:00 AM run, verify the job result and fresh output:

```bash
launchctl print "gui/$(id -u)/com.akannione.ai-signal-routine.daily" | rg 'last exit code|runs =|state ='
tail -80 ~/.ai-signal-routine-runtime/logs/launchd.out.log
tail -80 ~/.ai-signal-routine-runtime/logs/launchd.err.log
stat -f '%Sm %N' ~/.ai-signal-routine-runtime/reports/latest_briefing.md
```

Expected: a zero exit code, a new report timestamp, and no copied `TOBI_OS`, `career_system`, `business_os_mvp`, or `outputs` directory under the staged runtime.

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
