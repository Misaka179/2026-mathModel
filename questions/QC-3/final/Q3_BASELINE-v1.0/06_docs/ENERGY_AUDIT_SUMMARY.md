# 能量守恒审计总结（简版）

## 核心发现

**原诊断报告的"能量闭合误差"实际上是隐含弃光量。**

---

## 审计结果

### ✅ 模型物理正确

| 验证项 | 结果 | 误差 |
|--------|------|------|
| ΔSOC一致性（A=B=C） | 通过 | <0.01 kWh |
| 充放电关系 | 通过 | 0.000000 kWh |
| 能量平衡（含弃光） | 通过 | 0.000000 kWh |

### ⚠️ 大量隐含弃光

```
全年光伏发电：19,068,890 kWh
全年弃光量：  2,309,542 kWh
全年弃光率：  12.11%
```

| 统计指标 | Mean | Median | P95 | Max |
|---------|------|--------|-----|-----|
| 日弃光量 (kWh) | 6,915 | 4,357 | 21,990 | 26,903 |
| 日弃光率 (%) | 11.51 | 7.28 | 32.60 | 39.38 |

**334天中：**
- 100% 天数弃光率 > 1%
- 66.8% 天数弃光率 > 5%
- 37.1% 天数弃光率 > 10%
- 22.5% 天数弃光率 > 20%

---

## 正确的能量平衡方程

```
E_grid + E_PV + E_discharge = E_load + E_charge + E_curtail
```

**验证：完美闭合（误差 = 0.000000 kWh）** ✅

---

## 原诊断程序的错误

### 错误公式
```python
# 原诊断 (diagnostic_334days_run.py:136-141)
charge_loss = (1 - ETA) * total_charge          # ✓ 正确
discharge_loss = (1 / ETA - 1) * total_discharge # ✗ 错误（重复计算）
energy_in = E_buy + E_pv
energy_out = E_load + delta_SOC + charge_loss + discharge_loss  # 遗漏弃光
```

### 问题
1. **重复计算放电损耗**：模型中放电无损耗（discharge是输出功率）
2. **遗漏弃光项**：电力平衡约束是不等式（≥），允许供给>需求

### 实际含义
```
原报告的"能量闭合误差" ≈ 隐含弃光量
```

---

## 弃光产生原因

### 模型约束
```python
# q3_model_scenario_v1.2.py:689-691
prob += (E_plan[t] + E_emergency[t] + η·E_discharge[t]·DT ≥ 
         net_load_energy + E_charge[t]·DT)  # 不等式，允许弃光
```

### 可能原因
1. **储能容量饱和**（SOC达上限，无法继续充电）
2. **充电功率限制**（5 MW上限，光伏高发时无法全部吸纳）
3. **经济优化决策**（低电价时段宁可弃光）
4. **瞬时功率不匹配**（证据：0天SOC>90%，非系统性饱和）

---

## 改进建议

### 立即可做

**添加显式弃光变量和惩罚：**
```python
E_curtail = [pulp.LpVariable(f"E_curtail_{t}", lowBound=0) for t in range(N_SLOTS)]

# 电力平衡改为等式
prob += (E_plan[t] + E_emergency[t] + η·E_discharge[t]·DT == 
         net_load_energy + E_charge[t]·DT + E_curtail[t])

# 目标函数加入弃光成本
cost += sum([ALPHA_CURTAIL * price[t] * E_curtail[t] for t in range(N_SLOTS)])
```

### 中长期

1. **增加储能容量**（10.8 MWh → 15-20 MWh）
2. **增加充电功率**（5 MW → 7-10 MW）
3. **改进光伏预测**
4. **需求响应机制**

---

## 论文撰写建议

### ✅ 可以使用当前结果
- 能量守恒正确
- 物理约束满足
- 成本计算准确

### ⚠️ 必须说明
1. **报告弃光率**：全年12.11%
2. **解释原因**：瞬时功率不匹配、储能限制
3. **讨论改进**：添加弃光惩罚的对比实验

### 建议对比实验
- **Baseline**：当前模型（12.11%弃光）
- **Scenario A**：添加弃光惩罚（ALPHA_CURTAIL = 0.5）
- **Scenario B**：增加储能容量至15 MWh
- **Scenario C**：同时实施A+B

对比指标：总成本、弃光率、储能利用率

---

## 数据文件

| 文件 | 说明 |
|------|------|
| `ENERGY_AUDIT_REPORT.md` | 完整审计报告 |
| `curtailment_analysis.xlsx` | 334天弃光数据 |
| `final_energy_audit.xlsx` | 完整能量账本 |
| `curtailment_analysis.py` | 弃光分析脚本 |
| `final_energy_audit.py` | 能量审计脚本 |
| `energy_balance_theory.py` | 理论推导 |

---

## 结论

**模型物理守恒完全正确，"能量闭合误差"实际上是12.11%的隐含弃光。**

建议添加显式弃光变量和惩罚，进行对比实验后纳入论文。
