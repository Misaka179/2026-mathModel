# MathModeling Skills

团队定制的数学建模 Claude Code skills 集。

## v2（推荐，日常主力）

`math-modeling-v2/` — 31 个 skill，覆盖 G1–G6.5 全流程：问题解析、分类、方法选择、数据审计、代码生成与审查、结果判定、图表、论文写作、独立审计。已与各人本地 `~/.claude/skills/` 版本对齐。

安装（任选其一）：

```bash
# Windows（在 skills/ 目录）
.\install.ps1

# macOS / Linux
bash install.sh
```

脚本会备份同名旧目录后复制，安装后重启 Claude Code 生效。详细说明见 `../docs/skill_install.md`。

## v1（上游）

上游 `math-modeling` skill 未打包进仓库（体积大），需要时单独 clone：

```bash
git clone https://github.com/XiaoMaColtAI/math-modeling-skill.git
```

## Skill 清单（31）

problem-parser · problem-classifier · related-paper-analyzer · method-selector · decision-prompt-builder · modeler-decision-logger · data-auditor-cleaner · model-code-analyzer · python-model-code-generator · matlab-model-code-generator · code-reviewer · python-code-reviewer · matlab-code-reviewer · result-report-generator · robustness-checker · figure-table-planner · math-figure-generator · final-method-explainer · solution-package-builder · paper-section-writer · paper-polisher · humanizer-zh · reference-manager · consistency-auditor · completeness-auditor · quality-assurance-auditor · model-assumptions-builder · symbol-table-builder · problem-parser-pre · workflow-orchestrator · related-paper-analyzer
