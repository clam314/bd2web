#!/usr/bin/env bash
# 同步上游素材仓库（只取 spine/ 目录，约 2.8GB，增量更新只拉变化的文件），
# 然后重新生成 data/roster.json。可重复执行，适合放进 cron。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_URL="https://github.com/myssal/Brown-Dust-2-Asset.git"
UPSTREAM="$ROOT/upstream"

if [ ! -d "$UPSTREAM/.git" ]; then
  echo "==> 首次克隆（partial + sparse，只下载 spine/ 的文件）"
  git clone --filter=blob:none --sparse --depth 1 "$REPO_URL" "$UPSTREAM"
  git -C "$UPSTREAM" sparse-checkout set spine
else
  echo "==> 增量更新"
  git -C "$UPSTREAM" fetch --depth 1 origin master
  git -C "$UPSTREAM" reset --hard origin/master
fi

echo "==> 重新生成 roster.json"
python3 "$ROOT/tools/gen_roster.py"

echo "==> 完成 $(date '+%F %T')"
