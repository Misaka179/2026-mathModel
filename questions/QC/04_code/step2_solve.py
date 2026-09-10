"""Step 2: Solve with HiGHS using prepared data"""
import json
import pulp

print("=" * 70)
print("Q1 Microgrid Solver with HiGHS")
print("=" * 70)

# Load prepared data
print("\nLoading prepared data...")
with open("questions/QC/05_results/input_data.json", "r") as f:
    data = json.load(f)

Price = data["Price"]
Load = data["Load"]
PV = data["PV"]
print(f"Data loaded: {len(Price)} points")

# Parameters
DT = 1/6
ETA = 0.9
E_INIT = 6000
E_MIN, E_MAX = 1200, 10800
P_MAX = 5000
POWER_LIMIT = P_MAX * DT
N = 144

print("\nBuilding model...")
prob = pulp.LpProblem("Microgrid_Q1", pulp.LpMinimize)

# Variables
E_buy = pulp.LpVariable.dicts("Buy", range(N), lowBound=0)
E_charge = pulp.LpVariable.dicts("Chg", range(N), lowBound=0, upBound=POWER_LIMIT)
E_discharge = pulp.LpVariable.dicts("Dis", range(N), lowBound=0, upBound=POWER_LIMIT)
E_storage = pulp.LpVariable.dicts("Soc", range(N), lowBound=E_MIN, upBound=E_MAX)
print("Variables: 576 (144x4)")

# Objective
prob += pulp.lpSum([Price[t] * E_buy[t] for t in range(N)])
print("Objective added")

# Constraints
print("Adding constraints...")
for t in range(N):
    # Power balance
    prob += E_buy[t] + PV[t]*DT + E_discharge[t]*ETA >= Load[t]*DT + E_charge[t]

    # Storage dynamics
    prev = E_INIT if t == 0 else E_storage[t-1]
    prob += E_storage[t] == prev + E_charge[t]*ETA - E_discharge[t]

# Boundary
prob += E_storage[N-1] == E_INIT
print("Constraints: 289 (144 balance + 144 dynamics + 1 boundary)")

print("\nSolving with HiGHS...")
solver = pulp.HiGHS(msg=True, timeLimit=300)
status_code = prob.solve(solver)
status = pulp.LpStatus[status_code]

print(f"\nSolver Status: {status}")

if status == "Optimal":
    obj = pulp.value(prob.objective)

    # Extract results
    print("Extracting results...")
    buy_result = [E_buy[t].varValue for t in range(N)]
    charge_result = [E_charge[t].varValue for t in range(N)]
    discharge_result = [E_discharge[t].varValue for t in range(N)]
    storage_result = [E_storage[t].varValue for t in range(N)]

    total_buy = sum(buy_result)
    total_charge = sum(charge_result)
    total_discharge = sum(discharge_result)

    print("\n" + "=" * 70)
    print("SOLUTION FOUND")
    print("=" * 70)
    print(f"Total cost:        {obj:.2f} yuan")
    print(f"Total purchase:    {total_buy:.2f} kWh")
    print(f"Total charge:      {total_charge:.2f} kWh")
    print(f"Total discharge:   {total_discharge:.2f} kWh")
    print(f"Final SOC:         {storage_result[-1]:.2f} kWh")
    print(f"Initial SOC:       {E_INIT} kWh")
    print("=" * 70)

    # Save results
    result_data = {
        "solver": "HiGHS",
        "status": status,
        "total_cost_yuan": round(obj, 4),
        "total_buy_kWh": round(total_buy, 4),
        "total_charge_kWh": round(total_charge, 4),
        "total_discharge_kWh": round(total_discharge, 4),
        "final_soc_kWh": round(storage_result[-1], 4),
        "buy": [round(x, 4) for x in buy_result],
        "charge": [round(x, 4) for x in charge_result],
        "discharge": [round(x, 4) for x in discharge_result],
        "storage": [round(x, 4) for x in storage_result]
    }

    with open("questions/QC/05_results/q1_solution.json", "w") as f:
        json.dump(result_data, f, indent=2)

    print(f"\n✅ Results saved to: questions/QC/05_results/q1_solution.json")
    print("\n🎉 SUCCESS!")
else:
    print(f"\n❌ FAILED: Status = {status}")
