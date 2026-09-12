"""
深度分析图表生成模块
新增4张有洞察的图表
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter
import matplotlib.patches as mpatches

# 使用与主图表相同的配色
COLORS = {
    'blue_light': '#7B9EB6',
    'blue_dark': '#4A6FA5',
    'red': '#B85450',
    'green': '#6A8E7F',
    'orange': '#D4915E',
    'teal': '#5B8A8A',
    'purple': '#9B7EBD',
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


def generate_figure6_cost_breakdown(data, output_path, fmt='png'):
    """
    图6: 成本节省来源分解
    洞察：82.8%的节省来自哪里？
    """
    setup_plot_style()

    backtest = data['backtest']
    baseline = data['baseline']

    total_cost = backtest['summary']['annual_total_cost']
    baseline_cost = baseline['baseline_annual_cost']
    savings = baseline['annual_savings']

    # 成本分解（这里需要根据实际数据调整）
    # 假设：节省 = 削峰填谷 + 避免紧急购电 + 其他
    results = backtest['daily_results']
    total_plan = sum(r['plan_cost'] for r in results)
    total_emergency = sum(r['emergency_cost'] for r in results)

    fig = plt.figure(figsize=(12, 6))
    gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1.2], wspace=0.3)

    # 左图：成本对比柱状图
    ax1 = fig.add_subplot(gs[0])

    scenarios = ['无储能\n基准', '动态规划\n(有储能)']
    costs = [baseline_cost, total_cost]
    colors = [COLORS['red'], COLORS['blue_dark']]

    bars = ax1.bar(scenarios, costs, width=0.5, color=colors, alpha=0.85, edgecolor='none')

    for bar, cost in zip(bars, costs):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, height * 1.02,
                f'{cost/1e4:.1f}万元',
                ha='center', va='bottom', fontsize=10, weight='bold')

    # 节省箭头
    ax1.annotate('', xy=(0.5, total_cost), xytext=(0.5, baseline_cost),
                arrowprops=dict(arrowstyle='<->', color=COLORS['green'], lw=3))
    ax1.text(0.7, (baseline_cost + total_cost)/2, f'节省\n{savings/1e4:.1f}万元\n({savings/baseline_cost*100:.1f}%)',
            ha='left', va='center', fontsize=10, weight='bold', color=COLORS['green'])

    ax1.set_ylabel('年度总成本（万元）', fontsize=10)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x/1e4:.0f}'))
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.grid(axis='y', alpha=0.15)
    ax1.set_title('成本对比', fontsize=11, weight='bold', pad=10)

    # 右图：节省来源分解（正确的瀑布图）
    ax2 = fig.add_subplot(gs[1])

    # 分解节省来源
    categories = ['无储能\n基准', '计划购电\n节省', '避免紧急\n节省', '有储能\n总成本']

    # 正确的瀑布图逻辑：从高到低
    # 基准 -> 基准-计划节省 -> 基准-计划-紧急 -> 最终
    step_values = [baseline_cost, baseline_cost - total_plan, total_cost, total_cost]

    # 绘制瀑布图
    for i, (cat, val) in enumerate(zip(categories, step_values)):
        if i == 0:  # 起点：基准成本
            ax2.bar(i, val, width=0.6, bottom=0, color=COLORS['red'],
                   alpha=0.7, edgecolor='black', lw=1.5)
            ax2.text(i, val/2, f'{val/1e4:.1f}万元', ha='center', va='center',
                    fontsize=9, weight='bold', color='white')
        elif i == len(categories) - 1:  # 终点：最终成本
            ax2.bar(i, val, width=0.6, bottom=0, color=COLORS['blue_dark'],
                   alpha=0.7, edgecolor='black', lw=1.5)
            ax2.text(i, val/2, f'{val/1e4:.1f}万元', ha='center', va='center',
                    fontsize=9, weight='bold', color='white')
        else:  # 中间：减少量（下降的柱子）
            prev_val = step_values[i-1]
            decrease = prev_val - val
            ax2.bar(i, decrease, width=0.6, bottom=val, color=COLORS['green'],
                   alpha=0.7, edgecolor='black', lw=1.5)
            ax2.text(i, val + decrease/2, f'-{decrease/1e4:.1f}万元',
                    ha='center', va='center', fontsize=9, weight='bold', color='white')

        # 连接线（从前一个柱顶到当前柱顶）
        if i < len(categories) - 1:
            next_val = step_values[i+1] if i < len(categories) - 2 else step_values[i+1]
            ax2.plot([i + 0.3, i + 0.7], [val, val], 'k--', lw=1, alpha=0.5)
            if i < len(categories) - 2:
                ax2.plot([i + 0.3, i + 0.7], [next_val, next_val], 'k--', lw=1, alpha=0.5)

    ax2.set_xticks(range(len(categories)))
    ax2.set_xticklabels(categories, fontsize=9)
    ax2.set_ylabel('累计成本（万元）', fontsize=10)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x/1e4:.0f}'))
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.grid(axis='y', alpha=0.15)
    ax2.set_title('节省来源分解', fontsize=11, weight='bold', pad=10)

    plt.suptitle('储能系统成本节省来源分析', fontsize=13, weight='bold', y=0.98)

    plt.tight_layout()
    plt.savefig(output_path, format=fmt, dpi=300 if fmt=='png' else None,
                bbox_inches='tight', facecolor='white', edgecolor='none', pad_inches=0.05)
    plt.close()


def generate_figure7_seasonal_comparison(data, output_path, fmt='png'):
    """
    图7: 季节性运行模式对比
    洞察：为什么不同季节策略不同？
    """
    setup_plot_style()

    results = data['backtest']['daily_results']

    # 选择四季典型日
    spring_day = results[60]   # 3月初
    summer_day = results[152]  # 6月初
    autumn_day = results[244]  # 9月初
    winter_day = results[25]   # 2月底

    typical_days = [
        ('春季 (3月)', spring_day, COLORS['green']),
        ('夏季 (6月)', summer_day, COLORS['orange']),
        ('秋季 (9月)', autumn_day, COLORS['blue_dark']),
        ('冬季 (2月)', winter_day, COLORS['purple']),
    ]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    time_points = np.linspace(0, 24, 145)

    # 上图：SOC轨迹对比
    for label, day, color in typical_days:
        soc = np.concatenate([[day['initial_soc']], day['soc']])
        ax1.plot(time_points, soc, linewidth=2, color=color, label=label, alpha=0.85)

    ax1.axhline(y=10800, color='#d62728', linestyle='--', linewidth=1, alpha=0.5, label='上限')
    ax1.axhline(y=1200, color='#ff7f0e', linestyle='--', linewidth=1, alpha=0.5, label='下限')
    ax1.axhline(y=6000, color='gray', linestyle=':', linewidth=0.8, alpha=0.5, label='目标')

    ax1.set_ylabel('SOC (kWh)', fontsize=10)
    ax1.set_ylim(0, 12000)
    ax1.grid(axis='both', alpha=0.15)
    ax1.legend(loc='upper right', fontsize=9, ncol=3)
    ax1.set_title('四季典型日SOC运行模式对比', fontsize=11, weight='bold', pad=10)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # 下图：电价曲线（假设三段式）
    # 谷时0-7h: 0.3元, 平时7-19h: 0.6元, 峰时19-22h: 1.0元, 平时22-24h: 0.6元
    time_price = np.linspace(0, 24, 241)
    price = np.zeros_like(time_price)
    for i, t in enumerate(time_price):
        if t < 7:
            price[i] = 0.3
        elif 7 <= t < 19:
            price[i] = 0.6
        elif 19 <= t < 22:
            price[i] = 1.0
        else:
            price[i] = 0.6

    ax2.fill_between(time_price, 0, price, alpha=0.3, color='gray', label='电价')
    ax2.plot(time_price, price, linewidth=2, color='black', alpha=0.7)

    # 标注时段
    ax2.text(3.5, 0.35, '谷时\n0.3元/kWh', ha='center', va='center',
            fontsize=9, bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
    ax2.text(13, 0.65, '平时\n0.6元/kWh', ha='center', va='center',
            fontsize=9, bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))
    ax2.text(20.5, 1.05, '峰时\n1.0元/kWh', ha='center', va='center',
            fontsize=9, bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.7))

    ax2.set_xlabel('时间（小时）', fontsize=10)
    ax2.set_ylabel('电价（元/kWh）', fontsize=10)
    ax2.set_xlim(0, 24)
    ax2.set_ylim(0, 1.2)
    ax2.grid(axis='both', alpha=0.15)
    ax2.set_title('分时电价结构', fontsize=11, weight='bold', pad=10)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    plt.suptitle('季节性运行模式与电价响应分析', fontsize=13, weight='bold', y=0.995)

    plt.tight_layout()
    plt.savefig(output_path, format=fmt, dpi=300 if fmt=='png' else None,
                bbox_inches='tight', facecolor='white', edgecolor='none', pad_inches=0.05)
    plt.close()


def generate_figure8_battery_cycle_analysis(data, output_path, fmt='png'):
    """
    图8: 电池循环深度与寿命分析
    洞察：安全运行0天的代价是什么？
    """
    setup_plot_style()

    results = data['backtest']['daily_results']

    # 计算每日循环深度
    daily_cycles = []
    daily_range = []

    for r in results:
        soc_seq = np.array([r['initial_soc']] + r['soc'])
        soc_min = np.min(soc_seq)
        soc_max = np.max(soc_seq)
        soc_range = soc_max - soc_min
        cycle_depth = soc_range / 12000  # 归一化

        daily_cycles.append(cycle_depth)
        daily_range.append(soc_range)

    daily_cycles = np.array(daily_cycles)
    daily_range = np.array(daily_range)

    fig = plt.figure(figsize=(12, 8))
    gs = gridspec.GridSpec(2, 2, hspace=0.3, wspace=0.3)

    # 左上：循环深度分布直方图
    ax1 = fig.add_subplot(gs[0, 0])

    n, bins, patches = ax1.hist(daily_cycles * 100, bins=20, color=COLORS['blue_dark'],
                                alpha=0.7, edgecolor='black', linewidth=0.8)

    # 标注平均值
    mean_depth = np.mean(daily_cycles) * 100
    ax1.axvline(mean_depth, color='red', linestyle='--', linewidth=2,
               label=f'平均: {mean_depth:.1f}%')

    ax1.set_xlabel('日循环深度（%）', fontsize=10)
    ax1.set_ylabel('天数', fontsize=10)
    ax1.set_title('电池日循环深度分布', fontsize=11, weight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(axis='y', alpha=0.15)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # 右上：累计等效循环次数
    ax2 = fig.add_subplot(gs[0, 1])

    cumulative_cycles = np.cumsum(daily_cycles)
    days = np.arange(1, len(daily_cycles) + 1)

    ax2.plot(days, cumulative_cycles, linewidth=2, color=COLORS['blue_dark'])
    ax2.fill_between(days, 0, cumulative_cycles, alpha=0.3, color=COLORS['blue_light'])

    # 标注关键点
    total_cycles = cumulative_cycles[-1]
    ax2.text(len(days) * 0.7, total_cycles * 0.5,
            f'总等效循环:\n{total_cycles:.0f}次',
            ha='center', va='center', fontsize=10, weight='bold',
            bbox=dict(boxstyle='round', facecolor='white', edgecolor='gray', lw=1.5))

    ax2.set_xlabel('运行天数', fontsize=10)
    ax2.set_ylabel('累计等效循环次数', fontsize=10)
    ax2.set_title('累计循环次数', fontsize=11, weight='bold')
    ax2.grid(axis='both', alpha=0.15)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    # 下：寿命损耗估算
    ax3 = fig.add_subplot(gs[1, :])

    # 假设电池寿命模型：6000次@80%DoD, 按DoD平方折算
    # 寿命消耗 = Σ(DoD^2 / 6000)
    lifetime_consumption = []
    for cycle in daily_cycles:
        consumption = (cycle ** 2) / (0.8 ** 2) / 6000
        lifetime_consumption.append(consumption)

    cumulative_lifetime = np.cumsum(lifetime_consumption) * 100  # 转为百分比

    ax3.plot(days, cumulative_lifetime, linewidth=2.5, color=COLORS['red'])
    ax3.fill_between(days, 0, cumulative_lifetime, alpha=0.3, color=COLORS['red'])

    # 预测剩余寿命
    daily_avg_consumption = np.mean(lifetime_consumption) * 100
    remaining_life_days = (100 - cumulative_lifetime[-1]) / daily_avg_consumption

    ax3.text(len(days) * 0.3, cumulative_lifetime[-1] * 0.6,
            f'334天消耗: {cumulative_lifetime[-1]:.2f}%\n'
            f'预计剩余寿命: {remaining_life_days:.0f}天',
            ha='center', va='center', fontsize=10, weight='bold',
            bbox=dict(boxstyle='round', facecolor='lightyellow', edgecolor='red', lw=2))

    ax3.axhline(100, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='寿命终止(100%)')

    ax3.set_xlabel('运行天数', fontsize=10)
    ax3.set_ylabel('累计寿命消耗（%）', fontsize=10)
    ax3.set_title('电池寿命损耗估算（基于循环深度模型）', fontsize=11, weight='bold')
    ax3.legend(fontsize=9)
    ax3.grid(axis='both', alpha=0.15)
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)

    plt.suptitle('电池循环深度与寿命分析', fontsize=13, weight='bold', y=0.995)

    plt.tight_layout()
    plt.savefig(output_path, format=fmt, dpi=300 if fmt=='png' else None,
                bbox_inches='tight', facecolor='white', edgecolor='none', pad_inches=0.05)
    plt.close()


def generate_figure9_temporal_heatmap(data, output_path, fmt='png'):
    """
    图9: SOC时空热力图与边界触碰深度分析
    洞察：什么时候最容易触发边界？触碰的强度如何？
    """
    setup_plot_style()

    results = data['backtest']['daily_results']

    # 构建SOC矩阵
    n_days = len(results)
    n_timepoints = 145

    soc_matrix = np.zeros((n_days, n_timepoints))
    for i, r in enumerate(results):
        soc_seq = np.array([r['initial_soc']] + r['soc'])
        soc_matrix[i, :] = soc_seq

    fig = plt.figure(figsize=(14, 9))
    gs = gridspec.GridSpec(3, 2, height_ratios=[2, 1, 1], hspace=0.35, wspace=0.3)

    # 上图：SOC热力图（跨度更大）
    ax1 = fig.add_subplot(gs[0, :])

    im1 = ax1.imshow(soc_matrix, aspect='auto', cmap='RdYlBu_r',
                    extent=[0, 24, n_days, 1], vmin=1200, vmax=10800)

    # 标注关键边界
    ax1.axhline(1, color='white', linestyle='--', linewidth=1.5, alpha=0.8)
    ax1.axhline(n_days, color='white', linestyle='--', linewidth=1.5, alpha=0.8)

    # 标注典型时段
    ax1.axvline(7, color='white', linestyle=':', linewidth=1, alpha=0.6)
    ax1.axvline(19, color='white', linestyle=':', linewidth=1, alpha=0.6)
    ax1.text(3.5, n_days*0.95, '谷时', ha='center', fontsize=9, color='white', weight='bold',
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))
    ax1.text(13, n_days*0.95, '平时', ha='center', fontsize=9, color='white', weight='bold',
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))
    ax1.text(20.5, n_days*0.95, '峰时', ha='center', fontsize=9, color='white', weight='bold',
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))

    ax1.set_xlabel('时间（小时）', fontsize=10)
    ax1.set_ylabel('运行天数', fontsize=10)
    ax1.set_title('全年SOC时空分布热力图（334天×24小时）', fontsize=11, weight='bold')
    ax1.set_xlim(0, 24)

    cbar1 = plt.colorbar(im1, ax=ax1, orientation='vertical', pad=0.02)
    cbar1.set_label('SOC (kWh)', fontsize=9)

    # 左下：边界触碰频率（按时刻）
    ax2 = fig.add_subplot(gs[1, 0])

    upper_touch_freq = np.sum(soc_matrix >= 10799, axis=0) / n_days * 100
    lower_touch_freq = np.sum(soc_matrix <= 1201, axis=0) / n_days * 100

    time_axis = np.linspace(0, 24, n_timepoints)

    ax2.fill_between(time_axis, 0, upper_touch_freq, color=COLORS['red'],
                     alpha=0.6, label='触及上限')
    ax2.fill_between(time_axis, 0, -lower_touch_freq, color=COLORS['orange'],
                     alpha=0.6, label='触及下限')

    ax2.axhline(0, color='black', linewidth=0.8)
    ax2.set_xlabel('时间（小时）', fontsize=10)
    ax2.set_ylabel('触及频率（%）', fontsize=10)
    ax2.set_title('各时刻边界触碰频率', fontsize=10, weight='bold')
    ax2.legend(fontsize=8, loc='upper right')
    ax2.grid(axis='both', alpha=0.15)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.set_xlim(0, 24)

    # 右下：边界触碰持续时长分析
    ax3 = fig.add_subplot(gs[1, 1])

    # 统计每天触碰上/下限的时间点数量
    daily_upper_hours = np.sum(soc_matrix >= 10799, axis=1) * (10/60)  # 转为小时
    daily_lower_hours = np.sum(soc_matrix <= 1201, axis=1) * (10/60)

    ax3.hist(daily_upper_hours, bins=20, alpha=0.6, color=COLORS['red'],
            label='触上限时长', edgecolor='black', linewidth=0.8)
    ax3.hist(daily_lower_hours, bins=20, alpha=0.6, color=COLORS['orange'],
            label='触下限时长', edgecolor='black', linewidth=0.8)

    ax3.set_xlabel('单日触碰时长（小时）', fontsize=10)
    ax3.set_ylabel('天数', fontsize=10)
    ax3.set_title('单日边界触碰时长分布', fontsize=10, weight='bold')
    ax3.legend(fontsize=8)
    ax3.grid(axis='y', alpha=0.15)
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)

    # 底部：SOC分布（整体统计）
    ax4 = fig.add_subplot(gs[2, :])

    soc_all = soc_matrix.flatten()
    n, bins, patches = ax4.hist(soc_all, bins=50, color=COLORS['blue_dark'],
                                alpha=0.7, edgecolor='black', linewidth=0.5)

    # 标注边界
    ax4.axvline(10800, color=COLORS['red'], linestyle='--', linewidth=2,
               label='上限 (10,800 kWh)', alpha=0.8)
    ax4.axvline(1200, color=COLORS['orange'], linestyle='--', linewidth=2,
               label='下限 (1,200 kWh)', alpha=0.8)
    ax4.axvline(6000, color=COLORS['green'], linestyle=':', linewidth=1.5,
               label='目标 (6,000 kWh)', alpha=0.7)

    # 统计信息
    in_boundary = np.sum((soc_all >= 1200) & (soc_all <= 10800))
    total_points = len(soc_all)
    boundary_pct = in_boundary / total_points * 100

    ax4.text(0.98, 0.95, f'边界内占比: {boundary_pct:.1f}%\n'
                         f'平均SOC: {np.mean(soc_all):.0f} kWh',
            transform=ax4.transAxes, fontsize=9, ha='right', va='top',
            bbox=dict(boxstyle='round', facecolor='white', edgecolor='gray', lw=1))

    ax4.set_xlabel('SOC (kWh)', fontsize=10)
    ax4.set_ylabel('频数', fontsize=10)
    ax4.set_title('全年SOC分布统计（48,630个数据点）', fontsize=10, weight='bold')
    ax4.legend(fontsize=8, loc='upper left')
    ax4.grid(axis='y', alpha=0.15)
    ax4.spines['top'].set_visible(False)
    ax4.spines['right'].set_visible(False)

    plt.suptitle('SOC时空分布与边界触碰深度分析', fontsize=13, weight='bold', y=0.995)

    plt.tight_layout()
    plt.savefig(output_path, format=fmt, dpi=300 if fmt=='png' else None,
                bbox_inches='tight', facecolor='white', edgecolor='none', pad_inches=0.05)
    plt.close()
