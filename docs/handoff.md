# Handoff

三人交接协议（依据 `E:\训练计划\比赛流程.md`）。核心：**标准化中间产物交接，不做「微信发文件」**。交接文件是「人与人之间的接口」。

## 团队分工

| 角色 | 人 | 核心职责 |
|---|---|---|
| **A — 建模手** | 宋禹萱 | 问题解析 + 模型选择 + 初步数据分析 + 模型审查 |
| **B — 编程手** | 周小婷 | 深度数据处理 + 求解执行 + 结果验证 + 图表 |
| **C — 论文手** | 江宇巍 | 论文框架 + 初稿 + 论文审查 + 语言排版 |

> 如果具体执行过程中哪个环节很需要帮忙，由 A 进行游走支援。

## 交接总览

```
A：   Q1模型 ─────── Q2模型 ─────── Q3模型
             ↓                                  ↓
B：   Q1数据/求解 ───── Q2数据/求解 ───── Q3数据/求解
             ↓                                  ↓
C：   Q1论文 ──────── Q2论文 ────────── Q3论文
```

通过交接文件完成职责过渡。**每个交接文件必须有明确负责人**，内容规范见 `templates/` 对应模板。

### A → B/C：模型交接文件

| 文件 | 交接给 | 说明 |
|---|---|---|
| `problem_definition.md` | B、C | 问题定义（模板见 `templates/problem_definition.md`） |
| `A_data_profile.md` | B | 建模前数据概况（`templates/A_data_profile.md`） |
| `model_candidates.md` | Chorus / A 自己 | 2~4 候选方案 |
| `model_review.md` | A 自己 | 模型审查报告 |
| `model_decision.md` | B、C | 人类最终模型决策，末尾标 **MODEL FROZEN** |
| `model_spec.md` | B | 冻结模型规格，含「禁止修改的部分」 |

**A 冻结后 B 如需更改模型，必须返工给 A，而不是自己改。**

### B → C：结果交接文件

| 文件 | 交接给 | 说明 |
|---|---|---|
| `data_audit.md` | C | 数据审查与处理报告，保证 原始→清洗→最终数据 可追溯 |
| `cleaned_data/` | — | 清洗后数据 |
| `run_summary.md` | — | 模型运行记录（模型/数据/代码版本 + 参数/seed/是否收敛） |
| `results/` | — | 原始结果文件（raw_results.csv / predictions.csv / parameters.csv / sensitivity.csv…） |
| `metrics.md` | — | 模型评价指标 |
| `result_audit.md` | A、C | 结果找茬报告 |
| `verified_results.md` | C | 已验证结果，论文写作的根据 |
| `figure_plan.md` | C | 图表规划（每张图含 Core Claim） |
| `figures/` + `tables/` | C | 成品图与表 |

> C 原则上不修改数据内容，可对图调整尺寸/位置/排版；发现图数据有问题返回 B。

### C → 全队：论文交接文件

| 文件 | 说明 |
|---|---|
| `paper_v1.pdf` | 第一版完整论文 |
| `paper_review.md` | 论文内容检查（模型/数字/图文/逻辑/因果/假设/符号/单位/结构/表达/引用） |
| `paper_polished.pdf` | 语言排版版（中文表达/去AI味/公式图表排版/编号引用） |
| `final_paper.pdf` | 最终提交版 |

> 语言润色不得改变模型、数字、实验结果和结论含义。

## 交接操作

每次交接的约定动作：

```
git add .
git commit -m "Q1: freeze model"
git push
```

群里只发一句：**「Q1 模型已冻结，B 可开始接手。commit: xxxxx」**，接收方 `git pull` 后开工。

## 目录权限表（避免冲突）

| 目录 | 负责人 |
|---|---|
| `prompts/A_model/`、`questions/Qx/01_problem/`、`02_model/` | A（宋禹萱） |
| `prompts/B_data/`、`questions/Qx/03_data/`、`04_code/`、`05_results/`、`06_figures/` | B（周小婷） |
| `prompts/C_paper/`、`questions/Qx/07_paper/` | C（江宇巍） |
| `templates/`、`docs/`、`config/`、`README.md`、`RULES.md`、`final/` | 三人共同 |

**原则上每个人只改自己负责的目录。** 交叉改动前先沟通，避免 merge 冲突。

## 时间线（暂定，根据实际情况调整）

| 时间 | 阶段 | 核心负责人 |
|---|---|---|
| 9.10 18:00–22:00 | 全队读题 + 数据摸底 | A+B |
| 9.10 22:00–9.11 02:00 | 模型候选 + 决策 | **A** |
| 9.11 10:00–14:00 | 第一批模型求解 | **B** |
| 9.11 10:00 以后 | Q2/Q3 模型推进 | **A** |
| 9.11 14:00 以后 | 第一问论文同步 | **C** |
| 9.11–9.12 | 模型/求解/论文流水线 | 三人并行 |
| 9.12 18:00 | 完成所有模型求解结果并不再更改大方向 | 全队 |
| 9.13 10:00 前 | 完整论文 V1 | C 主导 |
| 9.13 10:00–12:00 | 三人核对论文内容 | 全队 |
| 9.13 12:00–17:00 | 最终排版、图像格式调整、语言调整 | C 主导，全队参与 |
| 9.13 12:00–17:00 | Final QA + 附录与其他材料整理 | A+B+C |
| 9.13 17:00–18:30 | 最终检查 | 全队 |
| 9.13 18:30–19:30 | 提交准备 | 全队 |
| 19:30 前 | **完成提交** | 全队 |

## 交接质量门槛

- A 交给 B 的 `model_spec.md`：含「禁止修改的部分」，经人冻结（MODEL FROZEN）。
- B 交给 C 的 `verified_results.md`：每个数字有来源、经人确认冻结。
- C 交给全队的论文：数字全部可溯源至 `verified_results.md`。

## 状态同步

每完成一项，更新 `questions/Qx/STATUS.md` 勾选 + `config/competition_status.yaml` 对应字段，随交接 commit 一起推。
