"""
生成Fig.1.2: Within vs Between效应对比图
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

print("=" * 80)
print("生成Fig.1.2: Within vs Between效应对比图")
print("=" * 80)
print()

# 数据（来自verified_results.md）
variables = ['week_within', 'week_between', 'bmi_within', 'bmi_between']
labels = ['Week\n(Within)', 'Week\n(Between)', 'BMI\n(Within)', 'BMI\n(Between)']
coefficients = [+0.003168, -0.003286, +0.000212, -0.002039]
se = [0.000185, 0.000724, 0.000963, 0.000536]
ci_lower = [+0.002805, -0.004705, -0.001676, -0.003090]
ci_upper = [+0.003532, -0.001867, +0.002100, -0.000988]

# Bootstrap CI
boot_lower = [+0.002601, -0.004391, -0.001873, -0.003031]
boot_upper = [+0.003691, -0.002162, +0.002709, -0.001134]

# 显著性
pvalues = [0.0000, 0.0000, 0.8255, 0.0001]
significant = [p < 0.05 for p in pvalues]

# 创建图表
fig, ax = plt.subplots(figsize=(12, 8))

# 位置
x_pos = np.arange(len(variables))

# 颜色：显著用深色，不显著用浅色
colors = ['#2E7D32' if sig else '#BDBDBD' for sig in significant]  # 深绿 vs 灰色
edge_colors = ['#1B5E20' if sig else '#757575' for sig in significant]

# 绘制系数点
scatter = ax.scatter(x_pos, coefficients, s=200, c=colors,
                     edgecolors=edge_colors, linewidth=2, zorder=5,
                     label='Point Estimate')

# 绘制参数CI（error bars）
for i in range(len(variables)):
    ax.plot([i, i], [ci_lower[i], ci_upper[i]],
            color=colors[i], linewidth=3, zorder=3,
            label='95% CI (Parametric)' if i == 0 else '')

# 绘制Bootstrap CI（虚线）
for i in range(len(variables)):
    ax.plot([i-0.1, i-0.1], [boot_lower[i], boot_upper[i]],
            color='#1976D2', linewidth=2, linestyle='--', zorder=2, alpha=0.7,
            label='95% CI (Bootstrap)' if i == 0 else '')

# 零线
ax.axhline(y=0, color='red', linestyle='-', linewidth=1.5, alpha=0.6, zorder=1)

# 添加系数数值标注
for i, (coef, sig) in enumerate(zip(coefficients, significant)):
    # 数值位置
    y_offset = 0.0005 if coef > 0 else -0.0005

    # 显著性星号
    stars = '***' if pvalues[i] < 0.001 else '**' if pvalues[i] < 0.01 else '*' if pvalues[i] < 0.05 else 'ns'

    ax.text(i, coef + y_offset, f'{coef:+.4f}\n{stars}',
            ha='center', va='bottom' if coef > 0 else 'top',
            fontsize=11, fontweight='bold',
            color='black' if sig else '#757575')

# 标题和标签
ax.set_xlabel('Effect Type', fontsize=14, fontweight='bold')
ax.set_ylabel('Coefficient (β)', fontsize=14, fontweight='bold')
ax.set_title('Fixed Effects Estimates with 95% Confidence Intervals\nM2 Mixed-Effects Model with Within-Between Decomposition',
             fontsize=16, fontweight='bold', pad=20)

# X轴标签
ax.set_xticks(x_pos)
ax.set_xticklabels(labels, fontsize=12)

# 网格
ax.grid(True, alpha=0.3, axis='y')
ax.set_axisbelow(True)

# 图例
legend_elements = [
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#2E7D32',
               markersize=10, markeredgecolor='#1B5E20', markeredgewidth=2,
               label='Significant (p<0.05)'),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#BDBDBD',
               markersize=10, markeredgecolor='#757575', markeredgewidth=2,
               label='Non-significant'),
    plt.Line2D([0], [0], color='#2E7D32', linewidth=3, label='95% CI (Parametric)'),
    plt.Line2D([0], [0], color='#1976D2', linewidth=2, linestyle='--',
               label='95% CI (Bootstrap)')
]
ax.legend(handles=legend_elements, loc='upper right', fontsize=11, framealpha=0.9)

# 添加注释框：Simpson悖论
textstr = 'Simpson\'s Paradox:\nWeek: Within (+) ≠ Between (−)\nMagnitude: |0.003| ≈ |0.003|'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=11,
        verticalalignment='top', bbox=props)

# 调整布局
plt.tight_layout()

# 保存
output_path = '06_figures/fig1_2_within_between_effects.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print(f"[SAVED] {output_path}")
print()

# 生成高分辨率版本（用于印刷）
fig, ax = plt.subplots(figsize=(14, 10))

# （重复上面的绘图代码，但字体更大）
x_pos = np.arange(len(variables))
colors = ['#2E7D32' if sig else '#BDBDBD' for sig in significant]
edge_colors = ['#1B5E20' if sig else '#757575' for sig in significant]

scatter = ax.scatter(x_pos, coefficients, s=300, c=colors,
                     edgecolors=edge_colors, linewidth=3, zorder=5)

for i in range(len(variables)):
    ax.plot([i, i], [ci_lower[i], ci_upper[i]],
            color=colors[i], linewidth=4, zorder=3)

for i in range(len(variables)):
    ax.plot([i-0.15, i-0.15], [boot_lower[i], boot_upper[i]],
            color='#1976D2', linewidth=3, linestyle='--', zorder=2, alpha=0.7)

ax.axhline(y=0, color='red', linestyle='-', linewidth=2, alpha=0.6, zorder=1)

for i, (coef, sig) in enumerate(zip(coefficients, significant)):
    y_offset = 0.0005 if coef > 0 else -0.0005
    stars = '***' if pvalues[i] < 0.001 else '**' if pvalues[i] < 0.01 else '*' if pvalues[i] < 0.05 else 'ns'
    ax.text(i, coef + y_offset, f'{coef:+.4f}\n{stars}',
            ha='center', va='bottom' if coef > 0 else 'top',
            fontsize=14, fontweight='bold',
            color='black' if sig else '#757575')

ax.set_xlabel('Effect Type', fontsize=18, fontweight='bold')
ax.set_ylabel('Coefficient (β)', fontsize=18, fontweight='bold')
ax.set_title('Fixed Effects Estimates with 95% Confidence Intervals\nM2 Mixed-Effects Model with Within-Between Decomposition',
             fontsize=20, fontweight='bold', pad=25)

ax.set_xticks(x_pos)
ax.set_xticklabels(labels, fontsize=16)
ax.tick_params(axis='y', labelsize=14)
ax.grid(True, alpha=0.3, axis='y')
ax.set_axisbelow(True)

ax.legend(handles=legend_elements, loc='upper right', fontsize=14, framealpha=0.9)

textstr = 'Simpson\'s Paradox:\nWeek: Within (+) ≠ Between (−)\nMagnitude: |0.003| ≈ |0.003|'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=14,
        verticalalignment='top', bbox=props)

plt.tight_layout()
output_path_hires = '06_figures/fig1_2_within_between_effects_hires.png'
plt.savefig(output_path_hires, dpi=600, bbox_inches='tight', facecolor='white')
plt.close()

print(f"[SAVED] {output_path_hires} (High-resolution for publication)")
print()

print("=" * 80)
print("Fig.1.2生成完成！")
print("=" * 80)
print()
print("文件:")
print(f"  - 标准版: {output_path} (300 dpi)")
print(f"  - 高清版: {output_path_hires} (600 dpi)")
print()
print("关键特征:")
print("  ✅ 显著效应用深绿色，非显著用灰色")
print("  ✅ 参数CI和Bootstrap CI都显示")
print("  ✅ 系数和显著性星号标注")
print("  ✅ Simpson悖论注释框")
print("  ✅ 零线标注")
