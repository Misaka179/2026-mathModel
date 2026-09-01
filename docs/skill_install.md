# Skill Install

本仓库使用两套 MathModeling skills：

## 1. v2 — 团队定制 31-skill 集（推荐，日常主力）

已打包在 `skills/math-modeling-v2/`，与个人已装的 `~/.claude/skills/` 版本一致。

**Windows：**

```powershell
cd skills
.\install.ps1
```

**macOS / Linux：**

```bash
cd skills
bash install.sh
```

脚本会：备份同名旧目录 → 把每个 skill 复制到 `~/.claude/skills/`。安装后重启 Claude Code 生效。

## 2. v1 — 上游 math-modeling skill（可选）

v1 是开源上游 skill（建模手/编程手/论文手三角色工作流），体积大未打包进仓库。按需安装：

```bash
git clone https://github.com/XiaoMaColtAI/math-modeling-skill.git
# 把克隆出的目录放入 ~/.claude/skills/math-modeling
```

## 版本对齐

- 若仓库 `skills/math-modeling-v2/` 有更新，请重新运行 install 脚本对齐版本。
- 各人本地 skills 与仓库不一致时，以仓库版本为准（或先沟通）。
