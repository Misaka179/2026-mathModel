"""
Q4-3 v2 Architecture 完整运行脚本
===================================

目标：
1. 运行2-12月共334天（1月仅用于预测参数估计）
2. 填写附件5的所有sheet：
   - 计划购电量（334行×147列）
   - 调整购电量（334行×147列）
   - 充放电量（334×6行×6列）
   - 紧急购电量（汇总）

按GPT-RE2.md建议的架构修正版本
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# 导入v2 architecture模型
sys.path.insert(0, str(Path(__file__).parent))
import importlib.util

spec = importlib.util.spec_from_file_location("q3_model_q4",
    str(Path(__file__).parent / "q3_model_scenario_q4_v2_arch.py"))
q3_model_q4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q3_model_q4)

# 导入必要的函数和常量
load_data = q3_model_q4.load_data
build_date_cache = q3_model_q4.build_date_cache
infer_day_types_from_jan1_14 = q3_model_q4.infer_day_types_from_jan1_14
optimize_single_day = q3_model_q4.optimize_single_day
N_SLOTS = q3_model_q4.N_SLOTS
E_INIT = q3_model_q4.E_INIT
ALPHA_EMERGENCY = q3_model_q4.ALPHA_EMERGENCY

print("="*70)
print("Q4-3 v2 Architecture: 完整运行（334天，2025-02-01至2025-12-31）")
print("="*70)
print("架构修正（按GPT-RE2.md建议）：")
print("1. 紧急购电从优化变量改为补偿项（derived variable）")
print("2. 使用波动电价：C_emg = 5 * price[t] * E_emg")
print("3. 与Q4-2的两阶段架构保持一致")
print("="*70)
print()

# 加载波动电价
def load_dynamic_price():
    """加载附件4的波动电价数据"""
    print("加载附件4: 波动电价数据...")

    price_file = Path("E:/数模资料/2026国赛准备/2026-mathModel/C题/附件/附件4.xlsx")
    df = pd.read_excel(price_file, sheet_name='Sheet1')

    dates = pd.to_datetime(df.iloc[:, 0])
    price_array = df.iloc[:, 1:145].values  # 365×144

    # 构建日期到电价的映射
    price_dict = {}
    for i, date in enumerate(dates):
        price_dict[date] = price_array[i]

    print(f"  [OK] 加载电价: {len(price_dict)} 天")
    print(f"  [OK] 电价范围: {price_array.min():.4f} - {price_array.max():.4f} 元/kWh")
    print(f"  [OK] 平均电价: {price_array.mean():.4f} 元/kWh")
    print()

    return price_dict

# 加载Q3数据
print("加载数据...")
price_fixed, load_real, pv_real, pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h = load_data()
load_by_date, pv_by_date = build_date_cache(load_real, pv_real)
price_dynamic = load_dynamic_price()

# 推断日类型（基于1月数据）
day_types = infer_day_types_from_jan1_14(load_by_date)

# 确定计费日期范围：2月1日至12月31日（334天）
billing_start = datetime(2025, 2, 1)
billing_end = datetime(2025, 12, 31)

billing_dates = []
current_date = billing_start
while current_date <= billing_end:
    if current_date in load_by_date and current_date in price_dynamic:
        billing_dates.append(current_date)
    current_date += timedelta(days=1)

print(f"计费期间: {len(billing_dates)} 天 (从 {billing_dates[0].date()} 到 {billing_dates[-1].date()})")
print(f"说明: 1月份（31天）仅用于预测参数估计，不计入成本")
print()

# 优化所有计费天数
results = []
E_storage = E_INIT

# 初始化数据存储
all_E_plan = []  # 计划购电量（每天144个时段）
all_E_adjust = []  # 调整购电量（每天144个时段）
all_E_charge = []  # 充电量（每天144个时段）
all_E_discharge = []  # 放电量（每天144个时段）
all_E_storage = []  # 储能量（每天144个时段）
all_E_emergency = []  # 紧急购电量（每天144个时段）

start_time = time.time()

for i, date in enumerate(billing_dates, 1):
    print(f"[{i}/{len(billing_dates)}] {date.date()}...", end=" ", flush=True)

    try:
        # 使用波动电价
        price = price_dynamic[date]
        load_real_day = load_by_date[date]
        pv_real_day = pv_by_date[date]
        pv_forecast_day = pv_forecast_0h.get(date, np.zeros(N_SLOTS))

        result = optimize_single_day(
            date, price, load_real_day, pv_real_day, pv_forecast_day, E_storage,
            load_by_date, pv_by_date,
            pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h,
            day_types
        )

        E_storage = result['E_storage_end']

        # 提取144时段数据
        all_E_plan.append(result['E_plan'])
        all_E_adjust.append(result['E_final'] - result['E_plan'])  # 调整量 = 最终 - 计划
        all_E_charge.append(result['E_charge_final'])
        all_E_discharge.append(result['E_discharge_final'])
        all_E_storage.append(result['E_storage_actual'])
        all_E_emergency.append(result['E_emergency'])

        # 计算紧急购电占比
        total_emergency = result['total_emergency_energy']
        total_final = sum(result['E_final'])
        emergency_ratio = total_emergency / total_final * 100 if total_final > 0 else 0

        results.append({
            'date': date,
            'Z_plan': result['Z_plan'],
            'Z_adjust': result['Z_adjust'],
            'Z_emergency': result['Z_emergency'],
            'Z_total': result['Z_total'],
            'emergency_ratio': emergency_ratio,
            'emergency_kWh': total_emergency,
            'total_kWh': total_final
        })

        print(f"成本={result['Z_total']:.0f}, 紧急={emergency_ratio:.2f}%")

    except Exception as e:
        print(f"失败: {e}")
        import traceback
        traceback.print_exc()
        # 失败时填充空值
        all_E_plan.append(np.zeros(N_SLOTS))
        all_E_adjust.append(np.zeros(N_SLOTS))
        all_E_charge.append(np.zeros(N_SLOTS))
        all_E_discharge.append(np.zeros(N_SLOTS))
        all_E_storage.append(np.zeros(N_SLOTS))
        all_E_emergency.append(np.zeros(N_SLOTS))
        continue

elapsed_time = time.time() - start_time

print()
print("="*70)
print("运行完成")
print("="*70)
print(f"总耗时: {elapsed_time/60:.1f} 分钟")
print(f"成功天数: {len(results)}/{len(billing_dates)}")
print()

# 统计
if results:
    df_results = pd.DataFrame(results)

    total_cost = df_results['Z_total'].sum()
    avg_emergency_ratio = df_results['emergency_ratio'].mean()
    max_emergency_ratio = df_results['emergency_ratio'].max()
    total_emergency_cost = df_results['Z_emergency'].sum()

    print(f"总成本: {total_cost/1e6:.2f} 百万元")
    print(f"紧急购电成本: {total_emergency_cost/1e6:.2f} 百万元 ({total_emergency_cost/total_cost*100:.1f}%)")
    print(f"平均紧急购电占比: {avg_emergency_ratio:.2f}%")
    print(f"最大紧急购电占比: {max_emergency_ratio:.2f}%")
    print()

    # 保存到附件5格式
    print("="*70)
    print("填写附件5: result4-3.xlsx")
    print("="*70)

    template_file = Path("E:/数模资料/2026国赛准备/2026-mathModel/C题/附件/附件5/result4-3.xlsx")
    output_file = Path("E:/数模资料/2026国赛准备/2026-mathModel/questions/Q4/Q4-3/02_results/result4-3_filled.xlsx")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 读取模板
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:

        # ========== Sheet 1: 计划购电量 ==========
        print("填写Sheet 1: 计划购电量...")

        # 构建时间列标签（144个时段）
        time_labels = []
        for h in range(24):
            for m in [10, 20, 30, 40, 50, 60]:
                if m == 60:
                    next_h = (h + 1) % 24
                    if next_h == 0:
                        time_labels.append(f"{h}:50-0:00+1")
                    else:
                        time_labels.append(f"{h}:50-{next_h}:00")
                else:
                    time_labels.append(f"{h}:{m-10:02d}-{h}:{m:02d}")

        # 创建DataFrame
        df_plan = pd.DataFrame(index=[d.date() for d in billing_dates])
        df_plan.index.name = '日期\\时间'

        # 填充144个时段
        for t in range(N_SLOTS):
            df_plan[time_labels[t]] = [all_E_plan[i][t] for i in range(len(billing_dates))]

        # 添加汇总列
        df_plan['全天购电量'] = [sum(all_E_plan[i]) for i in range(len(billing_dates))]
        df_plan['全天购电费'] = [results[i]['Z_plan'] for i in range(len(results))]

        df_plan.to_excel(writer, sheet_name='计划购电量')
        print(f"  [OK] 形状: {df_plan.shape}")

        # ========== Sheet 2: 调整购电量 ==========
        print("填写Sheet 2: 调整购电量...")

        df_adjust = pd.DataFrame(index=[d.date() for d in billing_dates])
        df_adjust.index.name = '日期\\时间'

        # 填充144个时段
        for t in range(N_SLOTS):
            df_adjust[time_labels[t]] = [all_E_adjust[i][t] for i in range(len(billing_dates))]

        # 添加汇总列
        df_adjust['全天购电量'] = [sum(all_E_adjust[i]) for i in range(len(billing_dates))]
        df_adjust['全天购电费'] = [results[i]['Z_adjust'] for i in range(len(results))]

        df_adjust.to_excel(writer, sheet_name='调整购电量')
        print(f"  [OK] 形状: {df_adjust.shape}")

        # ========== Sheet 3: 充放电量 ==========
        print("填写Sheet 3: 充放电量...")

        # 每天6行（6个4小时时段）
        charge_discharge_data = []

        for i, date in enumerate(billing_dates):
            # 6个时段：0-4, 4-8, 8-12, 12-16, 16-20, 20-24
            for period_idx in range(6):
                start_slot = period_idx * 24  # 每4小时=24个10分钟时段
                end_slot = start_slot + 24

                # 汇总该时段的充放电量
                charge_sum = sum(all_E_charge[i][start_slot:end_slot])
                discharge_sum = sum(all_E_discharge[i][start_slot:end_slot])

                # 时段结束时刻的储能量
                storage_end = all_E_storage[i][end_slot - 1] if end_slot <= N_SLOTS else all_E_storage[i][-1]

                # 时间标签
                start_hour = period_idx * 4
                end_hour = (period_idx + 1) * 4
                time_label = f"{start_hour}:00-{end_hour}:00"

                # 时刻标签（储能量对应的时刻）
                moment = f"{end_hour:02d}:00:00" if end_hour < 24 else "24:00"

                charge_discharge_data.append({
                    '日期': date.date() if period_idx == 0 else None,
                    '时间段': time_label,
                    '充电量': charge_sum,
                    '放电量': discharge_sum,
                    '时刻': moment,
                    '储电量': storage_end
                })

        df_charge_discharge = pd.DataFrame(charge_discharge_data)
        df_charge_discharge.to_excel(writer, sheet_name='充放电量', index=False)
        print(f"  [OK] 形状: {df_charge_discharge.shape}")

        # ========== Sheet 4: 紧急购电量 ==========
        print("填写Sheet 4: 紧急购电量...")

        # 统计有紧急购电的日期和时段
        emergency_data = []

        for i, date in enumerate(billing_dates):
            emergency_slots = []
            for t in range(N_SLOTS):
                if all_E_emergency[i][t] > 0.01:  # 有紧急购电
                    emergency_slots.append(t)

            if emergency_slots:
                # 合并连续时段
                total_emergency = sum(all_E_emergency[i])

                # 找到紧急购电的起止时刻
                start_slot = emergency_slots[0]
                end_slot = emergency_slots[-1]

                start_h = start_slot // 6
                start_m = (start_slot % 6) * 10
                end_h = (end_slot + 1) // 6
                end_m = ((end_slot + 1) % 6) * 10

                time_range = f"{start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d}"

                emergency_data.append({
                    '日期': date.date(),
                    '购电时间段': time_range,
                    '购电量': total_emergency
                })

        df_emergency = pd.DataFrame(emergency_data)
        df_emergency.to_excel(writer, sheet_name='紧急购电量', index=False)
        print(f"  [OK] 形状: {df_emergency.shape} ({len(emergency_data)}个紧急购电事件)")

    print()
    print(f"结果已保存到: {output_file}")
    print()
    print("="*70)
    print("完成！")
    print("="*70)

else:
    print("所有天数失败，未生成结果文件")
