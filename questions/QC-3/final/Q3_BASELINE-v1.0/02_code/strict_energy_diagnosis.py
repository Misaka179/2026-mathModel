"""
能量守恒严格诊断

目标：
1. 验证三个ΔSOC指标是否一致：A = B = C
   A. Endpoint ΔSOC = SOC_final - SOC_initial
   B. Sum of daily ΔSOC = Σ(SOC_end[d] - SOC_start[d])
   C. Charge-discharge implied ΔSOC = η * ΣCharge - ΣDischarge

2. 重新定义实际运行能量平衡，逐日计算闭合误差
"""

import pandas as pd
import numpy as np
from pathlib import Path

# 常数
ETA = 0.9
DT = 1/6  # 10分钟 = 1/6 小时

print("="*70)
print("能量守恒严格诊断")
print("="*70)
print()

# 加载334天诊断数据
data_path = Path("E:/数模资料/2026国赛准备/2026-mathModel/questions/QC-3/05_results/diagnostic_334days.xlsx")
df = pd.read_excel(data_path)

print(f"加载数据: {len(df)} 天")
print()

# ============================================================
# Part 1: 验证三个ΔSOC指标
# ============================================================
print("="*70)
print("Part 1: ΔSOC 一致性检查")
print("="*70)
print()

# A. Endpoint ΔSOC
SOC_initial = df['SOC_start'].iloc[0]
SOC_final = df['SOC_end'].iloc[-1]
A_endpoint = SOC_final - SOC_initial

print(f"A. Endpoint ΔSOC")
print(f"   SOC_initial (day 1): {SOC_initial:.2f} kWh")
print(f"   SOC_final (day 334): {SOC_final:.2f} kWh")
print(f"   A = {A_endpoint:.2f} kWh")
print()

# B. Sum of daily ΔSOC
B_sum_daily = df['delta_SOC'].sum()
print(f"B. Sum of daily ΔSOC")
print(f"   Σ(SOC_end[d] - SOC_start[d]) = {B_sum_daily:.2f} kWh")
print()

# C. Charge-discharge implied ΔSOC
total_charge = df['total_charge'].sum()
total_discharge = df['total_discharge'].sum()
C_implied = ETA * total_charge - total_discharge

print(f"C. Charge-discharge implied ΔSOC")
print(f"   Total charge: {total_charge:.2f} kWh")
print(f"   Total discharge: {total_discharge:.2f} kWh")
print(f"   C = η * ΣCharge - ΣDischarge")
print(f"   C = {ETA} * {total_charge:.2f} - {total_discharge:.2f}")
print(f"   C = {C_implied:.2f} kWh")
print()

# 验证一致性
print("-"*70)
print("一致性验证")
print("-"*70)
error_AB = abs(A_endpoint - B_sum_daily)
error_AC = abs(A_endpoint - C_implied)
error_BC = abs(B_sum_daily - C_implied)

print(f"  |A - B| = {error_AB:.2f} kWh")
print(f"  |A - C| = {error_AC:.2f} kWh")
print(f"  |B - C| = {error_BC:.2f} kWh")
print()

tolerance = 1.0  # 1 kWh容差
if error_AB < tolerance and error_AC < tolerance and error_BC < tolerance:
    print("  ✅ A = B = C (在容差范围内)")
    print(f"  → ΔSOC = {A_endpoint:.2f} kWh")
else:
    print("  ❌ A ≠ B ≠ C (存在不一致)")
    print("  → 需要检查 delta_SOC 或 total_charge/discharge 的计算逻辑")

print()
print()

# ============================================================
# Part 2: 逐日能量闭合误差
# ============================================================
print("="*70)
print("Part 2: 逐日能量闭合误差（实际执行层）")
print("="*70)
print()

print("能量平衡方程（实际执行）：")
print("  Supply = E_buy + E_PV")
print("  Demand = E_load + ΔSOC + Charge_loss + Discharge_loss")
print()
print("其中：")
print("  Charge_loss = (1 - η) * Charge")
print("  Discharge_loss = (1/η - 1) * Discharge")
print("  ΔSOC = SOC_end - SOC_start")
print()
print("闭合误差：ε = |Supply - Demand|")
print()
print("-"*70)

# 从 diagnostic_334days_run.py 重新读取完整数据
# 因为 Excel 中可能没有保存 E_buy, E_PV, E_load 等原始数据
# 我们需要从代码逻辑推导

# 根据代码逻辑：
# - actual_purchase = E_final + E_emergency
# - 实际购电 = 计划购电调整 + 紧急购电
# 但我们需要完整的逐时段数据才能精确计算

# 先用现有数据做估算
print("⚠️  注意：当前 Excel 数据不包含逐时段数据")
print("    将基于日汇总数据进行估算")
print()

# 从现有列计算
# actual_purchase 已经在 diagnostic 中计算
# 我们需要推导 E_PV 和 E_load

# 假设我们有这些列（需要从原始数据重新计算）
print("需要重新运行诊断脚本，保存以下逐日数据：")
print("  - E_buy (实际购电，kWh)")
print("  - E_PV (实际光伏，kWh)")
print("  - E_load (实际负载，kWh)")
print("  - ΔSOC (kWh)")
print("  - Charge (kWh)")
print("  - Discharge (kWh)")
print()

print("="*70)
print("建议：修改 diagnostic_334days_run.py")
print("="*70)
print()
print("在保存 record 时添加：")
print("  record['E_PV'] = np.sum(pv_by_date[date]) * DT")
print("  record['E_load'] = np.sum(load_by_date[date]) * DT")
print("  record['E_buy'] = actual_purchase  # 已有")
print()
print("然后可以计算：")
print("  Supply = E_buy + E_PV")
print("  Charge_loss = (1 - η) * Charge")
print("  Discharge_loss = (1/η - 1) * Discharge")
print("  Demand = E_load + ΔSOC + Charge_loss + Discharge_loss")
print("  Closure_error = |Supply - Demand|")
print()

# ============================================================
# Part 3: 分析现有的 energy_closure_error
# ============================================================
print("="*70)
print("Part 3: 分析现有的 energy_closure_error")
print("="*70)
print()

closure_errors = df['energy_closure_error']

print(f"统计分布:")
print(f"  Mean:   {closure_errors.mean():.2f} kWh")
print(f"  Median: {closure_errors.median():.2f} kWh")
print(f"  P95:    {closure_errors.quantile(0.95):.2f} kWh")
print(f"  Max:    {closure_errors.max():.2f} kWh")
print()

print(f"严重性分级:")
print(f"  > 1 kWh:    {(closure_errors > 1).sum()} 天 ({(closure_errors > 1).sum()/len(df)*100:.1f}%)")
print(f"  > 10 kWh:   {(closure_errors > 10).sum()} 天 ({(closure_errors > 10).sum()/len(df)*100:.1f}%)")
print(f"  > 100 kWh:  {(closure_errors > 100).sum()} 天 ({(closure_errors > 100).sum()/len(df)*100:.1f}%)")
print(f"  > 1000 kWh: {(closure_errors > 1000).sum()} 天 ({(closure_errors > 1000).sum()/len(df)*100:.1f}%)")
print()

# 相对误差（相对于日负载）
# 假设平均日负载约 60,000 kWh（从之前的数据）
avg_daily_load = 65000  # kWh (估算)
relative_errors = closure_errors / avg_daily_load * 100

print(f"相对于日负载的误差:")
print(f"  平均相对误差: {relative_errors.mean():.2f}%")
print(f"  > 1% 日负荷:  {(relative_errors > 1).sum()} 天 ({(relative_errors > 1).sum()/len(df)*100:.1f}%)")
print(f"  > 5% 日负荷:  {(relative_errors > 5).sum()} 天 ({(relative_errors > 5).sum()/len(df)*100:.1f}%)")
print(f"  > 10% 日负荷: {(relative_errors > 10).sum()} 天 ({(relative_errors > 10).sum()/len(df)*100:.1f}%)")
print()

# ============================================================
# 总结
# ============================================================
print("="*70)
print("诊断总结")
print("="*70)
print()

print("1. ΔSOC 一致性")
if error_AB < tolerance and error_AC < tolerance:
    print(f"   ✅ 三个指标一致：ΔSOC = {A_endpoint:.2f} kWh")
else:
    print(f"   ❌ 存在不一致，需要排查计算逻辑")
print()

print("2. 能量闭合误差")
if closure_errors.mean() > 1000:
    print(f"   🔴 平均误差 {closure_errors.mean():.0f} kWh/天 - 严重")
    print("      → 可能是计算公式问题（重复计算或遗漏项）")
elif closure_errors.mean() > 100:
    print(f"   🟡 平均误差 {closure_errors.mean():.0f} kWh/天 - 中等")
    print("      → 需要检查误差来源")
else:
    print(f"   ✅ 平均误差 {closure_errors.mean():.0f} kWh/天 - 可接受")
print()

print("3. 下一步行动")
print("   → 修改 diagnostic_334days_run.py，保存完整的逐日能量数据")
print("   → 重新计算能量闭合误差")
print("   → 分析误差来源（数值误差 vs 逻辑错误）")
print()

print("="*70)
