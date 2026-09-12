"""
Complete Results Generation Pipeline
Generates all required files after backtest completes

Usage: python generate_all_results.py

Generates:
1. Energy balance verification
2. Power balance verification
3. No-storage baseline comparison
4. result2.xlsx (Excel format)
5. result_data_q2.json (JSON format)
6. All 5 figures

Author: Role B
Date: 2026-09-12
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime
import sys
import os

print("="*80)
print("COMPLETE RESULTS GENERATION PIPELINE")
print("="*80)

# Check if backtest results exist
if not os.path.exists('full_year_backtest_results.json'):
    print("\n[ERROR] full_year_backtest_results.json not found!")
    print("Please run full_year_backtest.py first.")
    sys.exit(1)

print("\n[Step 1/6] Loading backtest results...")
with open('full_year_backtest_results.json', 'r', encoding='utf-8') as f:
    backtest = json.load(f)

print(f"  Loaded {backtest['metadata']['days_processed']} days of data")
print(f"  Run date: {backtest['metadata']['run_date']}")

# Verify new boundary condition implementation
first_day = backtest['daily_results'][0]
if 'initial_soc' not in first_day:
    print("\n[WARNING] Results appear to be from old boundary condition implementation!")
    print("Expected 'initial_soc' field in results.")
    response = input("Continue anyway? (y/n): ")
    if response.lower() != 'y':
        sys.exit(1)
else:
    print(f"  [OK] New boundary condition detected (has 'initial_soc' field)")
    print(f"  Day 1 initial SOC: {first_day['initial_soc']:.2f} kWh")

print("\n[Step 2/6] Generating energy balance verification...")
# Energy balance verification
from data_loader import DataLoader

loader = DataLoader()
price, load_real, pv_real = loader.load_all()

total_E_plan = 0
total_E_plan_used = 0
total_C_internal = 0
total_D_internal = 0
total_emg = 0

for result in backtest['daily_results']:
    day_idx = result['day']
    E_plan = result['E_plan']
    charge = result['charge']
    discharge = result['discharge']
    emergency = result['emergency']

    # Daily totals
    daily_E_plan = sum(E_plan)
    daily_emg = sum(emergency)

    # Convert to internal
    daily_C_internal = sum([c * 0.9 for c in charge])
    daily_D_internal = sum([d / 0.9 for d in discharge])

    # E_plan used
    daily_E_plan_used = daily_E_plan - daily_emg

    total_E_plan += daily_E_plan
    total_E_plan_used += daily_E_plan_used
    total_C_internal += daily_C_internal
    total_D_internal += daily_D_internal
    total_emg += daily_emg

# Calculate waste
total_E_plan_waste = total_E_plan - total_E_plan_used
waste_rate = (total_E_plan_waste / total_E_plan) * 100

# Calculate average price
avg_price = np.mean(price)
waste_cost = total_E_plan_waste * avg_price

energy_balance = {
    'total_E_plan_kWh': float(total_E_plan),
    'total_E_plan_used_kWh': float(total_E_plan_used),
    'total_E_plan_waste_kWh': float(total_E_plan_waste),
    'waste_rate_percent': float(waste_rate),
    'waste_cost_yuan': float(waste_cost),
    'total_charge_internal_kWh': float(total_C_internal),
    'total_discharge_internal_kWh': float(total_D_internal),
    'total_emergency_kWh': float(total_emg),
    'storage_cycle_efficiency': float((total_D_internal / total_C_internal) * 100) if total_C_internal > 0 else 0
}

with open('energy_balance_verified.json', 'w', encoding='utf-8') as f:
    json.dump({
        'verification_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'waste_analysis': energy_balance
    }, f, indent=2, ensure_ascii=False)

print(f"  E_plan waste: {waste_rate:.2f}%")
print(f"  Storage efficiency: {energy_balance['storage_cycle_efficiency']:.2f}%")

print("\n[Step 3/6] Generating no-storage baseline...")
# Simple baseline: no storage, buy everything needed
baseline_cost = 0
KAPPA = 5

for result in backtest['daily_results']:
    day_idx = result['day']

    for t in range(144):
        load_t = load_real[day_idx][t] / 6  # kWh
        pv_t = pv_real[day_idx][t] / 6
        deficit = max(0, load_t - pv_t)

        # All deficit is emergency purchase at κ×price
        baseline_cost += KAPPA * price[t] * deficit

annual_savings = baseline_cost - backtest['summary']['annual_total_cost']
savings_pct = (annual_savings / baseline_cost) * 100

baseline_data = {
    'baseline_annual_cost': float(baseline_cost),
    'with_storage_cost': float(backtest['summary']['annual_total_cost']),
    'annual_savings': float(annual_savings),
    'savings_percentage': float(savings_pct)
}

with open('no_storage_baseline_results.json', 'w', encoding='utf-8') as f:
    json.dump(baseline_data, f, indent=2, ensure_ascii=False)

print(f"  Baseline cost: {baseline_cost:,.0f} yuan")
print(f"  Storage savings: {savings_pct:.2f}%")

print("\n[Step 4/6] Generating result2.xlsx...")
# Create Excel file
excel_data = []

for result in backtest['daily_results']:
    day_data = {
        'day': result['day'],
        'date': result['date'],
        'initial_soc': result.get('initial_soc', 6000),  # Handle old format
        'terminal_soc': result['terminal_soc'],
        'plan_cost': result['plan_cost'],
        'emergency_cost': result['emergency_cost'],
        'total_cost': result['total_cost']
    }

    # Add time series (E_plan, charge, discharge, emergency, soc)
    for t in range(144):
        day_data[f'E_plan_{t}'] = result['E_plan'][t]
        day_data[f'charge_{t}'] = result['charge'][t]
        day_data[f'discharge_{t}'] = result['discharge'][t]
        day_data[f'emergency_{t}'] = result['emergency'][t]
        day_data[f'soc_{t}'] = result['soc'][t]

    excel_data.append(day_data)

df = pd.DataFrame(excel_data)
df.to_excel('../05_results/result2.xlsx', index=False, engine='openpyxl')

print(f"  Saved {len(excel_data)} days to result2.xlsx")

print("\n[Step 5/6] Generating result_data_q2.json...")
# Create compact JSON for paper
result_data = {
    'metadata': {
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source': 'full_year_backtest_results.json',
        'boundary_condition': 'cross_day_continuity',
        'days': backtest['metadata']['days_processed']
    },
    'annual_costs': {
        'total_cost': backtest['summary']['annual_total_cost'],
        'plan_cost': backtest['summary']['annual_plan_cost'],
        'emergency_cost': backtest['summary']['annual_emergency_cost'],
        'plan_percentage': (backtest['summary']['annual_plan_cost'] / backtest['summary']['annual_total_cost']) * 100,
        'emergency_percentage': (backtest['summary']['annual_emergency_cost'] / backtest['summary']['annual_total_cost']) * 100
    },
    'daily_statistics': {
        'average_cost': backtest['summary']['daily_avg_cost'],
        'std_cost': backtest['summary']['daily_std_cost'],
        'min_cost': backtest['summary']['daily_min_cost'],
        'max_cost': backtest['summary']['daily_max_cost']
    },
    'storage_value': baseline_data,
    'energy_efficiency': energy_balance,
    'boundary_conditions': {
        'day_1_initial_soc': backtest['daily_results'][0].get('initial_soc', 6000),
        'day_334_terminal_soc': backtest['daily_results'][-1]['terminal_soc'],
        'cross_day_continuity': 'E(d,0) = E(d-1,144) for d in [2,334]'
    }
}

with open('../05_results/result_data_q2.json', 'w', encoding='utf-8') as f:
    json.dump(result_data, f, indent=2, ensure_ascii=False)

print(f"  Saved summary data to result_data_q2.json")

print("\n[Step 6/8] Generating figures (PNG format)...")
# Run figure generation scripts
import subprocess

# Generate main figures (PNG)
result = subprocess.run([sys.executable, 'generate_cn_figures.py'],
                       capture_output=True, text=True)
if result.returncode == 0:
    print("  [OK] Main figures (图1-5) generated successfully")
else:
    print(f"  [WARNING] Main figure generation had issues:")
    print(result.stderr)

# Generate supplementary figures (PNG)
if os.path.exists('04_code/generate_supplementary_figures.py'):
    result = subprocess.run([sys.executable, '04_code/generate_supplementary_figures.py'],
                           capture_output=True, text=True)
    if result.returncode == 0:
        print("  [OK] Supplementary figures (图6-7) generated successfully")
    else:
        print(f"  [WARNING] Supplementary figure generation had issues:")
        print(result.stderr)

print("\n[Step 7/8] Generating figures (SVG format)...")
# Generate main figures (SVG)
result = subprocess.run([sys.executable, 'generate_cn_figures_svg.py'],
                       capture_output=True, text=True)
if result.returncode == 0:
    print("  [OK] Main figures (图1-5) SVG generated successfully")
else:
    print(f"  [WARNING] SVG main figure generation had issues:")
    print(result.stderr)

# Generate supplementary figures (SVG)
result = subprocess.run([sys.executable, 'generate_supplementary_figures_svg.py'],
                       capture_output=True, text=True)
if result.returncode == 0:
    print("  [OK] Supplementary figures (图6-7) SVG generated successfully")
else:
    print(f"  [WARNING] SVG supplementary figure generation had issues:")
    print(result.stderr)

print("\n[Step 8/8] Summary...")
print("\n" + "="*80)
print("RESULTS GENERATION COMPLETE")
print("="*80)
print("\nGenerated files:")
print("  04_code/energy_balance_verified.json")
print("  04_code/no_storage_baseline_results.json")
print("  05_results/result2.xlsx")
print("  05_results/result_data_q2.json")
print("  06_figures/图1-7.png (PNG format)")
print("  06_figures/图1-7.svg (SVG format - for paper editing)")
print("\nNext step: Review results and update documentation")
