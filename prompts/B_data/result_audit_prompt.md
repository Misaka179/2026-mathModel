# Prompt Name: Result Audit

## Purpose
G4 结果判定阶段：对模型求解结果做全面异常扫描与合理性验证，给出「结果是否可接受」的最终判定并签字。基于 `result-report-generator` + `robustness-checker` skill 的输出做深度找茬，不重复其计算。

## Input
- `02_model/model_decision.md` + `02_model/model_spec.md`（A 冻结模型与预期性能）
- `04_code/` 求解脚本、`04_code/run_summary.md`（运行记录：参数/seed/是否收敛）
- `05_results/` 结果文件（csv/json）、`05_results/metrics.md`
- `03_data/data_audit.md`（数据特征与限制）

## Output
- `05_results/result_audit.md`（按 `templates/result_audit.md`）
- 签字后：`05_results/verified_results.md`（按 `templates/verified_results.md`，论文写作的唯一数字来源）

## MUST
- 先调 `result-report-generator` → `robustness-checker`，再在其输出上做「7 类异常」深度扫描
- 7 类异常逐项检查并给定量判定（倍数、残差、CV、提升率、train/test 差距），不用「基本合理」
- 每个 🔴 都明确「回退目标阶段」（G3.5 重求解 / G2.5 重新选模型）
- 结果文件仅读取，审计意见写独立文件；签字前核对结果文件哈希

## MUST NOT
- 不得重复 `result-report-generator` / `robustness-checker` 已算的指标
- 不得跳过任何一类异常扫描
- 不得在存在 🔴 严重异常时仍签字通过
- 不得修改 A 冻结的模型（Rule 12）；发现模型需改，返工给 A

## 7 类异常扫描清单

| # | 异常类型 | 核心问题 | 可接受阈值 |
|---|---|---|---|
| 1 | 数量级 | 结果相比输入/历史基线是否合理？ | <3 倍 |
| 2 | 约束违反 | 最优解是否满足所有硬约束？ | 残差 <1e-6 |
| 3 | 边界粘滞 | 是否大量变量贴上下界？ | <30% 贴边 |
| 4 | 稳定性 | 换 seed/初值后结果变化多大？ | CV <10% |
| 5 | 基准提升 | 相比简单基线提升是否值得复杂度？ | >5% |
| 6 | 过拟合 | train/test 差距是否异常？ | <15% |
| 7 | 业务合理性 | 数学最优但现实是否可行？ | 需人工判断 |

## Human Decision Gate
以下情形**必须停下交 A / 人拍板**（本阶段有一票否决权）：
- 任何硬约束违反 >1e-4；数量级异常 >10 倍；边界粘滞 >70%
- 稳定性 CV >30%；基准提升 <1%；业务合理性存疑（如「全种高收益作物」）

## Chorus
关键判定（边界粘滞可接受性 / 基准提升充分性 / 业务合理性存疑项）用 B 的 `result-review` 模板做多模型复核；平票交人裁决。意见仅作辅助，最终归人。

## Validation
- 7 类异常全查完，每项有定量指标
- 🔴 异常有明确处理动作（回退/修复）
- 判定「可接受」时已填写签字声明；「不可接受」时已写清回退阶段
- 结果文件哈希已写入可追溯附录

## Output Path
`questions/Qx/05_results/result_audit.md` → `questions/Qx/05_results/verified_results.md`
