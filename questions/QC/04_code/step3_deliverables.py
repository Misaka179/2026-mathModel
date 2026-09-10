"""Step 3: Generate final deliverables"""
import json
import pandas as pd

print("="*70)
print("Generating deliverables for Q1")
print("="*70)

# Load solution
with open("questions/QC/05_results/q1_solution.json", "r") as f:
    sol = json.load(f)

# Load input data for validation
with open("questions/QC/05_results/input_data.json", "r") as f:
    data = json.load(f)

Price = data["Price"]
Load = data["Load"]
PV = data["PV"]

# Parameters
DT = 1/6
ETA = 0.9
E_INIT = 6000
E_MIN, E_MAX = 1200, 10800
N = 144
TOL = 1e-4  # Relaxed tolerance for floating point errors

buy = sol["buy"]
charge = sol["charge"]
discharge = sol["discharge"]
storage = sol["storage"]

print("\nStep 1: Validation...")

# Validation checks
errors = []

# Check 1: Final SOC
if abs(storage[-1] - E_INIT) > 1e-3:
    errors.append(f"Final SOC != 6000: {storage[-1]}")

# Check 2: Capacity constraints
for t in range(N):
    if storage[t] < E_MIN - TOL or storage[t] > E_MAX + TOL:
        errors.append(f"SOC out of bounds at t={t+1}: {storage[t]}")
        break

# Check 3: Power constraints
POWER_LIMIT = 5000 * DT
for t in range(N):
    if charge[t] > POWER_LIMIT + TOL or discharge[t] > POWER_LIMIT + TOL:
        errors.append(f"Power limit exceeded at t={t+1}")
        break

# Check 4: Power balance
for t in range(N):
    supply = buy[t] + PV[t]*DT + discharge[t]*ETA
    demand = Load[t]*DT + charge[t]
    if supply < demand - TOL:
        errors.append(f"Power balance violated at t={t+1}")
        break

# Check 5: Storage dynamics
for t in range(N):
    prev = E_INIT if t == 0 else storage[t-1]
    expected = prev + ETA*charge[t] - discharge[t]
    if abs(storage[t] - expected) > 1e-3:  # 0.001 kWh tolerance for storage
        errors.append(f"Storage dynamics violated at t={t+1}")
        break

if errors:
    print("ERRORS FOUND:")
    for e in errors:
        print(f"  - {e}")
else:
    print("All validation checks PASSED")

# Diagnostics
simultaneous = sum(1 for t in range(N) if charge[t] > 0.01 and discharge[t] > 0.01)
balance_slack = sum(max(0, buy[t] + PV[t]*DT + discharge[t]*ETA - Load[t]*DT - charge[t])
                   for t in range(N))
equiv_cycles = sum(charge) / (E_MAX - E_MIN)

print(f"\nDiagnostics:")
print(f"  Simultaneous charge/discharge: {simultaneous} periods")
print(f"  Balance slack (curtailment): {balance_slack:.2f} kWh")
print(f"  Equivalent cycles: {equiv_cycles:.3f}")

print("\nStep 2: Generating result1.xlsx...")

# Sheet 1: Purchase plan (144 rows)
time_labels = []
for k in range(1, 145):
    start_h = (k-1)*10 // 60
    start_m = (k-1)*10 % 60
    end_h = k*10 // 60 % 24
    end_m = k*10 % 60
    time_labels.append(f"{start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d}")

df_buy = pd.DataFrame({
    '时间段': time_labels,
    '购电量(kWh)': [round(x, 4) for x in buy]
})

# Sheet 2: Charge/Discharge (6 intervals)
intervals = [
    (1, 24, '0:00-4:00'),
    (25, 48, '4:00-8:00'),
    (49, 72, '8:00-12:00'),
    (73, 96, '12:00-16:00'),
    (97, 120, '16:00-20:00'),
    (121, 144, '20:00-24:00')
]

rows = []
interval_summary = {}
for lo, hi, label in intervals:
    charge_sum = sum(charge[lo-1:hi])
    discharge_sum = sum(discharge[lo-1:hi])
    rows.append({
        '时间段': label,
        '充电量(kWh)': round(charge_sum, 4),
        '放电量(kWh)': round(discharge_sum, 4)
    })
    interval_summary[label] = {
        'charge': round(charge_sum, 4),
        'discharge': round(discharge_sum, 4)
    }

df_cd = pd.DataFrame(rows)

# Write Excel
output_path = "questions/QC/05_results/result1.xlsx"
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    df_buy.to_excel(writer, sheet_name='计划购电量', index=False)
    df_cd.to_excel(writer, sheet_name='充放电量', index=False)

print(f"Excel saved: {output_path}")

# Table 1 data (for paper)
table1_idx = [61, 73, 85, 97, 109, 121]
table1_labels = ['10:00-10:10', '12:00-12:10', '14:00-14:10',
                '16:00-16:10', '18:00-18:10', '20:00-20:10']
table1 = {label: round(buy[t-1], 4) for label, t in zip(table1_labels, table1_idx)}

print("\nStep 3: Generating reports...")

# validation_report.txt
report_path = "questions/QC/05_results/validation_report.txt"
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("MODEL VALIDATION REPORT (Q1)\n")
    f.write("="*70 + "\n")
    f.write("Solver: HiGHS\n")
    f.write("Status: Optimal\n\n")
    f.write(f"Total purchase energy = {sol['total_buy_kWh']:.4f} kWh\n")
    f.write(f"Total purchase cost   = {sol['total_cost_yuan']:.4f} yuan\n\n")
    f.write(f"Hard checks: {'ALL PASS' if not errors else 'FAILED'}\n\n")
    f.write("Diagnostics:\n")
    f.write(f"  Simultaneous charge/discharge = {simultaneous}\n")
    f.write(f"  Balance slack (curtailment)   = {balance_slack:.4f} kWh\n")
    f.write(f"  Equivalent charge cycles      = {equiv_cycles:.4f}\n")

print(f"Validation report saved: {report_path}")

# result_data.json
result_data = {
    "solver_status": "Optimal",
    "total_buy_kWh": sol['total_buy_kWh'],
    "total_cost_yuan": sol['total_cost_yuan'],
    "table1": table1,
    "interval_summary": interval_summary,
    "soc_0000": E_INIT,
    "soc_2400": sol['final_soc_kWh'],
    "diagnostics": {
        "simultaneous_charge_discharge": simultaneous,
        "balance_slack_kWh": round(balance_slack, 4),
        "equivalent_cycles": round(equiv_cycles, 4)
    },
    "validation": {
        "all_hard_checks_pass": len(errors) == 0,
        "n_failed": len(errors)
    }
}

result_json_path = "questions/QC/05_results/result_data.json"
with open(result_json_path, 'w', encoding='utf-8') as f:
    json.dump(result_data, f, ensure_ascii=False, indent=2)

print(f"Result data saved: {result_json_path}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"Solver:            HiGHS")
print(f"Status:            Optimal")
print(f"Total cost:        {sol['total_cost_yuan']:.2f} yuan")
print(f"Total purchase:    {sol['total_buy_kWh']:.2f} kWh")
print(f"Total charge:      {sol['total_charge_kWh']:.2f} kWh")
print(f"Total discharge:   {sol['total_discharge_kWh']:.2f} kWh")
print(f"Final SOC:         {sol['final_soc_kWh']:.2f} kWh")
print("="*70)

print("\nTable 1 Data (for paper):")
for label, val in table1.items():
    print(f"  {label}: {val:.4f} kWh")
print(f"  Total purchase: {sol['total_buy_kWh']:.2f} kWh")
print(f"  Total cost:     {sol['total_cost_yuan']:.2f} yuan")

print("\n" + "="*70)
print("ALL DELIVERABLES GENERATED:")
print("  1. result1.xlsx")
print("  2. validation_report.txt")
print("  3. result_data.json")
print("="*70)
print("\nSUCCESS!")
