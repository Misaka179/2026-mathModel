"""
能量平衡理论推导

根据模型定义：
- E_charge, E_discharge 是功率 (kW)
- SOC更新：E_storage[t] = E_storage[t-1] + η·charge·DT - discharge·DT

推导正确的能量平衡方程
"""

import numpy as np

print("="*70)
print("能量平衡理论推导")
print("="*70)
print()

print("模型定义:")
print("  E_charge, E_discharge: 功率 (kW)")
print("  SOC更新: SOC[t] = SOC[t-1] + η·charge·DT - discharge·DT")
print()

print("="*70)
print("推导1：从SOC更新公式出发")
print("="*70)
print()

print("全天累加SOC更新方程：")
print("  ΔSOC = Σ(SOC[t] - SOC[t-1])")
print("       = Σ(η·charge[t]·DT - discharge[t]·DT)")
print("       = η·Σcharge[t]·DT - Σdischarge[t]·DT")
print("       = η·E_charge_total - E_discharge_total")
print()

print("其中：")
print("  E_charge_total = Σcharge[t]·DT  (充电能量，kWh)")
print("  E_discharge_total = Σdischarge[t]·DT  (放电能量，kWh)")
print()

print("="*70)
print("推导2：全系统能量守恒")
print("="*70)
print()

print("能量流向：")
print("  供给侧：")
print("    - E_grid: 从电网购入")
print("    - E_PV: 光伏发电")
print()
print("  消耗侧：")
print("    - E_load: 负载消耗")
print("    - E_charge_total: 充入储能（含损耗）")
print()
print("  储能侧：")
print("    - 充电效率η: 输入E_charge_total，实际储存η·E_charge_total")
print("    - 放电效率1: 从储能取出E_discharge_total，输出E_discharge_total")
print("    - ΔSOC = η·E_charge_total - E_discharge_total")
print()

print("全系统能量平衡：")
print("  供给 = 消耗")
print("  E_grid + E_PV + E_discharge_total = E_load + E_charge_total")
print()

print("[!] 注意：放电侧没有损耗！")
print("  因为模型中 discharge 是输出功率（到负载侧）")
print("  储能减少量 = discharge*DT（不是 discharge*DT/eta）")
print()

print("="*70)
print("推导3：验证两种形式的等价性")
print("="*70)
print()

print("形式A（含充放电）：")
print("  E_grid + E_PV + E_discharge_total = E_load + E_charge_total")
print()

print("形式B（含ΔSOC）：")
print("  从形式A移项：")
print("    E_grid + E_PV = E_load + E_charge_total - E_discharge_total")
print("  ")
print("  但 ΔSOC = eta*E_charge_total - E_discharge_total != E_charge_total - E_discharge_total")
print("  ")
print("  所以形式B应该是：")
print("    E_grid + E_PV = E_load + ΔSOC + (1-eta)*E_charge_total")
print()

print("验证：")
print("  右边 = E_load + eta*E_charge_total - E_discharge_total + (1-eta)*E_charge_total")
print("       = E_load + E_charge_total - E_discharge_total")
print("       = 形式A的右边 [OK]")
print()

print("="*70)
print("结论：正确的能量平衡方程")
print("="*70)
print()

print("形式A（推荐，清晰）：")
print("  E_grid + E_PV + E_discharge = E_load + E_charge")
print()

print("形式B（等价，含ΔSOC）：")
print("  E_grid + E_PV = E_load + ΔSOC + (1-eta)*E_charge")
print()

print("损耗项说明：")
print("  - 充电损耗 = (1-eta)*E_charge")
print("  - 放电损耗 = 0（模型中放电无损耗）")
print()

print("[!] 原诊断程序错误：")
print("  错误公式: E_grid + E_PV = E_load + ΔSOC + (1-eta)*E_charge + (1/eta-1)*E_discharge")
print("  问题: 重复计算了放电损耗")
print()

print("="*70)
print("数值验证")
print("="*70)
print()

# 使用Day1的数据
E_grid = 41874.13
E_PV = 41927.03
E_load = 76305.21
E_charge = 5680.56
E_discharge = 4986.11
delta_SOC = 126.39
ETA = 0.9

print("Day 1 数据:")
print(f"  E_grid = {E_grid:.2f} kWh")
print(f"  E_PV = {E_PV:.2f} kWh")
print(f"  E_load = {E_load:.2f} kWh")
print(f"  E_charge = {E_charge:.2f} kWh")
print(f"  E_discharge = {E_discharge:.2f} kWh")
print(f"  ΔSOC = {delta_SOC:.2f} kWh")
print()

print("形式A验证:")
Supply_A = E_grid + E_PV + E_discharge
Demand_A = E_load + E_charge
Error_A = Supply_A - Demand_A
print(f"  供给 = {Supply_A:.2f} kWh")
print(f"  消耗 = {Demand_A:.2f} kWh")
print(f"  差值 = {Error_A:.2f} kWh")
print(f"  相对误差 = {Error_A/E_load*100:.4f}%")
print()

print("形式B验证:")
Supply_B = E_grid + E_PV
Demand_B = E_load + delta_SOC + (1 - ETA) * E_charge
Error_B = Supply_B - Demand_B
print(f"  供给 = {Supply_B:.2f} kWh")
print(f"  消耗 = {Demand_B:.2f} kWh")
print(f"  差值 = {Error_B:.2f} kWh")
print(f"  相对误差 = {Error_B/E_load*100:.4f}%")
print()

print("等价性检查:")
print(f"  |Error_A - Error_B| = {abs(Error_A - Error_B):.6f} kWh")
if abs(Error_A - Error_B) < 0.01:
    print("  ✓ 两种形式完全等价")
else:
    print("  ✗ 两种形式不等价（不应该发生）")
print()

print("原诊断程序公式（错误）:")
Demand_Wrong = E_load + delta_SOC + (1 - ETA) * E_charge + (1/ETA - 1) * E_discharge
Error_Wrong = Supply_B - Demand_Wrong
print(f"  消耗（错误） = {Demand_Wrong:.2f} kWh")
print(f"  差值 = {Error_Wrong:.2f} kWh")
print(f"  与正确结果差 = {Error_Wrong - Error_B:.2f} kWh")
print()

print("="*70)
print("推导完成")
print("="*70)
