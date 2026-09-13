"""
Generate result4-2.xlsx from Q4-2 backtest results

生成3个工作表：
1. 计划购电量 (334天 × 144时段)
2. 充放电量 (334天 × 6区间 + 边界SOC)
3. 紧急购电量 (非零记录)
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

# Force UTF-8 encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("="*80)
print("生成 result4-2.xlsx")
print("="*80)

# 加载结果
print("\n[1/4] 加载Q4-2求解结果...")
with open('../../05_results/Q4-2/Q4_2_backtest_results_v2.json', 'r') as f:
    data = json.load(f)

results = data['results']
print(f"  ✓ 加载了 {len(results)} 天的结果")

# 生成工作表1：计划购电量
print("\n[2/4] 生成工作表1：计划购电量...")
dates = [r['date'] for r in results]
E_plan_array = np.array([r['E_plan'] for r in results])

time_labels = [f"{h:02d}:{m:02d}" for h in range(24) for m in [10, 20, 30, 40, 50, 60]][:144]
df_plan = pd.DataFrame(E_plan_array, index=dates, columns=time_labels)
df_plan.index.name = '日期'

print(f"  ✓ 计划购电量: {df_plan.shape[0]} 天 × {df_plan.shape[1]} 时段")
print(f"  总计划购电量: {E_plan_array.sum():,.2f} kWh")

# 生成工作表2：充放电量
print("\n[3/4] 生成工作表2：充放电量...")
charge_discharge_data = []

for r in results:
    charge = np.array(r['charge'])
    discharge = np.array(r['discharge'])
    soc = np.array(r['soc'])

    row = {
        '日期': r['date'],
        '0-4h充电量': charge[0:24].sum(),
        '4-8h充电量': charge[24:48].sum(),
        '8-12h充电量': charge[48:72].sum(),
        '12-16h充电量': charge[72:96].sum(),
        '16-20h充电量': charge[96:120].sum(),
        '20-24h充电量': charge[120:144].sum(),
        '0-4h放电量': discharge[0:24].sum(),
        '4-8h放电量': discharge[24:48].sum(),
        '8-12h放电量': discharge[48:72].sum(),
        '12-16h放电量': discharge[72:96].sum(),
        '16-20h放电量': discharge[96:120].sum(),
        '20-24h放电量': discharge[120:144].sum(),
        '0:00储电量': soc[0],
        '24:00储电量': soc[-1]  # 使用-1获取最后一个元素
    }
    charge_discharge_data.append(row)

df_charge_discharge = pd.DataFrame(charge_discharge_data)
print(f"  ✓ 充放电量: {len(charge_discharge_data)} 天")

# 生成工作表3：紧急购电量
print("\n[4/4] 生成工作表3：紧急购电量...")
emergency_records = []

for r in results:
    date = r['date']
    emergency = r['emergency']

    for t, e in enumerate(emergency):
        if e > 1e-6:
            h = (t * 10) // 60
            m = (t * 10) % 60 + 10
            if m == 70:
                h += 1
                m = 10
            time_str = f"{h:02d}:{m:02d}"

            emergency_records.append({
                '日期': date,
                '时段': time_str,
                '购电量': e
            })

df_emergency = pd.DataFrame(emergency_records)
print(f"  ✓ 紧急购电记录: {len(emergency_records)} 条")
print(f"  总紧急购电量: {df_emergency['购电量'].sum():,.2f} kWh")

# 生成Excel文件
print("\n生成Excel文件...")
output_file = '../../05_results/Q4-2/result4-2.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    df_plan.to_excel(writer, sheet_name='计划购电量')
    df_charge_discharge.to_excel(writer, sheet_name='充放电量', index=False)
    df_emergency.to_excel(writer, sheet_name='紧急购电量', index=False)

print(f"✓ Excel文件已生成: {output_file}")

# 成本汇总
print("\n" + "="*80)
print("Q4-2 成本汇总")
print("="*80)
total_cost = sum(r['total_cost'] for r in results)
plan_cost = sum(r['plan_cost'] for r in results)
emergency_cost = sum(r['emergency_cost'] for r in results)

print(f"总成本: {total_cost:,.2f} 元")
print(f"  - 计划购电: {plan_cost:,.2f} 元 ({plan_cost/total_cost*100:.1f}%)")
print(f"  - 紧急购电: {emergency_cost:,.2f} 元 ({emergency_cost/total_cost*100:.1f}%)")
print(f"日均成本: {total_cost/len(results):,.2f} 元/天")
print("\n" + "="*80)
print("✓ result4-2.xlsx 生成完成")
print("="*80)
