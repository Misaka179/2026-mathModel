# Chorus Config

多模型评审配置说明。模板按角色分目录存放：`chorus/templates/A/`（建模）、`B/`（编程）、`C/`（论文）。模板和 persona 在 chorus 的网页控制台里注册，注册后自动生效。

## 怎么注册模板 / persona（网页操作）

1. 确认 chorus 在跑：命令行敲 `chorus start`（或 `chorus status` 看是否已在运行）。
2. 浏览器打开 `http://127.0.0.1:5050`。
3. 注册模板：进 **Templates** 页，新建模板，把仓库里对应 YAML（如 `chorus/templates/B/result-review.yaml`）的内容整段粘贴进去，保存。
4. 注册 persona：进 **Personas** 页，为模板里引用的每个审查员各建一个，**id 要和模板 YAML 里写的 persona 名字完全一致**（如 `b-result-correctness-reviewer`），再填名称、一句话说明、系统提示词。

## 已有模板

| 模板 | 位置 | 用途 | 配置 |
|---|---|---|---|
| `q1-model-review.yaml` | A/ | 建模早期对候选方案的评审（题目分析报告/建模方案） | — |
| `mam-model-review.yaml` | A/ | 模型方案三方审查（数学建模 / 数据 / 求解算法） | `require: 3`，`crossLineage: true`（anthropic + openai + opencode 三家） |
| `mam-paper-review.yaml` | A/ | 论文评审 | — |
| `result-review.yaml` | B/ | 结果审计多模型复核（数学正确性/方法论/业务合理性） | `require: 3`，`crossLineage: true` |
| `figure-review.yaml` | B/ | 图表规划多模型复核（core_claim/归属/误导性） | `require: 3`，`crossLineage: true` |
| `data-review.yaml` | B/ | 数据审计多模型复核（缺失/异常/重复处理，数据变换/共线性/泄漏，模型假设匹配/参数可估计性）| `require: 3`，`crossLineage: true` |

## 典型调用时机

1. **候选评审**：生成 `model_candidates.md` 后，用 `q1-model-review.yaml` 评审全部候选方案；保存所有评审资料。

2. **三方审查**：选定最终模型后，用 `mam-model-review.yaml` 做三方审核。三方检查分工：
   - 数学建模审查员：变量 / 目标 / 约束 / 数学逻辑 / 假设 / 模型类型
   - 数据审查员：数据是否支持 / 质量 / 参数来源 / 分布假设 / 数据泄漏 / 处理
   - 算法审查员：LP/MILP/NLP / 求解器 / GA / 收敛 / 复杂度 / 参数 / 可复现性
3. **论文评审**：论文成稿后用 `mam-paper-review.yaml`。
4. **数据审计复核**：生成 `data_audit.md` 后，用 `data-review.yaml` 做三方复核。三位审查员分工：
   - 缺失/异常/重复审查员（`b-data-missing-reviewer`）：缺失值、异常值、重复值的识别与处理是否合理
   - 变换/共线性/泄漏审查员（`b-data-transform-reviewer`）：数据变换、共线性、数据泄漏
   - 假设匹配审查员（`b-data-assumption-reviewer`）：模型假设匹配、参数可估计性

## 与 skill 的配合

评审时调取 `skills/math-modeling-v2/` 下对应角色 skill 的参考资料（建模手/编程手角色目录），作为审查员的背景知识。

## 关键点

- Chorus 意见是**辅助**，最终裁决归人（Human Decision Gate）。
- 冲突点必须归类汇总进 `model_decision.md`，不能跳过。
