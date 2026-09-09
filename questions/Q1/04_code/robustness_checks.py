"""
稳健性检验补充脚本
响应Chorus审查员要求：Bootstrap + 敏感性分析
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.regression.mixed_linear_model import MixedLM
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("稳健性检验补充分析")
print("=" * 80)
print()

# 加载数据
data = pd.read_csv("03_data/q1_data_transformed.csv", encoding='utf-8')

# ============================================================================
# 1. 极端值分析
# ============================================================================

print("1. 极端值分析 (±3SD)")
print("=" * 80)

# 重新拟合M2获取残差
model_m2 = MixedLM.from_formula(
    'y_concentration ~ week_within + week_between + bmi_within + bmi_between',
    data=data,
    groups=data['woman_code'],
    re_formula='1'
)
result_m2 = model_m2.fit(reml=True, method='lbfgs')

residuals = result_m2.resid
mean_resid = residuals.mean()
std_resid = residuals.std()

# 识别±3SD外观测
beyond_3sd = np.abs(residuals - mean_resid) > 3 * std_resid
pct_beyond_3sd = beyond_3sd.sum() / len(residuals) * 100

print(f"残差统计:")
print(f"  均值: {mean_resid:.6f}")
print(f"  标准差: {std_resid:.6f}")
print(f"  ±3SD阈值: ±{3*std_resid:.6f}")
print()

print(f"极端值:")
print(f"  ±3SD外观测数: {beyond_3sd.sum()}")
print(f"  ±3SD外比例: {pct_beyond_3sd:.2f}%")
print(f"  理论正态: 0.3%")
print()

if pct_beyond_3sd < 1:
    print(f"  [OK] <1%, 接近正态")
elif pct_beyond_3sd < 2:
    print(f"  [WARNING] 1-2%, 轻微偏离")
else:
    print(f"  [CONCERN] >{pct_beyond_3sd:.1f}%, 偏离明显")

print()

# ============================================================================
# 2. 敏感性分析：排除极端值
# ============================================================================

print("2. 敏感性分析：排除±3SD外观测")
print("=" * 80)

# 创建排除极端值的数据集
data_clean = data[~beyond_3sd].copy()

print(f"原始数据: {len(data)} 观测")
print(f"排除后: {len(data_clean)} 观测 (排除{beyond_3sd.sum()}个)")
print()

# 重新拟合模型
print("重新拟合M2模型...")
model_m2_clean = MixedLM.from_formula(
    'y_concentration ~ week_within + week_between + bmi_within + bmi_between',
    data=data_clean,
    groups=data_clean['woman_code'],
    re_formula='1'
)
result_m2_clean = model_m2_clean.fit(reml=True, method='lbfgs')

print()
print("系数对比:")
print("-" * 80)
print(f"{'变量':<15} {'原始模型':>12} {'排除极端值':>12} {'变化%':>10}")
print("-" * 80)

for var in ['week_within', 'week_between', 'bmi_within', 'bmi_between']:
    beta_orig = result_m2.params[var]
    beta_clean = result_m2_clean.params[var]
    change_pct = (beta_clean - beta_orig) / beta_orig * 100 if beta_orig != 0 else 0

    print(f"{var:<15} {beta_orig:>+12.6f} {beta_clean:>+12.6f} {change_pct:>+9.1f}%")

print()

# 判定敏感性
max_change = max([
    abs((result_m2_clean.params[var] - result_m2.params[var]) / result_m2.params[var] * 100)
    for var in ['week_within', 'week_between', 'bmi_between']
    if result_m2.params[var] != 0
])

print(f"最大系数变化: {max_change:.1f}%")
if max_change < 5:
    print("  [OK] 变化<5%, 结果稳健")
elif max_change < 10:
    print("  [WARNING] 变化5-10%, 中等敏感")
else:
    print("  [CONCERN] 变化>10%, 结果敏感")

print()

# ============================================================================
# 3. Bootstrap置信区间
# ============================================================================

print("3. Bootstrap置信区间检验")
print("=" * 80)

n_bootstrap = 1000
print(f"Bootstrap迭代次数: {n_bootstrap}")
print("(这可能需要几分钟...)")
print()

# 准备存储Bootstrap结果
bootstrap_results = {
    'week_within': [],
    'week_between': [],
    'bmi_within': [],
    'bmi_between': []
}

# 获取唯一的孕妇ID
woman_ids = data['woman_code'].unique()
n_women = len(woman_ids)

np.random.seed(42)

successful_bootstraps = 0
for i in range(n_bootstrap):
    if (i+1) % 100 == 0:
        print(f"  进度: {i+1}/{n_bootstrap}")

    # Bootstrap抽样（以孕妇为单位）
    bootstrap_women = np.random.choice(woman_ids, size=n_women, replace=True)

    # 构建Bootstrap样本
    bootstrap_data = []
    for woman in bootstrap_women:
        woman_data = data[data['woman_code'] == woman].copy()
        bootstrap_data.append(woman_data)

    bootstrap_sample = pd.concat(bootstrap_data, ignore_index=True)

    # 拟合模型
    try:
        model_boot = MixedLM.from_formula(
            'y_concentration ~ week_within + week_between + bmi_within + bmi_between',
            data=bootstrap_sample,
            groups=bootstrap_sample['woman_code'],
            re_formula='1'
        )
        result_boot = model_boot.fit(reml=True, method='lbfgs', disp=False)

        # 存储系数
        for var in bootstrap_results.keys():
            bootstrap_results[var].append(result_boot.params[var])

        successful_bootstraps += 1

    except:
        # 收敛失败，跳过
        continue

print()
print(f"成功的Bootstrap样本: {successful_bootstraps}/{n_bootstrap}")
print()

# 计算Bootstrap置信区间
print("Bootstrap 95%置信区间对比:")
print("-" * 80)
print(f"{'变量':<15} {'原始CI':>25} {'Bootstrap CI':>25} {'一致性':>10}")
print("-" * 80)

for var in ['week_within', 'week_between', 'bmi_within', 'bmi_between']:
    # 原始CI
    ci_orig = result_m2.conf_int().loc[var]

    # Bootstrap CI (百分位法)
    boot_samples = np.array(bootstrap_results[var])
    ci_boot = np.percentile(boot_samples, [2.5, 97.5])

    # 检查一致性
    orig_sig = not (ci_orig[0] <= 0 <= ci_orig[1])
    boot_sig = not (ci_boot[0] <= 0 <= ci_boot[1])
    consistent = "Yes" if orig_sig == boot_sig else "NO"

    print(f"{var:<15} [{ci_orig[0]:>+8.5f}, {ci_orig[1]:>+8.5f}] "
          f"[{ci_boot[0]:>+8.5f}, {ci_boot[1]:>+8.5f}] {consistent:>10}")

print()

# 检查关键效应的稳健性
print("关键效应稳健性判定:")
print("-" * 80)

for var, name in [('week_within', 'Within效应'),
                   ('week_between', 'Between效应')]:
    boot_samples = np.array(bootstrap_results[var])
    ci_boot = np.percentile(boot_samples, [2.5, 97.5])

    # 检查是否跨越0
    if ci_boot[0] > 0 or ci_boot[1] < 0:
        print(f"  [OK] {name}: Bootstrap CI不跨越0, 结果稳健")
    else:
        print(f"  [WARNING] {name}: Bootstrap CI跨越0, 结果不稳健")

print()

# ============================================================================
# 4. 可视化
# ============================================================================

print("4. 生成可视化")
print("=" * 80)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Bootstrap分布图
for idx, (var, name) in enumerate([
    ('week_within', 'Week Within'),
    ('week_between', 'Week Between'),
    ('bmi_within', 'BMI Within'),
    ('bmi_between', 'BMI Between')
]):
    ax = axes[idx//2, idx%2]

    boot_samples = np.array(bootstrap_results[var])

    # 直方图
    ax.hist(boot_samples, bins=50, alpha=0.7, edgecolor='black', density=True)

    # 原始估计
    orig_est = result_m2.params[var]
    ax.axvline(orig_est, color='red', linestyle='--', linewidth=2, label='Original')

    # Bootstrap CI
    ci_boot = np.percentile(boot_samples, [2.5, 97.5])
    ax.axvline(ci_boot[0], color='green', linestyle=':', linewidth=2)
    ax.axvline(ci_boot[1], color='green', linestyle=':', linewidth=2, label='95% Boot CI')

    # 零线
    ax.axvline(0, color='black', linestyle='-', linewidth=1, alpha=0.3)

    ax.set_xlabel('Coefficient Value', fontsize=10)
    ax.set_ylabel('Density', fontsize=10)
    ax.set_title(f'{name}\nBoot: [{ci_boot[0]:.5f}, {ci_boot[1]:.5f}]',
                 fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('06_figures/bootstrap_distributions.png', dpi=300, bbox_inches='tight')
plt.close()

print("[SAVED] 06_figures/bootstrap_distributions.png")
print()

# ============================================================================
# 5. 总结报告
# ============================================================================

print("=" * 80)
print("稳健性检验总结")
print("=" * 80)
print()

print("1. 极端值分析:")
print(f"   - ±3SD外: {pct_beyond_3sd:.2f}%")
print(f"   - 判定: {'正常' if pct_beyond_3sd < 1 else '轻微偏离' if pct_beyond_3sd < 2 else '明显偏离'}")
print()

print("2. 敏感性分析:")
print(f"   - 最大系数变化: {max_change:.1f}%")
print(f"   - 判定: {'稳健' if max_change < 5 else '中等敏感' if max_change < 10 else '高度敏感'}")
print()

print("3. Bootstrap检验:")
print(f"   - 成功率: {successful_bootstraps/n_bootstrap*100:.1f}%")

# 检查关键效应
week_within_robust = not (np.percentile(bootstrap_results['week_within'], 2.5) <= 0 <=
                           np.percentile(bootstrap_results['week_within'], 97.5))
week_between_robust = not (np.percentile(bootstrap_results['week_between'], 2.5) <= 0 <=
                            np.percentile(bootstrap_results['week_between'], 97.5))

print(f"   - Week Within: {'稳健' if week_within_robust else '不稳健'}")
print(f"   - Week Between: {'稳健' if week_between_robust else '不稳健'}")
print()

# 最终判定
all_robust = (pct_beyond_3sd < 2 and max_change < 10 and
              week_within_robust and week_between_robust)

print("最终判定:")
if all_robust:
    print("  [OK] 所有稳健性检验通过，结果可靠")
else:
    print("  [WARNING] 部分检验显示敏感性，需在论文中说明")

print()
print("=" * 80)

# 保存详细结果
with open("05_results/robustness_checks.txt", 'w', encoding='utf-8') as f:
    f.write("稳健性检验详细结果\n")
    f.write("=" * 70 + "\n\n")

    f.write("1. 极端值分析\n")
    f.write(f"   ±3SD外: {beyond_3sd.sum()} ({pct_beyond_3sd:.2f}%)\n\n")

    f.write("2. 敏感性分析（排除极端值）\n")
    for var in ['week_within', 'week_between', 'bmi_within', 'bmi_between']:
        beta_orig = result_m2.params[var]
        beta_clean = result_m2_clean.params[var]
        change_pct = (beta_clean - beta_orig) / beta_orig * 100 if beta_orig != 0 else 0
        f.write(f"   {var}: {beta_orig:+.6f} -> {beta_clean:+.6f} ({change_pct:+.1f}%)\n")
    f.write(f"   最大变化: {max_change:.1f}%\n\n")

    f.write("3. Bootstrap置信区间\n")
    f.write(f"   迭代次数: {n_bootstrap}\n")
    f.write(f"   成功率: {successful_bootstraps/n_bootstrap*100:.1f}%\n")
    for var in ['week_within', 'week_between', 'bmi_within', 'bmi_between']:
        ci_boot = np.percentile(bootstrap_results[var], [2.5, 97.5])
        f.write(f"   {var}: [{ci_boot[0]:+.6f}, {ci_boot[1]:+.6f}]\n")

print("详细结果已保存至: 05_results/robustness_checks.txt")
print("=" * 80)
