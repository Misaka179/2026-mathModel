"""
Q1 完整分析脚本 - 阶段0-8一体化
包含：环境准备、BMI检查、模型拟合、诊断、检验
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
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

# Set plotting style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10

# Create output directories
os.makedirs("05_results", exist_ok=True)
os.makedirs("06_figures", exist_ok=True)

print("=" * 80)
print("Q1 Complete Analysis - Stages 0-8 (Integrated)")
print("=" * 80)
print(f"Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Check if we already ran Stage 0-3
if os.path.exists("03_data/q1_data_transformed.csv") and os.path.exists("04_code/DECISION_CASE_B.txt"):
    print("Stage 0-3 already completed. Loading results...")
    data = pd.read_csv("03_data/q1_data_transformed.csv", encoding='utf-8')
    use_case_B = True
    print(f"Data loaded: {len(data)} rows")
    print("Using Case B (BMI within-between decomposition)")
    print()

    # Re-fit M2 model for diagnostics
    print("Re-fitting M2 model for diagnostics...")
    model_m2 = MixedLM.from_formula(
        'y_concentration ~ week_within + week_between + bmi_within + bmi_between',
        data=data,
        groups=data['woman_code'],
        re_formula='1'
    )
    result_m2 = model_m2.fit(reml=True, method='lbfgs')
    print("M2 model fitted successfully")
    print()
else:
    print("ERROR: Please run q1_analysis_complete.py first (Stages 0-3)")
    sys.exit(1)

# ============================================================================
# Stage 4: Diagnostic Checks
# ============================================================================

print("=" * 80)
print("Stage 4: Diagnostic Checks (P0 Checklist)")
print("=" * 80)
print()

# Get residuals and fitted values
data['fitted_m2'] = result_m2.fittedvalues
data['resid_m2'] = result_m2.resid

print("4.1 Residual Plots (Heteroscedasticity Check)")
print("-" * 80)

# Residuals vs Fitted
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(data['fitted_m2'], data['resid_m2'], alpha=0.3, s=20, color='steelblue')
ax.axhline(y=0, color='red', linestyle='--', linewidth=2)
ax.set_xlabel('Fitted Values', fontsize=12)
ax.set_ylabel('Residuals', fontsize=12)
ax.set_title('M2: Residuals vs Fitted Values', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('06_figures/m2_resid_vs_fitted.png', dpi=300, bbox_inches='tight')
plt.close()
print("[SAVED] 06_figures/m2_resid_vs_fitted.png")

# Residuals vs week
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(data['gestational_week'], data['resid_m2'], alpha=0.3, s=20, color='steelblue')
ax.axhline(y=0, color='red', linestyle='--', linewidth=2)
ax.set_xlabel('Gestational Week', fontsize=12)
ax.set_ylabel('Residuals', fontsize=12)
ax.set_title('M2: Residuals vs Gestational Week', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('06_figures/m2_resid_vs_week.png', dpi=300, bbox_inches='tight')
plt.close()
print("[SAVED] 06_figures/m2_resid_vs_week.png")

# Residuals vs BMI
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(data['bmi'], data['resid_m2'], alpha=0.3, s=20, color='steelblue')
ax.axhline(y=0, color='red', linestyle='--', linewidth=2)
ax.set_xlabel('BMI', fontsize=12)
ax.set_ylabel('Residuals', fontsize=12)
ax.set_title('M2: Residuals vs BMI', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('06_figures/m2_resid_vs_bmi.png', dpi=300, bbox_inches='tight')
plt.close()
print("[SAVED] 06_figures/m2_resid_vs_bmi.png")

print()
print("4.2 Normality Checks (Q-Q Plots)")
print("-" * 80)

# Q-Q plot for residuals
fig, ax = plt.subplots(figsize=(10, 6))
stats.probplot(data['resid_m2'].dropna(), dist="norm", plot=ax)
ax.set_title('M2: Q-Q Plot (Residuals)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('06_figures/m2_qq_residuals.png', dpi=300, bbox_inches='tight')
plt.close()
print("[SAVED] 06_figures/m2_qq_residuals.png")

# Q-Q plot for random effects
ranef = result_m2.random_effects
ranef_values = [ranef[key].iloc[0] for key in ranef.keys()]
fig, ax = plt.subplots(figsize=(10, 6))
stats.probplot(ranef_values, dist="norm", plot=ax)
ax.set_title('M2: Q-Q Plot (Random Intercepts)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('06_figures/m2_qq_ranef.png', dpi=300, bbox_inches='tight')
plt.close()
print("[SAVED] 06_figures/m2_qq_ranef.png")

print()
print("4.3 Prediction Boundary Check")
print("-" * 80)

pred_min = data['fitted_m2'].min()
pred_max = data['fitted_m2'].max()
n_below_0 = (data['fitted_m2'] < 0).sum()
n_above_1 = (data['fitted_m2'] > 1).sum()
pct_out = (n_below_0 + n_above_1) / len(data) * 100

print(f"Fitted value range: [{pred_min:.6f}, {pred_max:.6f}]")
print(f"Records below 0: {n_below_0} ({n_below_0/len(data)*100:.2f}%)")
print(f"Records above 1: {n_above_1} ({n_above_1/len(data)*100:.2f}%)")
print(f"Total out-of-bounds: {pct_out:.2f}%")
print()

if pct_out < 5:
    print("[OK] Out-of-bounds < 5%, acceptable")
elif pct_out < 15:
    print("[WARNING] Out-of-bounds 5-15%, borderline")
else:
    print("[CONCERN] Out-of-bounds > 15%, may need transformation")

print()
print("4.4 Normality Test (Shapiro-Wilk on sample)")
print("-" * 80)

# Sample 1000 residuals if too many
resid_sample = data['resid_m2'].dropna()
if len(resid_sample) > 5000:
    resid_sample = resid_sample.sample(5000, random_state=42)

shapiro_stat, shapiro_p = stats.shapiro(resid_sample)
print(f"Shapiro-Wilk test: W={shapiro_stat:.4f}, p={shapiro_p:.4f}")
if shapiro_p > 0.05:
    print("[OK] Residuals appear normally distributed (p > 0.05)")
else:
    print("[NOTE] Residuals deviate from normality (p < 0.05)")
    print("       This is common in large samples and may not be problematic")

print()
print("[CHECKPOINT] Stage 4 completed!")
print("=" * 80)
print()

# Save diagnostic summary
with open("05_results/stage4_diagnostic_summary.txt", 'w', encoding='utf-8') as f:
    f.write("M2 Model Diagnostic Summary (Stage 4)\n")
    f.write("=" * 70 + "\n\n")
    f.write(f"Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write(f"Dataset: {len(data)} observations, {data['woman_code'].nunique()} women\n\n")
    f.write("4.1 Residual Plots\n")
    f.write("  - Resid vs Fitted: Check for fan pattern (heteroscedasticity)\n")
    f.write("  - Resid vs Week: Check for trend\n")
    f.write("  - Resid vs BMI: Check for trend\n\n")
    f.write("4.2 Q-Q Plots\n")
    f.write("  - Residuals Q-Q: Check for normality\n")
    f.write("  - Random effects Q-Q: Check for normality\n\n")
    f.write("4.3 Boundary Check\n")
    f.write(f"  Fitted range: [{pred_min:.6f}, {pred_max:.6f}]\n")
    f.write(f"  Out-of-bounds: {pct_out:.2f}%\n")
    f.write(f"  Status: {'OK' if pct_out < 5 else 'WARNING' if pct_out < 15 else 'CONCERN'}\n\n")
    f.write("4.4 Normality Test\n")
    f.write(f"  Shapiro-Wilk: W={shapiro_stat:.4f}, p={shapiro_p:.4f}\n")
    f.write(f"  Status: {'OK' if shapiro_p > 0.05 else 'Deviation noted'}\n\n")
    f.write("Diagnostic Figures:\n")
    f.write("  1. m2_resid_vs_fitted.png\n")
    f.write("  2. m2_resid_vs_week.png\n")
    f.write("  3. m2_resid_vs_bmi.png\n")
    f.write("  4. m2_qq_residuals.png\n")
    f.write("  5. m2_qq_ranef.png\n")

print("Diagnostic summary saved: 05_results/stage4_diagnostic_summary.txt")
print()
print("=" * 80)
print("All stages 0-4 completed successfully!")
print("Next: Stages 5-8 (Bootstrap, Sensitivity Analysis)")
print("=" * 80)
