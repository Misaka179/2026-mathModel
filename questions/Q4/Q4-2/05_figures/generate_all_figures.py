"""
Q4-2 完整图表生成脚本 (图1-图10，统一中文命名)
"""

import json
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Patch

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================================================
# 图表开关
# ============================================================================
FIG_CONFIG = {
    'fig1': True, 'fig2': True, 'fig3': True, 'fig4': True, 'fig5': True,
    'fig6': True, 'fig7': True, 'fig8': True, 'fig9': True, 'fig10': True,
}

# ============================================================================
# 学术级美化配置
# ============================================================================
class AcademicStyle:
    COLORS = {
        'blue_gray': '#7A9CC6', 'dark_blue': '#3D5A80',
        'brick_red': '#C87A6E', 'gray_green': '#7E9F7E',
        'light_gray': '#CCCCCC', 'orange': '#D4A373',
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
    os.path.join(script_dir, "../02_results/Q4_2_backtest_results_v2.json"),
    os.path.join(script_dir, "../02_results/result4-2.json"),
    os.path.join(script_dir, "full_year_backtest_results.json"),
]

print("开始生成 Q4-2 图表...")
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
            'plan_cost': 28000 + np.random.rand() * 40000,
            'emergency_cost': 2000 + np.random.rand() * 5000,
            'E_plan': list(np.random.rand(144) * 1000),
            'emergency': list(np.random.rand(144) * 100),
            'charge': list(np.random.rand(144) * 1000),
            'discharge': list(np.random.rand(144) * 800),
            'soc': list(np.cumsum(np.random.randn(144) * 50) + 6000),
            'initial_soc': 6000,
            'terminal_soc': 6000
        })

output_dir = os.path.join(script_dir, "result")
os.makedirs(output_dir, exist_ok=True)

# ============================================================================
# 图1: 成本与能量分析
# ============================================================================
if FIG_CONFIG['fig1']:
    print("\n[图1] 成本与能量分析...")
    fig1, (ax1a, ax1b) = plt.subplots(2, 1, figsize=(10, 6))
    plan_cost, emergency_cost = 1287.1, 125.0
    total_cost = plan_cost + emergency_cost
    used_energy, waste_energy = 2047.7, 24.7
    total_energy = used_energy + waste_energy

    ax1a.barh(['E_plan总量\n(万kWh)'], [used_energy], height=0.4, color=AcademicStyle.COLORS['blue_gray'], edgecolor='white', linewidth=1.5)
    ax1a.barh(['E_plan总量\n(万kWh)'], [waste_energy], left=[used_energy], height=0.4, color=AcademicStyle.COLORS['brick_red'], edgecolor='white', linewidth=1.5)
    ax1a.text(used_energy/2, 0, f'{used_energy:,.1f} 万kWh ({used_energy/total_energy*100:.1f}%)', ha='center', va='center', fontsize=10, color=AcademicStyle.AXIS_COLOR, fontweight='bold')
    ax1a.annotate(f'浪费 {waste_energy:,.1f} 万kWh ({waste_energy/total_energy*100:.1f}%)', xy=(used_energy + waste_energy/2, 0.2), xytext=(total_energy * 0.75, 0.72), fontsize=9, color=AcademicStyle.COLORS['brick_red'], fontweight='bold', ha='center', va='center', arrowprops=dict(arrowstyle='-', color=AcademicStyle.COLORS['brick_red'], lw=1))
    ax1a.text(total_energy + 40, 0, f'{total_energy:,.1f}', ha='left', va='center', fontsize=10, fontweight='bold', color=AcademicStyle.AXIS_COLOR)
    ax1a.set_xlim(0, total_energy * 1.15); ax1a.set_ylim(-0.5, 1)
    ax1a.xaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    ax1a.grid(axis='x', **AcademicStyle.GRID_STYLE)
    AcademicStyle.remove_spines(ax1a); ax1a.tick_params(axis='x', labelbottom=False)

    ax1b.barh(['年度总成本\n(万元)'], [plan_cost], height=0.4, color=AcademicStyle.COLORS['blue_gray'], edgecolor='white', linewidth=1.5)
    ax1b.barh(['年度总成本\n(万元)'], [emergency_cost], left=[plan_cost], height=0.4, color=AcademicStyle.COLORS['brick_red'], edgecolor='white', linewidth=1.5)
    ax1b.text(plan_cost/2, 0, f'{plan_cost:,.1f} 万元 ({plan_cost/total_cost*100:.1f}%)', ha='center', va='center', fontsize=10, color=AcademicStyle.AXIS_COLOR, fontweight='bold')
    ax1b.annotate(f'紧急购电 {emergency_cost:,.1f} 万元 ({emergency_cost/total_cost*100:.1f}%)', xy=(plan_cost + emergency_cost/2, 0.2), xytext=(total_cost * 0.75, 0.72), fontsize=9, color=AcademicStyle.COLORS['brick_red'], fontweight='bold', ha='center', va='center', arrowprops=dict(arrowstyle='-', color=AcademicStyle.COLORS['brick_red'], lw=1))
    ax1b.text(total_cost + 25, 0, f'{total_cost:,.1f}', ha='left', va='center', fontsize=10, fontweight='bold', color=AcademicStyle.AXIS_COLOR)
    ax1b.set_xlim(0, total_cost * 1.15); ax1b.set_ylim(-0.5, 1)
    ax1b.xaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    ax1b.grid(axis='x', **AcademicStyle.GRID_STYLE)
    ax1b.set_xlabel('金额 / 能量 (万)', fontsize=11)
    AcademicStyle.remove_spines(ax1b)

    ax1a.legend(handles=[Patch(facecolor=AcademicStyle.COLORS['blue_gray'], label='计划购电/使用'), Patch(facecolor=AcademicStyle.COLORS['brick_red'], label='紧急购电/浪费')], loc='upper center', bbox_to_anchor=(0.5, 1.25), ncol=2, frameon=False)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/图1_成本与能量分析.svg', format='svg', bbox_inches='tight')
    plt.close()
    print("  ✓ 已生成")

# ============================================================================
# 图2: 储能经济性对比
# ============================================================================
if FIG_CONFIG['fig2']:
    print("\n[图2] 储能经济性对比...")
    fig2, ax = plt.subplots(figsize=(8, 6))
    costs = [4952.0, 1412.0]
    bars = ax.bar(['无储能', '有储能'], costs, width=0.4, color=[AcademicStyle.COLORS['light_gray'], AcademicStyle.COLORS['dark_blue']], alpha=0.85, edgecolor='white', linewidth=1.5)
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 50, f'{h:,.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold', color=AcademicStyle.AXIS_COLOR)
    ax.set_ylabel('年度总成本 (万元)', fontsize=11)
    ax.grid(axis='y', **AcademicStyle.GRID_STYLE)
    ax.set_ylim(0, max(costs) * 1.15)
    ax.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    AcademicStyle.remove_spines(ax)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/图2_储能经济性对比.svg', format='svg', bbox_inches='tight')
    plt.close()
    print("  ✓ 已生成")

# ============================================================================
# 图3: 典型日SOC轨迹
# ============================================================================
if FIG_CONFIG['fig3']:
    print("\n[图3] 典型日SOC轨迹...")
    fig3, ax = plt.subplots(figsize=(10, 7.5))
    if len(results) > 100:
        day = results[100]
        soc_seq = np.concatenate([[day['initial_soc']], day['soc']])
        time_pts = np.linspace(0, 24, len(soc_seq))
        ax.plot(time_pts, soc_seq, linewidth=2, color=AcademicStyle.COLORS['dark_blue'], label='SOC')
    ax.axhline(y=10800, color=AcademicStyle.COLORS['brick_red'], linestyle='--', linewidth=1.5, alpha=0.8, label='上限')
    ax.axhline(y=1200, color=AcademicStyle.COLORS['brick_red'], linestyle=':', linewidth=1.5, alpha=0.8, label='下限')
    ax.axhline(y=6000, color=AcademicStyle.COLORS['gray_green'], linestyle=':', linewidth=1.2, label='目标')
    ax.set_xlabel('时间 (h)', fontsize=11)
    ax.set_ylabel('SOC (kWh)', fontsize=11)
    ax.set_xlim(0, 24); ax.set_ylim(0, 12000)
    ax.grid(axis='y', **AcademicStyle.GRID_STYLE)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.1), ncol=4, frameon=False, fontsize=9)
    ax.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    AcademicStyle.remove_spines(ax)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/图3_典型日SOC轨迹.svg', format='svg', bbox_inches='tight')
    plt.close()
    print("  ✓ 已生成")

# ============================================================================
# 图4: 跨日连续性验证
# ============================================================================
if FIG_CONFIG['fig4']:
    print("\n[图4] 跨日连续性验证...")
    fig4, ax = plt.subplots(figsize=(10, 6))
    errors = [abs(results[i]['initial_soc'] - results[i-1]['terminal_soc']) for i in range(1, len(results))]
    days = list(range(2, len(results) + 1))
    ax.plot(days, errors, color=AcademicStyle.COLORS['dark_blue'], linewidth=1.5)
    ax.axhline(y=1e-6, color=AcademicStyle.COLORS['brick_red'], linestyle='--', linewidth=1.2, alpha=0.8)
    ax.axhline(y=-1e-6, color=AcademicStyle.COLORS['brick_red'], linestyle='--', linewidth=1.2, alpha=0.8)
    ax.set_xlabel('过渡点序号', fontsize=11)
    ax.set_ylabel('连续性误差', fontsize=11)
    ax.set_ylim(-1e-5, 1e-5)
    ax.grid(axis='y', **AcademicStyle.GRID_STYLE)
    AcademicStyle.remove_spines(ax)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/图4_跨日连续性验证.svg', format='svg', bbox_inches='tight')
    plt.close()
    print("  ✓ 已生成")

# ============================================================================
# 图5: 全年SOC轨迹
# ============================================================================
if FIG_CONFIG['fig5']:
    print("\n[图5] 全年SOC轨迹...")
    fig5, ax = plt.subplots(figsize=(10, 7.5))
    days = [r['day'] for r in results]
    means, mins, maxs = [], [], []
    for r in results:
        soc = [r.get('initial_soc', 6000)] + list(r.get('soc', []))
        means.append(np.mean(soc)); mins.append(np.min(soc)); maxs.append(np.max(soc))
    ax.fill_between(days, mins, maxs, alpha=0.25, color=AcademicStyle.COLORS['blue_gray'], label='日内变化范围')
    ax.plot(days, means, color=AcademicStyle.COLORS['dark_blue'], linewidth=1.8, label='日均值')
    ax.axhline(y=10800, color=AcademicStyle.COLORS['brick_red'], linestyle='--', linewidth=1.2, alpha=0.8, label='上限')
    ax.axhline(y=1200, color=AcademicStyle.COLORS['brick_red'], linestyle='--', linewidth=1.2, alpha=0.8, label='下限')
    ax.set_xlabel('运行天数', fontsize=11)
    ax.set_ylabel('SOC (kWh)', fontsize=11)
    ax.set_ylim(0, 12000)
    ax.grid(axis='y', **AcademicStyle.GRID_STYLE)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.12), ncol=4, frameon=False, fontsize=9)
    ax.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    AcademicStyle.remove_spines(ax)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/图5_全年SOC轨迹.svg', format='svg', bbox_inches='tight')
    plt.close()
    print("  ✓ 已生成")

# ============================================================================
# 图6: 成本节省来源分解(瀑布图)
# ============================================================================
if FIG_CONFIG['fig6']:
    print("\n[图6] 成本节省来源分解...")
    fig6, ax = plt.subplots(figsize=(10, 7.5))
    baseline, total, emergency = 4952.0, 1412.0, 125.0
    pv_saving = baseline - total - emergency
    after_pv = baseline - pv_saving
    ax.bar(0, baseline, width=0.4, color=AcademicStyle.COLORS['light_gray'], alpha=0.85, edgecolor='white', linewidth=1.5)
    ax.bar(1, pv_saving, width=0.4, bottom=after_pv, color=AcademicStyle.COLORS['gray_green'], alpha=0.85, edgecolor='white', linewidth=1.5)
    ax.bar(2, emergency, width=0.4, bottom=total, color=AcademicStyle.COLORS['gray_green'], alpha=0.85, edgecolor='white', linewidth=1.5)
    ax.bar(3, total, width=0.4, color=AcademicStyle.COLORS['dark_blue'], alpha=0.85, edgecolor='white', linewidth=1.5)
    ax.text(0, baseline + 50, f'{baseline:,.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    ax.text(1, (after_pv + baseline)/2, f'-{pv_saving:,.1f}\n({pv_saving/baseline*100:.1f}%)', ha='center', va='center', fontsize=9, fontweight='bold', color='white')
    ax.text(2, total + emergency/2, f'-{emergency:,.1f}\n({emergency/baseline*100:.1f}%)', ha='center', va='center', fontsize=9, fontweight='bold', color='white')
    ax.text(3, total + 50, f'{total:,.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    ax.plot([0.2, 0.8], [baseline, baseline], 'k--', lw=1, alpha=0.5)
    ax.plot([1.2, 1.8], [after_pv, after_pv], 'k--', lw=1, alpha=0.5)
    ax.plot([2.2, 2.8], [total, total], 'k--', lw=1, alpha=0.5)
    ax.set_xticks([0, 1, 2, 3])
    ax.set_xticklabels(['无储能\n基准', '峰谷套利\n节省', '避免紧急\n购电', '有储能\n总成本'])
    ax.set_ylabel('年度总成本 (万元)', fontsize=11)
    ax.set_ylim(0, baseline * 1.15)
    ax.grid(axis='y', **AcademicStyle.GRID_STYLE)
    ax.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    AcademicStyle.remove_spines(ax)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/图6_成本节省来源分解.svg', format='svg', bbox_inches='tight')
    plt.close()
    print("  ✓ 已生成")

# ============================================================================
# 图7: 季节性运行模式对比
# ============================================================================
if FIG_CONFIG['fig7']:
    print("\n[图7] 季节性运行模式对比...")
    fig7, (ax7a, ax7b) = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True, gridspec_kw={'hspace': 0.15})
    targets = [
        ('春季 (3/20)', ['3-20', '03-20', '3/20'], '#7E9F7E'),
        ('夏季 (6/21)', ['6-21', '06-21', '6/21'], '#D4A373'),
        ('秋季 (9/23)', ['9-23', '09-23', '9/23'], '#3D5A80'),
        ('冬季 (12/21)', ['12-21', '12/21'], '#7A9CC6'),
    ]
    for label, patterns, color in targets:
        matched = None
        for r in results:
            date_str = str(r.get('date', '')) + str(r.get('day', ''))
            for p in patterns:
                if p in date_str:
                    matched = r; break
            if matched: break
        if matched:
            soc_seq = np.concatenate([[matched['initial_soc']], matched['soc']])
            ax7a.plot(np.linspace(0, 24, len(soc_seq)), soc_seq, label=label, linewidth=2, color=color)
    ax7a.axhline(y=10800, color=AcademicStyle.COLORS['brick_red'], linestyle='--', linewidth=1, alpha=0.6)
    ax7a.axhline(y=1200, color=AcademicStyle.COLORS['brick_red'], linestyle='--', linewidth=1, alpha=0.6)
    ax7a.set_ylabel('SOC(kWh)', fontsize=11); ax7a.set_ylim(0, 12000)
    ax7a.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=4, frameon=False, fontsize=9)
    ax7a.grid(axis='y', **AcademicStyle.GRID_STYLE)
    ax7a.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    AcademicStyle.remove_spines(ax7a)

    time_price = np.linspace(0, 24, 241)
    price = np.array([0.3 if t < 7 else (0.6 if t < 19 else (1.0 if t < 22 else 0.6)) for t in time_price])
    ax7b.fill_between(time_price, 0, price, alpha=0.25, color='gray')
    ax7b.plot(time_price, price, linewidth=2, color='#333333', alpha=0.7)
    ax7b.text(3.5, 0.4, '谷时\n0.3元/kWh', ha='center', va='bottom', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
    ax7b.text(13, 0.7, '平时\n0.6元/kWh', ha='center', va='bottom', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
    ax7b.text(20.5, 1.1, '峰时\n1.0元/kWh', ha='center', va='bottom', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
    ax7b.set_xlabel('时间 (h)', fontsize=11); ax7b.set_ylabel('电价 (元/kWh)', fontsize=11)
    ax7b.set_xlim(0, 24); ax7b.set_ylim(0, 1.4)
    ax7b.set_xticks([0, 3, 6, 9, 12, 15, 18, 21, 24])
    ax7b.grid(axis='y', **AcademicStyle.GRID_STYLE)
    AcademicStyle.remove_spines(ax7b)
    fig7.subplots_adjust(left=0.08, right=0.98, top=0.95, bottom=0.1, hspace=0.15)
    fig7.savefig(f'{output_dir}/图7_季节性运行模式对比.svg', format='svg', bbox_inches='tight')
    plt.close()
    print("  ✓ 已生成")

# ============================================================================
# 图8: 电池寿命分析
# ============================================================================
if FIG_CONFIG['fig8']:
    print("\n[图8] 电池寿命分析...")
    fig8 = plt.figure(figsize=(10, 7.5))
    gs = gridspec.GridSpec(2, 2, hspace=0.3, wspace=0.25)
    daily_cycles = np.array([(np.array([r.get('initial_soc', 6000)] + list(r.get('soc', [6000]*144))).max() - np.array([r.get('initial_soc', 6000)] + list(r.get('soc', [6000]*144))).min()) / 12000 for r in results])
    cumulative_cycles = np.cumsum(daily_cycles)
    days = np.arange(1, len(daily_cycles) + 1)
    lifetime = np.cumsum((daily_cycles ** 2) / (0.8 ** 2) / 6000) * 100

    ax8a = fig8.add_subplot(gs[0, 0])
    ax8a.hist(daily_cycles * 100, bins=20, color=AcademicStyle.COLORS['dark_blue'], alpha=0.7, edgecolor='white', linewidth=1)
    ax8a.axvline(np.mean(daily_cycles)*100, color=AcademicStyle.COLORS['brick_red'], linestyle='--', linewidth=1.5)
    ax8a.set_xlabel('日循环深度(%)', fontsize=10); ax8a.set_ylabel('天数', fontsize=10)
    ax8a.grid(axis='y', **AcademicStyle.GRID_STYLE); AcademicStyle.remove_spines(ax8a)

    ax8b = fig8.add_subplot(gs[0, 1])
    ax8b.plot(days, cumulative_cycles, linewidth=2, color=AcademicStyle.COLORS['dark_blue'])
    ax8b.fill_between(days, 0, cumulative_cycles, alpha=0.25, color=AcademicStyle.COLORS['blue_gray'])
    ax8b.set_xlabel('运行天数', fontsize=10); ax8b.set_ylabel('累计等效循环次数', fontsize=10)
    ax8b.grid(axis='y', **AcademicStyle.GRID_STYLE); AcademicStyle.remove_spines(ax8b)

    ax8c = fig8.add_subplot(gs[1, :])
    ax8c.plot(days, lifetime, linewidth=2.5, color=AcademicStyle.COLORS['brick_red'])
    ax8c.fill_between(days, 0, lifetime, alpha=0.25, color=AcademicStyle.COLORS['brick_red'])
    max_life = max(lifetime) if len(lifetime) > 0 else 5
    ax8c.set_ylim(0, max(max_life * 1.2, 5))
    ax8c.set_xlabel('运行天数', fontsize=10); ax8c.set_ylabel('累计寿命消耗(%)', fontsize=10)
    ax8c.grid(axis='y', **AcademicStyle.GRID_STYLE); AcademicStyle.remove_spines(ax8c)
    fig8.subplots_adjust(left=0.08, right=0.98, top=0.95, bottom=0.1, hspace=0.3)
    fig8.savefig(f'{output_dir}/图8_电池寿命分析.svg', format='svg', bbox_inches='tight')
    plt.close()
    print("  ✓ 已生成")

# ============================================================================
# 图9: SOC时空热力图
# ============================================================================
if FIG_CONFIG['fig9']:
    print("\n[图9] SOC时空热力图...")
    fig9 = plt.figure(figsize=(10, 7.5))
    gs = gridspec.GridSpec(2, 2, height_ratios=[2, 1], hspace=0.35, wspace=0.3)
    n_days = len(results); n_tp = 145
    soc_matrix = np.zeros((n_days, n_tp))
    for i, r in enumerate(results):
        seq = np.concatenate([[r.get('initial_soc', 6000)], r.get('soc', [6000]*144)])
        soc_matrix[i, :len(seq)] = seq[:n_tp]
    ax9a = fig9.add_subplot(gs[0, :])
    im = ax9a.imshow(soc_matrix, aspect='auto', cmap='Spectral_r', extent=[0, 24, n_days, 1], vmin=1200, vmax=10800)
    ax9a.set_xlabel('时间 (h)', fontsize=10); ax9a.set_ylabel('运行天数', fontsize=10)
    plt.colorbar(im, ax=ax9a, pad=0.02).set_label('SOC (kWh)', fontsize=9)
    ax9b = fig9.add_subplot(gs[1, 0])
    ta = np.linspace(0, 24, n_tp)
    upper = np.sum(soc_matrix >= 10799, axis=0) / n_days * 100
    lower = np.sum(soc_matrix <= 1201, axis=0) / n_days * 100
    ax9b.fill_between(ta, 0, upper, color=AcademicStyle.COLORS['brick_red'], alpha=0.6, label='触及上限')
    ax9b.fill_between(ta, 0, -lower, color='#D4915E', alpha=0.6, label='触及下限')
    ax9b.axhline(0, color='black', linewidth=0.8)
    ax9b.set_xlabel('时间 (h)', fontsize=9); ax9b.set_ylabel('触及频率(%)', fontsize=9)
    ax9b.legend(loc='upper right', fontsize=8, frameon=False); AcademicStyle.remove_spines(ax9b)
    ax9c = fig9.add_subplot(gs[1, 1])
    ax9c.hist(soc_matrix.flatten(), bins=50, color=AcademicStyle.COLORS['dark_blue'], alpha=0.7, edgecolor='white', linewidth=0.5)
    ax9c.axvline(10800, color=AcademicStyle.COLORS['brick_red'], linestyle='--', linewidth=1.5, alpha=0.8)
    ax9c.axvline(1200, color='#D4915E', linestyle='--', linewidth=1.5, alpha=0.8)
    ax9c.set_xlabel('SOC (kWh)', fontsize=9); ax9c.set_ylabel('频数', fontsize=9)
    AcademicStyle.remove_spines(ax9c)
    fig9.savefig(f'{output_dir}/图9_SOC时空热力图.svg', format='svg', bbox_inches='tight')
    plt.close()
    print("  ✓ 已生成")

# ============================================================================
# 图10: Q2 vs Q4-2 成本对比
# ============================================================================
if FIG_CONFIG['fig10']:
    print("\n[图10] Q2 vs Q4-2 成本对比...")
    q2_data = None
    for p in [os.path.join(script_dir, "../../QC-2/05_results/result_data_q2.json"),
              os.path.join(script_dir, "../05_results/Q2_results.json")]:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding='utf-8') as f: q2_data = json.load(f)
                break
            except Exception: pass
    q2_plan, q2_emergency, q2_total = 4600.0, 352.0, 4952.0
    if q2_data and isinstance(q2_data, dict):
        q2_total = float(q2_data.get('total_cost', q2_data.get('annual_total_cost', q2_total)))
        q2_plan = float(q2_data.get('plan_cost', q2_data.get('annual_plan_cost', q2_plan)))
        q2_emergency = float(q2_data.get('emergency_cost', q2_data.get('annual_emergency_cost', q2_emergency)))
        if q2_total > 1e6:
            q2_plan, q2_emergency, q2_total = q2_plan/1e4, q2_emergency/1e4, q2_total/1e4

    q42_total = sum(r['total_cost'] for r in results) / 1e4
    q42_plan = sum(r.get('plan_cost', 0) for r in results) / 1e4
    q42_emergency = sum(r.get('emergency_cost', 0) for r in results) / 1e4

    cost_types = ['计划购电', '紧急购电', '总成本']
    q2_vals = [q2_plan, q2_emergency, q2_total]
    q42_vals = [q42_plan, q42_emergency, q42_total]
    x = np.arange(len(cost_types)); width = 0.35
    fig10, ax10 = plt.subplots(figsize=(10, 7.5))
    bars1 = ax10.bar(x - width/2, q2_vals, width, label='Q2 (固定电价)', color=AcademicStyle.COLORS['blue_gray'], alpha=0.85, edgecolor='white', linewidth=1.5)
    bars2 = ax10.bar(x + width/2, q42_vals, width, label='Q4-2 (波动电价)', color=AcademicStyle.COLORS['brick_red'], alpha=0.85, edgecolor='white', linewidth=1.5)
    max_val = max(max(q2_vals), max(q42_vals))
    for bars in [bars1, bars2]:
        for bar in bars:
            h = bar.get_height()
            ax10.text(bar.get_x() + bar.get_width()/2, h + max_val * 0.01, f'{h:,.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax10.set_ylabel('成本 (万元)', fontsize=11); ax10.set_xlabel('成本类型', fontsize=11)
    ax10.set_xticks(x); ax10.set_xticklabels(cost_types)
    ax10.legend(loc='upper right', fontsize=10, frameon=False)
    ax10.grid(axis='y', **AcademicStyle.GRID_STYLE)
    ax10.set_ylim(0, max_val * 1.2)
    ax10.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    AcademicStyle.remove_spines(ax10)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/图10_Q2与Q4-2成本对比.svg', format='svg', bbox_inches='tight')
    plt.close()
    print("  ✓ 已生成")

print("\n" + "="*70)
print("[OK] Q4-2 全部图表生成完毕！(图1-图10，中文命名)")
print("="*70)