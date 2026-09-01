# Prompt Name: Model Candidate Generator

## Purpose
在 G2 文献/方法池阶段，为当前小问生成 2~4 个候选模型方案与执行优先级建议，供 Chorus 评审与人工决策使用。基于 `related-paper-analyzer` 的方法线索，不直接做最终选择。

## Input
- `01_problem/problem_definition.md`
- `related-paper-analyzer` 的输出（方法线索）
- （可选）已有 `model_candidates.md`（迭代时）

## Output
- `02_model/model_candidates.md`（按 `templates/model_candidates.md`）

## MUST
- 每个候选必须填满 15 项信息（方案名称…主要风险）
- 覆盖 `related-paper-analyzer` 的关键方法线索
- 给出执行优先级与理由

## MUST NOT
- 不得直接选定唯一模型（最终选择属 Human Decision Gate）
- 不得跳题/只给方案名不给细节

## Human Decision Gate
最终模型选择由人决定，本 Prompt 只产出候选池。

## Validation
- 候选数 ∈ [2, 4]
- 每候选 15 项完整
- 已存为 `model_candidates.md`

## Output Path
`questions/Qx/02_model/model_candidates.md`
