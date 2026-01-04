#!/usr/bin/env bash
set -e

CMD=${1:-push}
MSG=${2:-"update"}

if [ "$CMD" = "init" ]; then
  if [ ! -d .git ]; then
    git init
    git branch -M main || true
  fi
  echo ".venv/" >> .gitignore || true
  echo "__pycache__/" >> .gitignore || true
  echo ".DS_Store" >> .gitignore || true
  echo "data/pickle_data/" >> .gitignore || true
  echo "data/market_csv/" >> .gitignore || true
  echo "data/output/" >> .gitignore || true
  echo "data/oi_history/" >> .gitignore || true
  git add .
  git commit -m "init project"
  exit 0
fi

git add .
git commit -m "$MSG" || true
if git remote -v | grep -q origin; then
  git push origin main || git push -u origin main
else
  echo "No remote 'origin' configured. Set remote and rerun:"
  echo "git remote add origin <your_repo_url>"
  echo "bash scripts/sync_to_github.sh push \"update\""
fi

