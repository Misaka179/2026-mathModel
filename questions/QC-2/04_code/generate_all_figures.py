"""
Q2 最终版图表生成脚本 (完整版)
图1修复窄条标签：全部深色字体，红条引线标注
图7使用真实数据提取四季
图8 Y轴自适应
"""

import json
import os
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Patch
import numpy as np

# ============================================================================
# 学术级美化配置
# ============================================================================
class AcademicStyle:
    COLORS = {
        'blue_gray': '#7A9CC6',
        'dark_blue': '#3D5A80',
        'brick_red': '#C87A6E',
        'gray_green': '#7E9F7E',
        'light_gray': '#CCCCCC',
    }
    GRID_STYLE = {'color': '#E0E0E0', 'linestyle': '--', 'linewidth': 0.5, 'alpha': 0.7}
    AXIS_COLOR = '#333333'

    @staticmethod
    def apply_style():
        plt.rcParams['font.sans-serif'] = ['SimHei', 'SimSun', 'Times New Roman']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 11
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['axes.edgecolor'] = AcademicStyle.AXIS_COLOR
        plt.rcParams['axes.labelcolor'] = AcademicStyle.AXIS_COLOR
        plt.rcParams['xtick.color'] = AcademicStyle.AXIS_COLOR
        plt.rcParams['ytick.color'] = AcademicStyle.AXIS_COLOR
        plt.rcParams['svg.fonttype'] = 'path'

    @staticmethod
    def remove_spines(ax, keep_left=True, keep_bottom=True):
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        if not keep_left: ax.spines['left'].set_visible(False)
        if not keep_bottom: ax.spines['bottom'].set_visible(False)

def thousands_formatter(x, pos):
    return f'{int(x):,}'

# ============================================================================
# 数据加载
# ============================================================================
script_dir = os.path.dirname(os.path.abspath(__file__))

candidate_paths = [
    os.path.join(script_dir, "full_year_backtest_results.json"),
    os.path.join(script_dir, "../05_results/result_data_q2.json"),
    os.path.join(script_dir, "../05_results/Q4-2/Q4_2_backtest_results_v2.json"),
]

print("开始生成 Q2 图表...")
AcademicStyle.apply_style()

results = []
for path in candidate_paths:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding='utf-8') as f:
                raw_data = json.load(f)
            if isinstance(raw_data, list):
                results = raw_data
            elif isinstance(raw_data, dict):
                for key in ['results', 'data', 'daily_results', 'backtest_results', 'records']:
                    if key in raw_data and isinstance(raw_data[key], list):
                        results = raw_data[key]
                        break
                if not results:
                    list_keys = [k for k, v in raw_data.items() if isinstance(v, list)]
                    if list_keys:
                        results = raw_data[list_keys[0]]
            print(f"  ✓ 加载成功: {os.path.relpath(path, script_dir)}")
            print(f"  ✓ 共 {len(results)} 天")
            if results and isinstance(results[0], dict):
                print(f"  ℹ 字段示例: {list(results[0].keys())}")
            break
        except Exception as e:
            print(f"  ⚠ 读取 {path} 失败: {e}")

if not results:
    print("  ⚠ 未找到数据文件，使用模拟数据兜底")
    for i in range(334):
        results.append({
            'day': i+1, 'date': f'2025-{((i%12)+1):02d}-{((i%28)+1):02d}',
            'total_cost': 30000 + np.random.rand() * 50000,
            'E_plan': list(np.random.rand(144) * 1000),
            'emergency': list(np.random.rand(144) * 100),
            'charge': list(np.random.rand(144) * 1000),
            'discharge': list(np.random.rand(144) * 800),
            'soc': list(np.cumsum(np.random.randn(144) * 50) + 6000),
            'initial_soc': 6000,
            'terminal_soc': 6000
        })

output_dir = os.path.join(script_dir, "../06_figures")
os.makedirs(output_dir, exist_ok=True)

# ============================================================================
# 图1: 成本与能量分析 (双子图，全部深色字体 + 红条引线标注)
# ============================================================================
print("生成 图1...")
fig1, (ax1a, ax1b) = plt.subplots(2, 1, figsize=(10, 6))

plan_cost = 1287.1
emergency_cost = 125.0
total_cost = plan_cost + emergency_cost
used_energy = 2047.7
waste_energy = 24.7
total_energy = used_energy + waste_energy

# ---- 上方：E_plan ----
ax1a.barh(['E_plan总量\n(万kWh)'], [used_energy], height=0.4, color=AcademicStyle.COLORS['blue_gray'], edgecolor='white', linewidth=1.5)
ax1a.barh(['E_plan总量\n(万kWh)'], [waste_energy], left=[used_energy], height=0.4, color=AcademicStyle.COLORS['brick_red'], edgecolor='white', linewidth=1.5)

# ★ 大蓝条：深灰字体，居中
ax1a.text(used_energy/2, 0, f'{used_energy:,.1f} 万kWh ({used_energy/total_energy*100:.1f}%)',
          ha='center', va='center', fontsize=10, color=AcademicStyle.AXIS_COLOR, fontweight='bold')

# ★ 小红条：引线拉到上方空白处，砖红字
ax1a.annotate(f'浪费 {waste_energy:,.1f} 万kWh ({waste_energy/total_energy*100:.1f}%)',
              xy=(used_energy + waste_energy/2, 0.2),
              xytext=(total_energy * 0.75, 0.72),
              fontsize=9, color=AcademicStyle.COLORS['brick_red'], fontweight='bold',
              ha='center', va='center',
              arrowprops=dict(arrowstyle='-', color=AcademicStyle.COLORS['brick_red'], lw=1))

# 总量标签
ax1a.text(total_energy + 40, 0, f'{total_energy:,.1f}', ha='left', va='center', fontsize=10,
          fontweight='bold', color=AcademicStyle.AXIS_COLOR)

ax1a.set_xlim(0, total_energy * 1.15)
ax1a.set_ylim(-0.5, 1)
ax1a.xaxis.set_major_formatter(FuncFormatter(thousands_formatter))
ax1a.grid(axis='x', **AcademicStyle.GRID_STYLE)
AcademicStyle.remove_spines(ax1a)
ax1a.tick_params(axis='x', labelbottom=False)

# ---- 下方：成本 ----
ax1b.barh(['年度总成本\n(万元)'], [plan_cost], height=0.4, color=AcademicStyle.COLORS['blue_gray'], edgecolor='white', linewidth=1.5)
ax1b.barh(['年度总成本\n(万元)'], [emergency_cost], left=[plan_cost], height=0.4, color=AcademicStyle.COLORS['brick_red'], edgecolor='white', linewidth=1.5)

ax1b.text(plan_cost/2, 0, f'{plan_cost:,.1f} 万元 ({plan_cost/total_cost*100:.1f}%)',
          ha='center', va='center', fontsize=10, color=AcademicStyle.AXIS_COLOR, fontweight='bold')

ax1b.annotate(f'紧急购电 {emergency_cost:,.1f} 万元 ({emergency_cost/total_cost*100:.1f}%)',
              xy=(plan_cost + emergency_cost/2, 0.2),
              xytext=(total_cost * 0.75, 0.72),
              fontsize=9, color=AcademicStyle.COLORS['brick_red'], fontweight='bold',
              ha='center', va='center',
              arrowprops=dict(arrowstyle='-', color=AcademicStyle.COLORS['brick_red'], lw=1))

ax1b.text(total_cost + 25, 0, f'{total_cost:,.1f}', ha='left', va='center', fontsize=10,
          fontweight='bold', color=AcademicStyle.AXIS_COLOR)

ax1b.set_xlim(0, total_cost * 1.15)
ax1b.set_ylim(-0.5, 1)
ax1b.xaxis.set_major_formatter(FuncFormatter(thousands_formatter))
ax1b.grid(axis='x', **AcademicStyle.GRID_STYLE)
ax1b.set_xlabel('金额 / 能量 (万)', fontsize=11)
AcademicStyle.remove_spines(ax1b)

ax1a.legend(handles=[Patch(facecolor=AcademicStyle.COLORS['blue_gray'], label='计划购电/使用'),
                     Patch(facecolor=AcademicStyle.COLORS['brick_red'], label='紧急购电/浪费')],
            loc='upper center', bbox_to_anchor=(0.5, 1.25), ncol=2, frameon=False)

plt.tight_layout()
fig1.savefig(f'{output_dir}/图1_成本与能量分析.svg', format='svg', bbox_inches='tight')
plt.close(fig1)

# ============================================================================
# 图7: 季节性运行模式对比 (真实数据)
# ============================================================================
print("生成 图7...")
fig7, (ax7a, ax7b) = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True,
                                   gridspec_kw={'hspace': 0.15})

targets = [
    ('春季 (3/20)', ['3-20', '03-20', '3/20', '03/20'], '#7E9F7E'),
    ('夏季 (6/21)', ['6-21', '06-21', '6/21', '06/21'], '#D4A373'),
    ('秋季 (9/23)', ['9-23', '09-23', '9/23', '09/23'], '#3D5A80'),
    ('冬季 (12/21)', ['12-21', '12/21'], '#7A9CC6'),
]

for label, patterns, color in targets:
    matched_day = None
    for r in results:
        date_str = str(r.get('date', '')) + str(r.get('day', ''))
        for p in patterns:
            if p in date_str:
                matched_day = r
                break
        if matched_day:
            break

    if matched_day:
        soc_seq = np.concatenate([[matched_day['initial_soc']], matched_day['soc']])
        time_pts = np.linspace(0, 24, len(soc_seq))
        ax7a.plot(time_pts, soc_seq, label=label, linewidth=2, color=color)
        print(f"  ✓ 提取 {label}: {matched_day.get('date', matched_day.get('day'))}")
    else:
        print(f"  ⚠ 未找到 {label} 的真实数据")

ax7a.axhline(y=10800, color=AcademicStyle.COLORS['brick_red'], linestyle='--', linewidth=1, alpha=0.6)
ax7a.axhline(y=1200, color=AcademicStyle.COLORS['brick_red'], linestyle='--', linewidth=1, alpha=0.6)
ax7a.set_ylabel('SOC(kWh)', fontsize=11)
ax7a.set_ylim(0, 12000)
ax7a.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=4, frameon=False, fontsize=9)
ax7a.grid(axis='y', **AcademicStyle.GRID_STYLE)
ax7a.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
AcademicStyle.remove_spines(ax7a)

time_price = np.linspace(0, 24, 241)
price = np.zeros_like(time_price)
for i, t in enumerate(time_price):
    if t < 7: price[i] = 0.3
    elif 7 <= t < 19: price[i] = 0.6
    elif 19 <= t < 22: price[i] = 1.0
    else: price[i] = 0.6

ax7b.fill_between(time_price, 0, price, alpha=0.25, color='gray')
ax7b.plot(time_price, price, linewidth=2, color='#333333', alpha=0.7)
ax7b.text(3.5, 0.4, '谷时\n0.3元/kWh', ha='center', va='bottom', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
ax7b.text(13, 0.7, '平时\n0.6元/kWh', ha='center', va='bottom', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
ax7b.text(20.5, 1.1, '峰时\n1.0元/kWh', ha='center', va='bottom', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

ax7b.set_xlabel('时间 (h)', fontsize=11)
ax7b.set_ylabel('电价 (元/kWh)', fontsize=11)
ax7b.set_xlim(0, 24)
ax7b.set_ylim(0, 1.4)
ax7b.set_xticks([0, 3, 6, 9, 12, 15, 18, 21, 24])
ax7b.grid(axis='y', **AcademicStyle.GRID_STYLE)
AcademicStyle.remove_spines(ax7b)

fig7.subplots_adjust(left=0.08, right=0.98, top=0.95, bottom=0.1, hspace=0.15)
fig7.savefig(f'{output_dir}/图7_季节性运行模式对比.svg', format='svg', bbox_inches='tight')
plt.close(fig7)

# ============================================================================
# 图8: 电池寿命分析 (Y轴自适应)
# ============================================================================
print("生成 图8...")
fig8 = plt.figure(figsize=(10, 7.5))
gs = gridspec.GridSpec(2, 2, hspace=0.3, wspace=0.25)

daily_cycles = []
for r in results:
    soc_seq = np.array([r.get('initial_soc', 6000)] + list(r.get('soc', [6000]*144)))
    daily_cycles.append((soc_seq.max() - soc_seq.min()) / 12000)
daily_cycles = np.array(daily_cycles)

cumulative_cycles = np.cumsum(daily_cycles)
days = np.arange(1, len(daily_cycles) + 1)
lifetime_consumption = np.cumsum((daily_cycles ** 2) / (0.8 ** 2) / 6000) * 100

ax8a = fig8.add_subplot(gs[0, 0])
ax8a.hist(daily_cycles * 100, bins=20, color=AcademicStyle.COLORS['dark_blue'], alpha=0.7, edgecolor='white', linewidth=1)
ax8a.axvline(np.mean(daily_cycles)*100, color=AcademicStyle.COLORS['brick_red'], linestyle='--', linewidth=1.5)
ax8a.set_xlabel('日循环深度(%)', fontsize=10)
ax8a.set_ylabel('天数', fontsize=10)
ax8a.grid(axis='y', **AcademicStyle.GRID_STYLE)
AcademicStyle.remove_spines(ax8a)

ax8b = fig8.add_subplot(gs[0, 1])
ax8b.plot(days, cumulative_cycles, linewidth=2, color=AcademicStyle.COLORS['dark_blue'])
ax8b.fill_between(days, 0, cumulative_cycles, alpha=0.25, color=AcademicStyle.COLORS['blue_gray'])
ax8b.set_xlabel('运行天数', fontsize=10)
ax8b.set_ylabel('累计等效循环次数', fontsize=10)
ax8b.grid(axis='y', **AcademicStyle.GRID_STYLE)
AcademicStyle.remove_spines(ax8b)

ax8c = fig8.add_subplot(gs[1, :])
ax8c.plot(days, lifetime_consumption, linewidth=2.5, color=AcademicStyle.COLORS['brick_red'])
ax8c.fill_between(days, 0, lifetime_consumption, alpha=0.25, color=AcademicStyle.COLORS['brick_red'])

max_life = max(lifetime_consumption) if len(lifetime_consumption) > 0 else 5
ax8c.set_ylim(0, max(max_life * 1.2, 5))

ax8c.set_xlabel('运行天数', fontsize=10)
ax8c.set_ylabel('累计寿命消耗(%)', fontsize=10)
ax8c.grid(axis='y', **AcademicStyle.GRID_STYLE)
AcademicStyle.remove_spines(ax8c)

fig8.subplots_adjust(left=0.08, right=0.98, top=0.95, bottom=0.1, hspace=0.3)
fig8.savefig(f'{output_dir}/图8_电池寿命分析.svg', format='svg', bbox_inches='tight')
plt.close(fig8)

print("\n" + "="*70)
print("[OK] 所有图表生成完毕！")
print("="*70)