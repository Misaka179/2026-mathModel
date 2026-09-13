"""
Q3 诊断性全年运行 (334天)

目标：不修改模型，收集全年诊断数据，判断SOC上升是否系统性

诊断指标：
1. 每日 SOC_start / SOC_end
2. 每日 ΔSOC
3. 每日 Charge / Discharge
4. 每日计划购电量
5. 每日实际购电量
6. 每日紧急购电量
7. 每日总成本
8. 全年 energy closure error
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import time

# 导入主模块
import importlib.util
spec = importlib.util.spec_from_file_location("q3_model", "q3_model_scenario_v1.2.py")
q3_model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q3_model)

load_data = q3_model.load_data
build_date_cache = q3_model.build_date_cache
infer_day_types_from_jan1_14 = q3_model.infer_day_types_from_jan1_14
optimize_single_day = q3_model.optimize_single_day
N_SLOTS = q3_model.N_SLOTS
DT = q3_model.DT
E_MIN = q3_model.E_MIN
E_MAX = q3_model.E_MAX
E_INIT = q3_model.E_INIT
ETA = q3_model.ETA

print("="*70)
print("Q3 诊断性全年运行 (334天)")
print("="*70)
print()
print("⚠️  这是诊断性运行，不修改任何模型参数")
print("⚠️  目标：收集全年数据，判断SOC上升是否系统性")
print()

# 加载数据
print("加载数据...")
price, load_real, pv_real, pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h = load_data()
load_by_date, pv_by_date = build_date_cache(load_real, pv_real)

# 识别日类型
day_types = infer_day_types_from_jan1_14(load_by_date)
q3_model.LOW_LOAD_WEEKDAYS = day_types

print("  [OK] 数据加载完成")
print()

# 日期范围：2025-02-01 到 2025-12-31 (334天)
start_date = datetime(2025, 2, 1)
end_date = datetime(2025, 12, 31)
date_range = [start_date + timedelta(days=i) for i in range(334)]

print(f"运行范围: {start_date.date()} 至 {end_date.date()} (334天)")
print()

# 初始化诊断记录
diagnostic_records = []
E_storage_prev = E_INIT  # 第一天初始SOC = 6000 kWh

# 全局统计
total_infeasible = 0
total_soc_violations = 0
start_time = time.time()

print("开始全年优化...")
print()

for day_idx, date in enumerate(date_range, 1):
    try:
        # 获取0:00时刻的PV预测
        pv_forecast_day = q3_model.get_pv_forecast_as_of(
            date, 0, pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h
        )

        # 优化单日
        result = optimize_single_day(
            date=date,
            price=price,
            load_real_day=load_by_date[date],
            pv_real_day=pv_by_date[date],
            pv_forecast_day=pv_forecast_day,
            E_storage_prev=E_storage_prev,
            load_by_date=load_by_date,
            pv_by_date=pv_by_date,
            pv_forecast_0h=pv_forecast_0h,
            pv_forecast_6h=pv_forecast_6h,
            pv_forecast_12h=pv_forecast_12h,
            pv_forecast_18h=pv_forecast_18h,
            enable_stage_k=True
        )

        # 提取结果
        E_plan = result['E_plan']
        E_final = result['E_final']
        E_storage_actual = result['E_storage_actual']
        E_charge_final = result['E_charge_final']
        E_discharge_final = result['E_discharge_final']
        E_emergency = result['E_emergency']
        Z_plan = result['Z_plan']
        Z_adjust = result['Z_adjust']
        Z_emergency = result['Z_emergency']
        Z_total = result['Z_total']

        # 计算诊断指标
        # 修复：SOC_start应该是当天开始时的值（即上一天结束值），不是E_storage_actual[0]
        SOC_start = E_storage_prev  # 当天开始时的SOC（跨日连续）
        SOC_end = E_storage_actual[-1]  # 当天结束时的SOC（第143时段）
        delta_SOC = SOC_end - SOC_start

        # 充放电总量 (功率 * DT = 能量)
        total_charge = np.sum(E_charge_final) * DT
        total_discharge = np.sum(E_discharge_final) * DT

        # 购电量
        planned_purchase = np.sum(E_plan)
        actual_purchase = np.sum(E_final + E_emergency)
        emergency_purchase = np.sum(E_emergency)

        # 能量闭合检查
        E_buy = actual_purchase
        E_pv = np.sum(pv_by_date[date]) * DT
        E_load = np.sum(load_by_date[date]) * DT
        charge_loss = (1 - ETA) * total_charge
        discharge_loss = (1 / ETA - 1) * total_discharge

        energy_in = E_buy + E_pv
        energy_out = E_load + delta_SOC + charge_loss + discharge_loss
        energy_closure_error = abs(energy_in - energy_out)

        # SOC 违规检查
        soc_violations = np.sum((E_storage_actual < E_MIN - 0.1) | (E_storage_actual > E_MAX + 0.1))
        total_soc_violations += soc_violations

        # SOC 百分比
        soc_start_pct = (SOC_start - E_MIN) / (E_MAX - E_MIN) * 100
        soc_end_pct = (SOC_end - E_MIN) / (E_MAX - E_MIN) * 100

        # 记录
        record = {
            'date': date,
            'day_idx': day_idx,
            'SOC_start': SOC_start,
            'SOC_end': SOC_end,
            'delta_SOC': delta_SOC,
            'SOC_start_pct': soc_start_pct,
            'SOC_end_pct': soc_end_pct,
            'total_charge': total_charge,
            'total_discharge': total_discharge,
            'planned_purchase': planned_purchase,
            'actual_purchase': actual_purchase,
            'emergency_purchase': emergency_purchase,
            'Z_plan': Z_plan,
            'Z_adjust': Z_adjust,
            'Z_emergency': Z_emergency,
            'Z_total': Z_total,
            'energy_closure_error': energy_closure_error,
            'soc_violations': soc_violations,
        }

        diagnostic_records.append(record)

        # 更新跨日SOC
        E_storage_prev = SOC_end

        # 进度输出
        if day_idx % 30 == 0 or day_idx == 334:
            elapsed = time.time() - start_time
            avg_time = elapsed / day_idx
            eta = avg_time * (334 - day_idx)
            print(f"[{day_idx}/334] {date.date()} | SOC: {soc_start_pct:.1f}% → {soc_end_pct:.1f}% | "
                  f"Emergency: {emergency_purchase:.0f} kWh | Cost: {Z_total:.0f} 元 | "
                  f"ETA: {eta/60:.1f} min")

    except Exception as e:
        print(f"❌ [{day_idx}/334] {date.date()} 失败: {e}")
        total_infeasible += 1
        continue

elapsed_total = time.time() - start_time

print()
print("="*70)
print("全年运行完成！")
print("="*70)
print(f"运行时间: {elapsed_total/60:.1f} 分钟")
print(f"求解成功: {len(diagnostic_records)}/334 天")
print(f"求解失败: {total_infeasible} 天")
print(f"SOC违规时段: {total_soc_violations}")
print()

# 保存诊断数据
df = pd.DataFrame(diagnostic_records)
output_path = Path("E:/数模资料/2026国赛准备/2026-mathModel/questions/QC-3/05_results/diagnostic_334days.xlsx")
df.to_excel(output_path, index=False)
print(f"✅ 诊断数据已保存: {output_path}")
print()

# ========================================
# 全年诊断分析
# ========================================

print("="*70)
print("全年诊断分析")
print("="*70)
print()

# 1. SOC 轨迹分析
print("[1] SOC 轨迹分析")
print("-" * 50)
soc_start_first = df['SOC_start'].iloc[0]
soc_end_last = df['SOC_end'].iloc[-1]
soc_max = df['SOC_end'].max()
soc_min = df['SOC_start'].min()
soc_above_90 = (df['SOC_end_pct'] > 90).sum()
soc_above_95 = (df['SOC_end_pct'] > 95).sum()
soc_above_99 = (df['SOC_end_pct'] > 99).sum()

print(f"  第1天起始SOC: {soc_start_first:.0f} kWh ({(soc_start_first-E_MIN)/(E_MAX-E_MIN)*100:.1f}%)")
print(f"  第334天结束SOC: {soc_end_last:.0f} kWh ({(soc_end_last-E_MIN)/(E_MAX-E_MIN)*100:.1f}%)")
print(f"  全年SOC范围: {soc_min:.0f} - {soc_max:.0f} kWh")
print(f"  日末SOC > 90%: {soc_above_90} 天 ({soc_above_90/334*100:.1f}%)")
print(f"  日末SOC > 95%: {soc_above_95} 天 ({soc_above_95/334*100:.1f}%)")
print(f"  日末SOC > 99%: {soc_above_99} 天 ({soc_above_99/334*100:.1f}%)")
print()

# SOC趋势判断
if soc_above_99 > 300:
    print("  ⚠️  判断: SOC系统性饱和（>99%的天数超过90%）")
elif soc_above_95 > 250:
    print("  ⚠️  判断: SOC持续偏高（>95%的天数超过75%）")
elif soc_above_90 > 200:
    print("  ⚠️  判断: SOC轻微偏高（>90%的天数超过60%）")
else:
    print("  ✅ 判断: SOC在合理范围内波动")
print()

# 2. 能量平衡分析
print("[2] 能量平衡分析")
print("-" * 50)
total_delta_soc = df['delta_SOC'].sum()
total_charge = df['total_charge'].sum()
total_discharge = df['total_discharge'].sum()
avg_closure_error = df['energy_closure_error'].mean()
max_closure_error = df['energy_closure_error'].max()

print(f"  全年ΔSOC累计: {total_delta_soc:+.0f} kWh")
print(f"  全年充电总量: {total_charge:.0f} kWh")
print(f"  全年放电总量: {total_discharge:.0f} kWh")
print(f"  平均能量闭合误差: {avg_closure_error:.2f} kWh/天")
print(f"  最大能量闭合误差: {max_closure_error:.2f} kWh")
print()

if abs(total_delta_soc) > 1000:
    print(f"  ⚠️  全年SOC累计变化 {total_delta_soc:+.0f} kWh（偏离初始值）")
else:
    print(f"  ✅ 全年SOC累计变化在合理范围")
print()

# 3. 购电分析
print("[3] 购电分析")
print("-" * 50)
avg_planned = df['planned_purchase'].mean()
avg_actual = df['actual_purchase'].mean()
avg_emergency = df['emergency_purchase'].mean()
emergency_days = (df['emergency_purchase'] > 1).sum()
emergency_ratio = df['emergency_purchase'].sum() / df['actual_purchase'].sum() * 100

print(f"  平均计划购电: {avg_planned:.0f} kWh/天")
print(f"  平均实际购电: {avg_actual:.0f} kWh/天")
print(f"  平均紧急购电: {avg_emergency:.0f} kWh/天")
print(f"  紧急购电天数: {emergency_days} 天 ({emergency_days/334*100:.1f}%)")
print(f"  紧急购电占比: {emergency_ratio:.1f}%")
print()

if emergency_ratio > 50:
    print("  🔴 紧急购电占比过高（>50%）- 负载估计需要改进")
elif emergency_ratio > 20:
    print("  ⚠️  紧急购电占比偏高（>20%）")
else:
    print("  ✅ 紧急购电占比合理")
print()

# 4. 成本分析
print("[4] 成本分析")
print("-" * 50)
total_cost = df['Z_total'].sum()
total_plan = df['Z_plan'].sum()
total_adjust = df['Z_adjust'].sum()
total_emergency = df['Z_emergency'].sum()
avg_cost = df['Z_total'].mean()

print(f"  全年总成本: {total_cost:,.0f} 元")
print(f"    计划购电成本: {total_plan:,.0f} 元 ({total_plan/total_cost*100:.1f}%)")
print(f"    调整成本: {total_adjust:,.0f} 元 ({total_adjust/total_cost*100:.1f}%)")
print(f"    紧急购电成本: {total_emergency:,.0f} 元 ({total_emergency/total_cost*100:.1f}%)")
print(f"  平均日成本: {avg_cost:,.0f} 元/天")
print()

# 5. Stage K 调整统计
print("[5] Stage K 调整统计")
print("-" * 50)
days_with_adjustment = (df['Z_adjust'] > 0.01).sum()
print(f"  发生调整的天数: {days_with_adjustment} / 334 ({days_with_adjustment/334*100:.1f}%)")
print()

if days_with_adjustment == 0:
    print("  ⚠️  全年无任何Stage K调整 - 触发条件可能过严")
else:
    print(f"  ✅ Stage K调整正常触发")
print()

# 6. 最终判断
print("="*70)
print("最终诊断判断")
print("="*70)
print()

# 判断标准
issues = []

if soc_above_99 > 300:
    issues.append("🔴 SOC系统性饱和")
if emergency_ratio > 50:
    issues.append("🔴 紧急购电过高")
if max_closure_error > 50000:
    issues.append("🔴 能量守恒严重偏差")
if days_with_adjustment == 0:
    issues.append("🟡 Stage K从未触发")
if abs(total_delta_soc) > 3000:
    issues.append("🟡 全年SOC累计变化过大")

if issues:
    print("发现以下问题:")
    for issue in issues:
        print(f"  {issue}")
    print()
    print("建议:")
    if "SOC系统性饱和" in str(issues):
        print("  1. 检查Controller价值函数（高SOC惩罚）")
        print("  2. 检查Stage 0是否系统性过购")
    if "紧急购电过高" in str(issues):
        print("  3. 改进负载估计（90%分位数）")
    if "Stage K从未触发" in str(issues):
        print("  4. 审查Stage K触发阈值")
else:
    print("✅ 未发现明显系统性问题")
    print("   可以进入正式334天A/B对比实验")

print()
print("="*70)
print(f"诊断报告已完成")
print(f"详细数据: {output_path}")
print("="*70)
