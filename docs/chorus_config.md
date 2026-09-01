# Chorus Config

多模型评审配置说明。模板位于 `chorus/templates/`。

## 已有模板

| 模板 | 用途 | 配置 |
|---|---|---|
| `q1-model-review.yaml` | 建模早期对候选方案的评审（题目分析报告/建模方案） | — |
| `mam-model-review.yaml` | 模型方案三方审查（数学建模 / 数据 / 求解算法） | `require: 3`，`crossLineage: true`（anthropic + openai + opencode 三家） |
| `mam-paper-review.yaml` | 论文评审 | — |

## 典型调用时机（来自 A 建模决策 prompt）

1. **候选评审**：生成 `model_candidates.md` 后，用 `q1-model-review.yaml` 评审全部候选方案；保存所有评审资料。
2. **三方审查**：选定最终模型后，用 `mam-model-review.yaml` 做三方审核。三方检查分工：
   - 数学建模审查员：变量 / 目标 / 约束 / 数学逻辑 / 假设 / 模型类型
   - 数据审查员：数据是否支持 / 质量 / 参数来源 / 分布假设 / 数据泄漏 / 处理
   - 算法审查员：LP/MILP/NLP / 求解器 / GA / 收敛 / 复杂度 / 参数 / 可复现性
3. **论文评审**：论文成稿后用 `mam-paper-review.yaml`。

## 与 skill 的配合

评审时调取 `skills/math-modeling-v2/` 下对应角色 skill 的参考资料（建模手/编程手角色目录），作为审查员的背景知识。

## 关键点

- Chorus 意见是**辅助**，最终裁决归人（Human Decision Gate）。
- 冲突点必须归类汇总进 `model_decision.md`，不能跳过。
