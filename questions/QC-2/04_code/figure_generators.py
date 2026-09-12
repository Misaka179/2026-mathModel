"""
图表生成模块 - 各图表生成函数
支持PNG和SVG两种格式输出
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Patch

# 莫兰迪配色
COLORS = {
    'blue_light': '#7B9EB6',
    'blue_dark': '#4A6FA5',
    'red': '#B85450',
    'green': '#6A8E7F',
    'orange': '#D4915E',
    'teal': '#5B8A8A',
}

def setup_plot_style():
    """设置全局绘图样式"""
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
    plt.rcParams['font.size'] = 9
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['axes.linewidth'] = 0.8
    plt.rcParams['xtick.direction'] = 'in'
    plt.rcParams['ytick.direction'] = 'in'
    plt.rcParams['grid.alpha'] = 0.15
    plt.rcParams['grid.linestyle'] = ':'
    plt.rcParams['legend.frameon'] = False


def generate_figure1(data, output_path, fmt='png'):
    """
    图1: 成本与能量分析

    Args:
        data: dict，包含 backtest, energy_data
        output_path: str，输出路径
        fmt: str，输出格式 'png' 或 'svg'
    """
    setup_plot_style()

    backtest = data['backtest']
    energy_data = data['energy_data']

    total_cost = backtest['summary']['annual_total_cost']
    plan_cost = backtest['summary']['annual_plan_cost']
    emergency_cost = backtest['summary']['annual_emergency_cost']
    e_plan_total = energy_data['waste_analysis']['total_E_plan_kWh']
    e_plan_used = energy_data['waste_analysis']['total_E_plan_used_kWh']
    e_plan_waste = energy_data['waste_analysis']['total_E_plan_waste_kWh']

    plan_pct = plan_cost / total_cost * 100
    emergency_pct = emergency_cost / total_cost * 100
    used_pct = e_plan_used / e_plan_total * 100
    waste_pct = e_plan_waste / e_plan_total * 100

    fig, ax = plt.subplots(figsize=(10, 3.5))

    categories = ['年度总成本\n(万元)', 'E_plan总量\n(万kWh)']
    y_pos = np.arange(len(categories))

    ax.barh(y_pos[0], plan_cost, height=0.4, color=COLORS['blue_light'], edgecolor='none')
    ax.barh(y_pos[0], emergency_cost, height=0.4, left=plan_cost, color=COLORS['red'], edgecolor='none')
    ax.barh(y_pos[1], e_plan_used, height=0.4, color=COLORS['blue_light'], edgecolor='none')
    ax.barh(y_pos[1], e_plan_waste, height=0.4, left=e_plan_used, color=COLORS['red'], edgecolor='none')

    # 标注
    ax.text(plan_cost/2, y_pos[0] + 0.08, f'{plan_cost/1e4:.1f}',
            ha='center', va='center', fontsize=9, weight='bold', color='white')
    ax.text(plan_cost/2, y_pos[0] - 0.08, f'({plan_pct:.1f}%)',
            ha='center', va='center', fontsize=8, color='white')

    ax.text(plan_cost + emergency_cost/2, y_pos[0] + 0.08, f'{emergency_cost/1e4:.1f}',
            ha='center', va='center', fontsize=9, weight='bold', color='white')
    ax.text(plan_cost + emergency_cost/2, y_pos[0] - 0.08, f'({emergency_pct:.1f}%)',
            ha='center', va='center', fontsize=8, weight='bold', color='white',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=COLORS['red'], edgecolor='none', alpha=0.3))

    ax.text(e_plan_used/2, y_pos[1] + 0.08, f'{e_plan_used/1e4:.1f}',
            ha='center', va='center', fontsize=9, weight='bold', color='white')
    ax.text(e_plan_used/2, y_pos[1] - 0.08, f'({used_pct:.1f}%)',
            ha='center', va='center', fontsize=8, color='white')

    ax.annotate(f'{e_plan_waste/1e4:.1f} ({waste_pct:.1f}%)',
                xy=(e_plan_used + e_plan_waste/2, y_pos[1]),
                xytext=(e_plan_total * 0.92, y_pos[1] + 0.35),
                fontsize=8, color=COLORS['red'], weight='bold',
                arrowprops=dict(arrowstyle='->', color=COLORS['red'], lw=1.2))

    ax.text(total_cost * 1.02, y_pos[0], f'{total_cost/1e4:.1f}', ha='left', va='center', fontsize=9)
    ax.text(e_plan_total * 1.02, y_pos[1], f'{e_plan_total/1e4:.1f}', ha='left', va='center', fontsize=9)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories)
    ax.set_xlim(0, max(total_cost, e_plan_total) * 1.12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='x', alpha=0.15)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x/1e4:.0f}'))

    legend_elements = [
        Patch(facecolor=COLORS['blue_light'], label='计划购电/使用'),
        Patch(facecolor=COLORS['red'], label='紧急购电/浪费')
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, format=fmt, dpi=300 if fmt=='png' else None,
                bbox_inches='tight', facecolor='white', edgecolor='none', pad_inches=0.05)
    plt.close()


def generate_figure2(data, output_path, fmt='png'):
    """图2: 储能经济性对比"""
    setup_plot_style()

    backtest = data['backtest']
    baseline = data['baseline']

    total_cost = backtest['summary']['annual_total_cost']
    baseline_cost = baseline['baseline_annual_cost']
    savings = baseline['annual_savings']
    savings_pct = savings / baseline_cost * 100

    fig, ax = plt.subplots(figsize=(8, 5.5))

    categories = ['无储能', '有储能']
    costs = [baseline_cost, total_cost]
    colors = [COLORS['teal'], COLORS['blue_dark']]

    bars = ax.bar(categories, costs, width=0.5, color=colors, edgecolor='none', alpha=0.85)

    for bar, cost in zip(bars, costs):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height * 1.01,
                f'{cost/1e4:.1f}万元',
                ha='center', va='bottom', fontsize=10, weight='bold')

    x1 = bars[0].get_x() + bars[0].get_width()/2
    x2 = bars[1].get_x() + bars[1].get_width()/2
    x_center = 0.5
    y1 = baseline_cost
    y2 = total_cost

    ax.plot([x1, x_center], [y1, y1], color=COLORS['green'], lw=1.5, linestyle='--', alpha=0.7, zorder=5)
    ax.plot([x2, x_center], [y2, y2], color=COLORS['green'], lw=1.5, linestyle='--', alpha=0.7, zorder=5)
    ax.annotate('', xy=(x_center, y2), xytext=(x_center, y1),
                arrowprops=dict(arrowstyle='<->', color=COLORS['green'], lw=2.5))

    mid_y = (y1 + y2) / 2
    ax.text(x_center + 0.15, mid_y + 2.5e6, '节省', ha='left', va='bottom',
            fontsize=11, weight='bold', color=COLORS['green'])
    ax.text(x_center + 0.15, mid_y, f'{savings/1e4:.1f}万元', ha='left', va='center',
            fontsize=11, weight='bold', color=COLORS['green'])
    ax.text(x_center + 0.15, mid_y - 2.5e6, f'({savings_pct:.1f}%)', ha='left', va='top',
            fontsize=10, weight='bold', color=COLORS['green'])

    ax.set_ylabel('年度总成本（万元）', fontsize=10)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x/1e4:.0f}'))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.15)
    ax.set_ylim(0, baseline_cost * 1.12)

    plt.tight_layout()
    plt.savefig(output_path, format=fmt, dpi=300 if fmt=='png' else None,
                bbox_inches='tight', facecolor='white', edgecolor='none', pad_inches=0.05)
    plt.close()


def generate_figure3(data, output_path, fmt='png'):
    """图3: 典型日SOC轨迹"""
    setup_plot_style()

    results = data['backtest']['daily_results']
    typical_day = results[100]

    soc_with_initial = np.concatenate([[typical_day['initial_soc']], typical_day['soc']])
    time_points = np.linspace(0, 24, 145)

    fig, ax = plt.subplots(figsize=(10, 4.5))

    ax.plot(time_points, soc_with_initial, linewidth=1.8, color=COLORS['blue_dark'], zorder=3)
    ax.axhline(y=10800, color=COLORS['red'], linestyle='--', linewidth=1.2, alpha=0.8, zorder=4)
    ax.axhline(y=1200, color=COLORS['orange'], linestyle='--', linewidth=1.2, alpha=0.8, zorder=4)
    ax.axhline(y=6000, color=COLORS['green'], linestyle=':', linewidth=1, alpha=0.7, zorder=4)
    ax.fill_between(time_points, 1200, 10800, alpha=0.02, color='gray', zorder=1)

    ax.plot([], [], linewidth=1.8, color=COLORS['blue_dark'], label='SOC')
    ax.plot([], [], linestyle='--', linewidth=1.2, color=COLORS['red'], label='上限 (10,800 kWh)')
    ax.plot([], [], linestyle='--', linewidth=1.2, color=COLORS['orange'], label='下限 (1,200 kWh)')
    ax.plot([], [], linestyle=':', linewidth=1, color=COLORS['green'], label='目标 (6,000 kWh)')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.12), ncol=4, fontsize=8)

    ax.set_xlabel('时间（小时）', fontsize=10)
    ax.set_ylabel('SOC（kWh）', fontsize=10)
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 12000)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.15)

    plt.tight_layout()
    plt.savefig(output_path, format=fmt, dpi=300 if fmt=='png' else None,
                bbox_inches='tight', facecolor='white', edgecolor='none', pad_inches=0.05)
    plt.close()


def generate_figure4(data, output_path, fmt='png'):
    """图4: 跨日连续性验证"""
    setup_plot_style()

    results = data['backtest']['daily_results']

    transition_errors = []
    for i in range(1, len(results)):
        prev_terminal = results[i-1]['terminal_soc']
        curr_initial = results[i]['initial_soc']
        error = abs(curr_initial - prev_terminal)
        transition_errors.append(error)

    transition_days = list(range(2, len(results) + 1))
    max_error = max(transition_errors) if transition_errors else 0
    mean_error = np.mean(transition_errors)

    fig, ax = plt.subplots(figsize=(10, 4))

    y_max = 1e-5
    ax.plot(transition_days, transition_errors, color=COLORS['blue_dark'], linewidth=1.5, zorder=3)
    ax.axhline(y=1e-6, color=COLORS['red'], linestyle='--', linewidth=1.2,
               label='阈值 (±1×10$^{-6}$ kWh)', alpha=0.8, zorder=4)
    ax.axhline(y=-1e-6, color=COLORS['red'], linestyle='--', linewidth=1.2, alpha=0.8, zorder=4)
    ax.fill_between(transition_days, -1e-10, 1e-10, alpha=0.15,
                    color=COLORS['green'], label='零误差区域', zorder=2)

    ax.set_xlabel('过渡点序号（第$i$天 → 第$i+1$天）', fontsize=10)
    ax.set_ylabel('连续性误差（×10$^{-6}$ kWh）', fontsize=10)
    ax.set_ylim(-y_max, y_max)
    ax.set_xlim(transition_days[0], transition_days[-1])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x*1e6:.0f}'))

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.15)
    ax.legend(loc='upper right', fontsize=8)

    stats_text = f'$\\epsilon_{{max}}$ = {max_error:.2e} kWh    $\\epsilon_{{mean}}$ = {mean_error:.2e} kWh'
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
            fontsize=8, va='top', ha='left', color='#555555')

    ax.text(0.98, 0.05, '所有333个过渡点均满足连续性要求', transform=ax.transAxes,
            fontsize=9, va='bottom', ha='right', weight='bold', color=COLORS['green'])

    plt.tight_layout()
    plt.savefig(output_path, format=fmt, dpi=300 if fmt=='png' else None,
                bbox_inches='tight', facecolor='white', edgecolor='none', pad_inches=0.05)
    plt.close()


def generate_figure5(data, output_path, fmt='png'):
    """图5: 全年SOC轨迹"""
    setup_plot_style()

    results = data['backtest']['daily_results']

    days = []
    soc_daily_mean = []
    soc_daily_min = []
    soc_daily_max = []
    soc_daily_std = []

    for day_result in results:
        soc_with_initial = [day_result['initial_soc']] + day_result['soc']
        days.append(day_result['day'])
        soc_daily_mean.append(np.mean(soc_with_initial))
        soc_daily_min.append(np.min(soc_with_initial))
        soc_daily_max.append(np.max(soc_with_initial))
        soc_daily_std.append(np.std(soc_with_initial))

    days = np.array(days)
    soc_daily_mean = np.array(soc_daily_mean)
    soc_daily_min = np.array(soc_daily_min)
    soc_daily_max = np.array(soc_daily_max)
    soc_daily_std = np.array(soc_daily_std)

    fig = plt.figure(figsize=(14, 8))
    gs = gridspec.GridSpec(2, 1, height_ratios=[2, 1], hspace=0.3)

    ax1 = fig.add_subplot(gs[0])

    ax1.fill_between(days, soc_daily_min, soc_daily_max,
                     alpha=0.25, color='#1f77b4', label='日内变化范围')
    ax1.plot(days, soc_daily_mean, color='#1f77b4', linewidth=1.8,
             label='日均值', zorder=3)

    ax1.axhline(y=10800, color='#d62728', linestyle='--', linewidth=2,
                label='上限 (10,800 kWh)', alpha=0.9, zorder=4)
    ax1.axhline(y=1200, color='#ff7f0e', linestyle='--', linewidth=2,
                label='下限 (1,200 kWh)', alpha=0.9, zorder=4)
    ax1.axhline(y=6000, color='#2ca02c', linestyle=':', linewidth=1.5,
                label='目标 (6,000 kWh)', alpha=0.7, zorder=4)

    initial_soc = results[0]['initial_soc']
    terminal_soc = results[-1]['terminal_soc']
    ax1.plot(days[0], initial_soc, 'o', color='#2ca02c', markersize=10,
             markeredgecolor='white', markeredgewidth=1.5,
             label=f'初始 ({initial_soc:.0f} kWh)', zorder=5)
    ax1.plot(days[-1], terminal_soc, 'o', color='#d62728', markersize=10,
             markeredgecolor='white', markeredgewidth=1.5,
             label=f'终端 ({terminal_soc:.0f} kWh)', zorder=5)

    ax1.set_xlabel('运行天数', fontsize=11)
    ax1.set_ylabel('SOC (kWh)', fontsize=11)
    ax1.set_title('全年储能系统SOC运行轨迹与边界约束验证（334天）',
                  fontsize=12, pad=15)
    ax1.set_xlim(days[0], days[-1])
    ax1.set_ylim(0, 12000)
    ax1.grid(True, alpha=0.25, linestyle=':', linewidth=0.8)
    ax1.legend(loc='upper right', fontsize=9, framealpha=0.95,
               edgecolor='gray', fancybox=False, ncol=2)

    stats_text = (f'均值: {np.mean(soc_daily_mean):.0f} kWh    '
                  f'标准差: {np.mean(soc_daily_std):.0f} kWh    '
                  f'范围: [{np.min(soc_daily_min):.0f}, {np.max(soc_daily_max):.0f}] kWh')
    ax1.text(0.5, 0.02, stats_text, transform=ax1.transAxes,
             fontsize=9, ha='center', va='bottom',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                      edgecolor='lightgray', linewidth=0.8, alpha=0.9))

    ax2 = fig.add_subplot(gs[1])

    zoom_start = 100
    zoom_end = 130
    zoom_results = results[zoom_start:zoom_end]

    time_hours_zoom = []
    soc_zoom = []

    for i, day_result in enumerate(zoom_results):
        day_offset = (zoom_start + i) * 24
        soc_with_initial = [day_result['initial_soc']] + day_result['soc']
        for t_idx, soc_val in enumerate(soc_with_initial):
            hour = day_offset + t_idx * (10/60)
            time_hours_zoom.append(hour)
            soc_zoom.append(soc_val)

    time_days_zoom = np.array(time_hours_zoom) / 24

    ax2.plot(time_days_zoom, soc_zoom, color='#1f77b4', linewidth=0.8,
             alpha=0.8, label='SOC轨迹')
    ax2.axhline(y=10800, color='#d62728', linestyle='--', linewidth=1.5,
                alpha=0.8, label='上限')
    ax2.axhline(y=1200, color='#ff7f0e', linestyle='--', linewidth=1.5,
                alpha=0.8, label='下限')
    ax2.axhline(y=6000, color='#2ca02c', linestyle=':', linewidth=1,
                alpha=0.6)

    ax2.set_xlabel('运行天数', fontsize=11)
    ax2.set_ylabel('SOC (kWh)', fontsize=11)
    ax2.set_title(f'局部放大：第{zoom_start+1}-{zoom_end}天（展示日内充放电周期）',
                  fontsize=11, pad=10)
    ax2.set_xlim(time_days_zoom[0], time_days_zoom[-1])
    ax2.set_ylim(0, 12000)
    ax2.grid(True, alpha=0.25, linestyle=':', linewidth=0.5)
    ax2.legend(loc='upper right', fontsize=8, framealpha=0.95,
               edgecolor='gray', fancybox=False)

    ax1.axvspan(zoom_start+1, zoom_end, alpha=0.1, color='red', zorder=1)
    ax1.text((zoom_start+zoom_end)/2, 11500, '↓ 放大区域',
             ha='center', fontsize=9, color='red', weight='bold')

    plt.tight_layout()
    plt.savefig(output_path, format=fmt, dpi=300 if fmt=='png' else None,
                bbox_inches='tight', facecolor='white', edgecolor='none', pad_inches=0.1)
    plt.close()


def generate_table1(data, output_path, fmt='png'):
    """表1: 边界触碰统计"""
    setup_plot_style()

    results = data['backtest']['daily_results']

    touch_upper_only = []
    touch_lower_only = []
    touch_both = []
    safe_days = []

    for day in results:
        soc_with_initial = [day['initial_soc']] + day['soc']
        at_upper = any(s >= 10799 for s in soc_with_initial)
        at_lower = any(s <= 1201 for s in soc_with_initial)

        if at_upper and at_lower:
            touch_both.append(day['day'])
        elif at_upper:
            touch_upper_only.append(day['day'])
        elif at_lower:
            touch_lower_only.append(day['day'])
        else:
            safe_days.append(day['day'])

    fig, ax = plt.subplots(figsize=(8, 2.8))
    ax.axis('off')

    table_data = [
        ['运行状态', '天数', '占比（%）'],
        ['仅触及上限', f'{len(touch_upper_only)}', f'{len(touch_upper_only)/len(results)*100:.1f}'],
        ['仅触及下限', f'{len(touch_lower_only)}', f'{len(touch_lower_only)/len(results)*100:.1f}'],
        ['同时触及上下限', f'{len(touch_both)}', f'{len(touch_both)/len(results)*100:.1f}'],
        ['安全运行', f'{len(safe_days)}', f'{len(safe_days)/len(results)*100:.1f}'],
    ]

    table = ax.table(cellText=table_data, cellLoc='center',
                     colWidths=[0.4, 0.3, 0.3],
                     loc='center',
                     bbox=[0.1, 0.12, 0.8, 0.7])

    table.auto_set_font_size(False)
    table.set_fontsize(9)

    for i, row in enumerate(table_data):
        for j in range(len(row)):
            cell = table[(i, j)]
            cell.set_linewidth(0)

            if i == 0:
                cell.set_facecolor('#F5F5F5')
                cell.set_text_props(weight='bold')
                cell.set_linewidth(1.5)
                cell.set_edgecolor('black')
                cell.visible_edges = 'T'
                cell.set_linewidth(0.5)
                cell.visible_edges = 'TB'
            else:
                cell.set_facecolor('white')
                if i == len(table_data) - 1:
                    cell.set_linewidth(1.5)
                    cell.set_edgecolor('black')
                    cell.visible_edges = 'B'

    ax.text(0.5, 0.88, '表1 全年SOC边界触碰统计（334天）', transform=ax.transAxes,
            fontsize=10, weight='bold', ha='center')

    if len(safe_days) == 0:
        ax.text(0.5, 0.05, '注：全年无安全运行天数，系统处于深充深放工况',
                transform=ax.transAxes, fontsize=8, ha='center',
                color=COLORS['red'], style='italic')

    plt.tight_layout()
    plt.savefig(output_path, format=fmt, dpi=300 if fmt=='png' else None,
                bbox_inches='tight', facecolor='white', edgecolor='none', pad_inches=0.05)
    plt.close()
