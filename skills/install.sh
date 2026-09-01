#!/usr/bin/env bash
# MathModeling Skills v2 — 一键安装 (macOS/Linux)
# 用法: 在 skills/ 目录下运行  bash install.sh
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)/math-modeling-v2"
DST_ROOT="$HOME/.claude/skills"

if [ ! -d "$SRC" ]; then
  echo "ERROR: 未找到 $SRC，请确认脚本位于 skills/ 目录。" >&2
  exit 1
fi

mkdir -p "$DST_ROOT"

installed=0
for skill_dir in "$SRC"/*/; do
  [ -d "$skill_dir" ] || continue
  skill_name="$(basename "$skill_dir")"
  target="$DST_ROOT/$skill_name"

  if [ -e "$target" ]; then
    backup="$target.bak-$(date +%Y%m%d%H%M%S)"
    mv "$target" "$backup"
    echo "备份旧目录: $skill_name -> $backup"
  fi

  cp -R "$skill_dir" "$target"
  installed=$((installed + 1))
done

echo "安装完成: 共 $installed 个 skill 已复制到 $DST_ROOT"
echo "请重启 Claude Code 生效。"
