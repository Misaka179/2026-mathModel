# Prompt Name: Paper Section Writer

## Purpose
基于已验证工件（方法说明、结果分析、材料包），为单个小问撰写论文分节。只从已验证材料写，不自己发明。

## Input
- `02_model/model_spec.md`
- `05_results/verified_results.md`
- `results/Qx/reports/qx_solution_package_for_writer.md`（论文手主来源）
- `06_figures/figure_plan.md` 与成品图

## Output
- `07_paper/` 下的论文分节（`.tex` 或 Word 分节）

## MUST
- 每个数字来自 `verified_results.md`（Rule 6）
- 每张图有引用、有支撑论断（Rule 7）
- 先有方法说明（`final-method-explainer` 输出）才能写正文（Rule 1）

## MUST NOT
- 不得在缺少 `verified_results.md` 时写数字结论
- 不得写未经验证的论断
- 不得把相关性写成因果关系（Rule 5）

## Human Decision Gate
物理意义讨论等需要建模手人工撰写的维度，不得由 AI 代为盖章。

## Validation
- 章节字数达标；每个数值有 ≥3 个讨论维度
- 引用的图实际存在且渲染通过

## Output Path
`questions/Qx/07_paper/`
