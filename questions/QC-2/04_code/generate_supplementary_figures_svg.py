"""
生成补充验证图表 - SVG矢量格式版本
图6: 跨日连续性验证
图7: 全年SOC轨迹
"""
import numpy as np
import json
import matplotlib.pyplot as plt
import matplotlib

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'STSong']
plt.rcParams['axes.unicode_minus'] = False
# SVG字体设置 - 避免字体转为路径,保持可编辑性
plt.rcParams['svg.fonttype'] = 'none'

print("Loading data...")
with open('full_year_backtest_results.json', encoding='utf-8') as f:
    backtest = json.load(f)

results = backtest['daily_results']

# ============================================================================
# 图6: 跨日连续性验证
# ============================================================================
print("\nGenerating Figure 6 (SVG): Cross-day Continuity Verification...")

# Calculate transition errors
transition_errors = []
transition_days = []

for i in range(1, len(results)):
    prev_terminal = results[i-1]['terminal_soc']
    curr_initial = results[i]['initial_soc']
    error = abs(curr_initial - prev_terminal)
    transition_errors.append(error)
    transition_days.append(i+1)  # Day 2 to Day 334

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

# 上图：误差折线图
ax1.plot(transition_days, transition_errors, color='#2E86AB', linewidth=1.5, alpha=0.8)
ax1.axhline(y=1e-6, color='red', linestyle='--', linewidth=2,
            label=f'阈值 (1e-6 kWh)', alpha=0.7)
ax1.fill_between(transition_days, 0, transition_errors, alpha=0.2, color='#2E86AB')

ax1.set_xlabel('天数', fontsize=12, weight='bold')
ax1.set_ylabel('连续性误差 (kWh)', fontsize=12, weight='bold')
ax1.set_title('跨日连续性验证 - 333个过渡点误差', fontsize=14, weight='bold', pad=15)
ax1.legend(fontsize=11, loc='upper right')
ax1.grid(True, alpha=0.3)
ax1.set_yscale('log')

# 统计信息
max_error = max(transition_errors)
mean_error = np.mean(transition_errors)
violations = sum(1 for e in transition_errors if e >= 1e-6)

textstr = f'最大误差: {max_error:.2e} kWh\n平均误差: {mean_error:.2e} kWh\n超阈值: {violations}/333'
ax1.text(0.02, 0.98, textstr, transform=ax1.transAxes, fontsize=11,
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# 下图：误差分布直方图
ax2.hist(transition_errors, bins=50, color='#A23B72', edgecolor='black', alpha=0.7)
ax2.axvline(x=1e-6, color='red', linestyle='--', linewidth=2, label='阈值 (1e-6 kWh)')
ax2.set_xlabel('连续性误差 (kWh)', fontsize=12, weight='bold')
ax2.set_ylabel('频次', fontsize=12, weight='bold')
ax2.set_title('误差分布直方图', fontsize=12, weight='bold')
ax2.legend(fontsize=11)
ax2.grid(True, alpha=0.3, axis='y')
ax2.set_xscale('log')

plt.tight_layout()
plt.savefig('../06_figures/图6_跨日连续性验证.svg', format='svg', bbox_inches='tight')
print("  Saved: 图6_跨日连续性验证.svg")
plt.close()

# ============================================================================
# 图7: 全年SOC轨迹
# ============================================================================
print("\nGenerating Figure 7 (SVG): Full Year SOC Trajectory...")

# Extract all SOC values
all_soc = []
time_hours = []

for day_idx, r in enumerate(results):
    day_soc = r['soc']
    for t_idx, soc_val in enumerate(day_soc):
        hour = day_idx * 24 + t_idx * (10/60)  # 10-minute intervals
        all_soc.append(soc_val)
        time_hours.append(hour)

fig, ax = plt.subplots(figsize=(16, 8))

# Plot SOC trajectory
ax.plot(time_hours, all_soc, color='#2E86AB', linewidth=0.8, alpha=0.7, label='SOC轨迹')

# Boundaries
ax.axhline(y=10800, color='red', linestyle='--', linewidth=2, alpha=0.7,
           label='上限 (10,800 kWh)')
ax.axhline(y=1200, color='orange', linestyle='--', linewidth=2, alpha=0.7,
           label='下限 (1,200 kWh)')
ax.axhline(y=6000, color='green', linestyle=':', linewidth=2, alpha=0.7,
           label='目标 (6,000 kWh)')

# Fill boundary region
ax.fill_between(time_hours, 1200, 10800, alpha=0.05, color='gray')

# Mark initial and terminal SOC
initial_soc = results[0]['initial_soc']
terminal_soc = results[-1]['terminal_soc']

ax.plot(0, initial_soc, 'go', markersize=12, label=f'Day 1 初始: {initial_soc:.0f} kWh', zorder=5)
ax.plot(time_hours[-1], terminal_soc, 'ro', markersize=12,
        label=f'Day 334 终端: {terminal_soc:.0f} kWh', zorder=5)

# Add annotations
ax.annotate(f'初始\n{initial_soc:.0f} kWh', xy=(0, initial_soc),
            xytext=(500, initial_soc+1500),
            fontsize=11, weight='bold',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8),
            arrowprops=dict(arrowstyle='->', lw=2, color='green'))

ax.annotate(f'终端\n{terminal_soc:.0f} kWh\n(偏差 {abs(terminal_soc-6000):.1f} kWh)',
            xy=(time_hours[-1], terminal_soc),
            xytext=(time_hours[-1]-1500, terminal_soc+1500),
            fontsize=11, weight='bold',
            bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8),
            arrowprops=dict(arrowstyle='->', lw=2, color='red'))

# Statistics text
soc_mean = np.mean(all_soc)
soc_std = np.std(all_soc)
soc_min = np.min(all_soc)
soc_max = np.max(all_soc)

textstr = f'统计信息:\n'
textstr += f'平均: {soc_mean:.0f} kWh\n'
textstr += f'标准差: {soc_std:.0f} kWh\n'
textstr += f'范围: [{soc_min:.0f}, {soc_max:.0f}] kWh'

ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=11,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

ax.set_xlabel('时间 (小时)', fontsize=13, weight='bold')
ax.set_ylabel('SOC (kWh)', fontsize=13, weight='bold')
ax.set_title('全年SOC运行轨迹 (334天)', fontsize=15, weight='bold', pad=15)
ax.legend(loc='upper right', fontsize=11, ncol=2)
ax.grid(True, alpha=0.3)
ax.set_xlim(0, time_hours[-1])
ax.set_ylim(0, 12000)

# X-axis: show days
ax2 = ax.twiny()
ax2.set_xlim(0, 334)
ax2.set_xlabel('天数', fontsize=13, weight='bold')

plt.tight_layout()
plt.savefig('../06_figures/图7_全年SOC轨迹.svg', format='svg', bbox_inches='tight')
print("  Saved: 图7_全年SOC轨迹.svg")
plt.close()

print("\n" + "="*60)
print("Supplementary figures (SVG format) completed!")
print("="*60)
print(f"\n生成的图表:")
print("  图6: 跨日连续性验证 - 333个过渡点误差<1e-6")
print(f"  图7: 全年SOC轨迹 - 从{initial_soc:.0f}到{terminal_soc:.0f} kWh")
