# Prompt Name: Paper Reviewer

## Purpose
对论文初稿做系统性复核，检查模型一致性、数字溯源、图表支撑、语言质量与引用真实性，输出问题清单。

## Input
- 论文初稿（`07_paper/`）
- `02_model/model_spec.md`
- `05_results/verified_results.md`
- `06_figures/` 成品图

## Output
- `07_paper/paper_review.md`（按 `templates/paper_review.md`）

## MUST
- 逐项核对：模型描述与 spec 一致、数字可溯源、图表支撑
- 调用 `reference-manager` 校验引用真实
- 调用 `humanizer-zh` 去 AI 味

## MUST NOT
- 不得放过任何无法溯源的数字
- 不得自行修改结果文件（Rule 13）

## Human Decision Gate
发现的重大问题需交由对应负责人修复，不得静默放行。

## Validation
- 五个维度（模型/数字/图表/语言/引用）各有明确结论
- 问题清单可执行

## Output Path
`questions/Qx/07_paper/paper_review.md`
