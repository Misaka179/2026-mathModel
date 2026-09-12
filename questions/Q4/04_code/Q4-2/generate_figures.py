"""
Generate figures for Q4-2 results
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
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

print("="*80)
print("生成Q4-2图表")
print("="*80)

# 加载结果
print("\n[1/6] 加载数据...")
with open('../../05_results/Q4-2/Q4_2_backtest_results_v2.json', 'r') as f:
    data = json.load(f)

results = data['results']
print(f"  ✓ 加载了 {len(results)} 天的结果")

# 创建输出目录
output_dir = '../../06_figures/Q4-2'
os.makedirs(output_dir, exist_ok=True)

# 图1: 全年日成本曲线
print("\n[2/6] 生成图1：全年日成本曲线...")
dates = [datetime.strptime(r['date'], '%Y-%m-%d') for r in results]
total_costs = [r['total_cost'] for r in results]

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(dates, total_costs, linewidth=1.5, color='#2E86AB')
ax.set_xlabel('日期', fontsize=12)
ax.set_ylabel('日成本 (元)', fontsize=12)
ax.set_title('Q4-2 全年日成本曲线', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(f'{output_dir}/fig1_daily_cost_curve.png', dpi=300, bbox_inches='tight')
plt.savefig(f'{output_dir}/fig1_daily_cost_curve.svg', format='svg', bbox_inches='tight')
plt.close()
print(f"  ✓ 保存: fig1_daily_cost_curve.png + svg")

# 图2: 关键日期SOC轨迹
print("\n[3/6] 生成图2：关键日期SOC轨迹...")
key_dates = {
    '春分 3/20': 48,
    '夏至 6/21': 141,
    '秋分 9/23': 235,
    '冬至 12/21': 324
}

fig, ax = plt.subplots(figsize=(10, 6))
time_points = np.arange(144) * 10 / 60  # 修正为144个时间点

for label, idx in key_dates.items():
    soc = results[idx]['soc']
    ax.plot(time_points, soc, label=label, linewidth=2)

ax.axhline(y=1200, color='r', linestyle='--', linewidth=1, label='SOC下界')
ax.axhline(y=10800, color='r', linestyle='--', linewidth=1, label='SOC上界')
ax.set_xlabel('时间 (小时)', fontsize=12)
ax.set_ylabel('储能状态 (kWh)', fontsize=12)
ax.set_title('关键日期储能状态轨迹', fontsize=14, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{output_dir}/fig2_soc_trajectories.png', dpi=300, bbox_inches='tight')
plt.savefig(f'{output_dir}/fig2_soc_trajectories.svg', format='svg', bbox_inches='tight')
plt.close()
print(f"  ✓ 保存: fig2_soc_trajectories.png + svg")

# 图3: 月度成本分析
print("\n[4/6] 生成图3：月度成本分析...")
monthly_data = {}
for r in results:
    month = r['date'][:7]  # YYYY-MM
    if month not in monthly_data:
        monthly_data[month] = []
    monthly_data[month].append(r['total_cost'])

months = sorted(monthly_data.keys())
monthly_avg = [np.mean(monthly_data[m]) for m in months]

fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(range(len(months)), monthly_avg, color='#A23B72')
ax.set_xlabel('月份', fontsize=12)
ax.set_ylabel('平均日成本 (元/天)', fontsize=12)
ax.set_title('月度平均日成本', fontsize=14, fontweight='bold')
ax.set_xticks(range(len(months)))
ax.set_xticklabels([m[5:] + '月' for m in months], rotation=0)
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(f'{output_dir}/fig3_monthly_analysis.png', dpi=300, bbox_inches='tight')
plt.savefig(f'{output_dir}/fig3_monthly_analysis.svg', format='svg', bbox_inches='tight')
plt.close()
print(f"  ✓ 保存: fig3_monthly_analysis.png + svg")

# 图4: 电价策略分析（夏至）
print("\n[5/6] 生成图4：电价波动与购电策略...")
summer_idx = 141  # 夏至
r = results[summer_idx]

# 加载电价数据
df_price = pd.read_excel('../../../../C题/附件/附件4.xlsx')
price_all = df_price.iloc[:, 1:145].values
price_summer = price_all[summer_idx + 31, :]  # day 141对应附件4的第172行

time_points = np.arange(144) * 10 / 60

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# 子图1: 电价
ax1.plot(time_points, price_summer, color='#F18F01', linewidth=2)
ax1.set_ylabel('电价 (元/kWh)', fontsize=12)
ax1.set_title('夏至日 (6/21) 电价与购电策略', fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3)

# 子图2: 计划购电
ax2.plot(time_points, r['E_plan'], color='#2E86AB', linewidth=2)
ax2.set_xlabel('时间 (小时)', fontsize=12)
ax2.set_ylabel('计划购电量 (kWh)', fontsize=12)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{output_dir}/fig4_price_strategy_summer.png', dpi=300, bbox_inches='tight')
plt.savefig(f'{output_dir}/fig4_price_strategy_summer.svg', format='svg', bbox_inches='tight')
plt.close()
print(f"  ✓ 保存: fig4_price_strategy_summer.png + svg")

# 图5: 紧急购电分析
print("\n[6/6] 生成图5：紧急购电分析...")
emergency_counts = []
for r in results:
    count = sum(1 for e in r['emergency'] if e > 1e-6)
    emergency_counts.append(count)

fig, ax = plt.subplots(figsize=(12, 5))
ax.bar(range(len(emergency_counts)), emergency_counts, color='#C73E1D', alpha=0.7)
ax.set_xlabel('天数', fontsize=12)
ax.set_ylabel('紧急购电次数', fontsize=12)
ax.set_title('全年紧急购电频率', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(f'{output_dir}/fig5_emergency_analysis.png', dpi=300, bbox_inches='tight')
plt.savefig(f'{output_dir}/fig5_emergency_analysis.svg', format='svg', bbox_inches='tight')
plt.close()
print(f"  ✓ 保存: fig5_emergency_analysis.png + svg")

print("\n" + "="*80)
print("图表生成完成")
print("="*80)
print(f"\n生成了5张图表（PNG + SVG格式），保存在: {output_dir}/")
print("\n图表清单:")
print("  1. fig1_daily_cost_curve - 全年日成本曲线")
print("  2. fig2_soc_trajectories - 关键日期SOC轨迹")
print("  3. fig3_monthly_analysis - 月度成本分析")
print("  4. fig4_price_strategy_summer - 电价与策略分析（夏至）")
print("  5. fig5_emergency_analysis - 紧急购电分析")
print("\n每张图表包含两种格式:")
print("  - PNG格式 (300 DPI) - 用于论文打印")
print("  - SVG格式 (矢量) - 用于后续微调编辑")
print("="*80)
