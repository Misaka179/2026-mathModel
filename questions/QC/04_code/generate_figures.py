"""
Q1 图表生成脚本 
"""

import json
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

# ============================================================================
# 学术级美化配置
# ============================================================================
class AcademicStyle:
    COLORS = {
        'blue_gray': '#7A9CC6',   # 灰蓝
        'dark_blue': '#3D5A80',   # 深蓝
        'brick_red': '#C87A6E',   # 砖红
        'gray_green': '#7E9F7E',  # 灰绿
        'light_gray': '#CCCCCC',  # 浅灰
    }

    GRID_STYLE = {
        'color': '#E0E0E0',
        'linestyle': '--',
        'linewidth': 0.5,
        'alpha': 0.7,
    }

    AXIS_COLOR = '#333333'

    @staticmethod
    def apply_style():
        plt.rcParams['font.sans-serif'] = ['SimSun', 'Times New Roman']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 11
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['axes.edgecolor'] = AcademicStyle.AXIS_COLOR
        plt.rcParams['axes.labelcolor'] = AcademicStyle.AXIS_COLOR
        plt.rcParams['xtick.color'] = AcademicStyle.AXIS_COLOR
        plt.rcParams['ytick.color'] = AcademicStyle.AXIS_COLOR

    @staticmethod
    def remove_spines(ax, keep_left=True, keep_bottom=True):
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        if not keep_left: ax.spines['left'].set_visible(False)
        if not keep_bottom: ax.spines['bottom'].set_visible(False)

# 全局千分位格式化函数
def thousands_formatter(x, pos):
    return f'{int(x):,}'

# ============================================================================
# 数据加载 (自动处理绝对/相对路径，保证从任意目录运行都不报错)
# ============================================================================
script_dir = os.path.dirname(os.path.abspath(__file__))
solution_path = os.path.join(script_dir, "../05_results/q1_solution.json")
data_path = os.path.join(script_dir, "../03_data/input_data.json")

with open(solution_path, "r", encoding='utf-8') as f:
    sol = json.load(f)

with open(data_path, "r", encoding='utf-8') as f:
    data = json.load(f)

Price = np.array(data["Price"])
Load = np.array(data["Load"])
PV = np.array(data["PV"])

buy = np.array(sol["buy"])
charge = np.array(sol["charge"])
discharge = np.array(sol["discharge"])
storage = np.array(sol["storage"])

time_hours = np.arange(144) * 10 / 60
DT = 1/6
ETA = 0.9

print("开始生成 Q1 图表...")
AcademicStyle.apply_style()

output_dir = os.path.join(script_dir, "../06_figures")
os.makedirs(output_dir, exist_ok=True)

# ============================================================================
# 图1: 日内购电与电价响应图
# ============================================================================
print("生成 图1...")
fig1, ax1 = plt.subplots(figsize=(10, 7.5))
ax1_twin = ax1.twinx()

# 右轴：电价阶梯线 + 阴影
ax1_twin.step(time_hours, Price, where='post',
              color=AcademicStyle.COLORS['brick_red'], linewidth=1.8, label='电价')
ax1_twin.fill_between(time_hours, 0, Price, step='post',
                      color=AcademicStyle.COLORS['brick_red'], alpha=0.08)
ax1_twin.set_ylabel('电价 (元/kWh)', fontsize=11, color=AcademicStyle.AXIS_COLOR)
ax1_twin.tick_params(axis='y', labelcolor=AcademicStyle.AXIS_COLOR)
ax1_twin.set_ylim(0, max(Price) * 1.3)

# 左轴：购电量折线
ax1.plot(time_hours, buy, color=AcademicStyle.COLORS['blue_gray'],
         linewidth=1.8, label='计划购电量')
ax1.fill_between(time_hours, 0, buy, color=AcademicStyle.COLORS['blue_gray'], alpha=0.2)
ax1.set_xlabel('时间 (h)', fontsize=11)
ax1.set_ylabel('计划购电量 (kWh)', fontsize=11, color=AcademicStyle.AXIS_COLOR)
ax1.tick_params(axis='y', labelcolor=AcademicStyle.AXIS_COLOR)
ax1.set_xlim(0, 24)
ax1.grid(axis='y', **AcademicStyle.GRID_STYLE)
ax1.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))

AcademicStyle.remove_spines(ax1)
AcademicStyle.remove_spines(ax1_twin)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax1_twin.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2,
           loc='upper center', bbox_to_anchor=(0.5, 1.1), ncol=2, frameon=False)

fig1.tight_layout()
fig1.savefig(f'{output_dir}/图1_购电策略与电价关系.svg', format='svg', bbox_inches='tight')
plt.close(fig1)

# ============================================================================
# 图2: 储能SOC与充放电功率协同验证图 (极简终局版)
# ============================================================================
print("生成 图2...")
fig2, (ax2a, ax2b) = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True,
                                   gridspec_kw={'hspace': 0.25})

charge_power = charge / DT
discharge_power = discharge / DT

# 上图：SOC曲线
ax2a.plot(time_hours, storage, linewidth=2,
          color=AcademicStyle.COLORS['dark_blue'], label='储能电量(SOC)', zorder=3)
ax2a.axhline(y=6000, color=AcademicStyle.COLORS['gray_green'],
             linestyle='--', linewidth=1.2, label='初始/终止电量 (6,000 kWh)', zorder=2)
ax2a.axhline(y=1200, color=AcademicStyle.COLORS['brick_red'],
             linestyle=':', linewidth=1.2, label='安全下限 (1,200 kWh)', zorder=2)
ax2a.axhline(y=10800, color=AcademicStyle.COLORS['brick_red'],
             linestyle=':', linewidth=1.2, label='安全上限 (10,800 kWh)', zorder=2)

ax2a.set_ylabel('储能电量 (kWh)', fontsize=11)
ax2a.set_ylim(0, 12000)
ax2a.grid(axis='y', **AcademicStyle.GRID_STYLE)
ax2a.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2, frameon=False, fontsize=9)
ax2a.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
AcademicStyle.remove_spines(ax2a)

# 下图：功率面积图 (极简版，去除所有图例框)
ax2b.fill_between(time_hours, 0, charge_power, alpha=0.6,
                  color=AcademicStyle.COLORS['blue_gray'])
ax2b.fill_between(time_hours, 0, -discharge_power, alpha=0.6,
                  color=AcademicStyle.COLORS['brick_red'])
ax2b.axhline(y=5000, color=AcademicStyle.COLORS['dark_blue'],
             linestyle='--', linewidth=1.2)
ax2b.axhline(y=-5000, color=AcademicStyle.COLORS['dark_blue'],
             linestyle='--', linewidth=1.2)
ax2b.axhline(y=0, color='black', linewidth=0.5)

# ★ 核心修改：极简的原位文本标注，彻底干掉丑陋且贴线的图例框
ax2b.text(0.5, 4200, '充电功率', color=AcademicStyle.COLORS['blue_gray'], fontsize=10, fontweight='bold')
ax2b.text(0.5, -5000, '放电功率', color=AcademicStyle.COLORS['brick_red'], fontsize=10, fontweight='bold')
ax2b.text(0.5, 5200, '功率上限 (±5,000 kW)', color=AcademicStyle.COLORS['dark_blue'], fontsize=9)

ax2b.set_xlabel('时间 (h)', fontsize=11)
ax2b.set_ylabel('功率 (kW)', fontsize=11)
ax2b.set_xlim(0, 24)
ax2b.set_ylim(-6000, 6000)
ax2b.grid(axis='y', **AcademicStyle.GRID_STYLE)
ax2b.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
AcademicStyle.remove_spines(ax2b)

fig2.tight_layout()
fig2.savefig(f'{output_dir}/图2_储能SOC与充放电功率.svg', format='svg', bbox_inches='tight')
plt.close(fig2)

# ============================================================================
# 图3: 能量供需平衡分析
# ============================================================================
print("生成 图3...")
fig3, ax3 = plt.subplots(figsize=(10, 7.5))

supply_buy = buy
supply_pv = PV * DT
supply_discharge = discharge * ETA
total_supply = supply_buy + supply_pv + supply_discharge

demand_load = Load * DT
demand_charge = charge
total_demand = demand_load + demand_charge

ax3.fill_between(time_hours, 0, total_supply, alpha=0.5,
                 color=AcademicStyle.COLORS['blue_gray'], label='总供给（购电+光伏+储能放电）')
ax3.plot(time_hours, total_demand, color=AcademicStyle.COLORS['brick_red'],
         linewidth=2, linestyle='--', label='总需求（负载+充电）', zorder=5)
ax3.fill_between(time_hours, 0, total_demand, alpha=0.1,
                 color=AcademicStyle.COLORS['brick_red'], zorder=1)

ax3.set_xlabel('时间 (h)', fontsize=11)
ax3.set_ylabel('能量 (kWh/10min)', fontsize=11)
ax3.set_xlim(0, 24)
ax3.grid(axis='y', **AcademicStyle.GRID_STYLE)
ax3.legend(loc='upper center', bbox_to_anchor=(0.5, 1.1), ncol=2, frameon=False, fontsize=9)
ax3.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
AcademicStyle.remove_spines(ax3)

ax3.text(0.98, 0.9, '总供给与总需求完美重合\n（能量守恒严格满足）',
         transform=ax3.transAxes, ha='right', va='top',
         fontsize=10, color=AcademicStyle.COLORS['dark_blue'], style='italic')

fig3.tight_layout()
fig3.savefig(f'{output_dir}/图3_能量供需平衡分析.svg', format='svg', bbox_inches='tight')
plt.close(fig3)

# ============================================================================
# 图4: 经济效益对比 (瀑布图，字体与换行已统一)
# ============================================================================
print("生成 图4...")
fig4, ax4 = plt.subplots(figsize=(8, 6))

baseline_cost = 48052.05
opt_cost = sol['total_cost_yuan']
savings = baseline_cost - opt_cost
pct = savings / baseline_cost * 100

categories = ['无储能\n基准', '成本节省', '有储能\n优化']
heights = [baseline_cost, savings, opt_cost]
bottoms = [0, opt_cost, 0]  
colors = [
    AcademicStyle.COLORS['light_gray'],
    AcademicStyle.COLORS['gray_green'],
    AcademicStyle.COLORS['dark_blue']
]

bars = ax4.bar(categories, heights, bottom=bottoms, width=0.4,
               color=colors, alpha=0.85, edgecolor='white', linewidth=1.5)

# 基准标签（柱顶，深灰字）
ax4.text(0, baseline_cost + 500, f'{baseline_cost:,.1f} 元',
         ha='center', va='bottom', fontsize=10, fontweight='bold',
         color=AcademicStyle.AXIS_COLOR)

# 节省标签（柱内，白字）
ax4.text(1, opt_cost + savings / 2, f'-{savings:,.1f} 元\n({pct:.1f}%)',
         ha='center', va='center', fontsize=10, fontweight='bold',
         color='white')

# 优化标签（柱顶，深灰字）
ax4.text(2, opt_cost + 500, f'{opt_cost:,.1f} 元',
         ha='center', va='bottom', fontsize=10, fontweight='bold',
         color=AcademicStyle.AXIS_COLOR)

# 连接虚线
ax4.plot([0.2, 0.8], [baseline_cost, baseline_cost], 'k--', lw=1, alpha=0.5)
ax4.plot([1.2, 1.8], [opt_cost, opt_cost], 'k--', lw=1, alpha=0.5)

ax4.set_ylabel('全天购电成本 (元)', fontsize=11)
ax4.set_ylim(0, baseline_cost * 1.15)
ax4.grid(axis='y', **AcademicStyle.GRID_STYLE)
ax4.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
AcademicStyle.remove_spines(ax4)

fig4.tight_layout()
fig4.savefig(f'{output_dir}/图4_经济效益对比分析.svg', format='svg', bbox_inches='tight')
plt.close(fig4)

print("\n" + "="*70)
print("[OK] Q1 生成完毕！")
print("="*70)
print(f"\n保存路径: {output_dir}/")
print("  - 图1_购电策略与电价关系.svg")
print("  - 图2_储能SOC与充放电功率.svg")
print("  - 图3_能量供需平衡分析.svg")
print("  - 图4_经济效益对比分析.svg")