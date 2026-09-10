# C题Q1 模型实现规格说明

**模型状态**: 🔒 MODEL FROZEN  
**目标读者**: Role B (编程手)  
**前置文档**: model_decision.md (完整决策依据)、related_paper_analysis.md (文献依据)

---

## ⛔ 禁止修改的部分（B不得自行更改，如需变更返工给A）

以下为已冻结的模型核心，B只负责实现、不得重新解释题意或改动：

1. **模型类型**: 确定性线性规划(LP)，不改MILP/启发式（MILP仅作交叉验证）
2. **变量口径**: E_charge/E_discharge 为**名义充/放电能量**，效率η统一作用在流出方向：充电 `E_charge --η--> η·E_charge`（入池），放电 `E_discharge --η--> η·E_discharge`（供负荷）。**不得再用"电网侧/电池侧"混合措辞**（见下方"变量口径统一说明"）
3. **效率**: η = 0.9（单侧），电力平衡用 `+η·E_discharge` 与 `+E_charge`；状态方程用 `+η·E_charge` 与 `−E_discharge`。**不得改成 √0.9 或 /η**（√0.9仅在敏感性分析对比中出现）
4. **边界条件**: E_storage(0)=6000（参数）、E_storage(144)=6000（约束），初始电量**不是**优化变量
5. **容量/功率约束**: 1200≤E_storage≤10800，0≤C,D≤833.33
6. **目标函数**: min Σ Price(t)·E_buy(t)，无售电收益项
7. **求解器**: **HiGHS only**。HiGHS不可用或求解非Optimal → **STOP，返回A**，B不得自行改用CBC或其他求解器
8. **输出格式**: 见Step6，时段索引与工作表结构固定（10:00-10:10对应t=61，非t=60）
9. **执行流程**: 严格按Step0-7的8步架构（输入验证→建模→求解→状态验证→提取→硬验证→诊断→交接）；任一STEP的 `[STOP→A]` 触发即停并返回A，B不在执行中做模型决策

**允许B决定的部分**: 代码组织、变量命名、绘图细节、Excel写入的技术实现方式（列名以附件5模板为准）。

**B必须产出的交接物**: `result1.xlsx` + `validation_report.txt` + `result_data.json`（见Step7）。

---

## 快速参考

### 模型类型
线性规划 (LP) - 凸优化，全局最优保证

### 求解器
PuLP + HiGHS (Python)

### 预期性能
- 求解时间: <1秒
- 变量数: 576（144个时段 × 4类连续变量）
- 约束构成: 电力平衡(144) + 储能状态(144) + 容量上下界(288) + 充电功率上下界(288) + 放电功率上下界(288) + 购电非负(144) + 终止条件(1)

> 注: 变量的简单上下界(如0≤C≤833.33)通常由求解器作为bound处理，不计入约束矩阵行数。约束行数以求解器实际报告为准，此处仅说明模型结构，不写死具体数字。

---

## 决策变量 (576个)

```python
# 每个时段t ∈ {1, 2, ..., 144}
E_buy[t]       # 购电量 (kWh)，144个
E_charge[t]    # 名义充电能量 (kWh)，144个：输入E_charge，经效率η后 η·E_charge 存入电池
E_discharge[t] # 名义放电能量 (kWh)，144个：电池减少E_discharge，经效率η后 η·E_discharge 供给负荷
E_storage[t]   # 储电量 (kWh)，144个 (t=1~144)
```

**注意**: E_storage[0] = 6000 是参数，不是变量

**⚠️ 变量口径统一说明（消除歧义，全项目一致）**:
效率η统一作用在**流出方向**，不再区分"电网侧/电池侧"这类易矛盾的措辞：
- **充电**: `E_charge` --η--> `η·E_charge`（输入E_charge，损失10%，实际入池η·E_charge）
- **放电**: `E_discharge` --η--> `η·E_discharge`（电池放出E_discharge，损失10%，实际供负荷η·E_discharge）

对应到方程：电力平衡供给侧计 `η·E_discharge`，需求侧计 `E_charge`；状态方程入池 `+η·E_charge`、出池 `−E_discharge`。此定义数学自洽（往返η²=0.81），全文档、代码、论文一律沿用，**禁止再出现"E_discharge电池侧/E_charge电网侧"的混合表述**。

---

## 参数

```python
# 从附件1读取 (144个时间点)
Price[t]    # 电价 (元/kWh)
PV[t]       # 光伏功率预测 (kW)
Load[t]     # 负荷功率 (kW)

# 常数
dt = 1/6                    # 时间间隔 (h)
eta = 0.9                   # 单侧效率（往返81%）
E_init = 6000               # 初始/终止储电量 (kWh)
E_min = 1200                # 最小储电量 (kWh)
E_max = 10800               # 最大储电量 (kWh)
P_max = 5000                # 最大充放电功率 (kW)
E_max_per_period = P_max * dt  # 833.33 kWh
```

---

## 目标函数

```python
minimize: sum(Price[t] * E_buy[t] for t in range(1, 145))
```

---

## 约束条件

### 1. 电力平衡 (144个)
```python
for t in range(1, 145):
    E_buy[t] + PV[t]*dt + E_discharge[t]*eta >= Load[t]*dt + E_charge[t]
```

**物理意义**: 供给（购电+光伏+η·放电）≥ 需求（负荷+充电）

**⚠️ 用"≥"而非"="——允许弃光（论文必须写明）**:
- 光伏过剩时（发电 > 负荷+可吸收充电），多余部分弃掉，不强制消纳
- 隐含弃光量 W(t) = 供给 − 需求 ≥ 0；因目标只惩罚E_buy且无售电收益，优化器不会故意多购电
- **论文假设需声明**: "当光伏发电超过微网即时需求及储能可吸收量时，允许弃光，弃光不产生额外收益或成本"

### 2. 储能状态方程 (144个)
```python
for t in range(1, 145):
    E_storage[t] = E_storage[t-1] + E_charge[t]*eta - E_discharge[t]
```

**初始条件**: `E_storage[0] = 6000`

### 3. 容量约束 (288个)
```python
for t in range(1, 145):
    1200 <= E_storage[t] <= 10800
```

### 4. 充电能量约束 (288个)
```python
for t in range(1, 145):
    0 <= E_charge[t] <= 833.33   # = P_max·Δt = 5000×(1/6)
```

**侧别说明**: 5000 kW为储能装置名义最大充放电功率，直接约束名义能量变量E_charge/E_discharge，不拆分电网侧/电池侧（见model_decision.md"5000 kW功率约束的侧别定义"）。

### 5. 放电能量约束 (288个)
```python
for t in range(1, 145):
    0 <= E_discharge[t] <= 833.33
```

### 6. 购电非负 (144个)
```python
for t in range(1, 145):
    E_buy[t] >= 0
```

### 7. 边界条件 (2个)
```python
E_storage[0] = 6000    # 初始条件（参数）
E_storage[144] = 6000  # 终止条件（约束）
```

---

## 效率建模说明（重要！与上方"变量口径统一说明"一致）

**变量定义**（效率η统一作用在流出方向）:
- `E_charge[t]`: 名义充电能量，输入后损失10%，实际入池 `η·E_charge[t]`
- `E_discharge[t]`: 名义放电能量，电池放出后损失10%，实际供负荷 `η·E_discharge[t]`

**效率应用**:
- **充电**: 名义输入 `E_charge[t]` → 入池 `η·E_charge[t]`
  → 状态方程 `E_storage += η·E_charge[t]`
  
- **放电**: 电池放出 `E_discharge[t]` → 供负荷 `η·E_discharge[t]`
  → 状态方程 `E_storage −= E_discharge[t]`；电力平衡供给侧计 `η·E_discharge[t]`

**往返效率验证**:
- 名义充电1 kWh → 入池η → 原样放出后供负荷η² kWh
- η² = 0.9² = 0.81 ✓

> 说明: 此处两个变量的效率都体现在"流出损失"，数学上与decision约束1、约束2完全一致；不存在"一侧算损失、一侧不算"的矛盾。

---

## 实现步骤（8步可执行架构）

> **执行原则（GPT三审确立）**: B按此流程从上到下执行，遇STOP即返回A，**不得自行换求解器或改模型**。
> 流程: 输入验证 → 建模 → 求解 → 求解状态验证 → 结果提取 → 硬约束验证 → 诊断 → 输出交接
>
> **共享参数（模型与验证共用，改一处即全局生效，禁止散落硬编码）**:
> ```python
> import numpy as np
> import pandas as pd
> from pulp import LpProblem, LpVariable, LpMinimize, lpSum, LpStatus, value
> from pulp import HiGHS   # 若导入失败见Step0说明
>
> DT = 1/6                       # 时间间隔 (h)
> ETA = 0.9                      # 单侧效率（往返81%）
> E_INIT = 6000                  # 初始/终止储电量 (kWh)
> E_MIN, E_MAX = 1200, 10800     # 储电量范围 (kWh)
> P_MAX = 5000                   # 最大充放电功率 (kW)
> POWER_LIMIT = P_MAX * DT       # 每时段能量上界 = 833.333... kWh
> N = 144                        # 时段数
> TOL = 1e-5                     # 统一数值容差
> ```

### Step 0: 求解器可用性（HiGHS only，不允许fallback到CBC）
```python
# HiGHS是A冻结的唯一求解器。若不可用 → STOP，返回A，禁止B自行改CBC。
try:
    from pulp import HiGHS
    _solver = HiGHS(msg=True)
except Exception as e:
    raise RuntimeError(f"[STOP→A] HiGHS求解器不可用: {e}。"
                       f"请安装highspy或由A重新决策求解器，B不得自行改用CBC。")
```

### Step 1: 数据读取 + 输入验证（Level 1）
```python
df = pd.read_excel('附件1.xlsx')

# 列名以附件5/附件1真实字段为准；若与下列不符，由A确认后更新，B不自行猜测
REQUIRED_COLS = ['时间', '电价(元/kWh)', '小区负载(kW)', '光伏发电预测功率(kW)']
missing = [c for c in REQUIRED_COLS if c not in df.columns]
if missing:
    raise ValueError(f"[STOP→A] 缺少字段: {missing}；实际列名: {list(df.columns)}")

if len(df) != N:
    raise ValueError(f"[STOP→A] 数据行数应为{N}，实际{len(df)}")

# --- 时间序列验证（关键：第61个时段=10:00-10:10 的定义靠此保护）---
# 原则冻结：时间列必须严格对应 0:00, 0:10, ..., 23:50，且顺序正确。
# 附件1的“时间”若为区间字符串（如"0:00-0:10"），取起点解析；写法按附件实际格式微调，
# 但“严格等间隔10min、从0:00起、共144点、顺序正确”这一原则不得放宽。
time_raw = df['时间'].astype(str).str.split('-').str[0].str.strip()
time = pd.to_datetime(time_raw, format='%H:%M', errors='coerce')
if time.isnull().any():
    raise ValueError(f"[STOP→A] 时间列存在无法解析的值: {df['时间'][time.isnull()].tolist()}")
expected_time = pd.date_range(start=time.iloc[0].normalize(), periods=N, freq='10min')
if not (time.reset_index(drop=True) == expected_time).all():
    raise ValueError("[STOP→A] 时间序列与0:00起每10分钟的144时段不一致（起点/间隔/顺序）")

data_cols = ['电价(元/kWh)', '小区负载(kW)', '光伏发电预测功率(kW)']
if df[data_cols].isnull().any().any():
    raise ValueError("[STOP→A] 输入数据存在缺失值(NaN)")
# 除NaN外，另查无穷值（+∞/−∞ 与 NaN 不是一回事）
if not np.isfinite(df[data_cols].to_numpy(dtype=float)).all():
    raise ValueError("[STOP→A] 输入存在无穷或非有限数值(Inf)")

Price = df['电价(元/kWh)'].values.astype(float)
Load  = df['小区负载(kW)'].values.astype(float)
PV    = df['光伏发电预测功率(kW)'].values.astype(float)

assert len(Price) == len(Load) == len(PV) == N
# 电价：模型本身允许 Price=0；此处按“附件数据电价严格为正”这一数据语义设 STOP。
# 若后续确认题目允许零电价，将下行放宽为 (Price < 0).any() 即可（Price=0 合法）。
if (Price <= 0).any(): raise ValueError("[STOP→A] 电价应为正（按附件数据语义；如题目允许0电价则放宽为<0）")
if (Load  <  0).any(): raise ValueError("[STOP→A] 负荷不应为负")
if (PV    <  0).any(): raise ValueError("[STOP→A] 光伏不应为负")
print("[Level1 输入验证] PASS: 144行, 字段齐全, 时间序列正确, 无NaN/Inf, 数值合理")
```

### Step 2: 模型构建（Frozen LP，不修改）
```python
prob = LpProblem("Microgrid_Q1", LpMinimize)

# 决策变量（功率上界用共享参数POWER_LIMIT）
E_buy       = LpVariable.dicts("E_buy",       range(1, N+1), lowBound=0)
E_charge    = LpVariable.dicts("E_charge",    range(1, N+1), lowBound=0, upBound=POWER_LIMIT)
E_discharge = LpVariable.dicts("E_discharge", range(1, N+1), lowBound=0, upBound=POWER_LIMIT)
E_storage   = LpVariable.dicts("E_storage",   range(1, N+1), lowBound=E_MIN, upBound=E_MAX)

# 目标函数
prob += lpSum(Price[t-1] * E_buy[t] for t in range(1, N+1))

# 约束1: 电力平衡（≥，允许弃光）
for t in range(1, N+1):
    prob += E_buy[t] + PV[t-1]*DT + E_discharge[t]*ETA >= Load[t-1]*DT + E_charge[t]

# 约束2: 储能状态方程（充电入池 +η·E_charge，放电出池 −E_discharge）
for t in range(1, N+1):
    prev = E_INIT if t == 1 else E_storage[t-1]
    prob += E_storage[t] == prev + E_charge[t]*ETA - E_discharge[t]

# 约束3: 终止条件
prob += E_storage[N] == E_INIT
```

### Step 3: 求解 + 求解状态验证（Level 2）
```python
prob.solve(_solver)

status = LpStatus[prob.status]
if status != "Optimal":
    raise RuntimeError(f"[STOP→A] 模型未获最优解, solver status = {status}")

obj = value(prob.objective)
if obj is None or not np.isfinite(obj):
    raise RuntimeError(f"[STOP→A] 目标值非有限: {obj}")
print(f"[Level2 求解验证] PASS: Solver=HiGHS, Status=Optimal, Objective={obj:.2f}")
```

### Step 4: 结果提取（含 None 检查）
```python
def _vals(var):
    xs = [var[t].varValue for t in range(1, N+1)]
    if any(x is None for x in xs):
        raise RuntimeError("[STOP→A] 存在变量无取值(None)，求解异常")
    return xs

buy_result       = _vals(E_buy)
charge_result    = _vals(E_charge)
discharge_result = _vals(E_discharge)
storage_result   = _vals(E_storage)

total_buy  = sum(buy_result)
total_cost = sum(Price[t]*buy_result[t] for t in range(N))
```

### Step 5: 硬约束验证（Level 3）+ 诊断（Level 4）

见下方"## 验证清单"的 `validate_solution()`，必须在导出前调用。函数返回 `(all_pass, n_fail)`，`all_pass=False` 即 STOP→A；返回值同时写入 `result_data.json` 的 validation 字段（不写死True）。

### Step 6: 输出结果（格式已冻结，B按此实现，无需再解释题意）

**时段与时间对应关系**（关键，B必须严格遵守）:
- 附件1共144行，第k行(k=1..144)对应时段 [(k-1)×10min, k×10min]
- 例: 第1行=0:00-0:10，第60行=9:50-10:00，第61行=10:00-10:10
- **注意**: "10:00-10:10"是第61个时段(t=61)，不是t=60！

**表1指定时间点索引**（论文表1，6个点）:
| 时间段 | 时段索引t | Python索引(0基) |
|--------|-----------|-----------------|
| 10:00-10:10 | 61 | buy_result[60] |
| 12:00-12:10 | 73 | buy_result[72] |
| 14:00-14:10 | 85 | buy_result[84] |
| 16:00-16:10 | 97 | buy_result[96] |
| 18:00-18:10 | 109 | buy_result[108] |
| 20:00-20:10 | 121 | buy_result[120] |

**表2的6个4小时区间**（论文表2）:
| 时间段 | 时段范围t | 充电量 | 放电量 |
|--------|-----------|--------|--------|
| 0:00-4:00 | 1-24 | Σcharge | Σdischarge |
| 4:00-8:00 | 25-48 | Σcharge | Σdischarge |
| 8:00-12:00 | 49-72 | Σcharge | Σdischarge |
| 12:00-16:00 | 73-96 | Σcharge | Σdischarge |
| 16:00-20:00 | 97-120 | Σcharge | Σdischarge |
| 20:00-24:00 | 121-144 | Σcharge | Σdischarge |

- 0:00储电量 = E_init = 6000 kWh (参数)
- 24:00储电量 = E_storage[144] = 6000 kWh (约束保证)

```python
# 创建result1.xlsx（严格按附件5模板列名）
# 工作表1: "计划购电量" —— 144行，间隔10分钟的购电量
df_buy = pd.DataFrame({
    '时间段': [f"{(k-1)*10//60:02d}:{(k-1)*10%60:02d}-{k*10//60%24:02d}:{k*10%60:02d}"
             for k in range(1, 145)],
    '购电量(kWh)': buy_result
})

# 工作表2: "充放电量" —— 6个4小时区间 + 边界储电量
intervals = [(1,24,'0:00-4:00'), (25,48,'4:00-8:00'), (49,72,'8:00-12:00'),
             (73,96,'12:00-16:00'), (97,120,'16:00-20:00'), (121,144,'20:00-24:00')]
rows = []
for lo, hi, label in intervals:
    charge_sum = sum(charge_result[lo-1:hi])
    discharge_sum = sum(discharge_result[lo-1:hi])
    rows.append({'时间段': label, '充电量(kWh)': charge_sum, '放电量(kWh)': discharge_sum})
df_cd = pd.DataFrame(rows)

with pd.ExcelWriter('result1.xlsx') as writer:
    df_buy.to_excel(writer, sheet_name='计划购电量', index=False)
    df_cd.to_excel(writer, sheet_name='充放电量', index=False)
    # 0:00储电量=6000, 24:00储电量=storage_result[143]，附加写入或按附件5模板位置填写

# 论文表1数据（供C使用；total_buy/total_cost已在Step4算出）
table1_idx = [61, 73, 85, 97, 109, 121]  # 时段索引(1基)
table1 = {['10:00-10:10','12:00-12:10','14:00-14:10',
           '16:00-16:10','18:00-18:10','20:00-20:10'][i]: buy_result[t-1]
          for i, t in enumerate(table1_idx)}
print(f"全天购电量={total_buy:.2f} kWh, 全天购电费={total_cost:.2f} 元")
```

> **重要提醒给B**: 附件5的result1.xlsx模板已规定列名与工作表名，实现时以模板实际列名为准；如与上面示例列名不同，以附件5模板为准，但工作表逻辑结构不变。

### Step 7: 结果交接产物（供C/下一session，C不得从Excel或聊天记录抄数字）

除 `result1.xlsx` 外，B必须额外产出两个机器可读的交接文件：

```python
import json

# ① validation_report.txt —— 人读的验证报告
interval_summary = {label: {'charge': sum(charge_result[lo-1:hi]),
                            'discharge': sum(discharge_result[lo-1:hi])}
                    for lo, hi, label in intervals}
simultaneous = sum(1 for t in range(N)
                   if charge_result[t] > 0.01 and discharge_result[t] > 0.01)
balance_slack = sum(max(0, buy_result[t] + PV[t]*DT + discharge_result[t]*ETA
                        - Load[t]*DT - charge_result[t]) for t in range(N))
equiv_cycles = sum(charge_result) / (E_MAX - E_MIN)

with open('validation_report.txt', 'w', encoding='utf-8') as f:
    f.write("MODEL VALIDATION REPORT (Q1)\n============================\n")
    f.write("Solver: HiGHS\nStatus: Optimal\n\n")
    f.write(f"Total purchase energy = {total_buy:.4f} kWh\n")
    f.write(f"Total purchase cost   = {total_cost:.4f} yuan\n\n")
    f.write("Hard checks: ALL PASS (见validate_solution)\n\n")
    f.write("Diagnostics:\n")
    f.write(f"  Simultaneous charge/discharge = {simultaneous}\n")
    f.write(f"  Balance slack (供需富余量)     = {balance_slack:.4f} kWh\n")
    f.write(f"  Equivalent charge cycles       = {equiv_cycles:.4f}\n")

# ② result_data.json —— 机器/C/下一session读取，避免抄数字
result_data = {
    "solver_status": "Optimal",
    "total_buy_kWh": round(total_buy, 4),
    "total_cost_yuan": round(total_cost, 4),
    "table1": {k: round(v, 4) for k, v in table1.items()},
    "interval_summary": {k: {kk: round(vv, 4) for kk, vv in v.items()}
                         for k, v in interval_summary.items()},
    "soc_0000": E_INIT,
    "soc_2400": round(storage_result[-1], 4),
    "diagnostics": {
        "simultaneous_charge_discharge": simultaneous,
        "balance_slack_kWh": round(balance_slack, 4),
        "equivalent_cycles": round(equiv_cycles, 4)
    },
    # 来自 validate_solution() 实际返回值，非写死（能执行到这里即已通过前面的STOP断言）
    "validation": {"all_hard_checks_pass": validation_pass, "n_failed": validation_n_fail}
}
with open('result_data.json', 'w', encoding='utf-8') as f:
    json.dump(result_data, f, ensure_ascii=False, indent=2)
```

**交接给C的三个产物**: `result1.xlsx`（题目要求）+ `validation_report.txt`（验证报告）+ `result_data.json`（数字来源）。

---

## 验证清单

> **⚠️ 区分"必须通过的约束验证"与"诊断报告"（GPT二审要求）**:
> 同时充放电、弃光量、利用率等属于**诊断项**，不作为模型是否成立的硬门槛。
> `return` 只对约束类验证求 all()；诊断项仅打印，不影响通过判定。

```python
def validate_solution():
    """Level3硬约束验证 + Level4诊断。共用Step0的共享参数(DT/ETA/E_*/POWER_LIMIT/TOL/N)。"""
    # ===== Level 3: 必须通过的硬约束验证（决定 return）=====
    hard_checks = []

    # 1. 终止SOC边界
    hard_checks.append(("终止SOC=6000", abs(storage_result[-1] - E_INIT) < 1e-3))

    # 2. 容量约束（用共享参数+容差）
    hard_checks.append(("容量约束",
        all(E_MIN - TOL <= s <= E_MAX + TOL for s in storage_result)))

    # 3. 功率约束（上界=POWER_LIMIT，共享参数，改dt/P_max自动跟随）
    hard_checks.append(("充电功率",
        all(-TOL <= c <= POWER_LIMIT + TOL for c in charge_result)))
    hard_checks.append(("放电功率",
        all(-TOL <= d <= POWER_LIMIT + TOL for d in discharge_result)))

    # 3b. 购电量非负（Level3独立复核，不依赖变量lowBound）
    hard_checks.append(("购电量非负",
        all(b >= -TOL for b in buy_result)))

    # 4. 电力平衡（逐时）
    for t in range(N):
        supply = buy_result[t] + PV[t]*DT + discharge_result[t]*ETA
        demand = Load[t]*DT + charge_result[t]
        hard_checks.append((f"电力平衡t={t+1}", supply >= demand - TOL))

    # 5. 储能状态方程（逐时，充电+η·C、放电−D）
    for t in range(N):
        prev = E_INIT if t == 0 else storage_result[t-1]
        expected = prev + ETA*charge_result[t] - discharge_result[t]
        hard_checks.append((f"状态方程t={t+1}", abs(storage_result[t] - expected) < TOL*10))

    n_fail = sum(1 for _, ok in hard_checks if not ok)
    for name, ok in hard_checks:
        if not ok:
            print(f"❌ {name}")
    print(f"[Level3 硬约束] {'ALL PASS' if n_fail==0 else f'{n_fail} FAILED → STOP→A'}")
    all_pass = (n_fail == 0)

    # ===== Level 4: 诊断报告（不影响 return，仅供分析）=====
    simultaneous = sum(1 for t in range(N)
                       if charge_result[t] > 0.01 and discharge_result[t] > 0.01)
    balance_slack = sum(max(0, buy_result[t] + PV[t]*DT + discharge_result[t]*ETA
                            - Load[t]*DT - charge_result[t]) for t in range(N))
    equiv_cycles = sum(charge_result) / (E_MAX - E_MIN)  # 等效充电循环次数(可>1)
    print("--- Level4 诊断（非门槛）---")
    print(f"同时充放电时段数 = {simultaneous}  (理论预期0；>0则用MILP交叉验证)")
    print(f"供需平衡富余量(balance slack) = {balance_slack:.2f} kWh")
    print(f"等效充电循环次数 = {equiv_cycles:.3f}")

    return all_pass, n_fail  # 只由硬约束决定；n_fail供JSON记录

# 验证结果作为数据来源，不在JSON里写死True（GPT四审P0-3）
validation_pass, validation_n_fail = validate_solution()
if not validation_pass:
    raise RuntimeError(f"[STOP→A] 硬约束验证未通过，失败{validation_n_fail}项")
```

**命名说明（GPT三审）**:
- `balance_slack`（供需平衡富余量）: 平衡不等式的slack，非纯弃光；正电价+最小购电下通常对应弃光，但严格上只是富余量
- `equiv_cycles`（等效充电循环次数）: = 累计充电量/可用容量，可能>1（一天多次循环），不叫"利用率"
- 功率上界用共享参数 `POWER_LIMIT ± TOL`，不再写死833.33/833.34双口径

**四审新增（GPT四审）**:
- Level3 补 `购电量非负` 硬检查，使验证独立覆盖全部模型约束（不再仅依赖变量lowBound）
- `validate_solution()` 返回 `(all_pass, n_fail)`，验证结果作为数据写入JSON，不在JSON里写死True

---

## 敏感性分析（可选，不属于主执行流程）

> **GPT三审要求**: 敏感性分析**不写入主spec执行流程**，独立为 `sensitivity.md` / `sensitivity.py`，避免污染B的主任务（主spec里曾用未定义的 `solve_and_analyze()`，已移除）。

**内容**: 把主模型的Step 0-7封装为函数 `solve_q1(eta) -> result_data`，分别用 η=0.9（主方案）和 η=√0.9≈0.9487（往返90%解释）各跑一次，**对比总购电成本、总购电量、储能调度差异**。

**不预设结果方向及幅度**（删除原"预期5-15%"）: 虽然 √0.9>0.9 通常降低损耗，但具体差多少由结果决定，如实报告。

---

## 常见陷阱

❌ **错误1**: E_storage[0]作为变量
✅ **正确**: E_storage[0] = 6000是参数，不创建变量

❌ **错误2**: 效率在状态方程中用 `/eta`
✅ **正确**: 充电用`*eta`，放电直接减

❌ **错误3**: 忘记时间单位转换 PV[t]×dt
✅ **正确**: 功率(kW)需要乘以dt(h)得到能量(kWh)

❌ **错误4**: 数组索引不一致（Python从0开始，数学公式从1开始）
✅ **正确**: Price[t-1]对应数学上的Price(t)

---

## 输出文件要求

### result1.xlsx

**工作表1: 计划购电量**
- 144行，每行一个10分钟时段的购电量

**工作表2: 充放电量**
- 按题目要求的时间段汇总
- 包含0:00和24:00储电量

详细格式参考附件5模板。

---

## 联系方式

如有疑问，参考：
1. **完整决策依据**: `model_decision.md`
2. **题目分析**: `problem_definition.md`
3. **术语表**: `terminology_table.md`

---

**实现截止**: 根据workflow进度安排  
**验证标准**: Level1输入验证(144行/字段/时间序列/无NaN-Inf/数值) + Level2求解验证(Optimal) + Level3硬约束验证(含购电非负) 全部PASS  
**交付物**: `result1.xlsx` + `validation_report.txt` + `result_data.json`（三者缺一不可）
