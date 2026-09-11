# C题 问题2 术语表格

> **范围**: 仅列 Q2 相对 Q1 **新增或语义变化**的术语与符号。储能物理量（η、E_charge、E_discharge、E_storage、E_min、E_max、P_max、POWER_LIMIT、E_init、Δt）沿用 Q1 冻结口径，见 `questions/QC/01_problem/terminology_table.md`，本表不重复。
> **一致性要求**: 全项目符号统一，禁止近义词混用。
> **更新说明**: 2026-09-11 整合更新，新增日内执行层相关符号（§1.3、§2.2）。

## 1. Q2 新增决策变量与随机量

### 1.1 日前决策层（两阶段随机规划）

| 中文术语 | 英文术语 | 符号 | 定义 | 单位 | 首次出现 | 禁止混用 |
|---------|---------|------|------|------|---------|---------|
| 计划购电量 | planned purchase | E_plan(t) | 第一阶段变量，0:00锁定的时段t向外网计划购电量 | kWh | problem_definition §4.3 | 不与"紧急购电量""调整购电量(Q3)"混用 |
| 紧急购电量 | emergency purchase | E_emg^s(t) / E_emg_real(t) | 供电不足负载时按5×电价补的购电量；情景s下为E_emg^s，真实回测为E_emg_real | kWh | §4.4 | 不与计划购电量混用；不叫"补购" |
| 紧急购电倍数 | emergency price multiplier | κ | 紧急购电电价 = κ×交易时刻电价，κ=5（题目给定） | — | §4.2 | 固定为5，不写"惩罚系数"以免与优化罚项混淆 |
| 规划日 | planning day | d | 需制定策略的日期，d∈{2025.2.1,…,12.31}，共334天 | — | §4.1 | 不与"时段t"混用 |
| 情景 | scenario | s / ω | 第d天当天负载/光伏候选实现，s∈S_d（日前层用s，日内DP路径用ω） | — | §4.1 | 不与"场景日""历史日"混用 |
| 情景概率 | scenario probability | π_s | 情景s的发生概率，Σπ_s=1 | — | §4.1 | — |
| 情景负载 | scenario load | Load_d^s(t) | 第d天时段t负载在情景s下取值 | kW | §4.2 | 与真实负载Load_d(t)区分 |
| 情景光伏 | scenario PV | PV_d^s(t) | 第d天时段t光伏在情景s下取值 | kW | §4.2 | 与真实光伏PV_d(t)区分 |
| 真实负载 | realized load | Load_d(t) | 第d天时段t附件2真实负载值(回测用) | kW | §4.8 | — |
| 真实光伏 | realized PV | PV_d(t) | 第d天时段t附件2真实光伏值(回测用) | kW | §4.8 | — |

### 1.2 历史情景构造（日前层输入）

| 中文术语 | 英文术语 | 符号 | 定义 | 单位 | 首次出现 | 禁止混用 |
|---------|---------|------|------|------|---------|---------|
| 历史预测 | historical forecast | L̂_i(t), V̂_i(t) | 历史日i当时用可获得信息生成的预测（不泄露未来） | kW | §4.9 | 与当天预测L̂_d(t)区分 |
| 历史联合残差 | historical joint residual | ε_i^L(t), ε_i^V(t) | 历史日i的预测误差，ε^L=L−L̂，ε^V=V−V̂，**同日配对** | kW | §4.9 | — |
| 情景数 | number of scenarios | M / \|S\| | 日前LP使用的情景总数，M=30（前30天）或聚类后k≈10 | — | §4.9 | — |

### 1.3 日内执行层（DP价值执行器）

| 中文术语 | 英文术语 | 符号 | 定义 | 单位 | 首次出现 | 禁止混用 |
|---------|---------|------|------|------|---------|---------|
| 净缺口 | net deficit | r_t | 实时净缺口，r_t = Load_t·Δt − PV_t·Δt − E_plan_t | kWh | §5.2 | 不与净负载(kW)混用 |
| 内部增量 | internal increment | x_t | 储电量增量，x=E_t−E_{t-1}，充电时x>0，放电时x<0 | kWh | §5.3 | — |
| 效率转换函数 | efficiency conversion | ψ(x) | 内部增量转交流侧，ψ(x)=x/η (x≥0充电)，ψ(x)=ηx (x<0放电) | kWh | §5.3 | 继承Q1，max(x/η,ηx) |
| 允许增量集合 | feasible increment set | A_t(e,r) | 给定库存e、净缺口r下允许的内部增量x集合（满足功率容量约束、单向） | — | §5.3 | — |
| 历史路径价值函数 | historical path value | H_{t,ω}(e) | 情景ω下，时段t库存e的最低剩余紧急费用（DP反向递推） | 元 | §5.3 | — |
| 平均未来价值 | average future value | H̄_t(e) | M条历史路径平均，H̄_t(e)=(1/M)ΣH_{t,ω}(e)，用于实时决策 | 元 | §5.3 | — |
| 跨日库存价值 | inter-day storage value | v | 终端近似v·e，v≈0.48元/kWh（0:00-5:00电价均值除η） | 元/kWh | §5.3 | — |

## 2. Q2 新增模型与评价术语

### 2.1 日前决策层

| 中文术语 | 英文术语 | 符号 | 定义 | 单位 | 首次出现 |
|---------|---------|------|------|------|---------|
| 两阶段随机规划 | two-stage stochastic programming | — | 第一阶段(0:00计划,情景无关)+第二阶段(实时,情景相关)的LP | — | §2/§4.7 |
| 非提前性约束 | non-anticipativity | — | E_plan(t)对所有情景取同值，0:00不得偷看真值 | — | §4.6(G) |
| 期望值模型/基线 | expected value (EV) model | — | 用历史均值单点估计当天负载/光伏的确定性LP | — | §5.2 |
| 安全裕度 | safety margin | α | EV基线中对负载估计上抬的裕度系数 | — | §5.2 |
| 随机解价值 | value of stochastic solution | VSS | EV基线真实成本 − 随机规划真实成本 | 元 | §6.3 V4 |
| 完美信息期望价值 | expected value of perfect information | EVPI | 日前决策真实成本 − 完美信息(事后最优)成本 | 元 | §6.3 V3 |
| 计划购电费 | planned purchase cost | — | Σ Price(t)·E_plan(t) | 元 | §4.5 |
| 期望紧急购电费 | expected emergency cost | — | Σ_s π_s Σ_t κ·Price(t)·E_emg^s(t) | 元 | §4.5 |

### 2.2 日内执行层

| 中文术语 | 英文术语 | 符号 | 定义 | 单位 | 首次出现 |
|---------|---------|------|------|------|---------|
| DP价值执行器 | DP value executor | — | 基于历史路径平均未来价值H̄_t(e)的实时储能决策方法（主执行器） | — | §5.3 |
| 解析响应 | analytical response | — | 优先最小化当前紧急购电的简单执行器（基线对照） | — | §5.4 |
| MPC | model predictive control | — | 用预测修正做短期滚动优化的执行器（对照） | — | §5.4 |
| 固定计划对照实验 | fixed-plan comparison | — | 固定同一E_plan，三执行器比较，隔离执行层贡献（V7验证） | — | §5.5 |
| 保留水平 | reservation level | R_t | 基于H̄_t(e)斜率确定的动态库存保留阈值 | kWh | §5.3 |

### 2.3 通用术语

| 中文术语 | 英文术语 | 符号 | 定义 | 单位 | 首次出现 |
|---------|---------|------|------|------|---------|
| 净负载 | net load | — | Load(t)−PV(t)，需外部供给的净需求 | kW | A_data_profile §4 |
| 归一化均方根误差 | normalized RMSE | nRMSE | RMSE/极差，评日前可估计性 | — | A_data_profile §5 |

## 3. 单位与量纲约定（继承Q1）

- 功率 kW，能量 kWh，Δt=1/6 h；能量 = 功率 × Δt。
- 电价 元/kWh；紧急购电电价 = κ·Price(t) = 5·Price(t)。
- 成本 元；SOC 电量 kWh。
- 日内执行层：净缺口r_t为能量(kWh)，内部增量x_t为能量(kWh)。
