"""
Q1 数据分析脚本 - Part 1 (Python实现)
负责人：B（周小婷）
基于：questions/Q1/02_model/model_spec.md
日期：2026-09-09

本脚本执行model_spec.md的阶段0-2：
- 阶段0: 环境准备
- 阶段1: BMI前置检查（关键决策点）
- 阶段2: 创建within-between变量
"""

import pandas as pd
import numpy as np
import sys
import os

print("=" * 60)
print("Q1 数据分析 - 阶段0: 环境准备")
print("=" * 60)
print()

# 检查必需包
required_packages = ['pandas', 'numpy', 'scipy', 'statsmodels', 'matplotlib']
print("检查必需包...")
missing_packages = []
for pkg in required_packages:
    try:
        __import__(pkg)
        print(f"[OK] {pkg}")
    except ImportError:
        missing_packages.append(pkg)
        print(f"[MISSING] {pkg}")

if missing_packages:
    print(f"\n错误: 缺少以下包: {', '.join(missing_packages)}")
    print("请运行: pip install " + " ".join(missing_packages))
    sys.exit(1)

print("\n所有包已就绪!\n")

# ============================================================================
# 阶段0: 读取数据
# ============================================================================

print("读取清洗数据...")
data_path = "questions/Q1/03_data/q1_male_data_cleaned.csv"

if not os.path.exists(data_path):
    print(f"错误: 数据文件不存在: {data_path}")
    sys.exit(1)

data = pd.read_csv(data_path, encoding='utf-8')

print(f"数据加载成功: {len(data)} 行 × {len(data.columns)} 列\n")
print("数据结构:")
print(data.dtypes)
print("\n数据前5行:")
print(data.head())
print("\n数据摘要:")
print(data.describe())

# 确认关键字段存在
required_fields = ['woman_code', 'gestational_week', 'bmi', 'y_concentration']
missing_fields = [f for f in required_fields if f not in data.columns]
if missing_fields:
    print(f"\n错误: 缺少必需字段: {', '.join(missing_fields)}")
    sys.exit(1)

print("\n[OK] 所有必需字段已确认存在!\n")

# ============================================================================
# 阶段1: BMI前置检查（⚠️ 关键决策点）
# ============================================================================

print("=" * 60)
print("阶段1: BMI前置检查（关键决策点）")
print("=" * 60)
print()
print("目的：确认BMI是否随时间变化，决定使用情况A还是B\n")

# 检查BMI时间变异性
bmi_check_per_woman = data.groupby('woman_code')['bmi'].agg([
    ('n_obs', 'count'),
    ('bmi_mean', 'mean'),
    ('bmi_sd', 'std'),
    ('bmi_range', lambda x: x.max() - x.min())
])

# 汇总统计
total_women = len(bmi_check_per_woman)
pct_varying_bmi = (bmi_check_per_woman['bmi_sd'] > 0).sum() / total_women * 100
mean_bmi_sd = bmi_check_per_woman['bmi_sd'].mean()
mean_bmi_range = bmi_check_per_woman['bmi_range'].mean()

print("BMI时间变异性检查结果:")
print(f"  总孕妇数: {total_women}")
print(f"  BMI有变化的孕妇比例: {pct_varying_bmi:.2f}%")
print(f"  平均BMI标准差: {mean_bmi_sd:.4f}")
print(f"  平均BMI范围: {mean_bmi_range:.4f}")

# 决策规则
print(f"\n孕妇中BMI有变化的比例: {pct_varying_bmi:.2f}%")

if pct_varying_bmi < 10:
    print("\n[DECISION] 使用情况A（BMI仅个体间变异）")
    print("           继续按情况A执行")
    use_case_A = True
else:
    print(f"\n[WARNING] BMI有变化的孕妇比例 = {pct_varying_bmi:.2f}% >= 10%")
    print("          需要使用情况B（BMI也需分解）")
    print("          停止条件触发！必须联系A（宋禹萱）")
    sys.exit(1)

# ============================================================================
# 阶段2: 创建within-between变量
# ============================================================================

print("\n" + "=" * 60)
print("阶段2: 创建within-between变量")
print("=" * 60)
print()
print("情况A：BMI仅个体间变异\n")

# 计算孕周的组内均值
week_means = data.groupby('woman_code')['gestational_week'].transform('mean')

# 孕周分解
data['week_mean'] = week_means
data['week_within'] = data['gestational_week'] - data['week_mean']
data['week_between'] = data['week_mean']

# BMI（个体间，取第一次）
bmi_between = data.groupby('woman_code')['bmi'].transform('first')
data['bmi_between'] = bmi_between

print("变量创建完成!\n")

# 验证分解正确性
print("验证分解正确性...")
check_means = data.groupby('woman_code')['week_within'].mean()

print("week_within的组内均值摘要（应接近0）:")
print(check_means.describe())

max_abs_mean = check_means.abs().max()
if max_abs_mean < 1e-10:
    print(f"\n[VERIFIED] week_within组内均值最大绝对值 = {max_abs_mean:.2e} < 1e-10")
else:
    print(f"\n[WARNING] week_within组内均值最大绝对值 = {max_abs_mean:.2e}")

# 保存变换后数据
output_path = "questions/Q1/03_data/q1_data_transformed.csv"
data.to_csv(output_path, index=False, encoding='utf-8')
print(f"\n变换后数据已保存至: {output_path}")

print("\n阶段0-2执行完成!")
print("=" * 60)

# 输出变换后数据的关键统计
print("\n变换后数据关键变量摘要:")
print(data[['week_within', 'week_between', 'bmi_between', 'y_concentration']].describe())
