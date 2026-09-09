"""
Q1 数据分析脚本 - Part 1 简化版
负责人：B（周小婷）
基于：questions/Q1/02_model/model_spec.md
日期：2026-09-09

本脚本仅依赖pandas和numpy，执行阶段0-2：
- 阶段0: 环境准备
- 阶段1: BMI前置检查（关键决策点）
- 阶段2: 创建within-between变量
"""

import pandas as pd
import numpy as np
import sys
import os

print("=" * 60)
print("Q1 Data Analysis - Stage 0: Environment Setup")
print("=" * 60)
print()

# 检查必需包
print("Checking required packages...")
try:
    import pandas as pd
    import numpy as np
    print("[OK] pandas")
    print("[OK] numpy")
except ImportError as e:
    print(f"[ERROR] Missing package: {e}")
    sys.exit(1)

print("\nAll required packages are ready!\n")

# ============================================================================
# Stage 0: Read Data
# ============================================================================

print("Reading cleaned data...")
data_path = "03_data/q1_male_data_cleaned.csv"

if not os.path.exists(data_path):
    print(f"ERROR: Data file not found: {data_path}")
    sys.exit(1)

data = pd.read_csv(data_path, encoding='utf-8')

print(f"Data loaded successfully: {len(data)} rows x {len(data.columns)} columns\n")
print("Data structure:")
print(data.dtypes)
print("\nFirst 5 rows:")
print(data.head())
print("\nData summary:")
print(data.describe())

# Confirm required fields exist
required_fields = ['woman_code', 'gestational_week', 'bmi', 'y_concentration']
missing_fields = [f for f in required_fields if f not in data.columns]
if missing_fields:
    print(f"\nERROR: Missing required fields: {', '.join(missing_fields)}")
    sys.exit(1)

print("\n[OK] All required fields confirmed!\n")

# ============================================================================
# Stage 1: BMI Pre-check (KEY DECISION POINT)
# ============================================================================

print("=" * 60)
print("Stage 1: BMI Pre-check (KEY DECISION POINT)")
print("=" * 60)
print()
print("Purpose: Check if BMI varies over time, decide Case A or B\n")

# Check BMI temporal variability
bmi_check_per_woman = data.groupby('woman_code')['bmi'].agg([
    ('n_obs', 'count'),
    ('bmi_mean', 'mean'),
    ('bmi_std', 'std'),
    ('bmi_range', lambda x: x.max() - x.min())
])

# Summary statistics
total_women = len(bmi_check_per_woman)
women_with_varying_bmi = (bmi_check_per_woman['bmi_std'] > 0).sum()
pct_varying_bmi = women_with_varying_bmi / total_women * 100
mean_bmi_std = bmi_check_per_woman['bmi_std'].mean()
mean_bmi_range = bmi_check_per_woman['bmi_range'].mean()

print("BMI Temporal Variability Check Results:")
print(f"  Total women: {total_women}")
print(f"  Women with varying BMI: {women_with_varying_bmi}")
print(f"  Percentage with varying BMI: {pct_varying_bmi:.2f}%")
print(f"  Mean BMI std dev: {mean_bmi_std:.4f}")
print(f"  Mean BMI range: {mean_bmi_range:.4f}")

# Decision rule
print(f"\nPercentage of women with varying BMI: {pct_varying_bmi:.2f}%")

if pct_varying_bmi < 10:
    print("\n[DECISION] Use Case A (BMI between-subject only)")
    print("           Continue with Case A execution")
    use_case_A = True
else:
    print(f"\n[WARNING] Percentage with varying BMI = {pct_varying_bmi:.2f}% >= 10%")
    print("          Need to use Case B (BMI within-between decomposition)")
    print("          STOP CONDITION TRIGGERED! Must contact A (Song Yuxuan)")

    # Save checkpoint file
    checkpoint_path = "04_code/STOP_BMI_CHECK_FAILED.txt"
    with open(checkpoint_path, 'w', encoding='utf-8') as f:
        f.write(f"BMI Pre-check Failed\n")
        f.write(f"===================\n\n")
        f.write(f"Percentage of women with varying BMI: {pct_varying_bmi:.2f}%\n")
        f.write(f"Threshold: 10%\n\n")
        f.write(f"ACTION REQUIRED:\n")
        f.write(f"Contact A (Song Yuxuan) to modify model formula for Case B\n")
    print(f"\nCheckpoint saved to: {checkpoint_path}")
    sys.exit(1)

# ============================================================================
# Stage 2: Create Within-Between Variables
# ============================================================================

print("\n" + "=" * 60)
print("Stage 2: Create Within-Between Variables")
print("=" * 60)
print()
print("Case A: BMI between-subject variability only\n")

# Calculate gestational week group means
week_means = data.groupby('woman_code')['gestational_week'].transform('mean')

# Gestational week decomposition
data['week_mean'] = week_means
data['week_within'] = data['gestational_week'] - data['week_mean']
data['week_between'] = data['week_mean']

# BMI (between-subject, take first observation)
bmi_between = data.groupby('woman_code')['bmi'].transform('first')
data['bmi_between'] = bmi_between

print("Variables created successfully!\n")

# Verify decomposition correctness
print("Verifying decomposition correctness...")
check_means = data.groupby('woman_code')['week_within'].mean()

print("Summary of week_within group means (should be close to 0):")
print(check_means.describe())

max_abs_mean = check_means.abs().max()
if max_abs_mean < 1e-10:
    print(f"\n[VERIFIED] Max absolute week_within group mean = {max_abs_mean:.2e} < 1e-10")
else:
    print(f"\n[WARNING] Max absolute week_within group mean = {max_abs_mean:.2e}")

# Save transformed data
output_path = "03_data/q1_data_transformed.csv"
data.to_csv(output_path, index=False, encoding='utf-8')
print(f"\nTransformed data saved to: {output_path}")

print("\nStages 0-2 completed successfully!")
print("=" * 60)

# Output key statistics of transformed data
print("\nKey variable summary of transformed data:")
summary_vars = ['week_within', 'week_between', 'bmi_between', 'y_concentration']
print(data[summary_vars].describe())

# Save execution summary
summary_path = "04_code/part1_execution_summary.txt"
with open(summary_path, 'w', encoding='utf-8') as f:
    f.write("Q1 Analysis Part 1 - Execution Summary\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Execution Date: 2026-09-09\n")
    f.write(f"Status: SUCCESS\n\n")
    f.write(f"Stage 1: BMI Pre-check\n")
    f.write(f"  Total women: {total_women}\n")
    f.write(f"  Women with varying BMI: {women_with_varying_bmi}\n")
    f.write(f"  Percentage: {pct_varying_bmi:.2f}%\n")
    f.write(f"  Decision: Use Case A\n\n")
    f.write(f"Stage 2: Variable Creation\n")
    f.write(f"  Variables created: week_within, week_between, bmi_between\n")
    f.write(f"  Verification: Max abs mean = {max_abs_mean:.2e}\n\n")
    f.write(f"Output Files:\n")
    f.write(f"  - {output_path}\n")
    f.write(f"  - {summary_path}\n")

print(f"\nExecution summary saved to: {summary_path}")
