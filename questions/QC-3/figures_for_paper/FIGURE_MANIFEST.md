# Q3 论文图表清单

**生成时间**: 2026-09-13 04:57:54
**输出目录**: E:\数模资料\2026国赛准备\2026-mathModel\questions\QC-3\figures_for_paper
**总图数**: 9张（原始数据图3张 + 过程图3张 + 结果图3张）
**图型种类**: 5种（折线图、直方图、箱线图、条形图、饼图、散点图）

## 原始数据图（raw_q3_*）

1. **raw_q3_price** - 典型日电价曲线（折线图）
   - 用途：展示电价时段特征
   - 格式：PNG (300 DPI) + SVG

2. **raw_q3_curtailment_dist** - 弃光率分布直方图
   - 用途：展示全年弃光率分布特征
   - 关键数据：均值11.51%，>5%占66.8%
   - 格式：PNG (300 DPI) + SVG

3. **raw_q3_soc_boxplot** - SOC范围箱线图（按月）
   - 用途：展示不同月份SOC分布差异
   - 格式：PNG (300 DPI) + SVG

## 过程图（process_q3_*）

4. **process_q3_soc_trajectory** - 全年SOC轨迹（折线图）
   - 用途：展示储能运行全过程
   - 关键特征：从6000 kWh降至4002 kWh
   - 格式：PNG (300 DPI) + SVG

5. **process_q3_adjustment_stats** - Stage K调整触发统计（条形图）
   - 用途：展示调整策略触发频率
   - 关键数据：41.0%天数触发调整
   - 格式：PNG (300 DPI) + SVG

6. **process_q3_energy_balance** - 能量平衡流程图（条形图）
   - 用途：验证能量守恒
   - 关键数据：误差=0.000000 kWh
   - 格式：PNG (300 DPI) + SVG

## 结果图（result_q3_*）

7. **result_q3_cost_breakdown** - 全年总成本分解（饼图）
   - 用途：展示成本构成
   - 关键数据：总成本16,489,545元
   - 格式：PNG (300 DPI) + SVG

8. **result_q3_monthly_comparison** - 月度成本与购电量对比（双层条形图）
   - 用途：展示月度成本和购电量变化趋势
   - 格式：PNG (300 DPI) + SVG

9. **result_q3_curtail_soc_corr** - 弃光-SOC相关性（散点图+趋势线）
   - 用途：探索弃光与储能状态的关系
   - 格式：PNG (300 DPI) + SVG

## 使用说明

1. 所有图表均为色盲友好配色
2. PNG格式用于Word论文，SVG格式用于LaTeX论文
3. 图表命名符合math-modeling skill规范（raw/process/result前缀）
4. 每张图均可独立使用，也可组合为多面板图

## 数据来源

- diagnostic_334days.xlsx：334天完整诊断数据
- curtailment_analysis.xlsx：弃光分析数据
- verified_results.md：所有数值可溯源

---

**状态**: ✅ 已生成并验证
**符合规范**: math-modeling skill 图表要求
