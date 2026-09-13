"""
弃光分析

能量平衡方程（含弃光）：
  E_grid + E_PV + E_discharge = E_load + E_charge + E_curtail

隐含弃光：
  E_curtail = (E_grid + E_PV + E_discharge) - (E_load + E_charge)
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

DT = 1/6

print("="*70)
print("弃光分析")
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

E_pv = np.array([np.sum(pv_by_date[date]) * DT for date in date_range])
E_load = np.array([np.sum(load_by_date[date]) * DT for date in date_range])

# 从诊断数据提取
E_grid = df['actual_purchase'].values
E_charge = df['total_charge'].values
E_discharge = df['total_discharge'].values

# 计算隐含弃光
Supply = E_grid + E_pv + E_discharge
Demand = E_load + E_charge
E_curtail = Supply - Demand

# 弃光率
Curtail_rate = (E_curtail / E_pv) * 100

print("完整能量平衡方程（含弃光）：")
print("  E_grid + E_PV + E_discharge = E_load + E_charge + E_curtail")
print()

print("="*70)
print("弃光统计")
print("="*70)
print()

print(f"{'指标':<30} {'Mean':<15} {'Median':<15} {'P95':<15} {'Max':<15}")
print("-"*70)
print(f"{'弃光量 (kWh)':<30} {np.mean(E_curtail):<15.2f} {np.median(E_curtail):<15.2f} {np.percentile(E_curtail, 95):<15.2f} {np.max(E_curtail):<15.2f}")
print(f"{'弃光率 (%)':<30} {np.mean(Curtail_rate):<15.2f} {np.median(Curtail_rate):<15.2f} {np.percentile(Curtail_rate, 95):<15.2f} {np.max(Curtail_rate):<15.2f}")
print("-"*70)
print()

# 全年统计
total_pv = np.sum(E_pv)
total_curtail = np.sum(E_curtail)
annual_curtail_rate = (total_curtail / total_pv) * 100

print(f"全年汇总:")
print(f"  光伏总发电量   = {total_pv:,.0f} kWh")
print(f"  弃光总量       = {total_curtail:,.0f} kWh")
print(f"  全年弃光率     = {annual_curtail_rate:.2f}%")
print()

# 弃光天数统计
days_curtail_gt_0 = np.sum(E_curtail > 1)
days_curtail_gt_1pct = np.sum(Curtail_rate > 1)
days_curtail_gt_5pct = np.sum(Curtail_rate > 5)
days_curtail_gt_10pct = np.sum(Curtail_rate > 10)
days_curtail_gt_20pct = np.sum(Curtail_rate > 20)

print("弃光天数统计:")
print(f"  弃光 > 1 kWh:    {days_curtail_gt_0} 天 ({days_curtail_gt_0/334*100:.1f}%)")
print(f"  弃光率 > 1%:     {days_curtail_gt_1pct} 天 ({days_curtail_gt_1pct/334*100:.1f}%)")
print(f"  弃光率 > 5%:     {days_curtail_gt_5pct} 天 ({days_curtail_gt_5pct/334*100:.1f}%)")
print(f"  弃光率 > 10%:    {days_curtail_gt_10pct} 天 ({days_curtail_gt_10pct/334*100:.1f}%)")
print(f"  弃光率 > 20%:    {days_curtail_gt_20pct} 天 ({days_curtail_gt_20pct/334*100:.1f}%)")
print()

print("="*70)
print("能量闭合验证（含弃光）")
print("="*70)
print()

# 重新验证能量闭合
Error_with_curtail = Supply - (Demand + E_curtail)
print(f"新闭合误差统计（应该≈0）：")
print(f"  Mean   = {np.mean(Error_with_curtail):.6f} kWh")
print(f"  Median = {np.median(Error_with_curtail):.6f} kWh")
print(f"  Max    = {np.max(np.abs(Error_with_curtail)):.6f} kWh")
print()

if np.max(np.abs(Error_with_curtail)) < 0.01:
    print("  [OK] 含弃光的能量平衡完美闭合")
else:
    print("  [!!] 仍然存在闭合误差")
print()

print("="*70)
print("弃光详细案例（前10天）")
print("="*70)
print()

for i in range(min(10, len(df))):
    print(f"Day {i+1} ({date_range[i].date()}):")
    print(f"  PV发电         = {E_pv[i]:>10.2f} kWh")
    print(f"  弃光           = {E_curtail[i]:>10.2f} kWh ({Curtail_rate[i]:>5.1f}%)")
    print(f"  实际利用PV     = {E_pv[i] - E_curtail[i]:>10.2f} kWh")
    print()

# 保存结果
result_df = pd.DataFrame({
    'date': date_range,
    'E_PV_total': E_pv,
    'E_curtail': E_curtail,
    'Curtail_rate_pct': Curtail_rate,
    'E_grid': E_grid,
    'E_load': E_load,
    'E_charge': E_charge,
    'E_discharge': E_discharge,
})

output_path = "05_results/curtailment_analysis.xlsx"
result_df.to_excel(output_path, index=False)

print("="*70)
print(f"[OK] 弃光分析结果已保存：{output_path}")
print("="*70)
