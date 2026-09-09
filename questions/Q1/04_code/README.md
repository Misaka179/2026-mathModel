# Q1 代码说明

> 负责人：B（周小婷）  
> 基于：questions/Q1/02_model/model_spec.md  
> 日期：2026-09-09  
> 状态：环境配置中

## 代码文件清单

### 主要分析脚本

| 文件 | 说明 | 状态 |
|------|------|------|
| `q1_analysis_complete.py` | 完整分析脚本：阶段0-3（环境、BMI检查、模型拟合） | ✅ 完成 |
| `q1_analysis_integrated.py` | 诊断分析：阶段4（残差检查、Q-Q图、边界检查） | ✅ 完成 |
| `robustness_checks.py` | 稳健性检验：Bootstrap 1000次 + 敏感性分析 | ✅ 完成 |
| `verify_simpson.py` | Simpson悖论验证：定量证据 + 4张验证图 | ✅ 完成 |
| `verify_chorus_issues.py` | Chorus审查问题验证 | ✅ 完成 |
| `generate_fig1_2.py` | 生成Fig.1.2（Within vs Between对比图） | ✅ 完成 |

### 早期版本（已弃用）

| 文件 | 说明 | 状态 |
|------|------|------|
| `q1_analysis_part1.py` | 早期脚本（已整合到complete版本） | ⚠️ 已弃用 |
| `q1_analysis_part1.R` | R版本（已改用Python） | ⚠️ 已弃用 |
| `q1_part1_simple.py` | 简化版本（已整合） | ⚠️ 已弃用 |
| `q1_analysis_part2_diagnostics.py` | 早期诊断脚本（已整合到integrated版本） | ⚠️ 已弃用 |

## 执行顺序

### 方案A：R语言（原始设计）
```bash
# 需要安装R环境和以下包：
# lme4, lmerTest, sandwich, geepack, boot, ggplot2, dplyr, tidyr

Rscript q1_analysis_part1.R
Rscript q1_analysis_part2.R
Rscript q1_analysis_part3.R
Rscript q1_analysis_part4.R
```

### 方案B：Python实现（当前环境）
```bash
# 需要安装Python包：
pip install pandas numpy scipy statsmodels matplotlib seaborn

python q1_analysis_part1.py  # 环境准备、BMI检查、变量转换
python q1_analysis_part2.py  # 三模型拟合、诊断
python q1_analysis_part3.py  # 检验、敏感性分析
python q1_analysis_part4.py  # 生成结果表
```

## 模型规格（MODEL FROZEN）

### 主模型：M2线性混合效应模型

**公式（情况A）**：
```
Y_ij = β₀ + β₁^W * week_within_ij + β₂^B * week_between_i + β₃^B * BMI_i + u_i + ε_ij
```

- `u_i ~ N(0, σ²_u)`: 随机截距
- `ε_ij ~ N(0, σ²_e)`: 个体内残差

### 对照模型

- **M1**: 聚类稳健OLS
- **GEE**: 可交换相关

### 探索性扩展

- **M3**: 交互项（week_within × BMI）

## 关键检查点（停止条件）

执行过程中，遇到以下情况必须停止并联系A（宋禹萱）：

1. ⚠️ BMI有>10%孕妇时间变异
2. ⚠️ M1/M2/GEE系数符号不一致
3. ⚠️ M2不收敛（迭代>1000次）
4. ⚠️ 残差严重非正态且越界>15%
5. ⚠️ Within和Between效应符号相反

## 输入数据

- `questions/Q1/03_data/q1_male_data_cleaned.csv`（1082行×12列）

## 输出文件

### 数据
- `questions/Q1/03_data/q1_data_transformed.csv` - 变换后数据

### 结果
- `questions/Q1/05_results/q1_main_results_table.csv` - 主结果表
- `questions/Q1/05_results/q1_effect_interpretation.txt` - 效应解释
- `questions/Q1/05_results/metrics.md` - 模型评价指标
- `questions/Q1/05_results/run_summary.md` - 运行记录
- `questions/Q1/05_results/result_audit.md` - 结果审计
- `questions/Q1/05_results/verified_results.md` - 验证结果（人类签字）

### 图表
- `questions/Q1/06_figures/m2_resid_vs_fitted.png` - 残差vs拟合值
- `questions/Q1/06_figures/m2_resid_vs_week.png` - 残差vs孕周
- `questions/Q1/06_figures/m2_resid_vs_bmi.png` - 残差vs BMI
- `questions/Q1/06_figures/m2_qq_residuals.png` - 残差Q-Q图
- `questions/Q1/06_figures/m2_qq_ranef.png` - 随机效应Q-Q图

## 当前状态

- ✅ Part 1代码已创建（Python和R版本）
- ⏳ 等待Python环境配置完成（scipy, statsmodels, matplotlib安装中）
- ⏳ Part 2-4代码待创建
- ⏳ 模型拟合待执行

## 依赖关系

- 所有代码基于A角色交付的 `model_spec.md`（MODEL FROZEN）
- 不得修改模型结构
- 所有结果必须可追溯至清洗数据

## 注意事项

1. **不得修改A冻结的模型**（Rule 12）
2. **遇到停止条件立即停止**（Rule 17）
3. **所有结果必须可追溯**（Rule 14）
4. **人类决策门禁必须等待确认**（G4、G4.5）
