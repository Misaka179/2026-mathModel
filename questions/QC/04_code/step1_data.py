"""Step 1: Prepare data only"""
import pandas as pd
import json

print("Loading data from Excel...")
df = pd.read_excel(r"C:\Users\30292\Documents\shumo\题目\C题\附件\附件1.xlsx")

data = {
    "Price": df.iloc[:, 1].values.tolist(),
    "Load": df.iloc[:, 2].values.tolist(),
    "PV": df.iloc[:, 3].values.tolist()
}

with open("questions/QC/05_results/input_data.json", "w") as f:
    json.dump(data, f)

print(f"Data saved: {len(data['Price'])} points")
print("Price range:", min(data['Price']), "-", max(data['Price']))
print("Load range:", min(data['Load']), "-", max(data['Load']))
print("PV range:", min(data['PV']), "-", max(data['PV']))
