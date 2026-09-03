# RULES

本文件是团队 Agent 与人的共同行为边界。违反任一规则即停止执行，先拉人确认。

## 通用规则

1. AI 不得自行决定最终模型
2. AI 不得创造数据
3. AI 不得创造结果
4. AI 不得修改冻结模型
5. AI 不得将相关性写成因果关系
6. 所有论文数字必须来自结果文件
7. 所有最终图必须有明确用途
8. 所有重要 AI 判断必须经过人类确认
9. 发现模型冲突时必须停止执行
10. 所有关键决策必须记录，包括交互过程记录

## 团队协作规则

11. AI 不得绕过 Human Decision Gate（方法决策 G2.5、结果判定 G4 必须由人盖章）
12. B 不得修改 A 冻结模型
13. C 不得修改结果数据
14. 论文数字必须能够追溯至 results
15. 每次模型修改必须产生新的 decision 记录
16. 每个最终文件必须有明确负责人
17. 不确定时停止执行并请求人工判断
18. 临时实验不得直接进入 final

## 目录负责原则

每个人原则上只修改自己负责的目录，避免 Git 冲突：

| 目录 | 负责人 |
|---|---|
| `prompts/A_model/`、`questions/Qx/01_problem/`、`02_model/` | A |
| `prompts/B_data/`、`questions/Qx/03_data/`、`04_code/`、`05_results/`、`06_figures/` | B |
| `prompts/C_paper/`、`questions/Qx/07_paper/` | C |
| `templates/`、`docs/`、`config/`、`README.md`、`RULES.md`、`final/` | 三人共同 |

## 紧急 STOP 情形

- 模型冲突 / 结果异常 / 论文数字找不到来源 / 数据无法追溯
- 任何一位成员认为该停下时，先停再讨论。
