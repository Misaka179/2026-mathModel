# C题 参考文献总表（微网与外部电网电力调控策略）

> **整理人**: Role A (建模手)
> **整理时间**: 2026-09-10
> **书目核实**: 全部经 Crossref 核实（DOI 已验证，可直接用于 BibTeX/引用）
> **用途**: 供 C（论文手）在 reference-manager 阶段引用；供 A 论证方法选择
> **配套分析**: 各文献与题目的对应关系详见 `questions/QC/02_model/related_paper_analysis.md`

---

## 一、核心文献（4篇，用户指定）

### [1] 微网能源管理系统综述 —— Q1 方法论总纲
Zia, M. F., Elbouchikhi, E., & Benbouzid, M. (2018). Microgrids energy management systems: A critical review on methods, solutions, and prospects. *Applied Energy*, 222, 1033–1055. https://doi.org/10.1016/j.apenergy.2018.04.103

- **对应**: Q1（+全题总纲）
- **支撑**: 论证确定性 LP 是微网经济调度的首选方法；反向说明 Q1 无需 PSO/GA 等元启发式。

### [2] 光伏-电池混合系统需求侧管理 —— Q1 机理 / Q3 滚动
Wu, Z., Tazvinga, H., & Xia, X. (2015). Demand side management of photovoltaic-battery hybrid system. *Applied Energy*, 148, 294–304. https://doi.org/10.1016/j.apenergy.2015.03.109

- **对应**: Q1、Q3
- **支撑**: 设备结构（PV+储能+电网+负荷）与 C 题一致；解释"低价充电、高价放电"套利机理；滚动优化思想引出 Q3。

### [3] 电价结构对 PV-电池系统经济效益的影响 —— Q4
Parra, D., & Patel, M. K. (2016). Effect of tariffs on the performance and economic benefits of PV-coupled battery systems. *Applied Energy*, 164, 175–187. https://doi.org/10.1016/j.apenergy.2015.11.037

- **对应**: Q4
- **支撑**: 论证电价波动如何改变储能充放电与购电决策，使 Q4 从"换数据"升级为"机理分析"。

### [4] 考虑源荷不确定性的微网多时间尺度优化调度 —— Q3
Hou, J., Yu, W., Xu, Z., Ge, Q., Li, Z., & Meng, Y. (2023). Multi-time scale optimization scheduling of microgrid considering source and load uncertainty. *Electric Power Systems Research*, 216, 109037. https://doi.org/10.1016/j.epsr.2022.109037

- **对应**: Q3
- **支撑**: 日前调度 + 日内滚动调度的直接方法论；支撑"哪个时刻预报最有价值"的实验设计。

---

## 二、补充文献（5篇，按本题实际方向检索并核实）

### [5] 基于滚动时域策略的微网能量管理系统 —— Q3 方法论锚点
Palma-Behnke, R., Benavides, C., Lanas, F., Severino, B., Reyes, L., Llanos, J., & Sáez, D. (2013). A Microgrid Energy Management System Based on the Rolling Horizon Strategy. *IEEE Transactions on Smart Grid*, 4(2), 996–1006. https://doi.org/10.1109/TSG.2012.2231440

- **对应**: Q3
- **支撑**: 滚动时域(rolling horizon)EMS 的经典高被引文献，正是 Q3 要求的"日前计划 + 新预报到达后重新求解"架构，作为 Q3 方法论的权威锚点。

### [6] 基于模型预测控制的小时内微网经济调度 —— Q3 MPC 形式化
Velasquez, M. A., Barreiro-Gomez, J., Quijano, N., Cadena, A. I., & Shahidehpour, M. (2020). Intra-Hour Microgrid Economic Dispatch Based on Model Predictive Control. *IEEE Transactions on Smart Grid*, 11(3), 1968–1979. https://doi.org/10.1109/TSG.2019.2945692

- **对应**: Q3
- **支撑**: 较新的 MPC 微网经济调度严格形式化，补强 [5]，提供 receding-horizon 优化与"计划-调整"耦合的多时间尺度协调逻辑。

### [7] 面向韧性微网的最优随机能量管理系统 —— Q2 不确定性
Silva, J. A. A., López, J. C., Bañol Arias, N., Rider, M. J., & da Silva, L. C. P. (2021). An optimal stochastic energy management system for resilient microgrids. *Applied Energy*, 300, 117435. https://doi.org/10.1016/j.apenergy.2021.117435

- **对应**: Q2
- **支撑**: 基于场景的随机规划 EMS，显式处理光伏/负荷不确定性，含对缺电/紧急动作的惩罚——与 Q2"紧急购电 5 倍电价"结构一致，支撑两阶段随机(或场景)建模与补偿成本。

### [8] 实时电价环境下含价格预测的最优住宅负荷控制 —— Q4 动态电价锚点
Mohsenian-Rad, A.-H., & Leon-Garcia, A. (2010). Optimal Residential Load Control With Price Prediction in Real-Time Electricity Pricing Environments. *IEEE Transactions on Smart Grid*, 1(2), 120–133. https://doi.org/10.1109/TSG.2010.2055903

- **对应**: Q4
- **支撑**: 实时(时变)电价下优化用电/购电决策的奠基性高被引文献，提供响应动态电价的经典 LP/优化框架与价格不确定性处理，支撑 Q4 实时电价重优化。

### [9] 通过更精确的电池与退化建模改进并网锂电池最优控制 —— Q1 储能子模型补强
Reniers, J. M., Mulder, G., Ober-Blöbaum, S., & Howey, D. A. (2018). Improving optimal control of grid-connected lithium-ion batteries through more accurate battery and degradation modelling. *Journal of Power Sources*, 379, 91–102. https://doi.org/10.1016/j.jpowsour.2018.01.004

- **对应**: Q1（可作扩展/鲁棒性讨论）
- **支撑**: 并网电池套利(低买高卖/削峰填谷)的最优控制形式化，含充放电功率限制与 SOC 动态——约束集与 Q1 LP 一致；可用于论证若在基础 LP 之外加入效率/退化项的意义。

---

## 三、覆盖关系总览

| 子问题 | 核心文献 | 补充文献 |
|--------|---------|---------|
| **Q1** 确定性LP经济调度 | [1] 综述, [2] 机理 | [9] 电池最优控制 |
| **Q2** 不确定性+紧急购电 | — | [7] 随机EMS |
| **Q3** 日前+日内滚动 | [2] 滚动思想, [4] 多时间尺度 | [5] 滚动时域, [6] MPC |
| **Q4** 动态电价 | [3] 电价影响 | [8] 实时电价优化 |

**方法论一致性**: 9 篇文献共同支撑"逐问增加现实复杂度"的路线（确定性LP → 随机/紧急购电 → 滚动MPC → 动态电价），而非"每问换算法"。

---

## 四、可选补充方向（若需第10篇）

Q2 若采用**鲁棒优化**而非场景随机优化，可再补一篇 microgrid robust optimization 专文。当前 9 篇已足够覆盖 Q1-Q4，宁缺毋滥。

---

**文献状态**: ✅ 9 篇全部 Crossref 核实，DOI 可用
**BibTeX**: 见同目录 `references.bib`
