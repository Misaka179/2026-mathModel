# Q4-2 模型规格（基于Q2 + 波动电价）

**版本**: v2.0
**日期**: 2026-09-11
**负责人**: Role A (建模手)
**状态**: 🔒 待冻结

---

## ⚠️ 重要说明

根据GPT-RE.md的审查意见，**Q4-2的建模方案极其简单**：

> **Q4-2真正新增的东西只有一个核心变量：$P \rightarrow P_t$**

**核心变化**：
```python
# Q2（固定电价）
cost = P * E_grid[t]  # P是固定值

# Q4-2（波动电价）
cost = Price[t] * E_grid[t]  # Price[t]从附件4读取
```

**其他所有内容完全继承Q2，不需要重新建模**。

---

## 1. 完全继承Q2的部分（不修改）

### 1.1 模型架构（继承model_spec_2.md）

**两层串联架构**（GPT-REVIEW1修订后）：
- **日前层**：基于简化LP评估的E_plan优化
- **日内层**：DP价值执行器（主方法），解析响应/MPC（对照）

### 1.2 日前决策层（完全继承）

**情景构造**：
- 历史联合残差，前30天完整情景（M=30），等权
- 数据来源：附件2（2025.2.1前的历史数据）

**优化模型**：
```python
# Q2的简化LP（继承model_spec_2.md §4.1）
min sum(P * E_plan[t] for t in 1..144)  # ← 唯一改动点

subject to:
    # 功率平衡
    E_plan[t] + PV_forecast[t] + E_discharge[t] = Load_forecast[t] + E_charge[t]
    
    # 储能状态方程
    SOC[t+1] = SOC[t] + η_c * E_charge[t] - E_discharge[t] / η_d
    
    # SOC约束
    1200 <= SOC[t] <= 10800
    
    # 功率约束
    0 <= E_charge[t] <= 833.33
    0 <= E_discharge[t] <= 833.33
    
    # 边界条件
    SOC[0] = 6000, SOC[144] = 6000
```

**Q4-2的修改**：
```python
# 唯一变化：目标函数
min sum(Price[t] * E_plan[t] for t in 1..144)  # Price[t]从附件4读取
#       ^^^^^^^^ 波动电价
```

### 1.3 日内执行层（完全继承）

**DP价值执行器**（继承model_spec_2.md §4.2）：
- 状态：$(SOC_t, t)$
- 决策：$(u_{charge,t}, u_{discharge,t})$
- 价值函数：$V_t(SOC_t)$反向递推
- 策略提取：前向贪心执行

**关键点**：DP的即时成本函数需要使用波动电价

```python
# Q2的即时成本（继承model_spec_2.md）
cost_instant = P * E_emergency[t]  # 紧急购电成本

# Q4-2的即时成本
cost_instant = Price[t] * E_emergency[t]  # 使用波动电价
#              ^^^^^^^^
```

**DP递推方程修改**：
```python
# Q2的DP方程
V_t(s) = min_{u} [P * emergency(s,u,t) + V_{t+1}(s')]

# Q4-2的DP方程
V_t(s) = min_{u} [Price[t] * emergency(s,u,t) + V_{t+1}(s')]
#                 ^^^^^^^^ 波动电价
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
| Δt | 1/6 h | Q1冻结 |

### 1.5 验证标准（完全继承）

**P0验证**（继承model_spec_2.md §10）：
- V1: 储能约束
- V2: 边界条件
- V3: 电力平衡
- V4: 非负性
- V5: E_plan可行性

---

## 2. Q4-2的唯一变化：波动电价

### 2.1 电价数据源

**附件4**：`C题/附件/附件4.xlsx`

**数据结构**：
```
日期          时间        电价(元/kWh)
2025/1/1     0:00        0.45
2025/1/1     0:10        0.44
...          ...         ...
2025/12/31   23:50       0.52
```

**数据规格**：
- 时间范围：2025.1.1-12.31（365天）
- 时间粒度：10分钟（每天144个时段）
- 总数据量：365 × 144 = 52,560个电价值

### 2.2 电价读取（新增）

```python
def load_price_data():
    """从附件4读取波动电价"""
    df = pd.read_excel('附件/附件4.xlsx')
    
    # 验证数据完整性
    assert len(df) == 365 * 144, "电价数据不完整"
    assert (df['电价'] > 0).all(), "存在非正电价"
    
    # 转换为二维数组 Price[d, t]
    # d: 日期索引 (0..364)
    # t: 时段索引 (0..143)
    Price = df['电价'].values.reshape(365, 144)
    
    return Price

# Q4-2求解时使用
Price_all = load_price_data()

for d in range(31, 365):  # 2025.2.1-12.31  代码里明确做日期映射，不要单纯依靠“第31行就是2月1日”的隐含假设。
    Price_d = Price_all[d, :]  # 当天的波动电价
    result = solve_Q2_model(Price_d, Load[d], PV[d], ...)
```

### 2.3 目标函数修改对比

#### Q2目标函数（固定电价）

```python
# 日前层
Z_plan = sum(P * E_plan[t] for t in range(144))

# 日内层（DP价值函数）
V_t[s] = min_u [P * E_emergency + V_{t+1}[s']]

# 总成本
Z_total = Z_plan + Z_emergency
```

#### Q4-2目标函数（波动电价）

```python
# 日前层
Z_plan = sum(Price[t] * E_plan[t] for t in range(144))
#            ^^^^^^^^ 唯一变化

# 日内层（DP价值函数）
V_t[s] = min_u [Price[t] * E_emergency + V_{t+1}[s']]
#               ^^^^^^^^ 唯一变化

# 总成本
Z_total = Z_plan + Z_emergency
```

### 2.4 代码修改示例

```python
# ===== 日前层修改 =====
def solve_day_ahead_LP(Price_t, PV_scenarios, Load_scenarios):
    """
    Q2: Price_t是标量（固定电价）
    Q4-2: Price_t是数组（波动电价，144个值）
    """
    model = LpProblem("DayAhead", LpMinimize)
    
    # 决策变量（不变）
    E_plan = [LpVariable(f"E_plan_{t}", 0) for t in range(144)]
    E_charge = [LpVariable(f"E_charge_{t}", 0, 833.33) for t in range(144)]
    E_discharge = [LpVariable(f"E_discharge_{t}", 0, 833.33) for t in range(144)]
    SOC = [LpVariable(f"SOC_{t}", 1200, 10800) for t in range(145)]
    
    # 目标函数（唯一变化）
    # Q2: model += sum(Price_t * E_plan[t] for t in range(144))
    model += sum(Price_t[t] * E_plan[t] for t in range(144))  # Q4-2
    #            ^^^^^^^^^^^ 数组索引
    
    # 约束（完全不变）
    for t in range(144):
        # 功率平衡
        model += (E_plan[t] + PV_scenarios[0][t] + E_discharge[t] == 
                  Load_scenarios[0][t] + E_charge[t])
        
        # 储能状态方程
        model += SOC[t+1] == SOC[t] + 0.9 * E_charge[t] - E_discharge[t] / 0.9
    
    # 边界条件
    model += SOC[0] == 6000
    model += SOC[144] == 6000
    
    model.solve(HiGHS())
    return [E_plan[t].varValue for t in range(144)]

# ===== 日内层修改 =====
def dp_value_iteration(Price_t, E_plan, Load_real, PV_real):
    """
    Q2: Price_t是标量
    Q4-2: Price_t是数组（144个值）
    """
    # 初始化价值函数（不变）
    V = np.zeros((145, n_states))
    
    # 反向递推（修改即时成本）
    for t in range(143, -1, -1):
        for s_idx, soc in enumerate(state_grid):
            min_cost = float('inf')
            
            for u_charge, u_discharge in action_space:
                # 计算紧急购电量
                E_emergency = calc_emergency(soc, u_charge, u_discharge, 
                                             E_plan[t], Load_real[t], PV_real[t])
                
                # 即时成本（唯一变化）
                # Q2: instant_cost = Price_t * E_emergency
                instant_cost = Price_t[t] * E_emergency  # Q4-2
                #              ^^^^^^^^^^^ 数组索引
                
                # 下一状态
                soc_next = soc + 0.9 * u_charge - u_discharge / 0.9
                
                # 贝尔曼方程
                total_cost = instant_cost + V[t+1, discretize(soc_next)]
                
                if total_cost < min_cost:
                    min_cost = total_cost
            
            V[t, s_idx] = min_cost
    
    return V

# ===== 主求解循环 =====
Price_all = load_price_data()  # 365 × 144

for d in range(31, 365):  # 2025.2.1-12.31
    # 读取当天波动电价
    Price_d = Price_all[d, :]  # 144个值
    
    # 日前层（传入波动电价数组）
    E_plan = solve_day_ahead_LP(Price_d, PV_scenarios, Load_scenarios)
    
    # 日内层（传入波动电价数组）
    V = dp_value_iteration(Price_d, E_plan, Load_real[d], PV_real[d])
    E_final, E_emergency = extract_policy(V, E_plan, Load_real[d], PV_real[d])
    
    # 成本计算（使用波动电价）
    Cost_plan[d] = sum(Price_d[t] * E_plan[t] for t in range(144))
    Cost_emergency[d] = sum(Price_d[t] * E_emergency[t] for t in range(144))
    Cost_total[d] = Cost_plan[d] + Cost_emergency[d]
```

---

## 3. 其他完全不变的部分

### 3.1 功率平衡约束（不变）

$$
E_{grid,t} + PV_t + E_{discharge,t} = Load_t + E_{charge,t}
$$

**Q4-2**: 完全不变

### 3.2 储能状态方程（不变）

$$
SOC_{t+1} = SOC_t + \eta_c \cdot E_{charge,t} - \frac{E_{discharge,t}}{\eta_d}
$$

**Q4-2**: 完全不变

### 3.3 SOC上下限（不变）

$$
SOC_{min} \leq SOC_t \leq SOC_{max}
$$

**Q4-2**: 完全不变

### 3.4 充放电功率限制（不变）

$$
0 \leq E_{charge,t} \leq P_{max} \Delta t
$$
$$
0 \leq E_{discharge,t} \leq P_{max} \Delta t
$$

**Q4-2**: 完全不变

### 3.5 终端SOC（不变）

$$
SOC_{144} = 6000
$$

**Q4-2**: 完全不变

### 3.6 DP离散化（不变）

- 状态空间：SOC ∈ [1200, 10800]，步长Δs
- 动作空间：(u_charge, u_discharge) ∈ [0, 833.33]²
- 离散化方法：线性插值

**Q4-2**: 完全不变

### 3.7 验证标准（不变）

**P0验证**（继承model_spec_2.md §10）：
- V1-V5验证项完全相同
- 验证逻辑完全相同
- 阈值完全相同

**Q4-2**: 完全不变

---

## 4. 输出规格

### 4.1 result4-2.xlsx（格式继承result2.xlsx）

**工作表1：计划购电量**
- 334行（2025.2.1-12.31）× 144列（时段）
- 单位：kWh

**工作表2：充放电量**
- 334行 × 6个4小时区间
- 单位：kWh
- 新增：0:00储电量、24:00储电量

**工作表3：紧急购电量**
- 格式同result2.xlsx
- 记录：日期 + 时间段 + 购电量

### 4.2 对比分析（新增）

**Q4-2 vs Q2成本对比**：
```python
# 计算成本差异
Delta_Z_plan = Z_plan_Q4_2 - Z_plan_Q2
Delta_Z_emergency = Z_emergency_Q4_2 - Z_emergency_Q2
Delta_Z_total = Z_total_Q4_2 - Z_total_Q2

# 分析电价影响
Price_mean_Q2 = P_fixed  # 固定电价均值
Price_mean_Q4_2 = mean(Price_all)  # 波动电价均值

if Price_mean_Q4_2 > Price_mean_Q2:
    # 预期：Q4-2成本更高
    pass
```

---

## 5. 验证方案

### 5.1 回归测试（关键）

**目的**：验证Q4-2模型的正确性

**方法**：
```python
# 构造固定电价测试
Price_test = np.full((365, 144), P_fixed)  # 所有天相同

# 运行Q4-2
result_Q4_2_test = solve_Q4_2(Price_test, Load, PV)

# 对比Q2结果
assert abs(result_Q4_2_test.cost - result_Q2.cost) < 100
```

**通过标准**：成本差异<100元（求解器数值误差）

### 5.2 数据验证（新增）

```python
def validate_price_data(Price):
    """验证附件4电价数据"""
    # 完整性
    assert Price.shape == (365, 144), "数据维度错误"
    
    # 非负性
    assert (Price > 0).all(), "存在非正电价"
    
    # 合理性
    assert 0.1 < Price.min() < Price.max() < 5.0, "电价超出合理范围"
    
    # 时间对齐（检查是否有缺失）
    # ...
    
    print("✓ 电价数据验证通过")
```

### 5.3 其他验证（继承Q2）

- V1-V5验证（完全继承model_spec_2.md §10）

---

## 6. 禁止修改的部分（🔒 冻结）

**继承Q2的冻结规格**（model_spec_2.md §1）：
1. 模型架构：两层串联
2. 日前层：简化LP评估
3. 日内层：DP价值执行器
4. 储能参数：η_c=η_d=0.9, SOC范围1200-10800, 等
5. 边界条件：SOC(0)=SOC(144)=6000
6. 求解器：HiGHS（日前LP）
7. 验证标准：P0验证V1-V5

**Q4-2唯一新增冻结**：
- 电价数据源：附件4
- 电价格式：365天×144时段波动电价

---

## 7. 实现清单

### 7.1 编程手任务

**P0（必须完成）**：
- [ ] 读取附件4电价数据
- [ ] 验证电价数据完整性、合理性
- [ ] 修改日前LP目标函数：`P` → `Price[t]`
- [ ] 修改DP即时成本：`P * E_emg` → `Price[t] * E_emg`
- [ ] 逐日求解（334天）
- [ ] 生成result4-2.xlsx
- [ ] 运行回归测试

**P1（对比分析）**：
- [ ] Q4-2 vs Q2成本对比
- [ ] 电价波动对策略的影响分析
- [ ] 生成对比图表

**P2（验证）**：
- [ ] 运行P0验证（V1-V5）
- [ ] 验证result4-2.xlsx格式正确

### 7.2 预计工作量

- 数据验证：0.5小时
- 代码修改：1小时（只改电价输入）
- 求解运行：2小时（334天）
- 回归测试：0.5小时
- 对比分析：1小时

**总计**：约5小时

---

## 8. 关键提醒

### 8.1 核心原则

> **Q4-2 = Q2 + 波动电价，不需要重新建模**

### 8.2 常见误区

❌ **错误**：重新设计日前层或日内层
✅ **正确**：只修改电价输入，其他完全复用Q2代码

❌ **错误**：修改储能参数或约束
✅ **正确**：所有参数和约束完全继承Q2

❌ **错误**：改变DP离散化或验证标准
✅ **正确**：离散化和验证标准完全继承Q2

### 8.3 代码复用建议

```python
# 推荐做法：包装Q2求解函数
def solve_Q2(Price, Load, PV, scenarios):
    """
    通用Q2求解函数
    Price: 标量（Q2）或数组（Q4-2）
    """
    # 自动适配电价格式
    if isinstance(Price, (int, float)):
        Price_array = np.full(144, Price)  # 转为数组
    else:
        Price_array = Price  # 已是数组
    
    # 统一求解逻辑
    E_plan = solve_day_ahead_LP(Price_array, scenarios)
    E_final, E_emergency = solve_day_within_DP(Price_array, E_plan, Load, PV)
    
    return E_plan, E_final, E_emergency

# Q2调用
result_Q2 = solve_Q2(P_fixed, Load, PV, scenarios)

# Q4-2调用
result_Q4_2 = solve_Q2(Price_d, Load, PV, scenarios)  # Price_d是数组
```

---

## 9. 文档状态

**版本历史**：
- v1.0：初版（基于完整重建模思路）
- v2.0：根据GPT-RE.md修订（强调继承Q2，最小化变动）

**当前状态**：✅ 已修订，待冻结

**下一步**：等待人工确认 → 🔒 MODEL FROZEN → 交接给编程手

---

**修订说明**：
- 根据GPT-RE.md，Q4-2的核心变化只有 `P → P_t`
- 所有其他内容（模型架构、约束、参数、验证）完全继承Q2
- 大幅简化实现工作量（从14小时降至5小时）
- 强调代码复用和最小化修改原则

🔒 **MODEL FROZEN** (待标记)
