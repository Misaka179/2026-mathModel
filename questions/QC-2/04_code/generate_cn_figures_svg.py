"""
生成中文图表 - SVG矢量格式版本
用于论文排版和后续微调
"""
import numpy as np
import json
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.font_manager as fm

# 明确设置中文字体 - 使用系统中确认存在的字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'STSong']
plt.rcParams['axes.unicode_minus'] = False
# SVG字体设置 - 避免字体转为路径,保持可编辑性
plt.rcParams['svg.fonttype'] = 'none'

# 确认字体设置
print("Current font:", plt.rcParams['font.sans-serif'])
print("Generating SVG format figures...")

COLORS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']

print("Loading data...")
with open('full_year_backtest_results.json', encoding='utf-8') as f:
    backtest = json.load(f)
with open('no_storage_baseline_results.json', encoding='utf-8') as f:
    baseline = json.load(f)
with open('energy_balance_verified.json', encoding='utf-8') as f:
    energy_data = json.load(f)

total_cost = backtest['summary']['annual_total_cost']
plan_cost = backtest['summary']['annual_plan_cost']
emergency_cost = backtest['summary']['annual_emergency_cost']
e_plan_total = energy_data['waste_analysis']['total_E_plan_kWh']
e_plan_used = energy_data['waste_analysis']['total_E_plan_used_kWh']
e_plan_waste = energy_data['waste_analysis']['total_E_plan_waste_kWh']
waste_cost = energy_data['waste_analysis']['waste_cost_yuan']

print("Generating Figure 1 (SVG)...")
# 图1: 年度成本分解
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

costs = [plan_cost, emergency_cost]
labels = [f'计划购电\n{plan_cost/1e6:.2f}M元\n(91.2%)',
          f'紧急购电\n{emergency_cost/1e6:.2f}M元\n(8.8%)']
colors_pie = [COLORS[0], COLORS[3]]

wedges, texts, autotexts = ax1.pie(costs, labels=labels, colors=colors_pie,
                                     autopct='%1.1f%%', startangle=90,
                                     textprops={'size': 11, 'weight': 'bold'})
ax1.set_title(f'年度成本分解\n总成本: {total_cost/1e6:.2f}M元',
              fontsize=14, weight='bold', pad=20, fontproperties='Microsoft YaHei')

e_values = [e_plan_used, e_plan_waste]
e_labels = [f'使用\n{e_plan_used/1e6:.2f}M kWh\n(89.8%)',
            f'浪费\n{e_plan_waste/1e6:.2f}M kWh\n(10.2%)']
e_colors = [COLORS[4], COLORS[3]]

wedges2, texts2, autotexts2 = ax2.pie(e_values, labels=e_labels, colors=e_colors,
                                        autopct='%1.1f%%', startangle=90,
                                        textprops={'size': 11, 'weight': 'bold'})
ax2.set_title(f'E_plan能量利用\n总计划: {e_plan_total/1e6:.2f}M kWh',
              fontsize=14, weight='bold', pad=20, fontproperties='Microsoft YaHei')

plt.tight_layout()
plt.savefig('../06_figures/图1_成本分解.svg', format='svg', bbox_inches='tight')
print("  Saved: 图1_成本分解.svg")
plt.close()

print("Generating Figure 2 (SVG)...")
# 图2: 储能收益对比
fig, ax = plt.subplots(figsize=(10, 6))

categories = ['无储能', '有储能\n(当前方案)']
costs_compare = [baseline['baseline_annual_cost'], total_cost]
savings = baseline['annual_savings']

bars = ax.bar(categories, costs_compare, color=[COLORS[3], COLORS[0]],
              edgecolor='black', linewidth=1.5, alpha=0.8)

for bar, cost in zip(bars, costs_compare):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{cost/1e6:.2f}M',
            ha='center', va='bottom', fontsize=12, weight='bold')

ax.annotate('', xy=(1, costs_compare[1]), xytext=(0, costs_compare[0]),
            arrowprops=dict(arrowstyle='<->', color='red', lw=2))
ax.text(0.5, (costs_compare[0] + costs_compare[1])/2,
        f'节省\n{savings/1e6:.2f}M元\n(13.15%)',
        ha='center', va='center', fontsize=11, weight='bold',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))

ax.set_ylabel('年度成本 (元)', fontsize=12, weight='bold')
ax.set_title('储能经济性对比 (334天)', fontsize=14, weight='bold', pad=15)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('../06_figures/图2_储能收益对比.svg', format='svg', bbox_inches='tight')
print("  Saved: 图2_储能收益对比.svg")
plt.close()

print("Generating Figure 3 (SVG)...")
# 图3: 低效成本分析
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(1)
width = 0.6

p1 = ax.bar(x, plan_cost, width,
            label=f'有效成本\n{plan_cost/1e6:.2f}M元 (91.2%)',
            color=COLORS[4], edgecolor='black', linewidth=1.5)
p2 = ax.bar(x, emergency_cost, width, bottom=plan_cost,
            label=f'低效成本\n{emergency_cost/1e6:.2f}M元 (8.8%)',
            color=COLORS[3], edgecolor='black', linewidth=1.5)

ax.text(0, total_cost + 200000,
        f'E_plan浪费: {waste_cost/1e6:.2f}M元\n(未计入总成本)',
        ha='center', fontsize=10, style='italic',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

ax.set_ylabel('成本 (元)', fontsize=12, weight='bold')
ax.set_title('低效成本分析\n紧急购电占8.8%，E_plan浪费额外损失1.64M元',
             fontsize=14, weight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels(['总成本'], fontsize=12)
ax.legend(loc='upper left', fontsize=11)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))

plt.tight_layout()
plt.savefig('../06_figures/图3_低效成本分析.svg', format='svg', bbox_inches='tight')
print("  Saved: 图3_低效成本分析.svg")
plt.close()

print("Generating Figure 4 (SVG)...")
# 图4: 季节性分析
seasons_data = {
    'Spring': {'days': [], 'emergency_cost': 0, 'emergency_freq': 0},
    'Summer': {'days': [], 'emergency_cost': 0, 'emergency_freq': 0},
    'Autumn': {'days': [], 'emergency_cost': 0, 'emergency_freq': 0},
    'Winter': {'days': [], 'emergency_cost': 0, 'emergency_freq': 0}
}

for r in backtest['daily_results']:
    month = int(r['date'].split('-')[1])
    emergency_cost_day = r['emergency_cost']
    has_emergency = sum(r['emergency']) > 0.01

    if 2 <= month <= 4:
        season = 'Spring'
    elif 5 <= month <= 7:
        season = 'Summer'
    elif 8 <= month <= 10:
        season = 'Autumn'
    else:
        season = 'Winter'

    seasons_data[season]['days'].append(r['date'])
    seasons_data[season]['emergency_cost'] += emergency_cost_day
    if has_emergency:
        seasons_data[season]['emergency_freq'] += 1

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

seasons = ['Spring', 'Summer', 'Autumn', 'Winter']
season_names = ['春季\n(2-4月)', '夏季\n(5-7月)', '秋季\n(8-10月)', '冬季\n(11-12月)']
total_emergency = [seasons_data[s]['emergency_cost'] for s in seasons]

bars1 = ax1.bar(season_names, total_emergency, color=COLORS[:4],
                edgecolor='black', linewidth=1.5, alpha=0.8)

for bar, cost in zip(bars1, total_emergency):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             f'{cost/1000:.0f}K',
             ha='center', va='bottom', fontsize=10, weight='bold')

ax1.set_ylabel('紧急购电成本 (元)', fontsize=11, weight='bold')
ax1.set_title('各季节紧急购电成本', fontsize=13, weight='bold')
ax1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f'{x/1e3:.0f}K'))
ax1.grid(axis='y', alpha=0.3)

emergency_freq = [seasons_data[s]['emergency_freq'] for s in seasons]
n_days = [len(seasons_data[s]['days']) for s in seasons]
freq_pct = [f/n*100 if n > 0 else 0 for f, n in zip(emergency_freq, n_days)]

bars2 = ax2.bar(season_names, freq_pct, color=COLORS[:4],
                edgecolor='black', linewidth=1.5, alpha=0.8)

for bar, pct in zip(bars2, freq_pct):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             f'{pct:.1f}%',
             ha='center', va='bottom', fontsize=10, weight='bold')

ax2.set_ylabel('紧急购电频率 (%)', fontsize=11, weight='bold')
ax2.set_title('各季节紧急购电频率', fontsize=13, weight='bold')
ax2.axhline(y=50, color='red', linestyle='--', linewidth=2, alpha=0.7, label='50%基准')
ax2.legend(fontsize=10)
ax2.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('../06_figures/图4_季节性分析.svg', format='svg', bbox_inches='tight')
print("  Saved: 图4_季节性分析.svg")
plt.close()

print("Generating Figure 5 (SVG)...")
# 图5: SOC运行轨迹
typical_day = backtest['daily_results'][100]
soc = np.array(typical_day['soc'])
time_points = np.arange(0, 24, 24/144)

fig, ax = plt.subplots(figsize=(14, 6))

ax.plot(time_points, soc, linewidth=2.5, color=COLORS[0], label='SOC', marker='o', markersize=2)
ax.axhline(y=10800, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='上限 (10,800 kWh)')
ax.axhline(y=1200, color='orange', linestyle='--', linewidth=1.5, alpha=0.7, label='下限 (1,200 kWh)')
ax.axhline(y=6000, color='green', linestyle=':', linewidth=1.5, alpha=0.7, label='目标 (6,000 kWh)')
ax.fill_between(time_points, 1200, 10800, alpha=0.1, color='gray')

ax.set_xlabel('时间 (小时)', fontsize=12, weight='bold')
ax.set_ylabel('SOC (kWh)', fontsize=12, weight='bold')
ax.set_title(f'SOC运行轨迹示例 ({typical_day["date"]})', fontsize=14, weight='bold', pad=15)
ax.legend(loc='best', fontsize=11)
ax.grid(True, alpha=0.3)
ax.set_xlim(0, 24)

plt.tight_layout()
plt.savefig('../06_figures/图5_SOC运行轨迹.svg', format='svg', bbox_inches='tight')
print("  Saved: 图5_SOC运行轨迹.svg")
plt.close()

print("\n" + "="*60)
print("All Chinese figures (SVG format) completed!")
print("="*60)
