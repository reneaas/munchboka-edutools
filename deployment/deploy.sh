#!/bin/bash
# Pull-based deploy for Jeopardy and Livequiz, run by a cPanel cron job.
# Copies only; never deletes, so jeopardy-private/database.php is untouched.
set -euo pipefail

main() {
  local url=https://github.com/reneaas/munchboka-edutools.git
  local repo="$HOME/repositories/munchboka-edutools"
  local marker="$HOME/.munchboka-deployed-commit"

  if [ ! -d "$repo/.git" ]; then
    mkdir -p "$(dirname "$repo")"
    git clone --quiet --depth 1 "$url" "$repo"
  fi

  cd "$repo"
  git fetch --quiet --depth 1 origin main
  local commit
  commit=$(git rev-parse FETCH_HEAD)

  if [ "$(cat "$marker" 2>/dev/null || true)" = "$commit" ] && [ -z "${FORCE:-}" ]; then
    exit 0
  fi

  git reset --quiet --hard FETCH_HEAD

  copy() { mkdir -p "$2"; cp -Rf "$1/." "$2/"; }
  copy deployment/jeopardy/pilot/public "$HOME/public_html/jeopardy"
  copy deployment/jeopardy/pilot/private "$HOME/jeopardy-private"
  copy deployment/livequiz/public "$HOME/public_html/quiz"
  copy deployment/livequiz/private/livequiz "$HOME/jeopardy-private/livequiz"

  echo "$commit" > "$marker"
  echo "$(date '+%F %T') deployed $commit"
}

# Whole file is parsed before running, so git reset can safely replace this script.
main "$@"
exit
