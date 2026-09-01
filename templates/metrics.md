# Metrics 模板

> 用途：B 编程手汇总模型评价指标，供结果对比与论文引用。
> 负责人：B | 输出：`05_results/metrics.md`

## 指标说明

| 内容 | 示例 |
|---|---|
| 指标名称 | RMSE / MAE / R² / Accuracy 等 |
| 指标定义 | 数学公式 |
| 指标结果 | 最终数值 |
| Benchmark | baseline 结果 |
| 比较对象 | 不同模型/不同方案 |
| 结果解释 | 这个数值意味着什么 |
| 是否达标 | 是否满足预期 |

## 各方案指标汇总

| 方案 | RMSE | MAE | R² | 其他 | Benchmark | 是否达标 |
|---|---|---|---|---|---|---|
| Model A | 2.31 | 1.82 | 0.91 | | baseline | ✅ |
| Model B | | | | | | |

## 结论

<!-- 最终采用哪个方案及理由 -->

## 验收

- [ ] 每个指标有定义、结果与解释
- [ ] 有 baseline / 比较对象
- [ ] 与 `result_audit.md`、`verified_results.md` 一致
