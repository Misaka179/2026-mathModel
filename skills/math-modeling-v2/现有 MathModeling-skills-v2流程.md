现有 MathModeling-skills-v2流程

![image-20260823234148568](C:\Users\Song\AppData\Roaming\Typora\typora-user-images\image-20260823234148568.png)

| 阶段              | 调用的现有 skill                                             | skill 负责                                                   |
| ----------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| G1 问题解析       | `problem-parser`                                             | 题面→结构化任务说明                                          |
| G1.5 分类         | `problem-classifier`                                         | 子问题→问题类型映射                                          |
| G2 文献/方法池    | `related-paper-analyzer` → `method-selector`                 | 读 `workspace/papers/` → 方法线索；生成 2~4 候选 + 执行优先级 |
| G2.5 **方法决策** | `decision-prompt-builder` → `modeler-decision-logger`        | 生成"只有人能回答"的问题并拒绝作答；盖章归档                 |
| G3 数据           | `data-auditor-cleaner`                                       | 原始数据只读→审计+清洗+画像+cleaned copy                     |
| G3.5 代码         | `model-code-analyzer` → `python/matlab-model-code-generator` → `code-reviewer` | 代码计划→生成可运行代码→按语言审查                           |
| G4 **结果判定**   | `result-report-generator` → `robustness-checker`             | 实验→比较报告 + `[AI-SUGGESTED]`；扰动/敏感性计算 + ai_suggestion |
| G4.5 图           | `figure-table-planner` → `math-figure-generator`             | 规划图/表分类；渲染出版级图                                  |
| G5 方法说明       | `final-method-explainer` → `solution-package-builder`        | 转录人工决策→最终方法说明；整合 writer 方案包                |
| G5.5 论文草稿     | `paper-section-writer`                                       | 仅从已验证工件写分节                                         |
| G6 **论文判定**   | `paper-polisher` + `humanizer-zh` + `reference-manager`      | 润色语法/公式/过度声明；去 AI 味；引用校验                   |
| G6.5 冻结         | `consistency-auditor` → `completeness-auditor` → `quality-assurance-auditor` | 跨媒体一致性、审计文件存在、全链 QA                          |