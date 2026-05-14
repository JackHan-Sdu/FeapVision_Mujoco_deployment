#!/bin/bash
# Quick push to: https://github.com/JackHan-Sdu/Feap_vision_mujoco
# Usage (from repo root): bash QUICK_PUSH_GITHUB.sh
#
# HTTPS + PAT（不写进 origin URL）：
#   默认读取 /home/user/Jianghan/Code/github/git.txt
#     第 1 行：GitHub 用户名（如 JackHan-Sdu）
#     第 2 行：Personal Access Token（ghp_...，不要用账户登录密码）
#   或设置环境变量：GITHUB_CREDENTIALS=/path/to/git.txt

set -e
cd "$(dirname "$0")"

REPO_URL="https://github.com/JackHan-Sdu/Feap_vision_mujoco.git"
CRED_FILE="${GITHUB_CREDENTIALS:-/home/user/Jianghan/Code/github/git.txt}"

echo "=== Push to Feap_vision_mujoco ==="

if [[ ! -f "$CRED_FILE" ]]; then
  echo "Error: credentials file not found: $CRED_FILE"
  echo "Create it (2 lines: username, then PAT) or set GITHUB_CREDENTIALS."
  exit 1
fi

# GIT_ASKPASS：供本次 push 使用，不缓存到 git config
ASKPASS_HELPER="$(mktemp)"
chmod 700 "$ASKPASS_HELPER"
trap 'rm -f "$ASKPASS_HELPER"' EXIT
{
  echo '#!/bin/bash'
  printf 'CRED_FILE=%q\n' "$CRED_FILE"
  cat <<'READCREDS'
u=$(head -n1 "$CRED_FILE" | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
t=$(sed -n '2p' "$CRED_FILE" | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
if [[ -z "$u" || -z "$t" ]]; then
  echo "git-askpass: empty username or token in $CRED_FILE" >&2
  exit 1
fi
case "$1" in
  *Username*|*username*) printf '%s\n' "$u" ;;
  *Password*|*password*) printf '%s\n' "$t" ;;
  *) exit 1 ;;
esac
READCREDS
} >"$ASKPASS_HELPER"

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

echo "4. git push -u origin main (PAT from $CRED_FILE)"
# credential.helper= 避免与系统缓存冲突；GIT_TERMINAL_PROMPT=0 强制走 GIT_ASKPASS
if ! GIT_TERMINAL_PROMPT=0 GIT_ASKPASS="$ASKPASS_HELPER" git -c credential.helper= push -u origin main; then
  echo ""
  echo "Push failed. Typical fixes:"
  echo "  - Token: GitHub → PAT (classic) 勾选 repo；第 2 行必须是 ghp_... 不是登录密码。"
  echo "  - 确认仓库已创建: https://github.com/JackHan-Sdu/Feap_vision_mujoco"
  echo "  - 分叉历史: git pull --rebase origin main 后再 push。"
  echo "  - 谨慎覆盖远程: git push --force-with-lease -u origin main"
  exit 1
fi

echo ""
echo "Done: https://github.com/JackHan-Sdu/Feap_vision_mujoco"
echo "Branch: main"
