"""
Q1 数据分析 - Part 2: 诊断和检验
阶段4-8：模型诊断、Bootstrap、敏感性分析
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM
import pickle
import os

print("=" * 80)
print("Q1 Analysis - Part 2: Diagnostics and Tests (Stages 4-8)")
print("=" * 80)
print()

# Load transformed data and previous results
print("Loading transformed data and model results...")
data = pd.read_csv("03_data/q1_data_transformed.csv", encoding='utf-8')

# Check if models were saved
if os.path.exists("05_results/m2_model.pkl"):
    print("Loading saved M2 model...")
    with open("05_results/m2_model.pkl", 'rb') as f:
        result_m2 = pickle.load(f)
else:
    print("Re-fitting M2 model...")
    # Re-fit M2 model
    model_m2 = MixedLM.from_formula(
        'y_concentration ~ week_within + week_between + bmi_within + bmi_between',
        data=data,
        groups=data['woman_code'],
        re_formula='1'
    )
    result_m2 = model_m2.fit(reml=True, method='lbfgs')

    # Save for future use
    os.makedirs("05_results", exist_ok=True)
    with open("05_results/m2_model.pkl", 'wb') as f:
        pickle.dump(result_m2, f)

print("Model loaded successfully")
print()

# ============================================================================
# Stage 4: Diagnostic Checks
# ============================================================================

print("=" * 80)
print("Stage 4: Diagnostic Checks")
print("=" * 80)
print()

# Get residuals and fitted values
data['fitted_m2'] = result_m2.fittedvalues
data['resid_m2'] = result_m2.resid

print("4.1 Residual Plots (Heteroscedasticity Check)")
print("-" * 80)

# Residuals vs Fitted
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(data['fitted_m2'], data['resid_m2'], alpha=0.3, s=20)
ax.axhline(y=0, color='r', linestyle='--', linewidth=2)
ax.set_xlabel('Fitted Values')
ax.set_ylabel('Residuals')
ax.set_title('M2: Residuals vs Fitted Values')
plt.tight_layout()
plt.savefig('06_figures/m2_resid_vs_fitted.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: 06_figures/m2_resid_vs_fitted.png")

# Residuals vs week
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(data['gestational_week'], data['resid_m2'], alpha=0.3, s=20)
ax.axhline(y=0, color='r', linestyle='--', linewidth=2)
ax.set_xlabel('Gestational Week')
ax.set_ylabel('Residuals')
ax.set_title('M2: Residuals vs Gestational Week')
plt.tight_layout()
plt.savefig('06_figures/m2_resid_vs_week.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: 06_figures/m2_resid_vs_week.png")

# Residuals vs BMI
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(data['bmi'], data['resid_m2'], alpha=0.3, s=20)
ax.axhline(y=0, color='r', linestyle='--', linewidth=2)
ax.set_xlabel('BMI')
ax.set_ylabel('Residuals')
ax.set_title('M2: Residuals vs BMI')
plt.tight_layout()
plt.savefig('06_figures/m2_resid_vs_bmi.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: 06_figures/m2_resid_vs_bmi.png")

print()
print("4.2 Normality Checks (Q-Q Plots)")
print("-" * 80)

# Q-Q plot for residuals
fig, ax = plt.subplots(figsize=(10, 6))
stats.probplot(data['resid_m2'].dropna(), dist="norm", plot=ax)
ax.set_title('M2: Q-Q Plot (Residuals)')
plt.tight_layout()
plt.savefig('06_figures/m2_qq_residuals.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: 06_figures/m2_qq_residuals.png")

# Q-Q plot for random effects
ranef = result_m2.random_effects
ranef_values = [ranef[key].iloc[0] for key in ranef.keys()]
fig, ax = plt.subplots(figsize=(10, 6))
stats.probplot(ranef_values, dist="norm", plot=ax)
ax.set_title('M2: Q-Q Plot (Random Intercepts)')
plt.tight_layout()
plt.savefig('06_figures/m2_qq_ranef.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: 06_figures/m2_qq_ranef.png")

print()
print("4.3 Prediction Boundary Check")
print("-" * 80)

pred_min = data['fitted_m2'].min()
pred_max = data['fitted_m2'].max()
n_below_0 = (data['fitted_m2'] < 0).sum()
n_above_1 = (data['fitted_m2'] > 1).sum()
pct_out = (n_below_0 + n_above_1) / len(data) * 100

print(f"Fitted value range: [{pred_min:.6f}, {pred_max:.6f}]")
print(f"Records below 0: {n_below_0}")
print(f"Records above 1: {n_above_1}")
print(f"Out-of-bounds percentage: {pct_out:.2f}%")

if pct_out < 5:
    print("[OK] Out-of-bounds < 5%, acceptable")
elif pct_out < 10:
    print("[WARNING] Out-of-bounds 5-10%, borderline")
else:
    print("[CONCERN] Out-of-bounds > 10%, consider transformation")

print()
print("=" * 80)
print("Stage 4 diagnostic plots completed!")
print("All 5 diagnostic figures saved to 06_figures/")
print()

print("Summary of diagnostics:")
print(f"  - Residual plots: Check for patterns (should be random scatter)")
print(f"  - Q-Q plots: Check for normality (points should follow line)")
print(f"  - Boundary check: {pct_out:.2f}% out of bounds")
print()

# Save diagnostic summary
with open("05_results/diagnostic_summary.txt", 'w', encoding='utf-8') as f:
    f.write("M2 Model Diagnostic Summary\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Fitted value range: [{pred_min:.6f}, {pred_max:.6f}]\n")
    f.write(f"Out-of-bounds: {pct_out:.2f}%\n")
    f.write(f"Total observations: {len(data)}\n")
    f.write(f"Number of groups: {data['woman_code'].nunique()}\n\n")
    f.write("Diagnostic figures:\n")
    f.write("  1. m2_resid_vs_fitted.png\n")
    f.write("  2. m2_resid_vs_week.png\n")
    f.write("  3. m2_resid_vs_bmi.png\n")
    f.write("  4. m2_qq_residuals.png\n")
    f.write("  5. m2_qq_ranef.png\n")

print("Diagnostic summary saved to: 05_results/diagnostic_summary.txt")
print()
print("[CHECKPOINT] Stage 4 completed!")
print("=" * 80)
