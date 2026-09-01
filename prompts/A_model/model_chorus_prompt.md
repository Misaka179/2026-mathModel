# Prompt Name: Model Chorus Review Driver

## Purpose
在候选模型产出后，调用 Chorus 多模型评审，收集数学/数据/算法三方审查意见，输出冲突问题汇总供人工裁决。

## Input
- `02_model/model_candidates.md`
- Chorus 模板：`chorus/templates/q1-model-review.yaml`（候选评审）与 `mam-model-review.yaml`（三方审查）
- 评审时调取 `skills/math-modeling-v2/` 下建模手/编程手相关 skill 的参考资料

## Output
- Chorus 评审记录（保存于 `02_model/` 下）
- 冲突问题汇总（供 `model_decision.md` 使用）

## MUST
- 评审完成后保留全部模型评审资料
- 把冲突点按「数学建模 / 数据 / 算法」三方归类，供人裁决
- 遵循 Chorus 模板的 `require: 3` / `crossLineage` 配置

## MUST NOT
- 不得把 Chorus 意见当作最终决定
- 不得省略任一审查员的意见

## Human Decision Gate
冲突问题的裁决由人拍板，写入 `model_decision.md`。

## Validation
- 三方审查意见齐全
- 冲突点已归类且可追溯

## Output Path
`questions/Qx/02_model/`（评审记录与汇总）
