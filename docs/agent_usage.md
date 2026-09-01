# Agent Usage

给 A/B/C 三人各自的启动指引。原则：**各人独立 Claude Code 环境，互不覆盖**。

## 通用启动步骤

```bash
git clone <your-remote>
# 只装一次
.\skills\install.ps1        # Windows
bash skills/install.sh      # macOS/Linux
```

每道题开工时：

```bash
cd questions/Qx/
```

打开对应角色的 prompt，让 Claude Code 加载，再调对应 skill。

## A — 建模手

- **加载 prompt**：`prompts/A_model/`（`model_decision_prompt.md` 是主入口，内含完整推进流程）
- **主要 skill**：`problem-parser` → `problem-classifier` → `related-paper-analyzer` → `method-selector` → `decision-prompt-builder` → `modeler-decision-logger`
- **产出**：`01_problem/`、`02_model/`
- **注意**：G2.5 方法决策是人工门禁，模型冻结后不许再换。

## B — 编程手

- **加载 prompt**：`prompts/B_data/`（data_audit / result_audit / figure_planner 三份按阶段取用）
- **主要 skill**：`data-auditor-cleaner` → `model-code-analyzer` → `python/matlab-model-code-generator` → `code-reviewer` → `result-report-generator` → `robustness-checker` → `figure-table-planner` → `math-figure-generator`
- **产出**：`03_data/`、`04_code/`、`05_results/`、`06_figures/`
- **注意**：不得修改 A 冻结的模型（Rule 12）。

## C — 论文手

- **加载 prompt**：`prompts/C_paper/`（writer / review / polish 三份按阶段取用；`_extra/` 内有零散 skill/prompt 素材）
- **主要 skill**：`final-method-explainer` → `solution-package-builder` → `paper-section-writer` → `paper-polisher` + `humanizer-zh` + `reference-manager`
- **产出**：`07_paper/`
- **注意**：论文数字必须来自 `verified_results.md`（Rule 14），不得改结果文件（Rule 13）。

## 状态与交接

- 每完成一项：更新 `questions/Qx/STATUS.md` + `config/competition_status.yaml`，commit + push，群里报 commit 号。
- 不确定时 STOP 拉人（Rule 17）。
