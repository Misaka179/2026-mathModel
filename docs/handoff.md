# Handoff

三人交接协议。核心：**标准化中间产物交接，不做「微信发文件」**。

## 交接总览

| 步骤 | 交接物 | 提交人 → 接收人 | 接收方动作 |
|---|---|---|---|
| 1. 模型冻结 | `02_model/model_decision.md` + `model_spec.md` | A → B | `git pull`，核对 spec |
| 2. 结果验证 | `05_results/verified_results.md` + `06_figures/figure_plan.md` | B → C | `git pull`，核对数字 |
| 3. 论文完成 | `07_paper/paper_v1` + `paper_review.md` | C → 全队 | 全队复核 |

每次交接的约定动作：

```
git add .
git commit -m "Q1: freeze model"
git push
```

群里只发一句：**「Q1 模型已冻结，B 可开始接手。commit: xxxxx」**，接收方 `git pull` 后开工。

## 目录权限表（避免冲突）

| 目录 | 负责人 |
|---|---|
| `prompts/A_model/`、`questions/Qx/01_problem/`、`02_model/` | A |
| `prompts/B_data/`、`questions/Qx/03_data/`、`04_code/`、`05_results/`、`06_figures/` | B |
| `prompts/C_paper/`、`questions/Qx/07_paper/` | C |
| `templates/`、`docs/`、`config/`、`README.md`、`RULES.md`、`final/` | 三人共同 |

**原则上每个人只改自己负责的目录。** 交叉改动前先沟通，避免 merge 冲突。

## 交接质量门槛

- A 交给 B 的 `model_spec.md`：变量/目标/约束/假设完整，经人冻结。
- B 交给 C 的 `verified_results.md`：每个数字有来源、经人确认冻结。
- C 交给全队的论文：数字全部可溯源至 `verified_results.md`。

## 状态同步

每完成一项，更新 `questions/Qx/STATUS.md` 勾选 + `config/competition_status.yaml` 对应字段，随交接 commit 一起推。
