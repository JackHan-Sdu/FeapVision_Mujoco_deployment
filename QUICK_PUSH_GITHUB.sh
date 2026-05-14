#!/bin/bash
# Quick push to: https://github.com/JackHan-Sdu/Feap_vision_mujoco
# Usage (from repo root): bash QUICK_PUSH_GITHUB.sh

set -e
cd "$(dirname "$0")"

REPO_URL="https://github.com/JackHan-Sdu/Feap_vision_mujoco.git"

echo "=== Push to Feap_vision_mujoco ==="

# Initialize repo if needed (same idea as GitHub "create a new repository on the command line")
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "No git repo here — running git init"
  git init
fi

# origin → Feap_vision_mujoco (matches: git remote add origin <url>)
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REPO_URL"
  echo "Remote origin → $REPO_URL"
else
  git remote add origin "$REPO_URL"
  echo "Remote origin added → $REPO_URL"
fi

echo "1. git add ."
git add .

echo "2. commit (if there are changes)"
if git diff --cached --quiet && git diff --quiet; then
  echo "   Nothing to commit, skip"
else
  git commit -m "feat: Feap vision MuJoCo deploy

- MuJoCo vision deployment (proprio + depth + gamepad)
- TorchScript policy runner
- README and configs"
fi

echo "3. git branch -M main"
git branch -M main

if ! git rev-parse HEAD >/dev/null 2>&1; then
  echo "Error: no commits yet. Add files (or relax .gitignore), then run this script again."
  exit 1
fi

echo "4. git push -u origin main"
# First push to an empty GitHub repo; use --force-with-lease only if you intentionally rewrite remote main
if ! git push -u origin main; then
  echo ""
  echo "Push failed. Typical fixes:"
  echo "  - New empty repo: ensure GitHub repo exists and you are logged in (HTTPS credential / token)."
  echo "  - Divergent history: git pull --rebase origin main  then push again."
  echo "  - Intentional overwrite (careful): git push --force-with-lease -u origin main"
  exit 1
fi

echo ""
echo "Done: https://github.com/JackHan-Sdu/Feap_vision_mujoco"
echo "Branch: main"
