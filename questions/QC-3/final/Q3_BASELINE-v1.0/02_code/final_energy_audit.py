"""
最终能量账本审计 - 使用正确的能量平衡方程

正确公式：
  E_grid + E_PV + E_discharge = E_load + E_charge

损耗说明：
  - 充电损耗已包含在charge中（输入charge，实际储存eta*charge）
  - 放电无损耗（模型中discharge是输出功率）
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

DT = 1/6
ETA = 0.9

print("="*70)
print("最终能量账本审计")
print("="*70)
print()

# 读取诊断数据
df = pd.read_excel("05_results/diagnostic_334days.xlsx")

# 加载原始数据
sys.path.insert(0, "04_code")
import importlib.util
spec = importlib.util.spec_from_file_location("q3_model", "04_code/q3_model_scenario_v1.2.py")
q3_model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q3_model)

load_data = q3_model.load_data
build_date_cache = q3_model.build_date_cache

price, load_real, pv_real, pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h = load_data()
load_by_date, pv_by_date = build_date_cache(load_real, pv_real)

# 计算每日能量
start_date = datetime(2025, 2, 1)
date_range = [start_date + timedelta(days=i) for i in range(334)]

E_pv_daily = np.array([np.sum(pv_by_date[date]) * DT for date in date_range])
E_load_daily = np.array([np.sum(load_by_date[date]) * DT for date in date_range])

# 从诊断数据提取
E_grid = df['actual_purchase'].values
E_charge = df['total_charge'].values
E_discharge = df['total_discharge'].values
delta_SOC = df['delta_SOC'].values

# 正确的能量平衡
Supply = E_grid + E_pv_daily + E_discharge
Demand = E_load_daily + E_charge
Error = Supply - Demand

# 相对误差
Error_pct = (Error / E_load_daily) * 100

# 统计分析
print("能量平衡方程：")
print("  E_grid + E_PV + E_discharge = E_load + E_charge")
print()

print("="*70)
print("表1：能量闭合误差统计")
print("="*70)
print()
print(f"{'指标':<30} {'Mean':<15} {'Median':<15} {'P95':<15} {'Max':<15}")
print("-"*70)
print(f"{'能量闭合误差 (kWh)':<30} {np.mean(Error):<15.2f} {np.median(Error):<15.2f} {np.percentile(Error, 95):<15.2f} {np.max(np.abs(Error)):<15.2f}")
print(f"{'闭合误差 / 日负荷 (%)':<30} {np.mean(np.abs(Error_pct)):<15.4f} {np.median(np.abs(Error_pct)):<15.4f} {np.percentile(np.abs(Error_pct), 95):<15.4f} {np.max(np.abs(Error_pct)):<15.4f}")
print("-"*70)
print()

print("="*70)
print("表2：超过阈值的天数统计")
print("="*70)
print()
print(f"{'阈值':<30} {'天数':<15} {'占比 (%)':<15}")
print("-"*70)

days_gt_1pct = np.sum(np.abs(Error_pct) > 1)
days_gt_3pct = np.sum(np.abs(Error_pct) > 3)
days_gt_5pct = np.sum(np.abs(Error_pct) > 5)
days_gt_10pct = np.sum(np.abs(Error_pct) > 10)

print(f"{'闭合误差 > 1%':<30} {days_gt_1pct:<15} {days_gt_1pct/334*100:<15.2f}")
print(f"{'闭合误差 > 3%':<30} {days_gt_3pct:<15} {days_gt_3pct/334*100:<15.2f}")
print(f"{'闭合误差 > 5%':<30} {days_gt_5pct:<15} {days_gt_5pct/334*100:<15.2f}")
print(f"{'闭合误差 > 10%':<30} {days_gt_10pct:<15} {days_gt_10pct/334*100:<15.2f}")
print("-"*70)

days_gt_1kWh = np.sum(np.abs(Error) > 1)
days_gt_10kWh = np.sum(np.abs(Error) > 10)
days_gt_100kWh = np.sum(np.abs(Error) > 100)
days_gt_1000kWh = np.sum(np.abs(Error) > 1000)

print(f"{'|误差| > 1 kWh':<30} {days_gt_1kWh:<15} {days_gt_1kWh/334*100:<15.2f}")
print(f"{'|误差| > 10 kWh':<30} {days_gt_10kWh:<15} {days_gt_10kWh/334*100:<15.2f}")
print(f"{'|误差| > 100 kWh':<30} {days_gt_100kWh:<15} {days_gt_100kWh/334*100:<15.2f}")
print(f"{'|误差| > 1000 kWh':<30} {days_gt_1000kWh:<15} {days_gt_1000kWh/334*100:<15.2f}")
print("-"*70)
print()

# 判断标准
p95_rel = np.percentile(np.abs(Error_pct), 95)

print("="*70)
print("判断标准")
print("="*70)
print()
print(f"P95 闭合误差 / 日负荷 = {p95_rel:.4f}%")
print()

if p95_rel < 1:
    verdict = "PASS - 基本可以接受"
elif p95_rel < 3:
    verdict = "需要解释/修正"
elif p95_rel < 5:
    verdict = "明显需要查"
else:
    verdict = "不能直接拿最终结果写论文"

print(f"判断结果：{verdict}")
print()

if days_gt_10pct > 50:
    print("[!] 大量天数(>50天)误差超过10%")
    print("优先检查：")
    print("  1. 购电量数据来源（是功率还是能量？）")
    print("  2. 充放电数据是否正确累加")
    print("  3. Load和PV数据单位")
    print()

# 详细示例
print("="*70)
print("详细案例（前5天）")
print("="*70)
print()

for i in range(min(5, len(df))):
    print(f"Day {i+1} ({date_range[i].date()}):")
    print(f"  供给侧：")
    print(f"    E_grid       = {E_grid[i]:>12.2f} kWh")
    print(f"    E_PV         = {E_pv_daily[i]:>12.2f} kWh")
    print(f"    E_discharge  = {E_discharge[i]:>12.2f} kWh")
    print(f"    ────────────────────────")
    print(f"    合计         = {Supply[i]:>12.2f} kWh")
    print()
    print(f"  消耗侧：")
    print(f"    E_load       = {E_load_daily[i]:>12.2f} kWh")
    print(f"    E_charge     = {E_charge[i]:>12.2f} kWh")
    print(f"    ────────────────────────")
    print(f"    合计         = {Demand[i]:>12.2f} kWh")
    print()
    print(f"  闭合误差     = {Error[i]:>12.2f} kWh ({Error_pct[i]:>6.2f}%)")
    print()

# 保存结果
audit_df = pd.DataFrame({
    'date': date_range,
    'E_grid': E_grid,
    'E_PV': E_pv_daily,
    'E_discharge': E_discharge,
    'Supply': Supply,
    'E_load': E_load_daily,
    'E_charge': E_charge,
    'Demand': Demand,
    'Error_kWh': Error,
    'Error_pct': Error_pct,
})

output_path = "05_results/final_energy_audit.xlsx"
audit_df.to_excel(output_path, index=False)

print("="*70)
print(f"[OK] 审计结果已保存：{output_path}")
print("="*70)
