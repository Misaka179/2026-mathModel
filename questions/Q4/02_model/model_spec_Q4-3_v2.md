# Q4-3 模型规格（基于Q3 + 波动电价）

**版本**: v2.0（根据GPT-RE.md修订）
**日期**: 2026-09-11
**负责人**: Role A (建模手)
**状态**: 🔒 待冻结

---

## ⚠️ 重要说明

根据GPT-RE.md的审查意见，**Q4-3的建模方案极其简单**：

> **核心仍然只是：$P \rightarrow P_t$**

**你现在的Q3模型已经比较复杂了**，包含：
- 日前计划
- 预测光伏
- 实际光伏
- 滚动优化
- 调整量 δ⁺、δ⁻
- 储能、SOC
- 应急购电
- 100 kW 预测变化阈值

**这些东西第四问原则上都不需要重新建模**。

---

## 1. 完全继承Q3的部分（不修改）

### 1.1 模型类型（继承model_spec_3.md）

**确定性多阶段滚动优化**（Deterministic Multi-Stage Receding Horizon Optimization）

**决策时刻**：
- Stage 1 (0:00): 日前计划购电
- Stage 2 (6:00): 第一次调整
- Stage 3 (12:00): 第二次调整
- Stage 4 (18:00): 第三次调整

### 1.2 Stage 1优化（0:00日前计划）

**模型**（继承model_spec_3.md §3.1）：
```python
# Q3的Stage 1 LP
min sum(P * E_plan[t] for t in range(144))  # ← 唯一改动点

subject to:
    # 电力平衡
    E_plan[t] + PV_forecast_0[t] + E_discharge[t] = Load_forecast[t] + E_charge[t]
    
    # 储能状态方程
    SOC[t+1] = SOC[t] + 0.9 * E_charge[t] - E_discharge[t] / 0.9
    
    # SOC约束
    1200 <= SOC[t] <= 10800
    
    # 功率约束
    0 <= E_charge[t] <= 833.33
    0 <= E_discharge[t] <= 833.33
    
    # 边界条件
    SOC[0] = 6000, SOC[144] = 6000
```

**Q4-3的修改**：
```python
# 唯一变化：目标函数
min sum(Price[t] * E_plan[t] for t in range(144))  # Price[t]从附件4读取
#       ^^^^^^^^ 波动电价
```

### 1.3 Stage k调整优化（6:00/12:00/18:00）

**调整触发条件**（完全继承model_spec_3.md §3.2）：
```python
# 平均预报改善度
Delta_PV_avg = mean(abs(PV_forecast_k - PV_forecast_prev))

if Delta_PV_avg > 100:  # kW阈值
    # 启用调整
    solve_adjustment_LP(k)
```

**调整LP模型**（继承model_spec_3.md §3.2）：
```python
# Q3的Stage k LP
min sum(2.5 * P * delta_plus[t] - 0.5 * P * delta_minus[t] 
        for t in range(t_k, 144))  # ← 唯一改动点

subject to:
    # 调整关系
    E_adjust[t] = E_base[t] + delta_plus[t] - delta_minus[t]
    
    # 电力平衡（使用新预报）
    E_adjust[t] + PV_forecast_k[t] + E_discharge[t] = Load_forecast[t] + E_charge[t]
    
    # 储能约束（同Stage 1）
    # ...
```

**Q4-3的修改**：
```python
# 唯一变化：目标函数
min sum(2.5 * Price[t] * delta_plus[t] - 0.5 * Price[t] * delta_minus[t] 
        for t in range(t_k, 144))  # Price[t]从附件4读取
#       ^^^^^^^^                   ^^^^^^^^ 波动电价
```

### 1.4 储能参数（完全继承Q1冻结规格）

| 参数 | 值 | 来源 |
|------|-----|------|
| η_c | 0.9 | Q1冻结 |
| η_d | 0.9 | Q1冻结 |
| SOC_min | 1200 kWh | Q1冻结 |
| SOC_max | 10800 kWh | Q1冻结 |
| P_max | 5000 kW | Q1冻结 |
| SOC_init | 6000 kWh | Q1冻结 |

### 1.5 调整阈值（完全继承）

**预报改善度阈值**：100 kW（继承model_spec_3.md §4.3）

### 1.6 验证标准（完全继承）

**P0验证**（继承model_spec_3.md §11）：
- V1: 储能约束
- V2: 边界条件
- V3: 电力平衡
- V4: 因果性
- V5: 调整关系

---

## 2. Q4-3的唯一变化：波动电价

### 2.1 电价数据源（同Q4-2）

**附件4**：`C题/附件/附件4.xlsx`
- 365天 × 144时段 = 52,560个电价值

### 2.2 电价读取（同Q4-2）

```python
Price_all = load_price_data()  # 365 × 144

for d in range(31, 365):  # 2025.2.1-12.31
    Price_d = Price_all[d, :]  # 当天的波动电价
    result = solve_Q3_model(Price_d, Load[d], PV[d], PV_forecasts[d], ...)
```

### 2.3 目标函数修改对比

#### Q3目标函数（固定电价）

```python
# Stage 1 (0:00)
Z_plan = sum(P * E_plan[t] for t in range(144))

# Stage k (6:00/12:00/18:00)
Z_adjust_k = sum(1.5 * P * delta_plus[t] + 0.5 * P * delta_minus[t]
                 for t in range(t_k, 144))

# 总成本
Z_total = Z_plan + sum(Z_adjust_k) + Z_emergency
```

#### Q4-3目标函数（波动电价）

```python
# Stage 1 (0:00)
Z_plan = sum(Price[t] * E_plan[t] for t in range(144))
#            ^^^^^^^^ 唯一变化

# Stage k (6:00/12:00/18:00)
Z_adjust_k = sum(1.5 * Price[t] * delta_plus[t] + 0.5 * Price[t] * delta_minus[t]
#                      ^^^^^^^^                           ^^^^^^^^ 唯一变化
                 for t in range(t_k, 144))

# 总成本
Z_total = Z_plan + sum(Z_adjust_k) + Z_emergency
```

### 2.4 代码修改示例

```python
# ===== Stage 1修改 =====
def solve_stage1_LP(Price_t, PV_forecast_0, Load_forecast):
    """
    Q3: Price_t是标量（固定电价）
    Q4-3: Price_t是数组（波动电价，144个值）
    """
    model = LpProblem("Stage1", LpMinimize)
    
    # 决策变量（不变）
    E_plan = [LpVariable(f"E_plan_{t}", 0) for t in range(144)]
    E_charge = [LpVariable(f"E_charge_{t}", 0, 833.33) for t in range(144)]
    E_discharge = [LpVariable(f"E_discharge_{t}", 0, 833.33) for t in range(144)]
    SOC = [LpVariable(f"SOC_{t}", 1200, 10800) for t in range(145)]
    
    # 目标函数（唯一变化）
    # Q3: model += sum(Price_t * E_plan[t] for t in range(144))
    model += sum(Price_t[t] * E_plan[t] for t in range(144))  # Q4-3
    #            ^^^^^^^^^^^ 数组索引
    
    # 约束（完全不变）
    for t in range(144):
        model += (E_plan[t] + PV_forecast_0[t] + E_discharge[t] == 
                  Load_forecast[t] + E_charge[t])
        model += SOC[t+1] == SOC[t] + 0.9 * E_charge[t] - E_discharge[t] / 0.9
    
    model += SOC[0] == 6000
    model += SOC[144] == 6000
    
    model.solve(HiGHS())
    return [E_plan[t].varValue for t in range(144)]

# ===== Stage k调整修改 =====
def solve_stagek_LP(k, Price_t, E_base, PV_forecast_k, Load_forecast, SOC_init):
    """
    Q3: Price_t是标量
    Q4-3: Price_t是数组（144个值）
    """
    t_k = {6: 36, 12: 72, 18: 108}[k]
    model = LpProblem(f"Stage{k}", LpMinimize)
    
    # 决策变量（不变）
    E_adjust = [LpVariable(f"E_adjust_{t}", 0) for t in range(t_k, 144)]
    delta_plus = [LpVariable(f"delta_plus_{t}", 0) for t in range(t_k, 144)]
    delta_minus = [LpVariable(f"delta_minus_{t}", 0) for t in range(t_k, 144)]
    E_charge = [LpVariable(f"E_charge_{t}", 0, 833.33) for t in range(t_k, 144)]
    E_discharge = [LpVariable(f"E_discharge_{t}", 0, 833.33) for t in range(t_k, 144)]
    SOC = [LpVariable(f"SOC_{t}", 1200, 10800) for t in range(t_k, 145)]
    
    # 目标函数（唯一变化）
    # Q3: model += sum(2.5 * Price_t * delta_plus[t] - 0.5 * Price_t * delta_minus[t] ...)
    model += sum(2.5 * Price_t[t] * delta_plus[i] - 0.5 * Price_t[t] * delta_minus[i]
                 for i, t in enumerate(range(t_k, 144)))  # Q4-3
    #            ^^^^^^^^^^^ 数组索引        ^^^^^^^^^^^ 数组索引
    
    # 约束（完全不变）
    for i, t in enumerate(range(t_k, 144)):
        # 调整关系
        model += E_adjust[i] == E_base[t] + delta_plus[i] - delta_minus[i]
        
        # 电力平衡
        model += (E_adjust[i] + PV_forecast_k[t] + E_discharge[i] == 
                  Load_forecast[t] + E_charge[i])
        
        # 储能状态方程
        if i == 0:
            E_prev = SOC_init
        else:
            E_prev = SOC[i-1]
        model += SOC[i] == E_prev + 0.9 * E_charge[i] - E_discharge[i] / 0.9
    
    model += SOC[-1] == 6000
    
    model.solve(HiGHS())
    return [E_adjust[i].varValue for i in range(len(E_adjust))]

# ===== 主求解循环 =====
Price_all = load_price_data()  # 365 × 144

for d in range(31, 365):  # 2025.2.1-12.31
    # 读取当天波动电价
    Price_d = Price_all[d, :]  # 144个值
    
    # Stage 1: 0:00
    E_plan = solve_stage1_LP(Price_d, PV_forecast_0[d], Load_forecast[d])
    
    # Stage 2: 6:00（如果启用）
    if should_adjust(6, PV_forecast_6[d], PV_forecast_0[d]):
        E_adjust_6 = solve_stagek_LP(6, Price_d, E_plan, 
                                      PV_forecast_6[d], Load_forecast[d], SOC_6)
    
    # Stage 3: 12:00（如果启用）
    if should_adjust(12, PV_forecast_12[d], PV_forecast_6[d]):
        E_adjust_12 = solve_stagek_LP(12, Price_d, E_adjust_6 or E_plan,
                                       PV_forecast_12[d], Load_forecast[d], SOC_12)
    
    # Stage 4: 18:00（如果启用）
    if should_adjust(18, PV_forecast_18[d], PV_forecast_12[d]):
        E_adjust_18 = solve_stagek_LP(18, Price_d, E_adjust_12 or E_adjust_6 or E_plan,
                                       PV_forecast_18[d], Load_forecast[d], SOC_18)
    
    # 实时执行：计算紧急购电
    E_final = E_adjust_18 or E_adjust_12 or E_adjust_6 or E_plan
    E_emergency = calc_emergency(E_final, Load_real[d], PV_real[d])
    
    # 成本计算（使用波动电价）
    Cost_plan[d] = sum(Price_d[t] * E_plan[t] for t in range(144))
    Cost_adjust[d] = sum(1.5 * Price_d[t] * delta_plus[t] + 
                         0.5 * Price_d[t] * delta_minus[t] for adjustments)
    Cost_emergency[d] = sum(Price_d[t] * E_emergency[t] for t in range(144))
    Cost_total[d] = Cost_plan[d] + Cost_adjust[d] + Cost_emergency[d]
```

---

## 3. 其他完全不变的部分

### 3.1 功率平衡约束（不变）

$$
E_{grid,t} + PV_t + E_{discharge,t} = Load_t + E_{charge,t}
$$

**Q4-3**: 完全不变

### 3.2 储能状态方程（不变）

$$
SOC_{t+1} = SOC_t + \eta_c \cdot E_{charge,t} - \frac{E_{discharge,t}}{\eta_d}
$$

**Q4-3**: 完全不变

### 3.3 SOC上下限（不变）

$$
1200 \leq SOC_t \leq 10800
$$

**Q4-3**: 完全不变

### 3.4 调整关系（不变）

$$
E_{adjust,t} = E_{base,t} + \delta_t^+ - \delta_t^-
$$

**Q4-3**: 完全不变

### 3.5 因果性约束（不变）

- Stage k只能调整 $t \geq t_k$ 的时段
- 已执行时段不可回溯修改

**Q4-3**: 完全不变

### 3.6 调整触发逻辑（不变）

```python
Delta_PV_avg = mean(abs(PV_forecast_k - PV_forecast_prev))
if Delta_PV_avg > 100:  # kW
    trigger_adjustment = True
```

**Q4-3**: 完全不变

### 3.7 预报插值方法（不变）

- 线性插值：整点 → 10分钟粒度
- 负载估计：历史均值（日前）+ 真值（日内已过）

**Q4-3**: 完全不变

### 3.8 验证标准（不变）

**P0验证**（继承model_spec_3.md §11）：
- V1-V5验证项完全相同

**Q4-3**: 完全不变

---

## 4. 输出规格

### 4.1 result4-3.xlsx（格式继承result3.xlsx）

**工作表1：计划购电量**
- 334行×144列
- 单位：kWh

**工作表2：调整购电量**
- 记录有调整的日期 + 调整时刻 + 调整后购电量
- 格式同result3.xlsx

**工作表3：充放电量**
- 334行×6个4小时区间 + 0:00和24:00储电量
- 格式同result3.xlsx

**工作表4：紧急购电量**
- 日期 + 时间段 + 购电量
- 格式同result3.xlsx

### 4.2 对比分析（新增）

**Q4-3 vs Q3成本对比**：
```python
# 成本分解对比
Delta_Z_plan = Z_plan_Q4_3 - Z_plan_Q3
Delta_Z_adjust = Z_adjust_Q4_3 - Z_adjust_Q3
Delta_Z_emergency = Z_emergency_Q4_3 - Z_emergency_Q3
Delta_Z_total = Z_total_Q4_3 - Z_total_Q3

# 调整频率对比
freq_Q3 = count_adjustments(result_Q3)
freq_Q4_3 = count_adjustments(result_Q4_3)
```

---

## 5. 验证方案

### 5.1 回归测试（关键）

**目的**：验证Q4-3模型的正确性

**方法**：

```python
# 构造固定电价测试
Price_test = np.full((365, 144), P_fixed)  # 所有天相同

# 运行Q4-3
result_Q4_3_test = solve_Q4_3(Price_test, Load, PV, PV_forecasts)

# 对比Q3结果
assert abs(result_Q4_3_test.cost - result_Q3.cost) < 100
```

**通过标准**：成本差异<100元

### 5.2 数据验证（新增）

```python
def validate_price_data(Price):
    """验证附件4电价数据"""
    assert Price.shape == (365, 144)
    assert (Price > 0).all()
    assert 0.1 < Price.min() < Price.max() < 5.0
    print("✓ 电价数据验证通过")
```

### 5.3 其他验证（继承Q3）

- V1-V5验证（完全继承model_spec_3.md §11）

---

## 6. 禁止修改的部分（🔒 冻结）

**继承Q3的冻结规格**（model_spec_3.md §1-12）：
1. 模型类型：确定性多阶段滚动优化
2. 决策时刻：0:00/6:00/12:00/18:00
3. 调整阈值：100 kW（平均预报改善度）
4. 调整成本系数：1.5（增购）、0.5（减购）
5. 储能参数：η=0.9, SOC范围1200-10800, 等
6. 边界条件：SOC(0)=SOC(144)=6000
7. 求解器：HiGHS
8. 验证标准：P0验证V1-V5

**Q4-3唯一新增冻结**：
- 电价数据源：附件4
- 电价格式：365天×144时段波动电价

---

## 7. 实现清单

### 7.1 编程手任务

**P0（必须完成）**：
- [ ] 读取附件4电价数据
- [ ] 验证电价数据完整性、合理性
- [ ] 修改Stage 1 LP目标函数：`P` → `Price[t]`
- [ ] 修改Stage k LP目标函数：`1.5*P*δ⁺+0.5*P*δ⁻` → `1.5*Price[t]*δ⁺+0.5*Price[t]*δ⁻`
- [ ] 逐日求解（334天，每天最多4个阶段）
- [ ] 生成result4-3.xlsx
- [ ] 运行回归测试

**P1（对比分析）**：
- [ ] Q4-3 vs Q3成本对比
- [ ] 调整频率对比
- [ ] 波动电价对调整策略的影响分析
- [ ] 生成对比图表

**P2（验证）**：
- [ ] 运行P0验证（V1-V5）
- [ ] 验证result4-3.xlsx格式正确

### 7.2 预计工作量

- 数据验证：0.5小时
- 代码修改：1.5小时（修改3个LP的电价输入）
- 求解运行：3小时（334天×4阶段）
- 回归测试：0.5小时
- 对比分析：1.5小时

**总计**：约7小时

---

## 8. 关键提醒

### 8.1 核心原则

> **Q4-3 = Q3 + 波动电价，不需要重新建模**

### 8.2 常见误区

❌ **错误**：重新设计滚动优化或调整机制
✅ **正确**：只修改电价输入，其他完全复用Q3代码

❌ **错误**：修改调整阈值或调整成本系数
✅ **正确**：阈值100kW和系数1.5/0.5完全继承Q3

❌ **错误**：改变预报插值或负载估计方法
✅ **正确**：所有数据处理方法完全继承Q3

### 8.3 代码复用建议

```python
# 推荐做法：包装Q3求解函数
def solve_Q3(Price, Load, PV, PV_forecasts):
    """
    通用Q3求解函数
    Price: 标量（Q3）或数组（Q4-3）
    """
    # 自动适配电价格式
    if isinstance(Price, (int, float)):
        Price_array = np.full(144, Price)
    else:
        Price_array = Price
    
    # Stage 1
    E_plan = solve_stage1_LP(Price_array, PV_forecasts[0], Load_forecast)
    
    # Stage 2-4（如果启用）
    E_final = E_plan
    for k in [6, 12, 18]:
        if should_adjust(k, PV_forecasts[k], PV_forecasts[k-1]):
            E_final = solve_stagek_LP(k, Price_array, E_final, 
                                       PV_forecasts[k], Load_forecast, SOC_k)
    
    # 实时执行
    E_emergency = calc_emergency(E_final, Load, PV)
    
    return E_plan, E_final, E_emergency

# Q3调用
result_Q3 = solve_Q3(P_fixed, Load, PV, PV_forecasts)

# Q4-3调用
result_Q4_3 = solve_Q3(Price_d, Load, PV, PV_forecasts)  # Price_d是数组
```

---

## 9. 波动电价对Q4-3的特殊影响

### 9.1 调整策略的收益-成本权衡

**Q3（固定电价）**：
- 调整收益主要来自预报改善
- 调整成本固定（1.5P增购、0.5P减购）

**Q4-3（波动电价）**：
- 调整收益仍来自预报改善
- 但调整成本随电价波动：
  - 高电价时段：调整成本高，可能抑制调整
  - 低电价时段：调整成本低，可能促进调整

**示例**：
```python
# 假设某天6:00时刻
if Price[t] > 1.0:  # 高电价
    # 即使预报改善显著，调整成本1.5*Price[t]也很高
    # 可能选择不调整，接受紧急购电
    pass

if Price[t] < 0.5:  # 低电价
    # 调整成本1.5*Price[t]较低
    # 更倾向于调整
    pass
```

### 9.2 预期差异

**调整频率**：
- Q3的调整频率相对稳定（只看预报改善）
- Q4-3的调整频率可能更动态（受电价影响）

**总成本**：
- 如果波动电价均值高于固定电价，Z_Q4-3 > Z_Q3
- 但调整的相对价值可能变化

---

## 10. 文档状态

**版本历史**：
- v1.0：初版（基于完整重建模思路）
- v2.0：根据GPT-RE.md修订（强调继承Q3，最小化变动）

**当前状态**：✅ 已修订，待冻结

**下一步**：等待人工确认 → 🔒 MODEL FROZEN → 交接给编程手

---

**修订说明**：
- 根据GPT-RE.md，Q4-3的核心变化只有 `P → P_t`
- 所有其他内容（滚动优化、调整机制、阈值、参数）完全继承Q3
- 大幅简化实现工作量（从14小时降至7小时）
- 强调代码复用和最小化修改原则

🔒 **MODEL FROZEN** (待标记)
