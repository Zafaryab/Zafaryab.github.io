#!/usr/bin/env bash
set -euo pipefail

# git_update.sh
# Safe sync: fetch -> pull (rebase by default) -> optional push
# Usage:
#   ./git_update.sh            # pull --rebase (safe default)
#   ./git_update.sh --push     # pull --rebase then push
#   ./git_update.sh --merge    # pull with merge instead of rebase
#   ./git_update.sh --help

usage() {
  cat <<'EOF'
Usage: ./git_update.sh [--push] [--merge] [--remote origin]

Options:
  --push         After updating, push current branch to remote
  --merge        Use merge instead of rebase for pulling
  --remote NAME  Remote name (default: origin)
  --help         Show help

Notes:
- Default is pull --rebase to minimize merge commits and reduce push conflicts.
- Will auto-stash local changes during pull.
EOF
}

REMOTE="origin"
DO_PUSH="false"
USE_MERGE="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --push)  DO_PUSH="true"; shift ;;
    --merge) USE_MERGE="true"; shift ;;
    --remote) REMOTE="${2:-}"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

# Ensure we're in a git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "❌ Not inside a git repository."
  exit 1
fi

# Ensure remote exists
if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
  echo "❌ Remote '$REMOTE' not found."
  echo "   Available remotes: $(git remote)"
  exit 1
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"

if [[ "$BRANCH" == "HEAD" ]]; then
  echo "❌ Detached HEAD state. Checkout a branch first."
  exit 1
fi

echo "📌 Repo: $(basename "$(git rev-parse --show-toplevel)")"
echo "🌿 Branch: $BRANCH"
echo "🔗 Remote: $REMOTE"

# Fetch latest refs
echo "⬇️  Fetching..."
git fetch --prune "$REMOTE"

# Ensure upstream tracking is set (helps pull/push)
if ! git rev-parse --abbrev-ref --symbolic-full-name "@{u}" >/dev/null 2>&1; then
  if git show-ref --verify --quiet "refs/remotes/$REMOTE/$BRANCH"; then
    echo "🔧 Setting upstream to $REMOTE/$BRANCH"
    git branch --set-upstream-to "$REMOTE/$BRANCH" "$BRANCH"
  else
    echo "ℹ️  No upstream set and remote branch '$REMOTE/$BRANCH' not found."
    echo "   (This is fine for a new branch; push once with --push.)"
  fi
fi

# Determine ahead/behind (if upstream exists)
if git rev-parse --abbrev-ref --symbolic-full-name "@{u}" >/dev/null 2>&1; then
  set +e
  COUNTS="$(git rev-list --left-right --count HEAD...@{u} 2>/dev/null)"
  set -e
  AHEAD="$(echo "$COUNTS" | awk '{print $1}')"
  BEHIND="$(echo "$COUNTS" | awk '{print $2}')"
  echo "📊 Ahead: ${AHEAD:-0}  Behind: ${BEHIND:-0}"
fi

# Pull updates
echo "🔄 Updating local branch..."
if [[ "$USE_MERGE" == "true" ]]; then
  git pull --autostash "$REMOTE" "$BRANCH" || {
    echo "❌ Pull (merge) failed. Resolve conflicts, then run:"
    echo "   git status"
    echo "   git add -A"
    echo "   git commit"
    exit 1
  }
else
  git pull --rebase --autostash "$REMOTE" "$BRANCH" || {
    echo "❌ Pull (rebase) failed."
    echo "Resolve rebase conflicts, then run:"
    echo "   git status"
    echo "   git add -A"
    echo "   git rebase --continue"
    echo ""
    echo "Or abort rebase:"
    echo "   git rebase --abort"
    exit 1
  }
fi

echo "✅ Updated successfully."
git status --short --branch

# Optional push
if [[ "$DO_PUSH" == "true" ]]; then
  echo "⬆️  Pushing to $REMOTE/$BRANCH..."
  # Always push explicitly to the selected remote/branch. If there's no upstream, set it.
  if git rev-parse --abbrev-ref --symbolic-full-name "@{u}" >/dev/null 2>&1; then
    git push "$REMOTE" "$BRANCH" || {
      echo "❌ Push failed. Try: git push -u $REMOTE $BRANCH"
      exit 1
    }
  else
    git push -u "$REMOTE" "$BRANCH" || {
      echo "❌ Push (initial) failed. Resolve any auth/remote issues and retry."
      exit 1
    }
  fi
  echo "✅ Push complete."
fi
