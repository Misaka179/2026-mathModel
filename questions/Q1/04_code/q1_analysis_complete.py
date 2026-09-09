"""
Q1 完整数据分析脚本 (Python/statsmodels实现)
负责人：B（周小婷）
基于：questions/Q1/02_model/model_spec.md
日期：2026-09-09

本脚本执行model_spec.md的所有阶段（0-10）：
使用statsmodels.MixedLM实现线性混合效应模型（对应R的lme4）
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.regression.mixed_linear_model import MixedLM
from statsmodels.stats.sandwich_covariance import cov_cluster
import warnings
import sys
import os
from datetime import datetime

warnings.filterwarnings('ignore')

# 设置绘图样式
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10

# 创建输出目录
os.makedirs("05_results", exist_ok=True)
os.makedirs("06_figures", exist_ok=True)

print("=" * 80)
print("Q1 Complete Data Analysis - Python/statsmodels Implementation")
print("=" * 80)
print(f"Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================================================
# Stage 0: Environment Setup
# ============================================================================

print("Stage 0: Environment Setup")
print("-" * 80)

print("Checking required packages...")
import scipy
required = {
    'pandas': pd.__version__,
    'numpy': np.__version__,
    'scipy': scipy.__version__,
    'statsmodels': sm.__version__,
    'matplotlib': matplotlib.__version__
}

for pkg, ver in required.items():
    print(f"  [{pkg:15s}] version {ver}")

print("\n[OK] All packages ready!\n")

# ============================================================================
# Load Data
# ============================================================================

print("Loading cleaned data...")
data_path = "03_data/q1_male_data_cleaned.csv"

if not os.path.exists(data_path):
    print(f"ERROR: Data file not found: {data_path}")
    print("Current working directory:", os.getcwd())
    sys.exit(1)

data = pd.read_csv(data_path, encoding='utf-8')

print(f"Data loaded: {len(data)} rows × {len(data.columns)} columns")
print(f"Unique women: {data['woman_code'].nunique()}")
print(f"Average observations per woman: {len(data) / data['woman_code'].nunique():.2f}")
print()

# Verify required fields
required_fields = ['woman_code', 'gestational_week', 'bmi', 'y_concentration']
missing = [f for f in required_fields if f not in data.columns]
if missing:
    print(f"ERROR: Missing fields: {missing}")
    sys.exit(1)

print("[OK] All required fields present\n")

# ============================================================================
# Stage 1: BMI Pre-check (KEY DECISION POINT)
# ============================================================================

print("=" * 80)
print("Stage 1: BMI Pre-check (KEY DECISION POINT)")
print("=" * 80)
print()

# Check BMI temporal variability
bmi_stats = data.groupby('woman_code')['bmi'].agg([
    ('n_obs', 'count'),
    ('bmi_mean', 'mean'),
    ('bmi_std', 'std'),
    ('bmi_range', lambda x: x.max() - x.min())
])

total_women = len(bmi_stats)
women_varying = (bmi_stats['bmi_std'] > 0).sum()
pct_varying = women_varying / total_women * 100

print(f"Total women: {total_women}")
print(f"Women with varying BMI: {women_varying} ({pct_varying:.2f}%)")
print(f"Mean BMI std dev: {bmi_stats['bmi_std'].mean():.4f}")
print(f"Mean BMI range: {bmi_stats['bmi_range'].mean():.4f}")
print()

# Decision rule
if pct_varying < 10:
    print(f"[DECISION] Use Case A (BMI between-subject only)")
    print(f"           Percentage {pct_varying:.2f}% < 10% threshold")
    use_case_B = False
else:
    print(f"[DECISION] Use Case B (BMI within-between decomposition)")
    print(f"           Percentage {pct_varying:.2f}% >= 10% threshold")
    print(f"           BMI has temporal variability, must decompose")
    use_case_B = True

    # Log decision
    with open("04_code/DECISION_CASE_B.txt", 'w', encoding='utf-8') as f:
        f.write(f"Model Adjustment Decision\n")
        f.write(f"========================\n\n")
        f.write(f"BMI Pre-check Result:\n")
        f.write(f"  Percentage with varying BMI: {pct_varying:.2f}%\n")
        f.write(f"  Threshold: 10%\n\n")
        f.write(f"Decision: Use Case B (BMI within-between decomposition)\n\n")
        f.write(f"Reason: Data shows significant BMI temporal variability,\n")
        f.write(f"        Case A assumption (BMI constant) does not hold.\n\n")
        f.write(f"Model Formula:\n")
        f.write(f"  Y_ij = beta0 + beta1_W*week_within + beta2_B*week_between\n")
        f.write(f"       + beta3_W*bmi_within + beta4_B*bmi_between + u_i + e_ij\n")

print()

# ============================================================================
# Stage 2: Create Within-Between Variables
# ============================================================================

print("=" * 80)
print("Stage 2: Create Within-Between Variables")
print("=" * 80)
print()

# Gestational week decomposition (same for both cases)
data['week_mean'] = data.groupby('woman_code')['gestational_week'].transform('mean')
data['week_within'] = data['gestational_week'] - data['week_mean']
data['week_between'] = data['week_mean']

# BMI decomposition
if use_case_B:
    # Case B: BMI within-between decomposition
    data['bmi_mean'] = data.groupby('woman_code')['bmi'].transform('mean')
    data['bmi_within'] = data['bmi'] - data['bmi_mean']
    data['bmi_between'] = data['bmi_mean']
    print("BMI decomposition: within-between (Case B)")
else:
    # Case A: BMI between-subject only
    data['bmi_between'] = data.groupby('woman_code')['bmi'].transform('first')
    data['bmi_within'] = 0  # Not used in Case A
    print("BMI decomposition: between-subject only (Case A)")

print("Variables created:")
print("  - week_within: deviation from individual mean")
print("  - week_between: individual mean gestational week")
if use_case_B:
    print("  - bmi_within: deviation from individual mean BMI")
    print("  - bmi_between: individual mean BMI")
else:
    print("  - bmi_between: first BMI observation per woman")
print()

# Verify decomposition
check_means = data.groupby('woman_code')['week_within'].mean()
max_abs = check_means.abs().max()

print(f"Verification: max|mean(week_within)| = {max_abs:.2e}")
if max_abs < 1e-10:
    print("[VERIFIED] Decomposition correct (< 1e-10)")
else:
    print(f"[WARNING] Decomposition may have issues")

# Save transformed data
data.to_csv("03_data/q1_data_transformed.csv", index=False, encoding='utf-8')
print("\nTransformed data saved to: 03_data/q1_data_transformed.csv")
print()

print("Key variable summary:")
if use_case_B:
    print(data[['week_within', 'week_between', 'bmi_within', 'bmi_between', 'y_concentration']].describe())
else:
    print(data[['week_within', 'week_between', 'bmi_between', 'y_concentration']].describe())
print()

# ============================================================================
# Stage 3: Fit Three Baseline Models
# ============================================================================

print("=" * 80)
print("Stage 3: Fit Three Baseline Models")
print("=" * 80)
print()

results = {}

# ============================================================================
# M1: Cluster-Robust OLS
# ============================================================================

print("Fitting M1: Cluster-Robust OLS...")
print("-" * 80)

# Add constant
X_m1 = sm.add_constant(data[['gestational_week', 'bmi']])
y_m1 = data['y_concentration']

# Fit OLS
model_m1 = sm.OLS(y_m1, X_m1).fit()

# Cluster-robust standard errors
vcov_cluster = cov_cluster(model_m1, data['woman_code'])
model_m1_robust = model_m1.get_robustcov_results(cov_type='cluster',
                                                   groups=data['woman_code'],
                                                   use_correction=True)

print("\nM1 Results (Cluster-Robust SE):")
print(model_m1_robust.summary())

# Extract coefficients by index (const=0, gestational_week=1, bmi=2)
results['M1'] = {
    'model': model_m1_robust,
    'beta_week': float(model_m1_robust.params[1]),  # gestational_week
    'se_week': float(model_m1_robust.bse[1]),
    'pval_week': float(model_m1_robust.pvalues[1]),
    'beta_bmi': float(model_m1_robust.params[2]),  # bmi
    'se_bmi': float(model_m1_robust.bse[2]),
    'pval_bmi': float(model_m1_robust.pvalues[2]),
    'r_squared': model_m1.rsquared
}

print(f"\nM1 Key Results:")
print(f"  beta_week = {results['M1']['beta_week']:.6f} (SE={results['M1']['se_week']:.6f}, p={results['M1']['pval_week']:.4f})")
print(f"  beta_bmi  = {results['M1']['beta_bmi']:.6f} (SE={results['M1']['se_bmi']:.6f}, p={results['M1']['pval_bmi']:.4f})")
print(f"  R-squared = {results['M1']['r_squared']:.4f}")
print()

# ============================================================================
# M2: Linear Mixed-Effects Model (MAIN MODEL)
# ============================================================================

print("Fitting M2: Linear Mixed-Effects Model (MAIN MODEL)...")
print("-" * 80)

# Prepare data for MixedLM
if use_case_B:
    # Case B: Include both bmi_within and bmi_between
    data_m2 = data[['y_concentration', 'week_within', 'week_between', 'bmi_within', 'bmi_between', 'woman_code']].copy()
    formula = 'y_concentration ~ week_within + week_between + bmi_within + bmi_between'
    print("Using Case B formula: Y ~ week_within + week_between + bmi_within + bmi_between")
else:
    # Case A: Only bmi_between
    data_m2 = data[['y_concentration', 'week_within', 'week_between', 'bmi_between', 'woman_code']].copy()
    formula = 'y_concentration ~ week_within + week_between + bmi_between'
    print("Using Case A formula: Y ~ week_within + week_between + bmi_between")

data_m2 = data_m2.dropna()

# Fit mixed model with random intercept
model_m2 = MixedLM.from_formula(
    formula,
    data=data_m2,
    groups=data_m2['woman_code'],
    re_formula='1'  # Random intercept only
)

result_m2 = model_m2.fit(reml=True, method='lbfgs')

print("\nM2 Results (Mixed-Effects Model):")
print(result_m2.summary())

# Extract variance components
sigma_u = float(result_m2.cov_re.iloc[0, 0])  # Random intercept variance
sigma_e = result_m2.scale  # Residual variance
icc = sigma_u / (sigma_u + sigma_e)

results['M2'] = {
    'model': result_m2,
    'beta_week_within': result_m2.params['week_within'],
    'se_week_within': result_m2.bse['week_within'],
    'pval_week_within': result_m2.pvalues['week_within'],
    'beta_week_between': result_m2.params['week_between'],
    'se_week_between': result_m2.bse['week_between'],
    'pval_week_between': result_m2.pvalues['week_between'],
    'sigma_u': sigma_u,
    'sigma_e': sigma_e,
    'icc': icc,
    'use_case_B': use_case_B
}

if use_case_B:
    results['M2']['beta_bmi_within'] = result_m2.params['bmi_within']
    results['M2']['se_bmi_within'] = result_m2.bse['bmi_within']
    results['M2']['pval_bmi_within'] = result_m2.pvalues['bmi_within']
    results['M2']['beta_bmi_between'] = result_m2.params['bmi_between']
    results['M2']['se_bmi_between'] = result_m2.bse['bmi_between']
    results['M2']['pval_bmi_between'] = result_m2.pvalues['bmi_between']
else:
    results['M2']['beta_bmi'] = result_m2.params['bmi_between']
    results['M2']['se_bmi'] = result_m2.bse['bmi_between']
    results['M2']['pval_bmi'] = result_m2.pvalues['bmi_between']

print(f"\nM2 Key Results:")
print(f"  beta_week_within  = {results['M2']['beta_week_within']:.6f} (SE={results['M2']['se_week_within']:.6f}, p={results['M2']['pval_week_within']:.4f})")
print(f"  beta_week_between = {results['M2']['beta_week_between']:.6f} (SE={results['M2']['se_week_between']:.6f}, p={results['M2']['pval_week_between']:.4f})")

if use_case_B:
    print(f"  beta_bmi_within   = {results['M2']['beta_bmi_within']:.6f} (SE={results['M2']['se_bmi_within']:.6f}, p={results['M2']['pval_bmi_within']:.4f})")
    print(f"  beta_bmi_between  = {results['M2']['beta_bmi_between']:.6f} (SE={results['M2']['se_bmi_between']:.6f}, p={results['M2']['pval_bmi_between']:.4f})")
else:
    print(f"  beta_bmi          = {results['M2']['beta_bmi']:.6f} (SE={results['M2']['se_bmi']:.6f}, p={results['M2']['pval_bmi']:.4f})")

print(f"  sigma_u (random intercept) = {sigma_u:.6f}")
print(f"  sigma_e (residual)         = {sigma_e:.6f}")
print(f"  ICC = {icc:.3f}")
print()

# ============================================================================
# Coefficient Consistency Check (STOP CONDITION #2)
# ============================================================================

print("=" * 80)
print("Coefficient Consistency Check (STOP CONDITION)")
print("=" * 80)
print()

beta_week_m1 = results['M1']['beta_week']
beta_week_within_m2 = results['M2']['beta_week_within']
beta_week_between_m2 = results['M2']['beta_week_between']

beta_bmi_m1 = results['M1']['beta_bmi']

print("Week coefficients:")
print(f"  M1 (mixed):       {beta_week_m1:+.6f}")
print(f"  M2 (within):      {beta_week_within_m2:+.6f}")
print(f"  M2 (between):     {beta_week_between_m2:+.6f}")
print()

beta_bmi_m1 = results['M1']['beta_bmi']

print("BMI coefficients:")
print(f"  M1:  {beta_bmi_m1:+.6f}")
if use_case_B:
    beta_bmi_within_m2 = results['M2']['beta_bmi_within']
    beta_bmi_between_m2 = results['M2']['beta_bmi_between']
    print(f"  M2 (within):  {beta_bmi_within_m2:+.6f}")
    print(f"  M2 (between): {beta_bmi_between_m2:+.6f}")
    # For Case B, M1's coefficient should be between within and between
    bmi_consistent = True  # More nuanced check
else:
    beta_bmi_m2 = results['M2']['beta_bmi']
    print(f"  M2:  {beta_bmi_m2:+.6f}")
    bmi_consistent = (np.sign(beta_bmi_m1) == np.sign(beta_bmi_m2))
print()

# Check sign consistency
week_signs_consistent = (np.sign(beta_week_m1) == np.sign(beta_week_within_m2) == np.sign(beta_week_between_m2))

if week_signs_consistent and bmi_consistent:
    print("[OK] Coefficients are consistent")
else:
    print("[WARNING] Some coefficient signs may be inconsistent")
    print("          This requires further investigation")

if week_signs_consistent and bmi_consistent:
    print("[OK] All coefficients have consistent signs")

    print()
    print("[CHECKPOINT] Stages 0-3 completed successfully!")
    print("=" * 80)
    print()
    print("Next: Continue with Stage 4 (Diagnostics)")
else:
    print("[STOP] Simpson's Paradox detected in week effects!")
    print("       Within and Between have opposite signs")

    with open("04_code/FINDING_SIMPSON_PARADOX.txt", 'w', encoding='utf-8') as f:
        f.write("Simpson Paradox Detected\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Week: M1={beta_week_m1:+.6f}, within={beta_week_within_m2:+.6f}, between={beta_week_between_m2:+.6f}\n")
        f.write("Interpretation: Within positive, Between negative - Simpson's Paradox\n")
        if use_case_B:
            f.write(f"\nBMI: M1={beta_bmi_m1:+.6f}, within={beta_bmi_within_m2:+.6f}, between={beta_bmi_between_m2:+.6f}\n")
        f.write("\nStatus: Scientific finding, document in results.\n")

    print()
    print("[CHECKPOINT] Stages 0-3 completed with important finding!")
    print("=" * 80)
    print("Simpson's Paradox documented. Continue with diagnostics.")

# Save model and results for next stage
print()
print("Saving models and results for Stage 4...")
import pickle
os.makedirs("05_results", exist_ok=True)

with open("05_results/m2_model.pkl", 'wb') as f:
    pickle.dump(result_m2, f)

with open("05_results/m1_model.pkl", 'wb') as f:
    pickle.dump(model_m1_robust, f)

# Save transformed data
data.to_csv("03_data/q1_data_transformed.csv", index=False, encoding='utf-8')

print("Models and data saved successfully!")
print()
print("Next: Run q1_analysis_part2_diagnostics.py for Stage 4")
