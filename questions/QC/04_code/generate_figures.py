"""Q1 Figure表生成脚本"""
import json
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False

# 加载数据
with open("questions/QC/05_results/q1_solution.json", "r") as f:
    sol = json.load(f)

with open("questions/QC/03_data/input_data.json", "r") as f:
    data = json.load(f)

Price = np.array(data["Price"])
Load = np.array(data["Load"])
PV = np.array(data["PV"])

buy = np.array(sol["buy"])
charge = np.array(sol["charge"])
discharge = np.array(sol["discharge"])
storage = np.array(sol["storage"])

# 时间轴（小时）
time_hours = np.arange(144) * 10 / 60  # 0到24小时

DT = 1/6
ETA = 0.9

print("生成Q1Figure表...")

# ============================================================================
# Figure1: 购电策略与电价关系
# ============================================================================
fig1, ax1 = plt.subplots(figsize=(12, 6))

ax1_twin = ax1.twinx()

# 购电量（柱状Figure）
ax1.bar(time_hours, buy, width=0.15, alpha=0.6, color='steelblue', label='购电量')
ax1.set_xlabel('时间 (h)', fontsize=12)
ax1.set_ylabel('购电量 (kWh)', fontsize=12, color='steelblue')
ax1.tick_params(axis='y', labelcolor='steelblue')
ax1.set_xlim(0, 24)
ax1.grid(True, alpha=0.3)

# 电价（折线Figure）
ax1_twin.plot(time_hours, Price, color='red', linewidth=2, label='电价')
ax1_twin.set_ylabel('电价 (元/kWh)', fontsize=12, color='red')
ax1_twin.tick_params(axis='y', labelcolor='red')

plt.title('Figure1: 购电策略与电价关系', fontsize=14, fontweight='bold')
fig1.tight_layout()
fig1.savefig('questions/QC/06_figures/fig1_buy_vs_price.png', dpi=300, bbox_inches='tight')
print("[OK] Figure 1 saved: fig1_buy_vs_price.png")
plt.close(fig1)

# ============================================================================
# Figure2: 储能SOC变化曲线
# ============================================================================
fig2, ax2 = plt.subplots(figsize=(12, 6))

ax2.plot(time_hours, storage, linewidth=2.5, color='green', label='储能电量(SOC)')
ax2.axhline(y=6000, color='blue', linestyle='--', linewidth=1.5, label='初始/终止电量 (6000 kWh)')
ax2.axhline(y=1200, color='red', linestyle=':', linewidth=1, label='下限 (1200 kWh)')
ax2.axhline(y=10800, color='red', linestyle=':', linewidth=1, label='上限 (10800 kWh)')

ax2.fill_between(time_hours, 1200, 10800, alpha=0.1, color='gray')

ax2.set_xlabel('时间 (h)', fontsize=12)
ax2.set_ylabel('储能电量 (kWh)', fontsize=12)
ax2.set_xlim(0, 24)
ax2.set_ylim(0, 12000)
ax2.grid(True, alpha=0.3)
ax2.legend(loc='upper right', fontsize=10)

plt.title('Figure2: 储能电量(SOC)变化曲线', fontsize=14, fontweight='bold')
fig2.tight_layout()
fig2.savefig('questions/QC/06_figures/fig2_soc_curve.png', dpi=300, bbox_inches='tight')
print(" Figure2已保存: fig2_soc_curve.png")
plt.close(fig2)

# ============================================================================
# Figure3: 充放电功率曲线
# ============================================================================
fig3, ax3 = plt.subplots(figsize=(12, 6))

# 转换为功率（kW）
charge_power = charge / DT
discharge_power = discharge / DT

ax3.fill_between(time_hours, 0, charge_power, alpha=0.5, color='orange', label='充电功率')
ax3.fill_between(time_hours, 0, -discharge_power, alpha=0.5, color='purple', label='放电功率')

ax3.axhline(y=5000, color='red', linestyle='--', linewidth=1, label='功率上限 (5000 kW)')
ax3.axhline(y=-5000, color='red', linestyle='--', linewidth=1)
ax3.axhline(y=0, color='black', linewidth=0.5)

ax3.set_xlabel('时间 (h)', fontsize=12)
ax3.set_ylabel('功率 (kW)', fontsize=12)
ax3.set_xlim(0, 24)
ax3.set_ylim(-6000, 6000)
ax3.grid(True, alpha=0.3)
ax3.legend(loc='upper right', fontsize=10)

plt.title('Figure3: 储能充放电功率曲线', fontsize=14, fontweight='bold')
fig3.tight_layout()
fig3.savefig('questions/QC/06_figures/fig3_charge_discharge.png', dpi=300, bbox_inches='tight')
print(" Figure3已保存: fig3_charge_discharge.png")
plt.close(fig3)

# ============================================================================
# Figure4: 能量平衡分析
# ============================================================================
fig4, ax4 = plt.subplots(figsize=(12, 6))

# 供给侧
supply_buy = buy
supply_pv = PV * DT
supply_discharge = discharge * ETA

# 需求侧
demand_load = Load * DT
demand_charge = charge

# 堆叠面积Figure
ax4.fill_between(time_hours, 0, supply_buy, alpha=0.6, color='steelblue', label='购电')
ax4.fill_between(time_hours, supply_buy, supply_buy + supply_pv,
                 alpha=0.6, color='gold', label='光伏发电')
ax4.fill_between(time_hours, supply_buy + supply_pv,
                 supply_buy + supply_pv + supply_discharge,
                 alpha=0.6, color='purple', label='储能放电')

# 叠加需求线
total_demand = demand_load + demand_charge
ax4.plot(time_hours, total_demand, color='red', linewidth=2.5,
         linestyle='--', label='总需求(负载+充电)')

ax4.set_xlabel('时间 (h)', fontsize=12)
ax4.set_ylabel('能量 (kWh/10min)', fontsize=12)
ax4.set_xlim(0, 24)
ax4.grid(True, alpha=0.3)
ax4.legend(loc='upper left', fontsize=10)

plt.title('Figure4: 能量供需平衡分析', fontsize=14, fontweight='bold')
fig4.tight_layout()
fig4.savefig('questions/QC/06_figures/fig4_energy_balance.png', dpi=300, bbox_inches='tight')
print(" Figure4已保存: fig4_energy_balance.png")
plt.close(fig4)

# ============================================================================
# Figure5: 6时段充放电汇总（柱状Figure）
# ============================================================================
fig5, ax5 = plt.subplots(figsize=(10, 6))

intervals = [
    (0, 24, '0:00-4:00'),
    (24, 48, '4:00-8:00'),
    (48, 72, '8:00-12:00'),
    (72, 96, '12:00-16:00'),
    (96, 120, '16:00-20:00'),
    (120, 144, '20:00-24:00')
]

interval_labels = []
charge_sums = []
discharge_sums = []

for lo, hi, label in intervals:
    interval_labels.append(label)
    charge_sums.append(sum(charge[lo:hi]))
    discharge_sums.append(sum(discharge[lo:hi]))

x_pos = np.arange(len(interval_labels))
width = 0.35

bars1 = ax5.bar(x_pos - width/2, charge_sums, width, label='充电量',
                color='orange', alpha=0.8)
bars2 = ax5.bar(x_pos + width/2, discharge_sums, width, label='放电量',
                color='purple', alpha=0.8)

# 添加数值标签
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax5.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.0f}',
                    ha='center', va='bottom', fontsize=9)

ax5.set_xlabel('时间段', fontsize=12)
ax5.set_ylabel('能量 (kWh)', fontsize=12)
ax5.set_xticks(x_pos)
ax5.set_xticklabels(interval_labels, rotation=15, ha='right')
ax5.legend(loc='upper right', fontsize=11)
ax5.grid(True, alpha=0.3, axis='y')

plt.title('Figure5: 分时段充放电汇总', fontsize=14, fontweight='bold')
fig5.tight_layout()
fig5.savefig('questions/QC/06_figures/fig5_interval_summary.png', dpi=300, bbox_inches='tight')
print(" Figure5已保存: fig5_interval_summary.png")
plt.close(fig5)

# ============================================================================
# Figure6: 成本对比（基线 vs 优化）
# ============================================================================
fig6, (ax6a, ax6b) = plt.subplots(1, 2, figsize=(12, 5))

# 子FigureA: 成本对比
categories = ['无储能\n基线', '有储能\n优化']
costs = [48052.05, 35126.95]
colors = ['lightcoral', 'lightgreen']

bars = ax6a.bar(categories, costs, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
for i, bar in enumerate(bars):
    height = bar.get_height()
    ax6a.text(bar.get_x() + bar.get_width()/2., height,
             f'{height:.2f}\n元',
             ha='center', va='bottom', fontsize=11, fontweight='bold')

# 添加节省标注
ax6a.annotate('', xy=(1, 35126.95), xytext=(0, 35126.95),
             arrowprops=dict(arrowstyle='<->', color='red', lw=2))
ax6a.text(0.5, 40000, f'节省\n12,925.10元\n(26.9%)',
         ha='center', fontsize=11, color='red', fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.3))

ax6a.set_ylabel('全天购电成本 (元)', fontsize=12)
ax6a.set_ylim(0, 55000)
ax6a.grid(True, alpha=0.3, axis='y')
ax6a.set_title('(a) 成本对比', fontsize=12, fontweight='bold')

# 子FigureB: 购电量结构
time_labels = ['低价\n(<0.5)', '中价\n(0.5-1.0)', '高价\n(≥1.0)']
buy_amounts = [2968.05, 46893.86, 9620.78]
buy_pcts = [5.0, 78.8, 16.2]
colors_price = ['lightblue', 'lightyellow', 'lightcoral']

bars = ax6b.bar(time_labels, buy_amounts, color=colors_price, alpha=0.8,
               edgecolor='black', linewidth=1.5)
for i, (bar, pct) in enumerate(zip(bars, buy_pcts)):
    height = bar.get_height()
    ax6b.text(bar.get_x() + bar.get_width()/2., height,
             f'{height:.0f} kWh\n({pct:.1f}%)',
             ha='center', va='bottom', fontsize=9)

ax6b.set_ylabel('购电量 (kWh)', fontsize=12)
ax6b.set_xlabel('电价时段', fontsize=12)
ax6b.set_ylim(0, 52000)
ax6b.grid(True, alpha=0.3, axis='y')
ax6b.set_title('(b) 购电量结构', fontsize=12, fontweight='bold')

plt.suptitle('Figure6: 经济效益分析', fontsize=14, fontweight='bold', y=1.00)
fig6.tight_layout()
fig6.savefig('questions/QC/06_figures/fig6_cost_analysis.png', dpi=300, bbox_inches='tight')
print(" Figure6已保存: fig6_cost_analysis.png")
plt.close(fig6)

print("\n" + "="*70)
print("All figures generated successfully!")
print("="*70)
print("\nFigure表保存位置: questions/QC/06_figures/")
print("  - fig1_buy_vs_price.png       (购电策略与电价)")
print("  - fig2_soc_curve.png          (SOC变化曲线)")
print("  - fig3_charge_discharge.png   (充放电功率)")
print("  - fig4_energy_balance.png     (能量平衡)")
print("  - fig5_interval_summary.png   (分时段汇总)")
print("  - fig6_cost_analysis.png      (经济效益)")
print("\n建议论文使用: Figure1, Figure2, Figure5, Figure6")
