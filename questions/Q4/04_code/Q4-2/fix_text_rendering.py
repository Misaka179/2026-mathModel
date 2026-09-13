"""
修复图1、图5、图7的文本渲染问题
移除所有Markdown符号，使用matplotlib原生格式
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import sys

# Force UTF-8 encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10

print("="*80)
print("修复图表文本渲染问题")
print("="*80)

# 加载结果
print("\n[1/4] 加载数据...")
with open('../../05_results/Q4-2/Q4_2_backtest_results_v2.json', 'r') as f:
    data = json.load(f)

results = data['results']
print(f"  ✓ 加载了 {len(results)} 天的结果")

output_dir = '../../06_figures/Q4-2'

# ============================================================================
# 修复图1：全年日成本曲线
# ============================================================================
print("\n[2/4] 修复图1：全年日成本曲线...")

total_costs = [r['total_cost'] for r in results]
day_indices = np.arange(1, len(results) + 1)

max_cost_idx = np.argmax(total_costs)
max_cost = total_costs[max_cost_idx]
max_day = day_indices[max_cost_idx]
max_date = results[max_cost_idx]['date']

fig, ax = plt.subplots(figsize=(12, 5))

# 主曲线
ax.plot(day_indices, total_costs, linewidth=1.2, color='#2E86AB', alpha=0.8, zorder=1)

# Day 121特殊标注
ax.scatter([max_day], [max_cost], color='#E74C3C', s=200, zorder=5,
           edgecolors='darkred', linewidth=2, marker='*')

# 标注 - 移除Markdown符号
annotation_text = f'双重极值点\nDay {max_day} ({max_date})\n成本: {max_cost:,.0f}元\n紧急购电: 13.33小时'
ax.annotate(annotation_text,
            xy=(max_day, max_cost),
            xytext=(max_day + 40, max_cost + 5000),
            fontsize=9, fontweight='bold',
            ha='left',
            bbox=dict(boxstyle='round,pad=0.6', facecolor='#FFE4E1',
                     edgecolor='#E74C3C', linewidth=1.5),
            arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=2))

# TOP10区域标注
top10_indices = np.argsort(total_costs)[-10:]
ax.scatter(day_indices[top10_indices], np.array(total_costs)[top10_indices],
          color='#FFA500', s=50, alpha=0.6, zorder=3, label='成本TOP10')

ax.set_xlabel('运行天数 (Day 1-334)', fontsize=11, fontweight='bold')
ax.set_ylabel('日成本 (元)', fontsize=11, fontweight='bold')
ax.grid(True, alpha=0.15, linestyle='--', color='gray')
ax.set_xlim(0, 340)
ax.legend(loc='upper left', frameon=False, fontsize=10)

# 日期范围说明 - 移除乱码
info_text = f'时间范围: {results[0]["date"]} 至 {results[-1]["date"]}\n共334天'
ax.text(0.02, 0.02, info_text,
        transform=ax.transAxes, fontsize=8, va='bottom',
        color='gray', style='italic',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

plt.tight_layout()
plt.savefig(f'{output_dir}/图1_全年日成本曲线.png', dpi=300, bbox_inches='tight')
plt.savefig(f'{output_dir}/图1_全年日成本曲线.svg', format='svg', bbox_inches='tight')
plt.close()
print(f"  ✓ 修复完成: 图1")

# ============================================================================
# 修复图5：全年紧急购电时长
# ============================================================================
print("\n[3/4] 修复图5：全年紧急购电时长...")

emergency_hours = []
total_emergency_energy = []

for r in results:
    count = sum(1 for e in r['emergency'] if e > 1e-6)
    hours = count * (10 / 60)
    emergency_hours.append(hours)
    total_energy = sum(r['emergency'])
    total_emergency_energy.append(total_energy)

day_indices = np.arange(1, len(results) + 1)

fig, ax = plt.subplots(figsize=(12, 5))

# 主柱状图
bars = ax.bar(day_indices, emergency_hours, color='#C73E1D',
              alpha=0.7, edgecolor='none', width=1.0)

# Day 121特殊标注
bars[120].set_color('#8B0000')
bars[120].set_alpha(1.0)
bars[120].set_edgecolor('yellow')
bars[120].set_linewidth(2)

ax.set_xlabel('运行天数 (Day 1-334)', fontsize=11, fontweight='bold')
ax.set_ylabel('紧急购电时长 (小时/天)', fontsize=11, fontweight='bold')
ax.grid(True, alpha=0.15, axis='y', linestyle='--', color='gray')
ax.set_xlim(0, 340)

# Day 121箭头标注
max_hours_idx = np.argmax(emergency_hours)
max_hours = emergency_hours[max_hours_idx]
ax.annotate(f'Day 121\n图1图5双重极值点\n{max_hours:.2f}小时',
            xy=(121, max_hours),
            xytext=(170, max_hours - 2),
            fontsize=9, ha='left', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#FFE4E1', edgecolor='#E74C3C', linewidth=2),
            arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=2))

# 统计信息 - 移除Markdown符号
avg_hours = np.mean(emergency_hours)
days_with_emergency = sum(1 for h in emergency_hours if h > 0.01)

stats_text = (f'平均: {avg_hours:.2f} 小时/天\n'
              f'最高: {max_hours:.2f} 小时/天 (Day 121)\n'
              f'触发: {days_with_emergency}/{len(results)} 天 ({days_with_emergency/len(results)*100:.1f}%)\n'
              f'平均电量: {np.mean(total_emergency_energy):.0f} kWh/天\n'
              f'\n'
              f'说明: 触发率反映边界压榨策略\n'
              f'在经济性优化与鲁棒性保障之间\n'
              f'取得平衡')

ax.text(0.98, 0.97, stats_text, transform=ax.transAxes,
        fontsize=8.5, verticalalignment='top', horizontalalignment='right',
        bbox=dict(boxstyle='round,pad=0.7', facecolor='wheat', alpha=0.85))

# 日期范围
ax.text(0.02, 0.02, f'时间范围: {results[0]["date"]} 至 {results[-1]["date"]}',
        transform=ax.transAxes, fontsize=8, va='bottom', style='italic', color='gray')

plt.tight_layout()
plt.savefig(f'{output_dir}/图5_全年紧急购电时长.png', dpi=300, bbox_inches='tight')
plt.savefig(f'{output_dir}/图5_全年紧急购电时长.svg', format='svg', bbox_inches='tight')
plt.close()
print(f"  ✓ 修复完成: 图5")

# ============================================================================
# 修复图7：紧急购电关联分析
# ============================================================================
print("\n[4/4] 修复图7：紧急购电关联分析...")

day_indices = np.arange(1, len(results) + 1)
emergency_hours = []
emergency_costs = []
total_costs = []

for r in results:
    count = sum(1 for e in r['emergency'] if e > 1e-6)
    hours = count * (10 / 60)
    emergency_hours.append(hours)
    emergency_costs.append(r['emergency_cost'])
    total_costs.append(r['total_cost'])

triggered = np.array(emergency_hours) > 0.1

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9),
                                gridspec_kw={'height_ratios': [1, 1], 'hspace': 0.25})

# 子图1：紧急购电时长分布
bars = ax1.bar(day_indices, emergency_hours, color='#C73E1D',
              alpha=0.7, width=1.0, edgecolor='none')
bars[120].set_color('#8B0000')
bars[120].set_edgecolor('yellow')
bars[120].set_linewidth(2)

ax1.set_ylabel('紧急购电时长 (小时/天)', fontsize=11, fontweight='bold')
ax1.grid(True, alpha=0.15, axis='y', linestyle='--', color='gray')
ax1.set_xlim(0, 340)
ax1.set_title('紧急购电时长与成本关联分析', fontsize=13, fontweight='bold', pad=15)

# Day 121标注
ax1.annotate('Day 121\n双重极值点',
            xy=(121, emergency_hours[120]),
            xytext=(170, emergency_hours[120] - 2),
            fontsize=10, ha='left', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#FFE4E1', edgecolor='#E74C3C', linewidth=2),
            arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=2))

# 子图2：紧急购电成本 vs 总成本
ax2.scatter(day_indices[~triggered], np.array(total_costs)[~triggered],
          c='#3498DB', s=30, alpha=0.5, label='无紧急购电日')
ax2.scatter(day_indices[triggered], np.array(total_costs)[triggered],
          c='#E74C3C', s=50, alpha=0.8, label='有紧急购电日')

# Day 121特殊标注
ax2.scatter([121], [total_costs[120]], c='darkred', s=250,
          marker='*', zorder=10, edgecolors='yellow', linewidth=2)

ax2.set_xlabel('运行天数 (Day 1-334)', fontsize=11, fontweight='bold')
ax2.set_ylabel('日成本 (元)', fontsize=11, fontweight='bold')
ax2.grid(True, alpha=0.15, linestyle='--', color='gray')
ax2.legend(loc='upper left', frameon=False, fontsize=10)
ax2.set_xlim(0, 340)

# 统计信息 - 移除Markdown符号
triggered_count = np.sum(triggered)
avg_cost_triggered = np.mean(np.array(total_costs)[triggered])
avg_cost_not = np.mean(np.array(total_costs)[~triggered])

stats_text = (f'触发天数: {triggered_count}/334 ({triggered_count/334*100:.1f}%)\n'
              f'触发日平均成本: {avg_cost_triggered:,.0f} 元\n'
              f'未触发日平均成本: {avg_cost_not:,.0f} 元\n'
              f'成本差距: {avg_cost_triggered-avg_cost_not:,.0f} 元\n'
              f'\n'
              f'结论: 紧急购电显著推高日成本\n'
              f'Day 121是成本与紧急购电的\n'
              f'双重极值点')

ax2.text(0.98, 0.97, stats_text, transform=ax2.transAxes,
        fontsize=9, verticalalignment='top', horizontalalignment='right',
        bbox=dict(boxstyle='round,pad=0.7', facecolor='wheat', alpha=0.85))

plt.tight_layout()
plt.savefig(f'{output_dir}/图7_紧急购电关联分析.png', dpi=300, bbox_inches='tight')
plt.savefig(f'{output_dir}/图7_紧急购电关联分析.svg', format='svg', bbox_inches='tight')
plt.close()
print(f"  ✓ 修复完成: 图7")

print("\n" + "="*80)
print("文本渲染问题已全部修复")
print("="*80)
print("\n已修复3张图表:")
print("  1. 图1_全年日成本曲线")
print("  5. 图5_全年紧急购电时长")
print("  7. 图7_紧急购电关联分析")
print("\n所有Markdown符号已移除，使用matplotlib原生格式")
print("="*80)
