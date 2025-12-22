#!/usr/bin/env bash
set -euo pipefail

REMOTE="origin"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
MSG="${1:-}"

# ---------- checks ----------
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "❌ Not inside a git repository."
  exit 1
fi

if [[ "$BRANCH" == "HEAD" || -z "$BRANCH" ]]; then
  echo "❌ Detached HEAD. Checkout a branch first."
  exit 1
fi

if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
  echo "❌ Remote '$REMOTE' not found. Available: $(git remote)"
  exit 1
fi

echo "📌 Repo: $(basename "$(git rev-parse --show-toplevel)")"
echo "🌿 Branch: $BRANCH"
echo "🔗 Remote: $REMOTE"

# ---------- commit local changes if any ----------
if [[ -n "$(git status --porcelain)" ]]; then
  echo "📝 Local changes found → staging..."
  git add -A

  # Only commit if staging produced something to commit
  if ! git diff --cached --quiet; then
    if [[ -z "$MSG" ]]; then
      MSG="Update site $(date '+%Y-%m-%d %H:%M')"
    fi
    echo "✅ Committing: $MSG"
    git commit -m "$MSG"
  fi
else
  echo "✅ Working tree clean (no local changes to commit)."
fi

# ---------- update (pull safely) ----------
echo "⬇️  Fetching..."
git fetch --prune "$REMOTE"

# If upstream exists, rebase on it. If not, skip pull (new branch case).
if git rev-parse --abbrev-ref --symbolic-full-name "@{u}" >/dev/null 2>&1; then
  echo "🔄 Pulling with rebase (autostash)..."
  git pull --rebase --autostash
else
  echo "ℹ️  No upstream set yet (likely a new branch). Skipping pull."
fi

# ---------- push ----------
echo "⬆️  Pushing..."
if git rev-parse --abbrev-ref --symbolic-full-name "@{u}" >/dev/null 2>&1; then
  git push
else
  git push -u "$REMOTE" "$BRANCH"
fi

echo "✅ Done."
git status -sb
