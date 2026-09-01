# Prompt Name: Paper Polisher

## Purpose
在论文内容定稿后做语言与排版润色：语法/公式一致性、过度声明收敛、去 AI 味、排版检查。

## Input
- 定稿论文
- （可选）官方模板

## Output
- 润色后的论文
- 润色记录（改动点清单）

## MUST
- 保持语义拓扑不变，只改表达
- 调用 `humanizer-zh` 处理 AI 味
- 排版符合官方模板（若有）

## MUST NOT
- 不得改动数字、结论、引用内容（只改表达）
- 不得改变章节结构

## Human Decision Gate
涉及「降低/删除某个论断」时须人工确认。

## Validation
- 数字/结论与润色前一致
- 无模式化表达残留
- 排版检查通过

## Output Path
`questions/Qx/07_paper/`
