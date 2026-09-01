# Math Modeling Team

2026 国赛备赛团队协作仓库。**Git 管共同的东西，Claude Code 管个人的工作，交接文件管人与人之间的接口。**

## 1. Team Workflow

| 角色 | 负责 | 主要 skill |
|---|---|---|
| A — 建模手 | 建模分析 / 方法决策 | `problem-parser`、`problem-classifier`、`method-selector`、`decision-prompt-builder`、`modeler-decision-logger` |
| B — 编程手 | 数据 / 计算 / 可视化 | `data-auditor-cleaner`、`model-code-analyzer`、`python/matlab-model-code-generator`、`code-reviewer`、`result-report-generator`、`figure-table-planner`、`math-figure-generator` |
| C — 论文手 | 论文撰写 / 校对 | `final-method-explainer`、`solution-package-builder`、`paper-section-writer`、`paper-polisher`、`humanizer-zh`、`reference-manager` |

## 2. AI Stack

- **Claude Code**（三人各自的本地 Agent 环境，互不共用 workspace）
- **MathModeling Skills**：见 `skills/`（31 个 v2 skill 已打包，含一键安装脚本）
- **Chorus** 多模型评审：模板见 `chorus/templates/`

## 3. Rules

见 [RULES.md](RULES.md)。核心三条：AI 不得绕过 Human Decision Gate；A 冻结模型后 B/C 不得修改；论文数字必须能追溯至 `results/`。

## 4. Workspace Structure

```
questions/Q1/
├── STATUS.md
├── 01_problem/    问题定义（A）
├── 02_model/      模型候选/决策/规格（A）
├── 03_data/       数据审计（B）
├── 04_code/       求解代码（B）
├── 05_results/    结果与验证（B）
├── 06_figures/    图表（B）
└── 07_paper/      论文（C）
```

skill 原生输出（`planning/`、`methods/`、`results/`…）如何归档进上述编号目录，见 `docs/workflow.md` 末尾的映射表。

## 5. Role Prompt

- A → `prompts/A_model/`
- B → `prompts/B_data/`
- C → `prompts/C_paper/`

## 6. Handoff

| 步骤 | 交接物 | 提交人 → 接收人 |
|---|---|---|
| A 完成模型 | `02_model/model_decision.md` + `model_spec.md` | A → B |
| B 完成求解 | `05_results/verified_results.md` + `06_figures/figure_plan.md` | B → C |
| C 完成论文 | `07_paper/paper_v1` | C → 全队 |

交接协议与目录权限见 `docs/handoff.md`。

## 7. How to Start

```bash
git clone <your-remote>
# 安装 v2 skills（Windows）
.\skills\install.ps1
# 或 macOS/Linux
bash skills/install.sh
```

然后：进入 `questions/Qx/`，加载对应 `prompts/<role>/` 的 prompt，调用对应 skill。详细步骤见 `docs/agent_usage.md`。

## 8. Status

- 人看：`questions/Qx/STATUS.md`
- 机器读：`config/competition_status.yaml`（Claude Code 可读取该状态）

## 9. Emergency

遇到以下情况立即 **STOP** 并拉人，不要硬做：

- 模型冲突 → STOP
- 结果异常 → STOP
- 论文数字找不到来源 → STOP
- 数据缺失严重 / 无法追溯 → STOP
