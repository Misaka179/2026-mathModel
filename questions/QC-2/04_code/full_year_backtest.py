"""
Full Year Backtest - Run all 334 planning days

Generate complete results for Q2 B->C handoff:
- 334 days day-ahead LP + DP execution
- Save all results for file generation

Author: Role B (Zhou Xiaoting)
Date: 2026-09-11
Estimated runtime: 2-4 hours
"""

import numpy as np
import sys
import os
import time
import json
from datetime import datetime

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

sys.path.insert(0, os.path.dirname(__file__))

from data_loader import DataLoader
from scenario_builder import ScenarioBuilder
from dp_executor import DPValueExecutor
from pulp import LpProblem, LpVariable, lpSum, LpMinimize, LpStatus

# Parameters
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


def solve_day_ahead(day_d, scenarios, price, E_init_day, is_final_day=False, E_terminal=None):
    """
    Solve day-ahead LP with given initial SOC

    Args:
        day_d: Day index
        scenarios: List of scenarios
        price: Price vector
        E_init_day: Initial SOC for this day (6000 for day 1, previous day's terminal for others)
        is_final_day: If True, add terminal constraint
        E_terminal: Terminal SOC value for final day (if is_final_day=True)
    """
    M = len(scenarios)
    prob = LpProblem(f"DA_d{day_d}", LpMinimize)

    E_plan = [LpVariable(f"E_{t}", 0, None) for t in range(144)]
    E_charge_s = [[LpVariable(f"C{s}_{t}", 0, POWER_LIMIT) for t in range(144)] for s in range(M)]
    E_discharge_s = [[LpVariable(f"D{s}_{t}", 0, POWER_LIMIT) for t in range(144)] for s in range(M)]
    E_storage_s = [[LpVariable(f"S{s}_{t}", E_MIN, E_MAX) for t in range(144)] for s in range(M)]
    E_emg_s = [[LpVariable(f"Em{s}_{t}", 0, None) for t in range(144)] for s in range(M)]

    prob += (lpSum([price[t] * E_plan[t] for t in range(144)]) +
             lpSum([scenarios[s]['weight'] * lpSum([KAPPA * price[t] * E_emg_s[s][t] for t in range(144)])
                    for s in range(M)]))

    for s in range(M):
        load_s = scenarios[s]['load']
        pv_s = scenarios[s]['pv']

        for t in range(144):
            prob += (E_plan[t] + E_emg_s[s][t] + pv_s[t] * DT + ETA * E_discharge_s[s][t]
                    >= load_s[t] * DT + E_charge_s[s][t])

            E_prev = E_init_day if t == 0 else E_storage_s[s][t-1]
            prob += E_storage_s[s][t] == E_prev + ETA * E_charge_s[s][t] - E_discharge_s[s][t]

        # Terminal constraint for final day only
        if is_final_day and E_terminal is not None:
            prob += E_storage_s[s][143] == E_terminal

    status = prob.solve()  # Use default solver

    if LpStatus[status] != 'Optimal':
        return None, status

    E_plan_values = [E_plan[t].varValue for t in range(144)]
    return E_plan_values, status


print("="*80)
print("FULL YEAR BACKTEST - Q2 Complete Results Generation")
print("="*80)
print("\nConfiguration:")
print(f"  Planning period: 334 days (2025-02-01 to 2025-12-31)")
print(f"  Scenarios: M={M_VALUE}")
print(f"  Terminal value: v={V_VALUE}")
print(f"  Optimized DP: 30 state points, 10 action samples")
print(f"\nBoundary conditions:")
print(f"  Day 1 initial: E(1,0) = {E_INIT} kWh")
print(f"  Cross-day continuity: E(d,0) = E(d-1,144) for d ∈ [2,334]")
print(f"  Day 334 terminal: E(334,144) = {E_INIT} kWh (cyclic constraint)")
print("="*80)

# Load data
print("\n[1/4] Loading data...")
loader = DataLoader()
price, load_real, pv_real = loader.load_all()
feb1_idx, dec31_idx = loader.get_planning_period()

planning_days = list(range(feb1_idx, dec31_idx + 1))
print(f"       Planning days: {len(planning_days)} days (indices {feb1_idx} to {dec31_idx})")

# Initialize
print("\n[2/4] Initializing builder and executor...")
builder = ScenarioBuilder(load_real, pv_real, M=M_VALUE)

# Storage for results
results = []

# Cross-day state tracking
E_current = E_INIT  # Day 1 starts at 6000 kWh

# Run backtest
print("\n[3/4] Running full-year backtest...")
print(f"       Expected runtime: 2-4 hours")
print(f"       Progress updates every 50 days")
print(f"       Cross-day continuity: E(d,0) = E(d-1,144)")
print(f"       Terminal constraint: E(334,144) = {E_INIT} kWh")
print("-"*80)

start_time = time.time()
failed_days = []

for i, day_d in enumerate(planning_days):
    date_str = loader.dates[day_d].strftime('%Y-%m-%d')

    # Construct scenarios
    scenarios = builder.construct_scenarios(day_d)

    # Check if this is the final day
    is_final_day = (i == len(planning_days) - 1)

    # Solve day-ahead LP with current initial SOC
    # Add terminal constraint for final day: E(334,144) = E_INIT
    E_plan, status = solve_day_ahead(day_d, scenarios, price, E_current,
                                     is_final_day=is_final_day,
                                     E_terminal=E_INIT if is_final_day else None)

    if E_plan is None:
        print(f"  [WARNING] Day {day_d} ({date_str}): LP failed ({LpStatus[status]})")
        failed_days.append((day_d, date_str, LpStatus[status]))
        continue

    # Build DP value function
    dp_executor = DPValueExecutor(
        price=price, eta=ETA, E_init=E_current, E_min=E_MIN, E_max=E_MAX,
        power_limit=POWER_LIMIT, dt=DT, kappa=KAPPA, v=V_VALUE
    )
    dp_executor.build_average_value_function(E_plan, scenarios)

    # Execute with current initial SOC
    result_dp = dp_executor.execute(day_d, E_plan, load_real[day_d], pv_real[day_d])

    # Calculate costs
    plan_cost = sum(price[t] * E_plan[t] for t in range(144))
    emergency_cost = sum(KAPPA * price[t] * result_dp['emergency'][t] for t in range(144))
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

    # Update state for next day: E(d+1, 0) = E(d, 144)
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
print("BACKTEST COMPLETE")
print("="*80)
print(f"Total runtime: {elapsed_total/3600:.2f} hours ({elapsed_total/60:.1f} minutes)")
print(f"Days processed: {len(results)}/{len(planning_days)}")
if failed_days:
    print(f"Failed days: {len(failed_days)}")
    for day_d, date_str, status in failed_days[:5]:
        print(f"  - Day {day_d} ({date_str}): {status}")

# Summary statistics
print("\n[4/4] Computing summary statistics...")

total_costs = [r['total_cost'] for r in results]
plan_costs = [r['plan_cost'] for r in results]
emergency_costs = [r['emergency_cost'] for r in results]

annual_total = sum(total_costs)
annual_plan = sum(plan_costs)
annual_emergency = sum(emergency_costs)

avg_daily = np.mean(total_costs)
std_daily = np.std(total_costs)

print(f"\nAnnual costs (334 days):")
print(f"  Total cost:     {annual_total:,.2f} yuan")
print(f"  Plan cost:      {annual_plan:,.2f} yuan ({annual_plan/annual_total*100:.1f}%)")
print(f"  Emergency cost: {annual_emergency:,.2f} yuan ({annual_emergency/annual_total*100:.1f}%)")

print(f"\nDaily statistics:")
print(f"  Average:        {avg_daily:,.2f} yuan/day")
print(f"  Std deviation:  {std_daily:,.2f} yuan/day")
print(f"  Min:            {min(total_costs):,.2f} yuan/day")
print(f"  Max:            {max(total_costs):,.2f} yuan/day")

# Terminal SOC check - cross-day continuity verification
terminal_socs = [r['terminal_soc'] for r in results]
initial_socs = [r['initial_soc'] for r in results]

print(f"\nCross-day continuity verification:")
print(f"  Day 1 initial SOC: {initial_socs[0]:.2f} kWh (should be 6000)")
print(f"  Day 334 terminal SOC: {terminal_socs[-1]:.2f} kWh")
print(f"  SOC range: [{min(terminal_socs):.2f}, {max(terminal_socs):.2f}] kWh")
print(f"  Average terminal SOC: {np.mean(terminal_socs):.2f} kWh")

# Verify continuity: E(d,0) should equal E(d-1,144) for d>=2
continuity_errors = 0
for i in range(1, len(results)):
    expected = terminal_socs[i-1]
    actual = initial_socs[i]
    if abs(expected - actual) > 1e-6:
        continuity_errors += 1
        if continuity_errors <= 3:
            print(f"  [ERROR] Day {results[i]['day']}: expected init={expected:.2f}, got {actual:.2f}")

if continuity_errors == 0:
    print(f"  [OK] All {len(results)-1} cross-day transitions are continuous")
else:
    print(f"  [WARNING] {continuity_errors} continuity violations detected!")

# Save complete results
output = {
    'metadata': {
        'run_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'planning_period': f"{loader.dates[feb1_idx].strftime('%Y-%m-%d')} to {loader.dates[dec31_idx].strftime('%Y-%m-%d')}",
        'days_processed': len(results),
        'days_failed': len(failed_days),
        'runtime_hours': float(elapsed_total / 3600),
        'parameters': {
            'M': M_VALUE,
            'v': V_VALUE,
            'eta': ETA,
            'E_init': E_INIT,
            'kappa': KAPPA
        }
    },
    'summary': {
        'annual_total_cost': float(annual_total),
        'annual_plan_cost': float(annual_plan),
        'annual_emergency_cost': float(annual_emergency),
        'daily_avg_cost': float(avg_daily),
        'daily_std_cost': float(std_daily),
        'daily_min_cost': float(min(total_costs)),
        'daily_max_cost': float(max(total_costs))
    },
    'daily_results': results,
    'failed_days': [{'day': d, 'date': date, 'status': status} for d, date, status in failed_days]
}

output_file = 'full_year_backtest_results.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n[SAVED] Complete results saved to: {output_file}")
print(f"        File size: {os.path.getsize(output_file) / (1024*1024):.1f} MB")

print("\n" + "="*80)
print("NEXT STEP: Run generate_result_files.py to create Excel and final JSON")
print("="*80)
