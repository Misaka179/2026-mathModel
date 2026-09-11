# C题Q2 模型实现规格说明

**模型状态**: 🔒 MODEL FROZEN (已根据GPT-review1.md修订)  
**目标读者**: Role B (编程手)  
**前置文档**: model_decision.md (完整决策依据)、problem_definition.md (数学模型)

---

## ⛔ 禁止修改的部分（B不得自行更改，如需变更返工给A）

以下为已冻结的模型核心，B只负责实现、不得重新解释题意或改动：

### 架构层面（⚠️ 已修订）
1. **模型架构**: 日前随机优化 + 因果动态储能控制（两层串联），不融合成超级模型
2. **日前层定位**: ⚠️ 非标准两阶段随机LP，而是"基于简化LP评估的E_plan优化"
3. **日内层类型**: DP价值执行器（主方法），解析响应/MPC（对照）
4. **执行顺序**: 先日前LP得E_plan → 构建DP价值函数 → 实时执行

### 日前决策层（⚠️ 关键修订）
5. **情景构造**: 历史联合残差，前30天完整情景（M=30），等权π_s=1/M
6. **非提前性**: E_plan(t)对所有情景同值（第一阶段变量）
7. **储能变量说明**: ⚠️ LP中的E_charge^s, E_discharge^s, E_storage^s, E_emg^s **仅用于日前评估期望成本，不代表实际执行**
8. **边界条件**: ⚠️ E_storage^s(0)=6000、E_storage^s(144)=6000是**建模假设**（非题目明确要求），需敏感性分析
9. **目标函数**: min Σ Price·E_plan + Σ π_s·5·Price·E_emg^s（期望紧急费用的LP近似）
10. **求解器**: **HiGHS only**，不可用或非Optimal → **STOP→A**

### 日内执行层
11. **DP构建**: 每日0:00构建M条历史路径H_{t,ω}(e)，平均得H̄_t(e)
12. **实时决策**: argmin{当前紧急费 + H̄_{t+1}(e+x)}，平衡当前与未来，**满足因果性**
13. **效率转换**: ψ(x) = x/η (充电), ψ(x) = ηx (放电)
14. **终端价值**: H_{T+1,ω}(e) = -v·e，v≈0.48元/kWh（⚠️ 需敏感性分析v∈{0.3,0.4,0.48,0.6,0.8}）
15. **对照执行器**: 必须实现解析响应、MPC用于V7验证

### 继承Q1冻结核心
16. **效率**: η=0.9单侧，状态方程+η·C−D，平衡+η·D−C
17. **容量/功率**: 1200≤E≤10800，0≤C,D≤833.33
18. **变量口径**: E_charge/E_discharge为名义能量，效率统一流出方向
19. **求解器纪律**: HiGHS only，不fallback到CBC

### 验证要求（⚠️ 已修订）
20. **V7关键验证**: 固定计划执行器对照，⚠️ **比较三种执行器性能并分析**，不预设"DP≤MPC"为通过标准
21. **输出文件**: result2.xlsx + validation_report_q2.txt + result_data_q2.json + executor_comparison.xlsx

### 必须进行的敏感性分析（⚠️ 审稿强制要求）
22. **M值敏感性**: M ∈ {10, 30, 60}，验证M=30选择合理性（随机抽 **20–30 个代表性日期**即可，目的在于证明M=30 参数合理性。
23. **v值敏感性**: v ∈ {0.3, 0.48,  0.8}，验证终端价值参数稳定性（同样抽 20–30 天。
24. **SOC边界敏感性**: 至少做这三种：独立日(E(144)=6000) vs 终端价值函数(E(144)自由) vs 全年 SOC 连续衔接

**允许B决定的部分**: 代码组织、变量命名、绘图细节、Excel写入技术实现。

---

## 快速参考

### 模型类型
- 日前层：基于简化LP评估的随机优化（⚠️ 非标准两阶段随机LP）
- 日内层：DP因果储能控制（基于历史平均未来价值）
- 关键特点：日前评估与实际执行分离，通过历史回测验证偏差可接受

### 求解器
PuLP + HiGHS (Python)

### 预期性能
- 日前层：单日<5秒（M=30情景，≈17k变量）
- 日内层：每日0:00构建DP<10秒，实时决策<0.1秒/时段
- 全年334天：总计<30分钟

### 执行阶段
1. **P1门禁**（最小可运行）：日前LP + 解析响应 → result2.xlsx
2. **P2门禁**（编程终检）：DP执行器 + V7验证 → 全部交接文件

---

## 模型规格：日前决策层（基于简化LP评估的随机优化）

### ⚠️ 核心建模说明（必读）

**模型定位**：
本方案**不追求日前计划与日内控制策略在数学意义上的联合全局最优**，而采用**"日前近似随机优化 + 日内因果动态控制"的分层求解框架**，以降低多阶段随机优化的计算复杂度。

**日前层与日内层的关系**：
```
日前层优化问题：
  min_{E_plan} C_plan(E_plan) + E_s[C_LP-recourse(E_plan, s)]
  ↓
  生成 E_plan*

实际执行问题：
  给定 E_plan*，DP执行器按因果规则实时决策
  C_real = C_plan + C_DP(E_plan*, realized_path)

关键：C_LP-recourse ≠ C_DP（模型不一致）
```

**为什么这样做**：
- 完整多阶段非提前性约束需17k+变量，计算成本过高
- 日前LP用情景储能变量快速评估不同E_plan的风险与调节能力
- 日内DP用因果规则实际执行，满足非提前性
- **通过滚动历史回测评价整个闭环系统**，而非仅评价日前LP本身

**最终验证方式**：
不追求"日前LP预测准确"，而是验证"日前LP生成的E_plan + DP执行器闭环系统的实际成本优于基准方案"。

---

### 输入数据

```python
# 从附件读取
Price[t]       # 电价，144点 (元/kWh)，附件1，全区间复用
Load_real[d,t] # 真实负载，365×144 (kW)，附件2工作表1
PV_real[d,t]   # 真实光伏，365×144 (kW)，附件2工作表2

# 规划期
days = range(Feb1, Dec31)  # 2025.2.1-12.31，共334天
```

### 情景构造（历史联合残差）

```python
def construct_scenarios(day_d):
    """
    对规划日d，构造M个历史联合残差情景
    """
    # Step 1: 生成当天预测（仅用d之前历史）
    Load_forecast_d = historical_forecast_load(day_d, method='same_weekday_35days')
    PV_forecast_d = historical_forecast_pv(day_d, method='recent_7days')
    
    # Step 2: 获取前30天历史残差（同日配对）
    scenarios = []
    for i in range(d-30, d):  # 历史日i
        # 历史预测（用i日当时可获得信息）
        Load_forecast_i = historical_forecast_load(day_i, ...)
        PV_forecast_i = historical_forecast_pv(day_i, ...)
        
        # 历史残差（144点）
        ε_L_i = Load_real[i] - Load_forecast_i
        ε_V_i = PV_real[i] - PV_forecast_i
        
        # 生成情景（截断负值）
        Load_scenario_s = np.maximum(Load_forecast_d + ε_L_i, 0)
        PV_scenario_s = np.maximum(PV_forecast_d + ε_V_i, 0)
        
        scenarios.append({
            'load': Load_scenario_s,
            'pv': PV_scenario_s,
            'weight': 1.0/M  # 等权
        })
    
    return scenarios  # M=len(scenarios)

# 特殊情况处理
# - 2.1-2.29：历史天数<30，取实际可用天数
# - 1月：不进入规划期（题目从2.1开始）
```

### 决策变量（日前层）

```python
# 第一阶段变量（情景无关，144个）
E_plan = {t: LpVariable(f'E_plan_{t}', 0, None) for t in range(1, 145)}

# 第二阶段变量（每情景s一套，M×576个）
for s in scenarios:
    E_charge_s = {t: LpVariable(f'E_charge_s{s}_{t}', 0, POWER_LIMIT) 
                  for t in range(1, 145)}
    E_discharge_s = {t: LpVariable(f'E_discharge_s{s}_{t}', 0, POWER_LIMIT) 
                     for t in range(1, 145)}
    E_storage_s = {t: LpVariable(f'E_storage_s{s}_{t}', E_min, E_max) 
                   for t in range(1, 145)}
    E_emg_s = {t: LpVariable(f'E_emg_s{s}_{t}', 0, None) 
               for t in range(1, 145)}

# 总变量数：144（第一阶段）+ M×576（第二阶段）
# M=30时：144 + 30×576 = 17424个
```

### 参数（继承Q1）

```python
dt = 1/6                # 时间间隔 (h)
eta = 0.9               # 单侧效率（往返81%）
E_init = 6000           # 初始/终止储电量 (kWh)
E_min = 1200            # 最小储电量 (kWh)
E_max = 10800           # 最大储电量 (kWh)
P_max = 5000            # 最大充放电功率 (kW)
POWER_LIMIT = P_max * dt  # 833.33 kWh
kappa = 5               # 紧急购电倍数
TOL = 1e-5              # 验证容差
```

### 目标函数

```python
# 最小化：计划购电费 + 期望紧急购电费
objective = (
    lpSum(Price[t] * E_plan[t] for t in range(1, 145))  # 计划费
    + lpSum(scenario['weight'] * 
            lpSum(kappa * Price[t] * E_emg_s[t] for t in range(1, 145))
            for scenario, E_emg_s in zip(scenarios, all_E_emg_s))  # 期望紧急费
)

model.setObjective(objective, LpMinimize)
```

### 约束条件

```python
for s, scenario in enumerate(scenarios):
    Load_s = scenario['load']
    PV_s = scenario['pv']
    
    for t in range(1, 145):
        # 1. 电力平衡（允许弃光，用"≥"）
        model += (E_plan[t] + E_emg_s[s][t] + PV_s[t]*dt + E_discharge_s[s][t]*eta 
                  >= Load_s[t]*dt + E_charge_s[s][t])
        
        # 2. 储能状态方程
        if t == 1:
            E_prev = E_init  # 参数
        else:
            E_prev = E_storage_s[s][t-1]
        
        model += (E_storage_s[s][t] == E_prev + E_charge_s[s][t]*eta 
                  - E_discharge_s[s][t])
    
    # 3. 边界条件
    model += E_storage_s[s][144] == E_init  # 终止=初始=6000

# 注：容量约束(1200≤E_storage≤10800)和功率约束(0≤C,D≤833.33)
# 已在LpVariable定义时指定bounds
```

### 求解

```python
def solve_day_ahead(day_d):
    """
    求解日前两阶段随机LP
    """
    # 构造情景
    scenarios = construct_scenarios(day_d)
    
    # 建立模型
    model = LpProblem(f'Day_Ahead_d{day_d}', LpMinimize)
    # ... 添加变量、目标、约束 ...
    
    # 求解（HiGHS only）
    solver = HiGHS(msg=False)
    status = model.solve(solver)
    
    # 验证求解状态
    if status != LpStatusOptimal:
        raise Exception(f"[STOP→A] Day {day_d}: LP status={LpStatus[status]}, not Optimal")
    
    if model.objective.value() is None or not np.isfinite(model.objective.value()):
        raise Exception(f"[STOP→A] Day {day_d}: Objective value invalid")
    
    # 提取第一阶段结果
    E_plan_optimal = {t: E_plan[t].value() for t in range(1, 145)}
    
    return E_plan_optimal, scenarios, model

# 注：HiGHS不可用时，solve()会抛异常，直接STOP→A
```

---

## 模型规格：日内执行层（DP价值执行器）

### Phase 1：构建历史路径价值函数（每日0:00）

```python
def build_dp_value_functions(day_d, E_plan_optimal, scenarios):
    """
    构建M条历史路径的价值函数H_{t,ω}(e)
    """
    M = len(scenarios)
    H_paths = []  # 存储M条路径
    
    for omega, scenario in enumerate(scenarios):
        # 计算净缺口序列（给定E_plan）
        r_omega = []
        for t in range(1, 145):
            r_t = (scenario['load'][t] * dt 
                   - scenario['pv'][t] * dt 
                   - E_plan_optimal[t])
            r_omega.append(r_t)
        
        # 反向递推价值函数（t=144→1）
        H_omega = {}  # H_omega[t] = 凸折线函数（保存拐点与斜率）
        
        # 终端（t=145）
        v = 0.48  # 跨日库存价值 (元/kWh)
        H_omega[145] = PiecewiseLinear(
            breakpoints=[E_min, E_max],
            slopes=[-v, -v],  # 线性：H = -v*e
            values=[−v*E_min, -v*E_max]
        )
        
        # 反向递推
        for t in range(144, 0, -1):
            H_omega[t] = backward_dp_step(
                t, r_omega[t-1], H_omega[t+1], 
                Price[t], eta, E_min, E_max, POWER_LIMIT
            )
        
        H_paths.append(H_omega)
    
    return H_paths

def backward_dp_step(t, r_t, H_next, price, eta, E_min, E_max, S):
    """
    单步DP递推：H_t(e) = min_x { cost(r_t,x) + H_{t+1}(e+x) }
    
    返回：PiecewiseLinear对象（凸折线）
    """
    # 遍历可达库存区间，计算最优x(e)
    # 利用凸性：H_t(e)也是凸折线，通过合并拐点构造
    
    # 伪代码（实际需实现凸折线合并算法）
    H_t = PiecewiseLinear()
    for e in grid(E_min, E_max, step):
        # 允许的内部增量范围
        A_t_e_r = feasible_increments(e, r_t, eta, E_min, E_max, S)
        
        # 枚举x，找最小
        min_cost = inf
        for x in A_t_e_r:
            current_cost = 5 * price * max(0, r_t + psi(x, eta))
            future_cost = H_next.evaluate(e + x)
            total = current_cost + future_cost
            if total < min_cost:
                min_cost = total
        
        H_t.add_point(e, min_cost)
    
    return H_t.simplify()  # 合并共线段

def psi(x, eta):
    """效率转换函数"""
    if x >= 0:
        return x / eta  # 充电
    else:
        return eta * x  # 放电（x<0，结果<0）

def feasible_increments(e, r, eta, E_min, E_max, S):
    """
    给定库存e、净缺口r，返回允许的内部增量x范围
    
    约束：
    - 充电/放电单向（r<0只能充，r>0只能放）
    - 功率限制
    - 容量限制 E_min ≤ e+x ≤ E_max
    """
    if r < 0:  # 富余，只能充电 x>0
        x_min = 0
        x_max = min(S*eta, (E_max - e))
    else:  # 缺口，只能放电 x<0
        x_min = max(-S/eta, -(e - E_min))
        x_max = 0
    
    return (x_min, x_max)
```

### Phase 2：平均未来价值

```python
def average_value_functions(H_paths):
    """
    平均M条路径：H̄_t(e) = (1/M) Σ H_{t,ω}(e)
    """
    M = len(H_paths)
    H_bar = {}
    
    for t in range(1, 146):
        # 合并M条折线的拐点
        all_breakpoints = set()
        for H_omega in H_paths:
            all_breakpoints.update(H_omega[t].breakpoints)
        
        breakpoints = sorted(all_breakpoints)
        
        # 在每个拐点评估平均值
        values = []
        for e in breakpoints:
            avg_value = sum(H_omega[t].evaluate(e) for H_omega in H_paths) / M
            values.append(avg_value)
        
        # 构造平均折线
        H_bar[t] = PiecewiseLinear(breakpoints, values)
    
    return H_bar

# 性质验证
def verify_value_function_properties(H_bar):
    """
    验证H̄_t(e)的凸性与非增性（V8验证）
    """
    for t in range(1, 145):
        # 凸性：检查二阶差分≥0
        assert H_bar[t].is_convex(), f"H_bar[{t}] not convex"
        
        # 非增性：e增加时H̄_t(e)不增
        assert H_bar[t].is_non_increasing(), f"H_bar[{t}] not non-increasing"
```

### Phase 3：实时执行（DP价值执行器）

⚠️ **因果性保证**：DP执行器只使用当前观测(SOC_t, Load_t, PV_t, E_plan_t)与历史平均未来价值H̄_t(e)（每日0:00构建，不依赖当天真值），满足非提前性。

⚠️ **终端SOC约束**：DP执行器必须确保SOC_144=6000（与日前LP边界一致），在倒数几个时段动作空间需自动排除无法回到6000的动作。

```python
def dp_value_executor(day_d, E_plan_optimal, H_bar):
    """
    DP价值执行器：实时根据观测决策储能充放电
    
    关键约束：
    1. 只依赖当前观测(t, SOC[t-1], Load[t], PV[t], E_plan[t])
    2. 未来价值H̄来自历史情景（每日0:00构建，不用当天真值）
    3. 终端SOC_144必须=6000
    """
    # 初始化
    SOC = [E_init]  # SOC[0] = 6000
    C_actual = []
    D_actual = []
    E_emg_actual = []
    
    # 读取当天真实数据（逐时段读取，模拟实时观测）
    Load_real_d = Load_real[day_d]
    PV_real_d = PV_real[day_d]
    
    # 逐时段执行
    for t in range(1, 145):
        # 观测当前时段（只能看到t及之前，不能看到t+1）
        r_t = Load_real_d[t]*dt - PV_real_d[t]*dt - E_plan_optimal[t]
        e = SOC[t-1]
        
        # ⚠️ 终端约束处理：倒数几个时段需确保能回到6000
        if t >= 140:  # 最后5个时段，检查终端可达性
            feasible_terminal = True
        else:
            feasible_terminal = False
        
        # DP决策：argmin { current_cost + H̄_{t+1}(e+x) }
        A_t = feasible_increments(e, r_t, eta, E_min, E_max, POWER_LIMIT, 
                                   t=t, terminal_target=E_init if feasible_terminal else None)
        
        best_x = None
        min_total_cost = inf
        for x in sample_range(A_t, num_samples=100):  # 离散采样或解析求解
            # ⚠️ 因果性：当前成本只依赖(r_t, x, Price[t])
            current_cost = 5 * Price[t] * max(0, r_t + psi(x, eta))
            
            # ⚠️ 因果性：未来价值H̄_{t+1}来自历史，不依赖当天未来真值
            future_cost = H_bar[t+1].evaluate(e + x)
            
            total = current_cost + future_cost
            
            if total < min_total_cost:
                min_total_cost = total
                best_x = x
        
        # 恢复交流侧动作
        if best_x >= 0:  # 充电
            C_t = best_x / eta
            D_t = 0
        else:  # 放电
            C_t = 0
            D_t = -best_x * eta
        
        # 紧急购电
        E_emg_t = max(0, r_t + psi(best_x, eta))
        
        # 更新SOC
        SOC_t = e + eta*C_t - D_t
        
        # 记录
        C_actual.append(C_t)
        D_actual.append(D_t)
        E_emg_actual.append(E_emg_t)
        SOC.append(SOC_t)
    
    # ⚠️ 验证终端约束
    assert abs(SOC[144] - E_init) < TOL, f"DP终端SOC={SOC[144]:.2f}，应为{E_init}"
    
    return {
        'charge': C_actual,
        'discharge': D_actual,
        'emergency': E_emg_actual,
        'soc': SOC
    }


def feasible_increments(e, r, eta, E_min, E_max, P_limit, t=None, terminal_target=None):
    """
    计算可行内部增量集合 A_t(e, r)
    
    参数：
    - e: 当前库存
    - r: 净缺口
    - terminal_target: 若非None，需确保从当前状态能到达该终端目标
    """
    # 基础约束
    if r < 0:  # 富余，只能充电
        x_max = min(-r*eta, P_limit*eta, E_max - e)
        x_min = 0
    else:  # 缺口，只能放电
        x_min = max(-r/eta, -P_limit/eta, E_min - e)
        x_max = 0
    
    # 终端约束（倒数几个时段）
    if terminal_target is not None and t is not None:
        # 计算从当前e到terminal_target需要的平均调整速率
        remaining_steps = 145 - t
        required_adjustment_per_step = (terminal_target - e) / remaining_steps
        
        # 排除那些明显无法在剩余时段内回到目标的动作
        # （简化实现：确保当前动作不偏离目标太远）
        if abs(e - terminal_target) > P_limit * remaining_steps:
            # 强制朝目标方向移动
            if e < terminal_target:
                x_min = max(x_min, 0)  # 必须充电
            else:
                x_max = min(x_max, 0)  # 必须放电
    
    return (x_min, x_max)
```

### 对照执行器

```python
def analytical_response_executor(day_d, E_plan_optimal):
    """
    解析响应：优先最小化当前紧急购电
    """
    SOC = [E_init]
    C_actual, D_actual, E_emg_actual = [], [], []
    
    Load_real_d = Load_real[day_d]
    PV_real_d = PV_real[day_d]
    
    for t in range(1, 145):
        r_t = Load_real_d[t]*dt - PV_real_d[t]*dt - E_plan_optimal[t]
        e = SOC[t-1]
        
        if r_t < 0:  # 富余，充电
            C_t = min(-r_t, POWER_LIMIT, (E_max - e)/eta)
            D_t = 0
        else:  # 缺口，放电
            D_t = min(r_t, POWER_LIMIT, eta*(e - E_min))
            C_t = 0
        
        # 紧急购电补缺口
        balance = r_t + C_t - D_t*eta
        E_emg_t = max(0, balance)
        
        # 更新SOC
        SOC_t = e + eta*C_t - D_t
        
        C_actual.append(C_t)
        D_actual.append(D_t)
        E_emg_actual.append(E_emg_t)
        SOC.append(SOC_t)
    
    return {'charge': C_actual, 'discharge': D_actual, 
            'emergency': E_emg_actual, 'soc': SOC}

def mpc_executor(day_d, E_plan_optimal):
    """
    MPC：用预测修正做短期滚动优化
    """
    # 实现细节见problem_definition.md §5.4
    # 1. 估计相邻时段相关系数ρ（前30天）
    # 2. 每时段t：修正N̂_{t+j|t} = N̂_{t+j|t} + ρ^j(N_t^act - N̂_t)
    # 3. 滚动优化剩余时段，固定E_plan，min剩余紧急费-v·E_T
    # 4. 执行首个动作
    
    # （为简化，可先实现DP+解析响应，MPC可选）
    pass
```

---

## 验证方案

### Step 1：输入验证（Level 1）

```python
def validate_input(Price, Load_real, PV_real):
    """
    验证输入数据质量
    """
    # 检查1：维度
    assert Price.shape == (144,), "Price must be 144 points"
    assert Load_real.shape == (365, 144), "Load must be 365×144"
    assert PV_real.shape == (365, 144), "PV must be 365×144"
    
    # 检查2：无缺失
    assert not np.isnan(Price).any(), "Price has NaN"
    assert not np.isnan(Load_real).any(), "Load has NaN"
    assert not np.isnan(PV_real).any(), "PV has NaN"
    
    # 检查3：数值合理
    assert (Price >= 0).all() and (Price <= 10).all(), "Price out of range [0, 10]"
    assert (Load_real >= 0).all(), "Load has negative values"
    assert (PV_real >= 0).all(), "PV has negative values"
```

### Step 2：求解状态验证

```python
# 日前LP求解后
if status != LpStatusOptimal:
    raise Exception(f"[STOP→A] LP status not Optimal")

if model.objective.value() is None or not np.isfinite(model.objective.value()):
    raise Exception(f"[STOP→A] Objective value invalid")
```

### Step 3：硬约束验证（V1-V6）

```python
def validate_hard_constraints(results, day_d):
    """
    验证硬约束（继承Q1验证逻辑）
    """
    E_plan = results['plan']
    C = results['charge']
    D = results['discharge']
    SOC = results['soc']
    E_emg = results['emergency']
    
    Load = Load_real[day_d]
    PV = PV_real[day_d]
    
    passed = []
    
    for t in range(1, 145):
        # V1: 电力平衡
        supply = E_plan[t] + E_emg[t] + PV[t]*dt + D[t]*eta
        demand = Load[t]*dt + C[t]
        assert supply >= demand - TOL, f"V1 failed at t={t}"
        
        # V1: 储能状态方程
        if t == 1:
            E_prev = E_init
        else:
            E_prev = SOC[t-1]
        assert abs(SOC[t] - (E_prev + eta*C[t] - D[t])) < TOL, f"V1 failed at t={t}"
        
        # V1: 容量约束
        assert E_min - TOL <= SOC[t] <= E_max + TOL, f"V1 failed at t={t}"
        
        # V1: 功率约束
        assert -TOL <= C[t] <= POWER_LIMIT + TOL, f"V1 failed at t={t}"
        assert -TOL <= D[t] <= POWER_LIMIT + TOL, f"V1 failed at t={t}"
        
        passed.append(True)
    
    # V1: 边界条件
    assert abs(SOC[0] - E_init) < 0.1, "V1: Initial SOC failed"
    assert abs(SOC[144] - E_init) < 0.1, "V1: Terminal SOC failed"
    
    return all(passed)
```

### Step 4：诊断验证（V5-V8）

```python
def diagnostic_checks(results):
    """
    诊断性检查（报告用，不阻塞）
    """
    C = results['charge']
    D = results['discharge']
    E_emg = results['emergency']
    
    # V6: 同时充放电诊断
    simultaneous = sum(1 for c, d in zip(C, D) if c > 0.01 and d > 0.01)
    print(f"V6: Simultaneous charge/discharge: {simultaneous} periods")
    
    # V5: 紧急购电统计
    emg_events = sum(1 for e in E_emg if e > 0.01)
    emg_total = sum(E_emg)
    print(f"V5: Emergency purchase events: {emg_events}, total: {emg_total:.2f} kWh")
    
    # 储能利用率
    total_charge = sum(C)
    total_discharge = sum(D)
    equiv_cycles = total_charge / (E_max - E_min)
    print(f"Equivalent cycles: {equiv_cycles:.2f}")
```

### Step 5：V7 固定计划执行器对照（⭐关键）

```python
def executor_comparison_experiment(days):
    """
    V7：固定计划对照实验
    
    目的：隔离执行层贡献，比较三种执行器在相同E_plan下的实际表现
    
    ⚠️ 修订（GPT-REVIEW2）：不预设"DP≤MPC"为通过标准，
    而是报告实际成本、紧急购电量、事件数并分析适用场景
    """
    results = {'analytical': [], 'mpc': [], 'dp': []}
    
    for day_d in days:
        # 1. 生成日前计划（用随机LP或解析响应）
        E_plan_fixed, scenarios, _ = solve_day_ahead(day_d)
        
        # 2. 构建DP价值函数
        H_paths = build_dp_value_functions(day_d, E_plan_fixed, scenarios)
        H_bar = average_value_functions(H_paths)
        
        # 3. 固定同一计划，三执行器分别执行
        result_analytical = analytical_response_executor(day_d, E_plan_fixed)
        result_mpc = mpc_executor(day_d, E_plan_fixed)
        result_dp = dp_value_executor(day_d, E_plan_fixed, H_bar)
        
        # 4. 计算成本与指标
        cost_analytical = calculate_total_cost(E_plan_fixed, result_analytical, day_d)
        cost_mpc = calculate_total_cost(E_plan_fixed, result_mpc, day_d)
        cost_dp = calculate_total_cost(E_plan_fixed, result_dp, day_d)
        
        emg_events_analytical = count_emergency_events(result_analytical['emergency'])
        emg_events_mpc = count_emergency_events(result_mpc['emergency'])
        emg_events_dp = count_emergency_events(result_dp['emergency'])
        
        results['analytical'].append({
            'cost': cost_analytical,
            'emg_events': emg_events_analytical,
            'emg_total': sum(result_analytical['emergency'])
        })
        results['mpc'].append({
            'cost': cost_mpc,
            'emg_events': emg_events_mpc,
            'emg_total': sum(result_mpc['emergency'])
        })
        results['dp'].append({
            'cost': cost_dp,
            'emg_events': emg_events_dp,
            'emg_total': sum(result_dp['emergency'])
        })
    
    # 5. 汇总比较（报告实际结果，不预设排序）
    total_analytical = sum(r['cost'] for r in results['analytical'])
    total_mpc = sum(r['cost'] for r in results['mpc'])
    total_dp = sum(r['cost'] for r in results['dp'])
    
    print("V7 Executor Comparison (Fixed Plan):")
    print(f"  Analytical Response: {total_analytical/1e4:.2f} 万元")
    print(f"  MPC: {total_mpc/1e4:.2f} 万元")
    print(f"  DP Value Executor: {total_dp/1e4:.2f} 万元")
    
    # ⚠️ 修订：不预设通过标准，报告实际性能
    if total_dp < total_analytical:
        savings = (total_analytical - total_dp) / total_analytical * 100
        print(f"  DP相对解析响应节省: {savings:.2f}%")
    else:
        print(f"  注意：DP成本高于解析响应 {(total_dp-total_analytical)/total_analytical*100:.2f}%")
    
    if total_dp < total_mpc:
        savings = (total_mpc - total_dp) / total_mpc * 100
        print(f"  DP相对MPC节省: {savings:.2f}%")
    else:
        print(f"  注意：DP成本高于MPC {(total_dp-total_mpc)/total_mpc*100:.2f}%")
    
    # 输出到Excel
    save_executor_comparison(results, "executor_comparison.xlsx")
    
    return results

def calculate_total_cost(E_plan, result, day_d):
    """
    计算当天总成本 = 计划购电费 + 紧急购电费
    """
    plan_cost = sum(Price[t] * E_plan[t] for t in range(1, 145))
    emg_cost = sum(5 * Price[t] * result['emergency'][t-1] 
                   for t in range(1, 145))
    return plan_cost + emg_cost
```

---

## P0级别验证（必须先完成，否则STOP→A）

⚠️ **优先级最高**：以下验证必须在任何敏感性分析之前完成，否则后续结果不可信。

### P0-1：DP终端SOC验证

```python
def verify_dp_terminal_soc(days_sample=20):
    """
    验证DP执行器是否严格满足SOC_144 = 6000
    
    问题：日前LP约束SOC_144=6000，但DP执行器如果未显式保证，
          可能产生SOC_144=5800/6200，导致模型接口不一致
    """
    violations = []
    
    for day_d in random.sample(days, days_sample):
        E_plan, scenarios, _ = solve_day_ahead(day_d)
        H_paths = build_dp_value_functions(day_d, E_plan, scenarios)
        H_bar = average_value_functions(H_paths)
        
        result_dp = dp_value_executor(day_d, E_plan, H_bar)
        
        soc_terminal = result_dp['soc'][144]
        if abs(soc_terminal - E_init) > TOL:
            violations.append({
                'day': day_d,
                'soc_terminal': soc_terminal,
                'deviation': soc_terminal - E_init
            })
    
    if violations:
        print(f"⚠️ P0-1 FAILED: {len(violations)} days have terminal SOC violations")
        for v in violations:
            print(f"  Day {v['day']}: SOC_144={v['soc_terminal']:.2f}, deviation={v['deviation']:.2f}")
        raise Exception("[STOP→A] DP terminal SOC constraint violated")
    else:
        print(f"✅ P0-1 PASSED: All {days_sample} days satisfy SOC_144=6000")

# 必须通过才能继续
verify_dp_terminal_soc()
```

### P0-2：DP因果性验证（未来扰动不影响当前决策）

```python
def verify_dp_causality(num_tests=10):
    """
    验证DP执行器满足因果性：未来扰动不影响当前决策
    
    方法：固定t时刻之前的所有观测，构造两条未来路径A和B
          （t之后不同），验证t时刻的DP决策相同
    """
    violations = []
    
    for test_i in range(num_tests):
        day_d = random.choice(days)
        t_check = random.randint(50, 100)  # 中间时段
        
        # 生成基准路径
        E_plan, scenarios, _ = solve_day_ahead(day_d)
        H_paths = build_dp_value_functions(day_d, E_plan, scenarios)
        H_bar = average_value_functions(H_paths)
        
        # 构造两条路径：0:t相同，t+1:144不同
        Load_A = Load_real[day_d].copy()
        Load_B = Load_real[day_d].copy()
        Load_B[t_check+1:] *= 1.2  # 未来扰动
        
        PV_A = PV_real[day_d].copy()
        PV_B = PV_real[day_d].copy()
        PV_B[t_check+1:] *= 0.8  # 未来扰动
        
        # 分别执行到t时刻
        decision_A = simulate_dp_until_t(t_check, E_plan, H_bar, Load_A, PV_A)
        decision_B = simulate_dp_until_t(t_check, E_plan, H_bar, Load_B, PV_B)
        
        # 验证t时刻决策相同（未来扰动不应影响）
        if abs(decision_A['x_t'] - decision_B['x_t']) > TOL:
            violations.append({
                'test': test_i,
                'day': day_d,
                't': t_check,
                'x_A': decision_A['x_t'],
                'x_B': decision_B['x_t']
            })
    
    if violations:
        print(f"⚠️ P0-2 FAILED: {len(violations)} causality violations")
        for v in violations:
            print(f"  Test {v['test']}: t={v['t']}, x_A={v['x_A']:.2f}, x_B={v['x_B']:.2f}")
        raise Exception("[STOP→A] DP violates causality (uses future info)")
    else:
        print(f"✅ P0-2 PASSED: All {num_tests} tests satisfy causality")

# 必须通过才能继续
verify_dp_causality()
```

### P0-3：日前LP → DP接口一致性

```python
def verify_lp_dp_interface(days_sample=20):
    """
    验证日前LP生成的E_plan能够被DP正常执行
    """
    failures = []
    
    for day_d in random.sample(days, days_sample):
        try:
            # 日前LP
            E_plan, scenarios, status = solve_day_ahead(day_d)
            if status != LpStatusOptimal:
                failures.append({'day': day_d, 'reason': 'LP not optimal'})
                continue
            
            # 构建DP
            H_paths = build_dp_value_functions(day_d, E_plan, scenarios)
            H_bar = average_value_functions(H_paths)
            
            # DP执行
            result_dp = dp_value_executor(day_d, E_plan, H_bar)
            
            # 验证基本可行性
            validate_hard_constraints(result_dp, day_d)
            
        except Exception as e:
            failures.append({'day': day_d, 'reason': str(e)})
    
    if failures:
        print(f"⚠️ P0-3 FAILED: {len(failures)} days have LP→DP interface issues")
        for f in failures:
            print(f"  Day {f['day']}: {f['reason']}")
        raise Exception("[STOP→A] LP-DP interface inconsistent")
    else:
        print(f"✅ P0-3 PASSED: All {days_sample} days execute successfully")

# 必须通过才能继续
verify_lp_dp_interface()
```

---

## 输出规格

### result2.xlsx（三工作表）

**工作表1：计划购电量**
- 行：334天（2025.2.1-12.31）
- 列：144个时段（0:10-0:00+1）
- 单位：kWh
- 格式：与附件5模板一致

**工作表2：充放电量**
- 行：334天
- 列：按表2格式，6个4小时区段
  - 0:00-4:00充电量、放电量
  - 4:00-8:00充电量、放电量
  - 8:00-12:00充电量、放电量
  - 12:00-16:00充电量、放电量
  - 16:00-20:00充电量、放电量
  - 20:00-24:00充电量、放电量
  - 0:00储电量、24:00储电量
- 单位：kWh

**工作表3：紧急购电量**
- 列：日期 | 紧急购电时间段 | 紧急购电量
- 格式：
  - 日期：2025/3/20
  - 时间段：17:00-17:30（连续正值合并）
  - 购电量：31.137994
- 同日多个事件分多行

### validation_report_q2.txt

```
Q2 Validation Report
====================
Date: 2026-09-11
Days: 334 (2025.2.1-12.31)

Input Validation
----------------
✓ Price: 144 points, range [0.2629, 1.2629] yuan/kWh
✓ Load: 365×144, no NaN, range [0, 10000] kW
✓ PV: 365×144, no NaN, range [0, 8000] kW

V1: Hard Constraints
--------------------
✓ All 334 days passed
  - Power balance: ✓
  - State equation: ✓
  - Capacity bounds: ✓
  - Power bounds: ✓
  - Boundary conditions: ✓

V2: Real Backtest Feasibility
------------------------------
✓ All days feasible, no infeasibility

V3: EVPI (Relative to Perfect Information)
-------------------------------------------
✓ Day-ahead cost ≥ Perfect info cost
  EVPI = 120.5 万元 (0.86%)

V4: VSS (Relative to EV Baseline)
----------------------------------
✓ Stochastic LP cost < EV baseline cost
  VSS = 85.3 万元 (0.60%)

V5: Emergency Purchase Seasonality
-----------------------------------
✓ Winter (12月) > Summer (6月)
  12月: 8523 events, 6月: 2341 events

V6: Simultaneous Charge/Discharge
----------------------------------
✓ Total: 0 periods across all days

V7: Executor Comparison (Fixed Plan) ⭐
---------------------------------------
✓ DP ≤ Analytical Response ≤ MPC
  Analytical Response: 1417.42 万元
  MPC: 1427.89 万元
  DP Value Executor: 1402.23 万元
  Savings: 1.07%

V8: DP Value Function Properties
---------------------------------
✓ H̄_t(e) convex for all t
✓ H̄_t(e) non-increasing in e for all t

Summary
-------
All validations PASSED ✓
Model ready for paper writing.
```

### result_data_q2.json（C论文数字来源）

```json
{
  "total_plan_cost_yuan": 12931901.23,
  "total_emergency_cost_yuan": 1090377.10,
  "total_cost_yuan": 14022278.33,
  "total_plan_kWh": 20808142.02,
  "total_emergency_kWh": 204387.31,
  "emergency_events": 559,
  "days": 334,
  "specified_days": {
    "2025-03-20": {
      "plan_cost": 40397.47,
      "emergency_cost": 1052.55,
      "total_cost": 41450.02,
      "plan_kWh": 65969.25,
      "emergency_kWh": 176.26
    },
    "2025-06-21": {...},
    "2025-09-23": {...},
    "2025-12-21": {...}
  },
  "executor_comparison": {
    "analytical_response_total": 14174236.10,
    "mpc_total": 14278883.47,
    "dp_value_executor_total": 14022232.01,
    "dp_savings_pct": 1.07
  },
  "vss_yuan": 853142.57,
  "evpi_yuan": 1204563.89
}
```

### executor_comparison.xlsx

- 列：日期 | 解析响应成本 | MPC成本 | DP成本 | DP节省
- 334行数据 + 汇总行

---

## 实施流程（8步架构）

### Step 0：环境准备
```python
import pulp
import numpy as np
import pandas as pd
from pulp import LpProblem, LpVariable, lpSum, LpMinimize, HiGHS

# 验证HiGHS可用
try:
    solver = HiGHS()
except:
    raise Exception("[STOP→A] HiGHS not available")
```

### Step 1：输入验证
```python
Price, Load_real, PV_real = load_data("附件1.xlsx", "附件2.xlsx")
validate_input(Price, Load_real, PV_real)
```

### Step 2：主循环（334天）
```python
for day_d in range(Feb1, Dec31):
    # 2a. 日前决策层
    E_plan_optimal, scenarios, model = solve_day_ahead(day_d)
    
    # 2b. 日内准备：构建DP价值函数
    H_paths = build_dp_value_functions(day_d, E_plan_optimal, scenarios)
    H_bar = average_value_functions(H_paths)
    verify_value_function_properties(H_bar)  # V8
    
    # 2c. 日内执行：DP价值执行器
    result_dp = dp_value_executor(day_d, E_plan_optimal, H_bar)
    
    # 2d. 硬约束验证
    validate_hard_constraints(result_dp, day_d)  # V1-V6
    
    # 2e. 诊断
    diagnostic_checks(result_dp)  # V5-V6
    
    # 2f. 记录结果
    store_results(day_d, E_plan_optimal, result_dp)
```

### Step 3：V7执行器对照实验
```python
executor_results = executor_comparison_experiment(range(Feb1, Dec31))
```

### Step 4：生成交接文件
```python
save_result2_xlsx(all_results, "result2.xlsx")
save_validation_report(validation_log, "validation_report_q2.txt")
save_result_data_json(summary_metrics, "result_data_q2.json")
save_executor_comparison(executor_results, "executor_comparison.xlsx")
```

### Step 5：P1门禁自检
```python
# P1检查清单：
# ✓ result2.xlsx三工作表存在且格式正确
# ✓ 日前LP全部Optimal
# ✓ 真实回测无不可行
```

### Step 6：P2门禁准备
```python
# P2检查清单：
# ✓ DP价值执行器实现完成
# ✓ V7固定计划对照实验完成，DP≤解析响应
# ✓ 全部验证V1-V8通过
# ✓ 四个交接文件齐全
```

### Step 7：交接给C
```python
# 交接文件：
# - result2.xlsx
# - validation_report_q2.txt
# - result_data_q2.json
# - executor_comparison.xlsx
#
# C论文数字来源：result_data_q2.json
# C不得从Excel或聊天记录抄数字
```

---

## P1级别：必须补充的敏感性分析（在P0验证通过后执行）

⚠️ **审稿强制要求（GPT-REVIEW2）**：以下三类敏感性分析是论文必备，必须完成并报告结果。

### P1-1：M值敏感性分析（情景数量）

```python
def sensitivity_M(M_values=[10, 20, 30, 45, 60]):
    """
    M值敏感性分析：比较不同历史窗口长度下模型性能
    
    ⚠️ 注意（GPT-REVIEW2）：
    - M不仅改变样本数量，还改变历史时间跨度
    - 不预设"M越大/越小越好"
    - 应说明"考察局部平稳性假设的稳健性"
    """
    results = {}
    
    for M in M_values:
        print(f"\n=== Testing M={M} ===")
        
        # 修改情景构造函数使用M个历史样本
        total_cost = 0
        total_emg = 0
        emg_events = 0
        solve_times = []
        
        for day_d in days:
            # 构造M个情景（取最近M天）
            scenarios = construct_scenarios_with_M(day_d, M)
            
            # 求解日前LP
            start_time = time.time()
            E_plan, _, status = solve_day_ahead_with_scenarios(day_d, scenarios)
            solve_times.append(time.time() - start_time)
            
            # DP执行
            H_paths = build_dp_value_functions(day_d, E_plan, scenarios)
            H_bar = average_value_functions(H_paths)
            result = dp_value_executor(day_d, E_plan, H_bar)
            
            # 统计
            cost = calculate_total_cost(E_plan, result, day_d)
            total_cost += cost
            total_emg += sum(result['emergency'])
            emg_events += count_emergency_events(result['emergency'])
        
        results[M] = {
            'total_cost': total_cost,
            'total_emg': total_emg,
            'emg_events': emg_events,
            'avg_solve_time': np.mean(solve_times),
            'max_solve_time': np.max(solve_times)
        }
        
        print(f"  Total cost: {total_cost/1e4:.2f} 万元")
        print(f"  Emergency total: {total_emg:.2f} kWh")
        print(f"  Emergency events: {emg_events}")
        print(f"  Avg solve time: {np.mean(solve_times):.2f}s")
    
    # 生成对比表格
    print("\n=== M Sensitivity Analysis Summary ===")
    print("M    | Cost(万元) | Emg(kWh) | Events | Solve(s)")
    print("-----|-----------|----------|--------|----------")
    for M in M_values:
        r = results[M]
        print(f"{M:4d} | {r['total_cost']/1e4:9.2f} | {r['total_emg']:8.1f} | "
              f"{r['emg_events']:6d} | {r['avg_solve_time']:8.2f}")
    
    # 保存结果
    save_sensitivity_results('M_sensitivity', results)
    
    return results

# 执行
M_sensitivity_results = sensitivity_M()
```

### P1-2：v值敏感性分析（终端价值参数）

```python
def sensitivity_v(v_values=[0.3, 0.4, 0.48, 0.6, 0.8]):
    """
    v值敏感性分析：终端价值参数对DP执行器性能的影响
    
    ⚠️ 修订（GPT-REVIEW2）：
    - 不预设v=0.48最优
    - 若结果对v不敏感，说明"模型对终端价值参数稳健"
    - 比v的具体推导更重要
    """
    results = {}
    
    # 使用固定的日前计划（消除日前层影响）
    print("Generating fixed day-ahead plans...")
    fixed_plans = {}
    for day_d in days:
        E_plan, scenarios, _ = solve_day_ahead(day_d)
        fixed_plans[day_d] = (E_plan, scenarios)
    
    for v in v_values:
        print(f"\n=== Testing v={v} ===")
        
        total_cost = 0
        total_emg = 0
        emg_events = 0
        avg_soc_terminal = []
        
        for day_d in days:
            E_plan, scenarios = fixed_plans[day_d]
            
            # 构建DP价值函数（使用当前v值）
            H_paths = build_dp_value_functions_with_v(day_d, E_plan, scenarios, v)
            H_bar = average_value_functions(H_paths)
            
            # DP执行
            result = dp_value_executor(day_d, E_plan, H_bar)
            
            # 统计
            cost = calculate_total_cost(E_plan, result, day_d)
            total_cost += cost
            total_emg += sum(result['emergency'])
            emg_events += count_emergency_events(result['emergency'])
            avg_soc_terminal.append(result['soc'][144])
        
        results[v] = {
            'total_cost': total_cost,
            'total_emg': total_emg,
            'emg_events': emg_events,
            'avg_soc_terminal': np.mean(avg_soc_terminal)
        }
        
        print(f"  Total cost: {total_cost/1e4:.2f} 万元")
        print(f"  Emergency total: {total_emg:.2f} kWh")
        print(f"  Emergency events: {emg_events}")
        print(f"  Avg SOC_terminal: {np.mean(avg_soc_terminal):.1f} kWh")
    
    # 生成对比表格
    print("\n=== v Sensitivity Analysis Summary ===")
    print("v    | Cost(万元) | Emg(kWh) | Events | SOC_term")
    print("-----|-----------|----------|--------|----------")
    for v in v_values:
        r = results[v]
        print(f"{v:.2f} | {r['total_cost']/1e4:9.2f} | {r['total_emg']:8.1f} | "
              f"{r['emg_events']:6d} | {r['avg_soc_terminal']:8.1f}")
    
    # 计算相对偏差
    base_cost = results[0.48]['total_cost']
    print(f"\nRelative deviation from v=0.48:")
    for v in v_values:
        if v != 0.48:
            deviation = (results[v]['total_cost'] - base_cost) / base_cost * 100
            print(f"  v={v:.2f}: {deviation:+.2f}%")
    
    # 保存结果
    save_sensitivity_results('v_sensitivity', results)
    
    return results

# 执行
v_sensitivity_results = sensitivity_v()
```

### P1-3：SOC终端处理方式的稳健性分析

⚠️ **重要修订（GPT-REVIEW2）**：这不是简单的"参数敏感性"，而是**三种不同的模型假设**，应称为"终端库存处理方式的稳健性分析"。

```python
def sensitivity_soc_boundary():
    """
    SOC终端处理方式稳健性分析
    
    三种方案：
    - 方案A（独立日）：E(0)=E(144)=6000，每日独立
    - 方案B（终端价值）：E(0)=6000，E(144)自由∈[1200,10800]，H_T+1(e)=-v·e
    - 方案C（全年串联）：E_d(0)=E_{d-1}(144)，允许跨日储能
    
    ⚠️ 比较指标（GPT-REVIEW2）：
    不仅比总成本，还要比较：紧急购电量、平均/最低/最高SOC、
    跨日储能量、计算时间
    """
    results = {}
    
    # === 方案A：独立日（当前方案）===
    print("\n=== Scheme A: Independent Day (SOC_144=6000) ===")
    results_A = run_full_simulation_independent_day()
    results['A_independent'] = {
        'total_cost': results_A['total_cost'],
        'total_emg': results_A['total_emg'],
        'emg_events': results_A['emg_events'],
        'avg_soc': np.mean(results_A['all_soc']),
        'min_soc': np.min(results_A['all_soc']),
        'max_soc': np.max(results_A['all_soc']),
        'cross_day_storage': 0,  # 固定为0
        'compute_time': results_A['compute_time']
    }
    
    # === 方案B：终端价值函数 ===
    print("\n=== Scheme B: Terminal Value Function (SOC_144 free) ===")
    results_B = run_full_simulation_terminal_value(v=0.48)
    results['B_terminal_value'] = {
        'total_cost': results_B['total_cost'],
        'total_emg': results_B['total_emg'],
        'emg_events': results_B['emg_events'],
        'avg_soc': np.mean(results_B['all_soc']),
        'min_soc': np.min(results_B['all_soc']),
        'max_soc': np.max(results_B['all_soc']),
        'cross_day_storage': compute_cross_day_storage(results_B['daily_soc_terminal']),
        'compute_time': results_B['compute_time']
    }
    
    # === 方案C：全年串联 ===
    print("\n=== Scheme C: Year-Long Coupling (E_d(0)=E_{d-1}(144)) ===")
    results_C = run_full_simulation_year_coupling()
    results['C_year_coupling'] = {
        'total_cost': results_C['total_cost'],
        'total_emg': results_C['total_emg'],
        'emg_events': results_C['emg_events'],
        'avg_soc': np.mean(results_C['all_soc']),
        'min_soc': np.min(results_C['all_soc']),
        'max_soc': np.max(results_C['all_soc']),
        'cross_day_storage': compute_cross_day_storage(results_C['daily_soc_terminal']),
        'compute_time': results_C['compute_time']
    }
    
    # === 生成对比表格 ===
    print("\n=== SOC Boundary Handling: Robustness Analysis ===")
    print("Scheme       | Cost(万元) | Emg(kWh) | Events | AvgSOC | MinSOC | MaxSOC | CrossDay | Time(s)")
    print("-------------|-----------|----------|--------|--------|--------|--------|----------|----------")
    
    for scheme_name, scheme_key in [
        ('A: 独立日', 'A_independent'),
        ('B: 终端价值', 'B_terminal_value'),
        ('C: 全年串联', 'C_year_coupling')
    ]:
        r = results[scheme_key]
        print(f"{scheme_name:12s} | {r['total_cost']/1e4:9.2f} | {r['total_emg']:8.1f} | "
              f"{r['emg_events']:6d} | {r['avg_soc']:6.1f} | {r['min_soc']:6.1f} | "
              f"{r['max_soc']:6.1f} | {r['cross_day_storage']:8.1f} | {r['compute_time']:8.1f}")
    
    # 计算相对偏差
    base_cost = results['A_independent']['total_cost']
    print(f"\nCost deviation from Scheme A:")
    print(f"  Scheme B: {(results['B_terminal_value']['total_cost']-base_cost)/base_cost*100:+.2f}%")
    print(f"  Scheme C: {(results['C_year_coupling']['total_cost']-base_cost)/base_cost*100:+.2f}%")
    
    # 保存结果
    save_sensitivity_results('soc_boundary_robustness', results)
    
    return results

def compute_cross_day_storage(daily_soc_terminal):
    """
    计算跨日储能量：Σ|SOC_d(144) - 6000|
    """
    return sum(abs(soc - 6000) for soc in daily_soc_terminal)

# 执行
soc_boundary_results = sensitivity_soc_boundary()
```

---

## P2级别：报告偏差而非预设阈值

⚠️ **修订（GPT-REVIEW2）**：不预设"偏差<5%通过"，而是报告实际偏差并分析其数量级及稳定性。

### 日前LP评估 vs 实际DP执行成本偏差分析

```python
def analyze_lp_dp_cost_deviation(days):
    """
    分析日前LP评估成本与实际DP执行成本的偏差
    
    ⚠️ 不预设通过阈值，报告实际偏差分布
    """
    deviations = []
    
    for day_d in days:
        # 日前LP评估
        E_plan, scenarios, status = solve_day_ahead(day_d)
        lp_plan_cost = sum(Price[t] * E_plan[t] for t in range(1, 145))
        lp_expected_emg_cost = extract_expected_emg_cost_from_lp(day_d)
        lp_total_cost = lp_plan_cost + lp_expected_emg_cost
        
        # 实际DP执行
        H_paths = build_dp_value_functions(day_d, E_plan, scenarios)
        H_bar = average_value_functions(H_paths)
        result_dp = dp_value_executor(day_d, E_plan, H_bar)
        dp_actual_cost = calculate_total_cost(E_plan, result_dp, day_d)
        
        # 偏差
        deviation_abs = dp_actual_cost - lp_total_cost
        deviation_rel = deviation_abs / lp_total_cost * 100
        
        deviations.append({
            'day': day_d,
            'lp_cost': lp_total_cost,
            'dp_cost': dp_actual_cost,
            'deviation_abs': deviation_abs,
            'deviation_rel': deviation_rel
        })
    
    # 统计
    deviations_rel = [d['deviation_rel'] for d in deviations]
    print("\n=== LP Evaluation vs DP Execution Cost Deviation ===")
    print(f"Mean deviation: {np.mean(deviations_rel):.2f}%")
    print(f"Std deviation: {np.std(deviations_rel):.2f}%")
    print(f"Median deviation: {np.median(deviations_rel):.2f}%")
    print(f"Min deviation: {np.min(deviations_rel):.2f}%")
    print(f"Max deviation: {np.max(deviations_rel):.2f}%")
    print(f"Percentiles: 25%={np.percentile(deviations_rel, 25):.2f}%, "
          f"75%={np.percentile(deviations_rel, 75):.2f}%")
    
    # 结论（不预设阈值）
    if np.abs(np.mean(deviations_rel)) < 3:
        print("\n结论：偏差整体较小且稳定，日前LP评估与实际执行基本一致")
    elif np.abs(np.mean(deviations_rel)) < 10:
        print("\n结论：存在系统性偏差但在可接受范围，通过闭环回测验证整体性能")
    else:
        print("\n⚠️ 警告：日前LP与实际执行存在明显偏差，需重新评估模型一致性")
    
    return deviations

# 执行
lp_dp_deviations = analyze_lp_dp_cost_deviation(days)
```

---

## 📌 模型状态声明（根据GPT-REVIEW2更新）

**当前状态**: ⚠️ **模型结构冻结，参数与稳健性分析待验证**

### 已冻结部分
- ✅ 模型架构：日前随机优化 + 因果动态储能控制
- ✅ 日前层：基于简化LP评估的E_plan优化
- ✅ 日内层：DP因果储能控制（满足非提前性）
- ✅ 验证体系：P0（实现正确性）+ P1（敏感性分析）+ P2（偏差报告）
- ✅ 输出规格：四个交接文件

### 待完成验证（B的工作）
- ⏳ **P0-1**: DP终端SOC验证（SOC_144=6000？）
- ⏳ **P0-2**: DP因果性验证（未来扰动不影响当前决策）
- ⏳ **P0-3**: LP→DP接口一致性
- ⏳ **P1-1**: M值敏感性分析（M∈{10,20,30,45,60}）
- ⏳ **P1-2**: v值敏感性分析（v∈{0.3,0.4,0.48,0.6,0.8}）
- ⏳ **P1-3**: SOC终端处理方式稳健性分析（独立日 vs 终端价值 vs 全年串联）
- ⏳ **P2**: LP-DP成本偏差分析（报告实际偏差，不预设阈值）

### 工作优先级（GPT-REVIEW2建议）

**P0级别**（必须先完成，否则后续结果不可信）：
1. DP终端SOC验证
2. DP因果性验证
3. LP→DP接口一致性

**P1级别**（论文必备敏感性分析）：
4. M值敏感性分析
5. v值敏感性分析
6. SOC终端处理方式稳健性分析

**P2级别**（论文表述优化）：
7. LP-DP成本偏差报告
8. 论文措辞修订（见model_decision.md）

### B的职责边界

**✅ B可以做的**：
- 按规格实现代码
- 完成P0/P1/P2全部验证
- 产出四个交接文件
- 报告实验结果（不预设结论）

**❌ B不能做的**：
- 修改模型架构、决策点、验证标准
- 遇到P0验证失败时自行改模型（必须STOP→A）
- 预设敏感性分析"应该"得到的结果
- 从Excel或聊天记录给C提供数字（只能用result_data_q2.json）

### 关键原则（GPT-REVIEW2强调）

1. **模型定位诚实**：不追求日前与日内联合全局最优，而是分层求解 + 闭环回测验证
2. **实验不预设结论**：V7不预设"DP≤MPC"，敏感性不预设"M=30最优"，偏差不预设"<5%通过"
3. **验证优先于参数调优**：P0验证比M/v调优更重要
4. **报告实际结果**：论文应诚实报告模型近似性与实际性能，不包装成"理论最优"

---

**签署**:  
Role A (建模手) - 宋禹萱  
Date: 2026-09-11（整合完成 + GPT-REVIEW2修订完成）

**📍 下一步**：B开始实现，优先完成P0验证，通过后再进行P1/P2工作。
