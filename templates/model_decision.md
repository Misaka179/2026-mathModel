# Model Decision 模板

> 用途：A 建模手在 Chorus 评审后的人工决策记录（Human Decision Gate G2.5）。
> 负责人：A（必须由人盖章，AI 不得代填） | 输出：`02_model/model_decision.md`

## 决策记录

- **决策编号**：`Qx-D0`（每次模型修改产生新编号）
- **决策日期**：
- **决策人**：
- **状态**：`DECIDED` / `PENDING`

## 选择结果

- **最终模型**：<方案名称>
- **理由**（必须引用具体证据/候选编号，不得抄 AI 建议）：
- **否决的备选**：<方案名>，理由：<…>

## Chorus 评审结论

<!-- 汇总 mam-model-review / q1-model-review 三方评审的冲突点与裁决 -->

## 决策后约束

- 从本决策起，随后的 agent 工作**不允许更换模型**。
- 如需修改，必须产生新的 `model_decision.md` 记录。

## 验收

- [ ] `decided_by: human`，理由有具体证据引用
- [ ] 否决备选的理由完整
