# Final QA 模板

> 用途：终稿提交前的最后质检（对应 G6.5 三个审计 skill）。
> 负责人：三人共同 | 输出：`07_paper/final_QA.md`

## 1. 一致性审计（`consistency-auditor`）

- [ ] 跨媒体数字一致（正文 = 表格 = 图 = 结果文件）
- [ ] 符号 / 参数全局一致
- [ ] 文件路径引用有效

## 2. 完整性审计（`completeness-auditor`）

- [ ] 所有小问覆盖
- [ ] 每个结论有实质性工件支撑
- [ ] 无遗留 `TODO` / `待补充` / 占位符

## 3. 全链 QA（`quality-assurance-auditor`）

- [ ] 三条关键规则通过（方法说明/结果分析/材料包齐全）
- [ ] 无捏造数据 / 结果
- [ ] 提交包完整（论文 PDF + 源码 + 复现清单）

## 验收

- [ ] 三个审计全部 PASS（Gate G6）
- [ ] 结果写入 `final/submission/`
