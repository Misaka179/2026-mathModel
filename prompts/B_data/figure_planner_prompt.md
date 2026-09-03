# Prompt Name: Figure Planner

## Purpose
G4.5 图表规划阶段：规划所有图表的用途、类型、数据源，确保每张进正文的图都有明确的论证目标（core_claim）。基于 `figure-table-planner` + `math-figure-generator` skill 的输出做「用途审核 + core_claim 起草」，不重复其渲染工作。

## Input
- `05_results/verified_results.md`（B 已签字的验证结果，图表数据的唯一来源）
- `05_results/result_audit.md`（结果审计结论）
- `03_data/data_audit.md`（数据特征与分布）
- `02_model/model_decision.md` + `02_model/model_spec.md`（模型逻辑）
- `01_problem/problem_definition.md`（子问题与论证需求）

## Output
- `06_figures/figure_plan.md`（按 `templates/figure_plan.md`）
- `06_figures/figures/` + `06_figures/tables/` 成品图与表

## MUST
- 先调 `figure-table-planner` → `math-figure-generator`，再在其输出上审核用途
- 每张 Type 3 论文图起草 core_claim，含 4 层论证（事实 / 观察 / 结论 / 定位）
- 每张图的数据源必须在 `verified_results.md` 中可追溯（Rule 6）
- 检查误导性：Y 轴是否从 0 起、配色是否暗示价值、双 Y 轴是否已标注独立

## MUST NOT
- 不得重复 `figure-table-planner` / `math-figure-generator` 的渲染
- 不得规划「无目的的美化图」（Rule 7：所有最终图必须有明确用途）
- 不得使用未经 `verified_results.md` 签字的数据
- 不得将诊断图（残差/QQ/ACF）放入正文，除非直接支撑某论点
- 不得把相关性画成因果关系（Rule 5）

## 图表分类

| 类型 | 用途 | 是否进正文 |
|---|---|---|
| Type 1 诊断图 | 验证模型假设 / 数据质量（残差、QQ、ACF、缺失热图） | ❌ 否（放附录） |
| Type 2 对比图 | 模型性能 / 方案比较（收敛曲线、train-test 对比、敏感性） | 🟡 视情况（关键对比进正文） |
| Type 3 论文图 | 直接支撑论文核心论点 | ✅ 是 |
| Type 4 附录图 | 补充信息 / 详细数据 | ❌ 否（仅附录） |

## Human Decision Gate
core_claim 的分工：**AI 起草** core_claim（事实/观察/结论/定位四层），**人（B，周小婷）逐条确认并签字**后才算数。AI 不得替人盖章；人未确认的 core_claim 不得进入正文。

以下情形**必须停下交人拍板**：
- 论证链缺关键图（核心论点无图支撑）；core_claim 与 result_audit 结论冲突
- 某张图的数据不在 `verified_results.md` 签字范围内
- 误导性检查发现风险（如 Y 轴截断）但去除后视觉效果变差

## Chorus
关键规划决策（图进正文还是附录 / core_claim 是否够撑论点 / 配色是否误导）用 B 的 `figure-review` 模板做多模型复核；平票交人裁决。意见仅作辅助，最终归人。

## Validation
- 每张图有明确用途，Type 3 图都有 core_claim（人已签字）
- 每张图数据源可追溯至 `verified_results.md`
- 误导性检查（Y 轴/配色/双 Y 轴/饼图/3D）通过
- 渲染通过（SVG + 300 DPI PNG）

## Output Path
`questions/Qx/06_figures/figure_plan.md`
