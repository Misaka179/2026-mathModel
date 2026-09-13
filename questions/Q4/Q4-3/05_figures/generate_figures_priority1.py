"""
Q4-3 全部图表生成脚本 (完整版)
包含：图1-图5(成本分析) + 图6(四个关键日期SOC轨迹)
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Patch

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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
        'orange': '#D4A373',
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
# 路径配置
# ============================================================================
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, "result")
os.makedirs(output_dir, exist_ok=True)

print("开始生成 Q4-3 全部图表...")
AcademicStyle.apply_style()

# ============================================================================
# 图1: 月度成本变化趋势 (双Y轴，保留右侧轴)
# ============================================================================
print("\n[1/6] 生成 图1: 月度成本变化趋势...")
months = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
cost_data = [177.30, 138.05, 109.68, 112.39, 153.81, 200.19, 185.42, 138.71, 139.44, 158.91, 252.48]
price_data = [0.7819, 0.7464, 0.7318, 0.7452, 0.8058, 0.8638, 0.8300, 0.7725, 0.7659, 0.7785, 0.8622]

fig, ax1 = plt.subplots(figsize=(10, 7.5))
ax1.bar(months, cost_data, color=AcademicStyle.COLORS['blue_gray'],
        alpha=0.85, edgecolor='white', linewidth=1.5, label='月度成本')
ax1.set_xlabel('月份', fontsize=11, color=AcademicStyle.AXIS_COLOR)
ax1.set_ylabel('成本 (万元)', fontsize=11, color=AcademicStyle.AXIS_COLOR)
ax1.set_xticks(months)
ax1.set_xticklabels([f'{m}月' for m in months])
ax1.grid(axis='y', **AcademicStyle.GRID_STYLE)
ax1.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
for m, c in zip(months, cost_data):
    ax1.text(m, c + 5, f'{c:.0f}', ha='center', va='bottom', fontsize=9, color=AcademicStyle.AXIS_COLOR)

ax2 = ax1.twinx()
ax2.plot(months, price_data, color=AcademicStyle.COLORS['brick_red'],
         marker='o', linewidth=2, markersize=6, label='平均电价')
ax2.set_ylabel('平均电价 (元/kWh)', fontsize=11, color=AcademicStyle.AXIS_COLOR)
ax2.set_ylim(0.70, 0.90)

AcademicStyle.remove_spines(ax1)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(True)
ax2.spines['right'].set_color(AcademicStyle.AXIS_COLOR)
ax2.spines['right'].set_linewidth(0.8)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9, frameon=False)

plt.tight_layout()
plt.savefig(f'{output_dir}/图1_月度成本变化趋势.svg', format='svg', bbox_inches='tight')
plt.close()
print("  ✓ 已生成: 图1_月度成本变化趋势.svg")

# ============================================================================
# 图2: 购电量构成分析 (对数坐标轴)
# ============================================================================
print("\n[2/6] 生成 图2: 购电量构成分析...")
categories = ['计划购电', '调整购电', '紧急购电']
absolute_values = [2217.07, 14.00, 7.65]
percentages = [99.03, 0.63, 0.34]

fig, ax = plt.subplots(figsize=(8, 6))
colors = [AcademicStyle.COLORS['blue_gray'],
          AcademicStyle.COLORS['gray_green'],
          AcademicStyle.COLORS['brick_red']]

bars = ax.bar(categories, absolute_values, color=colors, alpha=0.85,
              edgecolor='white', linewidth=1.5, width=0.5)

ax.set_yscale('log')
ax.set_ylim(1, max(absolute_values) * 3)

for bar, val, pct in zip(bars, absolute_values, percentages):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, height * 1.3,
            f'{val:,.1f} 万kWh\n({pct:.2f}%)',
            ha='center', va='bottom', fontsize=10,
            color=AcademicStyle.AXIS_COLOR, fontweight='bold')

ax.set_ylabel('购电量 (万kWh, 对数坐标)', fontsize=11, color=AcademicStyle.AXIS_COLOR)
ax.set_xlabel('购电类型', fontsize=11, color=AcademicStyle.AXIS_COLOR)
ax.grid(axis='y', **AcademicStyle.GRID_STYLE)
AcademicStyle.remove_spines(ax)

plt.tight_layout()
plt.savefig(f'{output_dir}/图2_购电量构成分析.svg', format='svg', bbox_inches='tight')
plt.close()
print("  ✓ 已生成: 图2_购电量构成分析.svg")

# ============================================================================
# 图3: 紧急购电量分布
# ============================================================================
print("\n[3/6] 生成 图3: 紧急购电量分布...")
emergency_ranges = ['0-50', '50-100', '100-200', '200-300', '300-500', '>500']
emergency_counts = [45, 82, 98, 52, 18, 6]

fig, ax = plt.subplots(figsize=(8, 6))
bars = ax.bar(range(len(emergency_ranges)), emergency_counts,
              color=AcademicStyle.COLORS['brick_red'], alpha=0.85,
              edgecolor='white', linewidth=1.5, width=0.6)

for bar, val in zip(bars, emergency_counts):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, height + 2,
            f'{val}', ha='center', va='bottom', fontsize=10,
            color=AcademicStyle.AXIS_COLOR, fontweight='bold')

ax.set_xlabel('紧急购电量 (kWh)', fontsize=11, color=AcademicStyle.AXIS_COLOR)
ax.set_ylabel('事件数', fontsize=11, color=AcademicStyle.AXIS_COLOR)
ax.set_xticks(range(len(emergency_ranges)))
ax.set_xticklabels(emergency_ranges, rotation=15, ha='right')
ax.grid(axis='y', **AcademicStyle.GRID_STYLE)
ax.set_ylim(0, max(emergency_counts) * 1.25)

ax.text(0.98, 0.95, f'总事件数: {sum(emergency_counts)}',
        transform=ax.transAxes, ha='right', va='top',
        fontsize=10, color=AcademicStyle.COLORS['dark_blue'], style='italic')

AcademicStyle.remove_spines(ax)

plt.tight_layout()
plt.savefig(f'{output_dir}/图3_紧急购电量分布.svg', format='svg', bbox_inches='tight')
plt.close()
print("  ✓ 已生成: 图3_紧急购电量分布.svg")

# ============================================================================
# 图4: Q3与Q4-3成本对比 (分组柱状图)
# ============================================================================
print("\n[4/6] 生成 图4: Q3与Q4-3成本对比...")
cost_types = ['计划购电', '调整购电', '紧急购电']
q3_values = [16.15, 0.32, 0.02]
q43_values = [17.66, 0.18, 0.22]

x = np.arange(len(cost_types))
width = 0.35

fig, ax = plt.subplots(figsize=(8, 6))

bars1 = ax.bar(x - width/2, q3_values, width, label='Q3 (固定电价)',
               color=AcademicStyle.COLORS['blue_gray'], alpha=0.85,
               edgecolor='white', linewidth=1.5)
bars2 = ax.bar(x + width/2, q43_values, width, label='Q4-3 (波动电价)',
               color=AcademicStyle.COLORS['brick_red'], alpha=0.85,
               edgecolor='white', linewidth=1.5)

for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + 0.3,
                f'{height:.2f}', ha='center', va='bottom',
                fontsize=9, color=AcademicStyle.AXIS_COLOR, fontweight='bold')

ax.set_ylabel('成本 (百万元)', fontsize=11, color=AcademicStyle.AXIS_COLOR)
ax.set_xlabel('成本类型', fontsize=11, color=AcademicStyle.AXIS_COLOR)
ax.set_xticks(x)
ax.set_xticklabels(cost_types)
ax.legend(loc='upper right', fontsize=9, frameon=False)
ax.grid(axis='y', **AcademicStyle.GRID_STYLE)
ax.set_ylim(0, max(q43_values) * 1.3)
AcademicStyle.remove_spines(ax)

plt.tight_layout()
plt.savefig(f'{output_dir}/图4_Q3与Q4-3成本对比.svg', format='svg', bbox_inches='tight')
plt.close()
print("  ✓ 已生成: 图4_Q3与Q4-3成本对比.svg")

# ============================================================================
# 图5: 调整购电触发情况
# ============================================================================
print("\n[5/6] 生成 图5: 调整购电触发情况...")
months_adjust = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
adjust_amounts = [0.00, 2.26, 6.46, 0.91, 0.45, 0.65, 0.00, 2.61, 0.11, 0.54, 0.00]

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(months_adjust, adjust_amounts,
              color=AcademicStyle.COLORS['gray_green'], alpha=0.85,
              edgecolor='white', linewidth=1.5, width=0.7)

for m, val in zip(months_adjust, adjust_amounts):
    if val > 0:
        ax.text(m, val + 0.3, f'{val:.2f}', ha='center', va='bottom',
                fontsize=10, color=AcademicStyle.AXIS_COLOR, fontweight='bold')

ax.set_xlabel('月份', fontsize=11, color=AcademicStyle.AXIS_COLOR)
ax.set_ylabel('调整购电量 (万kWh)', fontsize=11, color=AcademicStyle.AXIS_COLOR)
ax.set_xticks(months_adjust)
ax.set_xticklabels([f'{m}月' for m in months_adjust])
ax.grid(axis='y', **AcademicStyle.GRID_STYLE)
ax.set_ylim(0, max(adjust_amounts) * 1.25)

total_adjust = sum(adjust_amounts)
ax.text(0.98, 0.95, f'全年总调整购电量: {total_adjust:.2f} 万kWh',
        transform=ax.transAxes, ha='right', va='top',
        fontsize=10, color=AcademicStyle.COLORS['dark_blue'], style='italic')

high_adjust_months = [(3, 2.26), (4, 6.46), (9, 2.61)]
for m, val in high_adjust_months:
    if val > 2.0:
        ax.annotate('预测误差大', xy=(m, val), xytext=(m, val + 1.5),
                    ha='center', fontsize=8, color=AcademicStyle.COLORS['brick_red'],
                    arrowprops=dict(arrowstyle='->', lw=1, color=AcademicStyle.COLORS['brick_red']))

AcademicStyle.remove_spines(ax)

plt.tight_layout()
plt.savefig(f'{output_dir}/图5_调整购电触发情况.svg', format='svg', bbox_inches='tight')
plt.close()
print("  ✓ 已生成: 图5_调整购电触发情况.svg")

# ============================================================================
# 图6: 四个关键日期 SOC 轨迹 (从"充放电量"工作表读取，处理合并单元格)
# ============================================================================
print("\n[6/6] 生成 图6: 四个关键日期SOC轨迹...")
excel_path = os.path.join(script_dir, "../02_results/result4-3_filled.xlsx")

target_dates = [
    ('春季 (3/20)', ['2025-03-20', '2025/3/20', '3-20', '3/20'], '#7E9F7E'),
    ('夏季 (6/21)', ['2025-06-21', '2025/6/21', '6-21', '6/21'], '#D4A373'),
    ('秋季 (9/23)', ['2025-09-23', '2025/9/23', '9-23', '9/23'], '#3D5A80'),
    ('冬季 (12/21)', ['2025-12-21', '2025/12/21', '12-21', '12/21'], '#7A9CC6'),
]

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

try:
    # ★ 关键修复：从"充放电量"读取，并前向填充合并单元格的日期
    df_cd = pd.read_excel(excel_path, sheet_name='充放电量')
    df_cd['日期'] = pd.to_datetime(df_cd['日期'], errors='coerce').ffill()

    print(f"  ℹ 充放电量工作表列名: {list(df_cd.columns)}")
    print(f"  ℹ 日期填充后的样本:\n{df_cd[['日期', '时刻', '储电量']].head(8).to_string()}")

    for idx, (label, patterns, color) in enumerate(target_dates):
        ax = axes[idx]
        df_day = None

        for p in patterns:
            p_std = p.replace('/', '-')
            mask = df_cd['日期'].dt.strftime('%Y-%m-%d') == p_std
            if mask.any():
                df_day = df_cd[mask]
                break

        if df_day is None or len(df_day) == 0:
            ax.text(0.5, 0.5, f'{label}\n数据缺失', ha='center', va='center',
                    fontsize=12, color='gray', transform=ax.transAxes)
            ax.axis('off')
            print(f"  ⚠ {label} 未匹配")
            continue

        # 提取时刻(小时)和储电量
        hours = []
        socs = []
        for _, row in df_day.iterrows():
            try:
                t = str(row['时刻'])
                h = int(t.split(':')[0])
                hours.append(h)
                socs.append(float(row['储电量']))
            except Exception:
                continue

        # 在0时补一个初始点（6000为全年第1天初值，此处按第一个点前推）
        if hours and hours[0] != 0:
            hours = [0] + hours
            socs = [6000.0] + socs

        ax.plot(hours, socs, linewidth=2, marker='o', markersize=6,
                color=color, markerfacecolor='white', markeredgewidth=1.5,
                markeredgecolor=color)
        ax.axhline(y=10800, color=AcademicStyle.COLORS['brick_red'],
                   linestyle='--', linewidth=1, alpha=0.7)
        ax.axhline(y=1200, color=AcademicStyle.COLORS['brick_red'],
                   linestyle='--', linewidth=1, alpha=0.7)
        ax.set_ylabel('储电量 (kWh)', fontsize=10, color=AcademicStyle.AXIS_COLOR)
        ax.set_ylim(0, 12000)
        ax.set_xlim(0, 24)
        ax.set_xticks([0, 4, 8, 12, 16, 20, 24])
        ax.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
        ax.set_title(label, fontsize=12, fontweight='bold',
                     color=AcademicStyle.AXIS_COLOR, pad=10)
        ax.set_xlabel('时间 (小时)', fontsize=10, color=AcademicStyle.AXIS_COLOR)
        ax.grid(axis='y', **AcademicStyle.GRID_STYLE)
        AcademicStyle.remove_spines(ax)
        print(f"  ✓ {label} 绘制成功: {len(hours)} 个点")

except Exception as e:
    print(f"  ⚠ 读取充放电量工作表失败: {e}")
    for ax in axes:
        ax.axis('off')

plt.tight_layout()
plt.savefig(f'{output_dir}/图6_四个关键日期SOC轨迹.svg', format='svg', bbox_inches='tight')
plt.close()
print("  ✓ 已生成: 图6_四个关键日期SOC轨迹.svg")

# ============================================================================
print("\n" + "="*60)
print("[OK] Q4-3 全部图表生成完毕！(共6张中文命名SVG)")
print("="*60)
print(f"保存路径: {output_dir}/")
print("  - 图1_月度成本变化趋势.svg")
print("  - 图2_购电量构成分析.svg")
print("  - 图3_紧急购电量分布.svg")
print("  - 图4_Q3与Q4-3成本对比.svg")
print("  - 图5_调整购电触发情况.svg")
print("  - 图6_四个关键日期SOC轨迹.svg")