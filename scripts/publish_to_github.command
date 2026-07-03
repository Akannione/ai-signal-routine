#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

REMOTE_URL="https://github.com/Akannione/ai-signal-routine.git"
DEFAULT_BRANCH_NAME="codex/build-clinic-outreach-automation"
COMMIT_MESSAGE="Expand daily signal coverage and digest guidance"

FILES=(
  ".gitignore"
  "README.md"
  "config/sources.json"
  "config/local.env.example"
  "dashboard.py"
  "docs/operator_playbook.md"
  "reports/latest_sms_digest.txt"
  "reports/next_execution_plan.md"
  "scripts/check_github_token.sh"
  "scripts/install_daily_agent.command"
  "scripts/install_launch_agent.sh"
  "scripts/publish_to_github.command"
  "src/ai_signal_routine/cli.py"
  "src/ai_signal_routine/digests.py"
  "src/ai_signal_routine/history.py"
  "src/ai_signal_routine/mini_projects.py"
  "src/ai_signal_routine/reporting.py"
  "src/ai_signal_routine/scoring.py"
  "src/ai_signal_routine/sources.py"
  "tests/test_scoring.py"
  "tests/test_sources.py"
)

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This folder is not a git repository."
  exit 1
fi

if [[ -z "$(git config user.name || true)" ]]; then
  git config user.name "Akannione"
fi

if [[ -z "$(git config user.email || true)" ]]; then
  git config user.email "tobioniyide27@gmail.com"
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "$REMOTE_URL"
elif [[ "$(git remote get-url origin)" != "$REMOTE_URL" ]]; then
  git remote set-url origin "$REMOTE_URL"
fi

CURRENT_BRANCH="$(git branch --show-current || true)"
if [[ -z "$CURRENT_BRANCH" || "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
  git switch -c "$DEFAULT_BRANCH_NAME"
  CURRENT_BRANCH="$DEFAULT_BRANCH_NAME"
fi

git fetch origin "$CURRENT_BRANCH" >/dev/null 2>&1 || true
if git show-ref --verify --quiet "refs/remotes/origin/$CURRENT_BRANCH" && \
  ! git merge-base --is-ancestor "origin/$CURRENT_BRANCH" HEAD; then
  echo "Remote branch origin/$CURRENT_BRANCH is not an ancestor of local HEAD." >&2
  echo "Fetch and reconcile the branch before publishing; this helper will not force-push." >&2
  exit 1
fi

git add "${FILES[@]}"

if git diff --cached --quiet; then
  echo "No changes are staged for publish."
  exit 0
fi

if ! git diff --cached --quiet; then
  git commit -m "$COMMIT_MESSAGE"
fi

git push -u origin "$CURRENT_BRANCH"

echo
echo "Pushed $CURRENT_BRANCH to GitHub."
echo "Open a compare view to review or create a pull request:"
echo "https://github.com/Akannione/ai-signal-routine/compare/main...${CURRENT_BRANCH}?expand=1"

if command -v open >/dev/null 2>&1; then
  open "https://github.com/Akannione/ai-signal-routine/compare/main...${CURRENT_BRANCH}?expand=1"
fi
