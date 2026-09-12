"""
Q4-2 Full Year Solver V2 - 波动电价版本（基于Q2最新代码）

关键更新：
1. 基于Q2最新代码（2026-09-12 09:56版本）
2. 唯一修改：电价从固定值改为波动数组 Price[d, t]
3. 包含12月31日终端约束：E(334,144) = 6000 kWh

日期：2026-09-12
版本：V2（完全同步Q2）
"""

import numpy as np
import sys
import os
import time
import json
from datetime import datetime

# Force unbuffered output and UTF-8 encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
else:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

sys.path.insert(0, os.path.dirname(__file__))

from data_loader import DataLoader
from scenario_builder import ScenarioBuilder
from dp_executor import DPValueExecutor
from pulp import LpProblem, LpVariable, lpSum, LpMinimize, LpStatus

# Parameters (继承Q2)
DT = 1/6
ETA = 0.9
E_INIT = 6000
E_MIN = 1200
E_MAX = 10800
P_MAX = 5000
POWER_LIMIT = P_MAX * DT
KAPPA = 5
M_VALUE = 30
V_VALUE = 0.48


def solve_day_ahead_Q4_2(day_d, scenarios, price_d, E_init_day, is_final_day=False, E_terminal=None):
    """
    Q4-2日前决策LP（完全继承Q2，仅电价参数化）

    关键修改：price参数从全局数组改为当天price_d数组

    Args:
        day_d: Day index
        scenarios: List of scenarios
        price_d: 当天电价向量 (144,) - Q4-2的核心修改
        E_init_day: Initial SOC for this day
        is_final_day: If True, add terminal constraint (继承Q2)
        E_terminal: Terminal SOC value for final day (继承Q2)
    """
    M = len(scenarios)
    prob = LpProblem(f"DA_Q4_2_d{day_d}", LpMinimize)

    E_plan = [LpVariable(f"E_{t}", 0, None) for t in range(144)]
    E_charge_s = [[LpVariable(f"C{s}_{t}", 0, POWER_LIMIT) for t in range(144)] for s in range(M)]
    E_discharge_s = [[LpVariable(f"D{s}_{t}", 0, POWER_LIMIT) for t in range(144)] for s in range(M)]
    E_storage_s = [[LpVariable(f"S{s}_{t}", E_MIN, E_MAX) for t in range(144)] for s in range(M)]
    E_emg_s = [[LpVariable(f"Em{s}_{t}", 0, None) for t in range(144)] for s in range(M)]

    # Q4-2核心修改：使用price_d[t]而不是全局price[t]
    prob += (lpSum([price_d[t] * E_plan[t] for t in range(144)]) +
             lpSum([scenarios[s]['weight'] * lpSum([KAPPA * price_d[t] * E_emg_s[s][t] for t in range(144)])
                    for s in range(M)]))

    for s in range(M):
        load_s = scenarios[s]['load']
        pv_s = scenarios[s]['pv']

        for t in range(144):
            # 能量守恒约束（不等式）- 允许供给>需求（弃风弃光）
            # 注意：model_spec要求等式，但等式导致infeasible
            # 不等式是实际求解的必要条件
            prob += (E_plan[t] + E_emg_s[s][t] + pv_s[t] * DT + ETA * E_discharge_s[s][t]
                    >= load_s[t] * DT + E_charge_s[s][t])

            E_prev = E_init_day if t == 0 else E_storage_s[s][t-1]
            prob += E_storage_s[s][t] == E_prev + ETA * E_charge_s[s][t] - E_discharge_s[s][t]

        # 继承Q2：终端约束（最后一天）
        if is_final_day and E_terminal is not None:
            prob += E_storage_s[s][143] == E_terminal

    status = prob.solve()

    if LpStatus[status] != 'Optimal':
        return None, status

    E_plan_values = [E_plan[t].varValue for t in range(144)]
    return E_plan_values, status


print("="*80)
print("Q4-2 FULL YEAR SOLVER V2 - 波动电价版本")
print("="*80)
print("\n核心变化：")
print("  V1 → V2: 基于Q2最新代码（2026-09-12 09:56）")
print("  新增：12月31日终端约束 E(334,144) = 6000 kWh")
print("\nConfiguration:")
print(f"  Planning period: 334 days (2025-02-01 to 2025-12-31)")
print(f"  Scenarios: M={M_VALUE}")
print(f"  Terminal value: v={V_VALUE}")
print(f"  Optimized DP: 30 state points, 10 action samples")
print(f"\nBoundary conditions (完全继承Q2):")
print(f"  Day 1 initial: E(1,0) = {E_INIT} kWh")
print(f"  Cross-day continuity: E(d,0) = E(d-1,144) for d ∈ [2,334]")
print(f"  Day 334 terminal: E(334,144) = {E_INIT} kWh (cyclic constraint)")
print("="*80)

# Load data
print("\n[1/4] Loading data...")
loader = DataLoader()
price_fixed, load_real, pv_real = loader.load_all()
feb1_idx, dec31_idx = loader.get_planning_period()

# Q4-2关键：加载波动电价（附件4）
print("       Loading dynamic prices from 附件4...")
import pandas as pd
df_price = pd.read_excel('C题/附件/附件4.xlsx')
price_all = df_price.iloc[:, 1:145].values  # (365, 144)
print(f"       ✓ Dynamic prices loaded: {price_all.shape}")
print(f"       Price range: [{price_all.min():.4f}, {price_all.max():.4f}] yuan/kWh")

planning_days = list(range(feb1_idx, dec31_idx + 1))
print(f"       Planning days: {len(planning_days)} days (indices {feb1_idx} to {dec31_idx})")

# Initialize
print("\n[2/4] Initializing builder and executor...")
builder = ScenarioBuilder(load_real, pv_real, M=M_VALUE)

# Storage for results
results = []

# Cross-day state tracking
E_current = E_INIT

# Run backtest
print("\n[3/4] Running Q4-2 V2 full-year backtest...")
print(f"       Expected runtime: 2-4 hours")
print(f"       Progress updates every 50 days")
print(f"       Cross-day continuity: E(d,0) = E(d-1,144)")
print(f"       Terminal constraint: E(334,144) = {E_INIT} kWh")
print("-"*80)

start_time = time.time()
failed_days = []

for i, day_d in enumerate(planning_days):
    date_str = loader.dates[day_d].strftime('%Y-%m-%d')

    # Q4-2关键：获取当天波动电价
    price_d = price_all[day_d, :]

    # Construct scenarios
    scenarios = builder.construct_scenarios(day_d)

    # Check if this is the final day
    is_final_day = (i == len(planning_days) - 1)

    # Solve day-ahead LP with dynamic price
    E_plan, status = solve_day_ahead_Q4_2(day_d, scenarios, price_d, E_current,
                                          is_final_day=is_final_day,
                                          E_terminal=E_INIT if is_final_day else None)

    if E_plan is None:
        print(f"  [WARNING] Day {day_d} ({date_str}): LP failed ({LpStatus[status]})")
        failed_days.append((day_d, date_str, LpStatus[status]))
        continue

    # Build DP value function with dynamic price
    dp_executor = DPValueExecutor(
        price=price_d,
        eta=ETA, E_init=E_current, E_min=E_MIN, E_max=E_MAX,
        power_limit=POWER_LIMIT, dt=DT, kappa=KAPPA, v=V_VALUE
    )
    dp_executor.build_average_value_function(E_plan, scenarios)

    # Execute with current initial SOC
    result_dp = dp_executor.execute(day_d, E_plan, load_real[day_d], pv_real[day_d])

    # Calculate costs with dynamic price
    plan_cost = sum(price_d[t] * E_plan[t] for t in range(144))
    emergency_cost = sum(KAPPA * price_d[t] * result_dp['emergency'][t] for t in range(144))
    total_cost = plan_cost + emergency_cost

    # Store results
    terminal_soc = result_dp['soc'][-1]
    results.append({
        'day': int(day_d),
        'date': date_str,
        'initial_soc': float(E_current),
        'E_plan': [float(x) for x in E_plan],
        'charge': [float(x) for x in result_dp['charge']],
        'discharge': [float(x) for x in result_dp['discharge']],
        'emergency': [float(x) for x in result_dp['emergency']],
        'soc': [float(x) for x in result_dp['soc']],
        'plan_cost': float(plan_cost),
        'emergency_cost': float(emergency_cost),
        'total_cost': float(total_cost),
        'terminal_soc': float(terminal_soc)
    })

    # Update state for next day
    E_current = terminal_soc

    # Progress update
    if (i+1) % 50 == 0:
        elapsed = time.time() - start_time
        avg_time_per_day = elapsed / (i+1)
        remaining_days = len(planning_days) - (i+1)
        eta_seconds = avg_time_per_day * remaining_days
        eta_hours = eta_seconds / 3600

        avg_cost = np.mean([r['total_cost'] for r in results])
        print(f"  [{i+1}/{len(planning_days)}] Progress: {(i+1)/len(planning_days)*100:.1f}%")
        print(f"            Avg cost so far: {avg_cost:,.2f} yuan/day")
        print(f"            Elapsed: {elapsed/60:.1f} min, ETA: {eta_hours:.1f} hours")

elapsed_total = time.time() - start_time

print("\n" + "="*80)
print("Q4-2 V2 BACKTEST COMPLETE")
print("="*80)
print(f"Total runtime: {elapsed_total/3600:.2f} hours ({elapsed_total/60:.1f} minutes)")
print(f"Completed days: {len(results)}/{len(planning_days)}")
if failed_days:
    print(f"Failed days: {len(failed_days)}")

# Calculate statistics
total_costs = [r['total_cost'] for r in results]
plan_costs = [r['plan_cost'] for r in results]
emergency_costs = [r['emergency_cost'] for r in results]

print(f"\nCost Summary (Q4-2 V2):")
print(f"  Total cost: {sum(total_costs):,.2f} yuan (334 days)")
print(f"    - Plan cost: {sum(plan_costs):,.2f} yuan")
print(f"    - Emergency cost: {sum(emergency_costs):,.2f} yuan")
print(f"  Average daily cost: {np.mean(total_costs):,.2f} yuan/day")

# 验证终端约束
last = results[-1]
print(f"\nTerminal constraint verification:")
print(f"  Day 334 (2025-12-31) terminal SOC: {last['terminal_soc']:.2f} kWh")
print(f"  Expected: {E_INIT:.2f} kWh")
print(f"  Difference: {abs(last['terminal_soc'] - E_INIT):.2f} kWh")

# Save results
print("\n[4/4] Saving results...")
output_dir = '../05_results/Q4-2'
os.makedirs(output_dir, exist_ok=True)

output_file = os.path.join(output_dir, 'Q4_2_backtest_results_v2.json')
with open(output_file, 'w') as f:
    json.dump({
        'metadata': {
            'model': 'Q4-2 V2',
            'version': 'v2',
            'base': 'Q2 2026-09-12 09:56',
            'runtime_seconds': elapsed_total,
            'completed_days': len(results),
            'failed_days': len(failed_days),
            'terminal_constraint': f'E(334,144) = {E_INIT} kWh'
        },
        'results': results
    }, f, indent=2)

print(f"  ✓ Results saved: {output_file}")
print("\n" + "="*80)
