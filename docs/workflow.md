# Workflow

团队整体流程基于 `math-modeling-v2` 的 G1–G6.5 阶段表。每问独立推进，不同小问可能处于不同阶段。

## 阶段总览

| 阶段 | 调用的 skill | 负责 | 门禁 |
|---|---|---|---|
| G1 问题解析 | `problem-parser` | 题面→结构化任务说明 | — |
| G1.5 分类 | `problem-classifier` | 子问题→问题类型映射 | — |
| G2 文献/方法池 | `related-paper-analyzer` → `method-selector` | 方法线索；2~4 候选+优先级 | — |
| G2.5 **方法决策** | `decision-prompt-builder` → `modeler-decision-logger` | 人回答「只有人能答的问题」并盖章 | ★ 人工门禁 |
| G3 数据 | `data-auditor-cleaner` | 只读→审计+清洗+画像+cleaned copy | — |
| G3.5 代码 | `model-code-analyzer` → `python/matlab-model-code-generator` → `code-reviewer` | 代码计划→可运行代码→审查 | — |
| G4 **结果判定** | `result-report-generator` → `robustness-checker` | 比较报告+`[AI-SUGGESTED]`；扰动/敏感性 | ★ 人工门禁 |
| G4.5 图 | `figure-table-planner` → `math-figure-generator` | 图/表规划；出版级渲染 | — |
| G5 方法说明 | `final-method-explainer` → `solution-package-builder` | 转录人工决策→方法说明；writer 材料包 | — |
| G5.5 论文草稿 | `paper-section-writer` | 仅从已验证工件写分节 | — |
| G6 **论文判定** | `paper-polisher` + `humanizer-zh` + `reference-manager` | 润色；去 AI 味；引用校验 | — |
| G6.5 冻结 | `consistency-auditor` → `completeness-auditor` → `quality-assurance-auditor` | 跨媒体一致性；文件存在；全链 QA | ★ 全部 PASS |

★ = Human Decision Gate，AI 不得绕过（见 `RULES.md`）。

## skill 输出 → 仓库编号目录映射

v2 skill 原生按 `planning/ methods/ code/ results/ robustness/ paper/ workspace/` 工作（各人本地 workspace）。交接进仓库时归档到编号目录：

| skill 原生输出 | 归档到（questions/Qx/） | 说明 |
|---|---|---|
| `planning/parse/`、`planning/classification/` | `01_problem/` | 问题定义 |
| `methods/Qx/`（候选/决策/方法说明） | `02_model/` | 模型 |
| `workspace/data/data_report.md` | `03_data/` | 数据审计 |
| `code/Qx/`（复现清单、运行记录） | `04_code/` | 代码 |
| `results/Qx/reports/qx_final_result_analysis.md`、`frozen_numbers.json` | `05_results/` | 结果 |
| `results/Qx/experiments/final/figures/`、`paper/figures/` | `06_figures/` | 图表 |
| `paper/sections/` | `07_paper/` | 论文 |

## 建议的每问推进顺序

```
问题 → 建模(G1→G2.5) → 数据(G3) → 代码(G3.5) → 实验/结果(G4) → 图(G4.5)
     → 方法说明+材料包(G5) → 论文(G5.5) → 判定(G6) → 冻结(G6.5)
```

依赖关系：建模在前、数据/计算居中、论文在后。Q1 未冻结前不建议开 Q2 的同阶段工作（若 Q2 依赖 Q1 结果）。
