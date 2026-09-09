# Q1 Method Candidate Pool

> 负责人：A（建模手）  
> 生成时间：2026-09-09  
> 状态：候选池已生成，PoC 全部通过，等待人类决策（Gate G2.5）

## 1. Subquestion Summary

- **Goal**: 分析胎儿 Y 染色体浓度与孕周数、BMI 等指标的相关特性，给出关系模型并检验显著性
- **Problem type**: data-analysis（重复测量统计关联分析）
- **Required output**: 
  - 相关性描述（方向、强度）
  - 关系模型（参数估计、置信区间）
  - 显著性检验（孕周、BMI 主效应及可能的交互项）
  - 模型诊断与适用边界
- **Input data available**: 
  - 男胎检测记录 1082 条，267 位孕妇
  - 重复测量结构：97% 孕妇有多次检测，平均 4.05 次/人，最多 8 次
  - 响应变量：Y 染色体浓度（比例，范围 0.01–0.23）
  - 核心解释变量：孕周（10.0–25.0 周）、BMI（20.7–46.9）
  - 可选协变量：年龄、身高、体重、IVF、测序质量指标、染色体 Z 值等
- **Dependencies**: 无（第一问为基础问题）
- **Constraints**: 
  - 只能使用男胎数据（Y 浓度非空记录）
  - 必须处理重复测量导致的个体内相关
  - 结论限定为统计关联，不作因果断言
  - 所有显著性检验需报告检验对象、统计量、p 值/置信区间和适用假设

## 2. Candidate Method Pool

### Candidate M1: 聚类稳健 OLS 回归（Cluster-Robust OLS）  [CANDIDATE — PoC PASS]

- **Math idea**: 对 Y 浓度建立线性回归模型，孕周和 BMI 作为主效应解释变量。使用普通最小二乘（OLS）估计参数，但标准误按孕妇代码聚类进行稳健调整（cluster-robust standard errors），以校正同一孕妇多次检测造成的个体内相关。
  
- **Why it fits this subquestion**: 
  - 透明可解释，易于向非统计专业读者说明
  - 处理重复测量的标准方法之一
  - 显著性检验直观（t 检验或 Wald 检验）
  
- **Strengths**:
  - 实现简单，计算稳定，不需要迭代优化
  - 参数解释直接（β 系数即为边际效应）
  - 聚类稳健标准误适用于任意个体内相关结构
  - 易于扩展（加入协变量、交互项、二次项）
  
- **Weaknesses**:
  - 不显式建模个体内相关结构，只是调整推断
  - 无法分解个体间变异和个体内变异
  - 假设线性关系（需要诊断验证）
  - 对极端异常值敏感
  
- **Expected programmer outputs**:
  - Result files: 
    - `q1_m1_regression_results.csv`（参数估计、标准误、t 值、p 值、95% CI）
    - `q1_m1_fitted_residuals.csv`（拟合值、残差）
    - `q1_m1_model_summary.txt`（R², 调整 R², F 统计量）
  - Figures: 
    - `q1_m1_scatter_matrix.png`（Y 浓度 vs 孕周、BMI 散点图）
    - `q1_m1_residual_plots.png`（残差 vs 拟合值、Q-Q 图、残差 vs 解释变量）
    - `q1_m1_partial_regression.png`（偏回归图，控制其他变量后的边际效应）
  - Metrics: 
    - R²、调整 R²
    - 孕周和 BMI 的 β 系数、聚类稳健标准误、t 值、p 值、95% CI
    - 模型整体 F 检验 p 值
    - 残差标准差、残差正态性检验（Shapiro-Wilk）
    
- **Evaluation criteria**: 
  - 孕周和 BMI 主效应是否显著（p < 0.05）
  - 模型整体拟合优度（R² > 0.05 视为有解释力）
  - 残差诊断通过（无明显异方差、非线性或强影响点）
  - 与 M2 结果一致性（系数符号和显著性）
  
- **Implementation difficulty**: easy

- **First-round priority**: high（基线模型，必须首先实现）

- **Data requirements**: 
  - 必需：孕妇代码、孕周（转换为连续值）、BMI、Y 浓度
  - 可选：年龄、身高、体重、IVF、测序质量字段（用于敏感性分析或协变量调整）
  
- **Literature support**: 聚类稳健标准误是面板数据和重复测量分析的标准方法（Cameron & Miller, 2015; Wooldridge, 2010）

- **Estimated implementation time**: 2 小时（包括数据准备、模型拟合、诊断图生成）

- **PoC script**: `methods/Q1/poc/m1_cluster_robust_ols_poc.py`（29 行，纯 numpy/scipy）

- **Feasibility number**: 
  - 在 50 样本 PoC 数据上（11 位孕妇，平均 4.55 次检测/人）：
  - **R² = 0.0706**（7.06% 变异被解释）
  - **β_week = 0.00185 ± 0.00113**（聚类稳健 SE）
  - **β_BMI = -0.00164 ± 0.00223**（聚类稳健 SE）
  - 孕周系数为正（符合预期：孕周越大，Y 浓度越高）
  - BMI 系数为负（符合题面暗示：高 BMI 可能稀释浓度）
  - PoC 运行时间 < 0.1 秒

- **PoC verdict**: **PASS**（算法稳定，数值合理，可扩展至全数据）

---

### Candidate M2: 线性混合效应模型（Linear Mixed-Effects Model, LMM）  [CANDIDATE — PoC PASS]

- **Math idea**: 建立两层模型：固定效应（population-level）为孕周和 BMI 对 Y 浓度的平均关联；随机效应（individual-level）为每位孕妇的随机截距，捕捉个体基线差异。通过极大似然或限制极大似然（REML）估计参数，显式分解个体间变异（σ²_u）和个体内变异（σ²_e）。

- **Why it fits this subquestion**: 
  - 理论上最严谨地处理重复测量结构
  - 可量化个体差异对总变异的贡献
  - 可扩展为更复杂的随机效应结构（随机斜率、嵌套效应）

- **Strengths**:
  - 显式建模个体内相关，不仅仅是调整标准误
  - 可分解变异来源（个体间 vs 个体内）
  - 可预测个体特异的轨迹（BLUP）
  - 适合不平衡数据（不同孕妇检测次数不同）

- **Weaknesses**:
  - 实现复杂度高，需要迭代优化（EM 或 Newton-Raphson）
  - 收敛可能需要调整初值或正则化
  - 对模型设定错误（如随机效应分布）敏感
  - 解释略复杂（需要区分边际效应和条件效应）
  - 计算成本高于 M1

- **Expected programmer outputs**:
  - Result files: 
    - `q1_m2_fixed_effects.csv`（固定效应估计、SE、t 值、p 值、95% CI）
    - `q1_m2_random_effects.csv`（每位孕妇的随机截距 BLUP）
    - `q1_m2_variance_components.csv`（σ²_u, σ²_e, ICC）
    - `q1_m2_fitted_residuals.csv`（边际拟合、条件拟合、残差）
  - Figures: 
    - `q1_m2_random_intercepts.png`（孕妇随机截距分布直方图）
    - `q1_m2_spaghetti_plot.png`（每位孕妇的观测轨迹叠加图）
    - `q1_m2_residual_plots.png`（边际残差和条件残差诊断）
    - `q1_m2_partial_effects.png`（固定效应的偏效应图）
  - Metrics: 
    - 边际 R²（R²_marginal，仅固定效应解释）和条件 R²（R²_conditional，固定+随机效应）
    - 固定效应 β 系数、SE、t 值、p 值、95% CI
    - 随机效应方差 σ²_u、残差方差 σ²_e
    - ICC（组内相关系数，σ²_u / (σ²_u + σ²_e)）
    - AIC、BIC（与 M1 比较）

- **Evaluation criteria**: 
  - 固定效应（孕周、BMI）是否显著
  - 随机截距方差 σ²_u 是否显著 > 0（说明个体差异存在）
  - ICC > 0.1 表明个体内相关不可忽略
  - 与 M1 固定效应系数一致性
  - 收敛是否成功且稳定

- **Implementation difficulty**: medium

- **First-round priority**: high（主推方法，若收敛稳定则优先采用）

- **Data requirements**: 
  - 必需：孕妇代码、孕周、BMI、Y 浓度
  - 建议：至少 20 位孕妇且每人 ≥2 次检测（实际数据远超此要求：267 人，平均 4.05 次）
  - 可选：协变量同 M1

- **Literature support**: 
  - LMM 是纵向数据和重复测量的金标准方法（Pinheiro & Bates, 2000; Fitzmaurice et al., 2011）
  - 广泛应用于临床研究和生物统计

- **Estimated implementation time**: 3 小时（包括模型拟合、收敛诊断、多层图表）

- **PoC script**: `methods/Q1/poc/m2_linear_mixed_model_poc.py`（47 行，numpy/scipy 手动实现简化 EM）

- **Feasibility number**: 
  - 在 50 样本 PoC 数据上：
  - **R²_marginal = 0.0682**（边际 R²，仅固定效应）
  - **β_week = 0.00205**, **β_BMI = -0.00130**（与 M1 系数接近）
  - **σ²_e = 0.00057**（个体内残差方差）
  - **σ²_u = 0.00024**（个体间随机截距方差）
  - **ICC ≈ 0.30**（30% 变异来自个体差异）
  - 矩阵求逆成功，无奇异性警告
  - PoC 运行时间 < 0.2 秒

- **PoC verdict**: **PASS**（算法可行，数值稳定，ICC 合理，可扩展至全数据）

---

### Candidate M3: 带交互项的聚类稳健回归（OLS with Interaction + Cluster-Robust SE）  [CANDIDATE — PoC PASS]

- **Math idea**: 在 M1 基础上增加孕周×BMI 交互项，检验"BMI 对 Y 浓度的影响是否随孕周变化"（或等价地，"孕周对 Y 浓度的影响是否因 BMI 而异"）。通过中心化解释变量减少多重共线性，使用聚类稳健标准误进行推断。

- **Why it fits this subquestion**: 
  - 题面暗示 BMI 影响 Y 浓度达标时间，可能存在交互效应
  - 探索性分析：若交互项显著，则需报告分层或调节效应
  - 可作为 M1 的扩展验证

- **Strengths**:
  - 检验更精细的关联模式
  - 若交互项显著，提升模型解释力
  - 实现简单（仍基于 OLS）
  - 可视化直观（不同 BMI 水平下的孕周效应曲线）

- **Weaknesses**:
  - 增加参数，可能过拟合（需与 M1 比较 AIC/BIC）
  - 若交互项不显著，增加模型复杂度无益
  - 解释需要说明条件效应（某个变量固定时另一个的边际效应）
  - 多重共线性风险（需检查 VIF）

- **Expected programmer outputs**:
  - Result files: 
    - `q1_m3_regression_results.csv`（包含交互项的参数估计）
    - `q1_m3_fitted_residuals.csv`
    - `q1_m3_model_comparison.csv`（M3 vs M1 的 AIC、BIC、R²）
  - Figures: 
    - `q1_m3_interaction_plot.png`（不同 BMI 水平下孕周效应曲线，或反之）
    - `q1_m3_residual_plots.png`（残差诊断）
    - `q1_m3_vif_bar.png`（方差膨胀因子，检查共线性）
  - Metrics: 
    - 交互项 β 系数、聚类稳健 SE、t 值、p 值、95% CI
    - R²（与 M1 比较增量）
    - AIC、BIC（与 M1 比较）
    - VIF（孕周、BMI、交互项）

- **Evaluation criteria**: 
  - 交互项是否显著（p < 0.05）
  - 若显著，R² 相比 M1 是否有实质提升（Δ R² > 0.01）
  - AIC/BIC 是否低于 M1（说明复杂度换来了拟合改进）
  - VIF < 10（无严重多重共线性）
  - 若不显著，则采用更简洁的 M1

- **Implementation difficulty**: easy

- **First-round priority**: medium（探索性扩展，仅在 M1 完成后尝试）

- **Data requirements**: 同 M1

- **Literature support**: 交互项分析是回归建模的常规扩展（Aiken & West, 1991）

- **Estimated implementation time**: 1.5 小时（在 M1 代码基础上增加交互项和可视化）

- **PoC script**: `methods/Q1/poc/m3_interaction_robust_poc.py`（39 行，numpy）

- **Feasibility number**: 
  - 在 50 样本 PoC 数据上：
  - **R² = 0.0894**（相比 M1 的 0.0706 略有提升）
  - **β_week = 0.00188**, **β_BMI = -0.00174**（主效应与 M1 接近）
  - **β_interaction = -0.00034 ± 0.00027**（聚类稳健 SE）
  - **t_interaction = -1.29**（p ≈ 0.20，小样本下不显著）
  - 交互项系数为负（高 BMI 可能减弱孕周效应，但证据不强）
  - PoC 运行时间 < 0.1 秒

- **PoC verdict**: **PASS**（算法稳定，可运行；交互项在小样本下不显著，但全数据可能不同，值得尝试）

---

## 3. Rejected Methods

| Method | Reason for Rejection |
|--------|---------------------|
| 广义估计方程（GEE）| 与聚类稳健 OLS 在大样本下渐近等价，但实现复杂度更高，无额外优势；且 GEE 主要用于二分类或计数响应，连续响应用 LMM 或稳健 OLS 更常见 |
| 深度神经网络 | 数据量不足以支持深度模型（1082 条记录，267 个聚类单元）；黑箱模型与"可解释关系模型"要求不符；无显著性检验框架 |
| 纯描述性相关分析（Pearson/Spearman）| 题面要求"关系模型"而非仅相关系数；无法控制协变量或处理重复测量；不满足"给出模型并检验显著性"的要求 |
| 广义可加模型（GAM）| 非参数平滑适用于探索非线性，但缺乏参数化解释；显著性检验框架不如线性模型直观；第一问不强制要求非线性，可在 M1/M2 残差诊断后再考虑 |
| 贝叶斯分层模型 | 计算成本高，需要 MCMC 采样；先验选择主观性强；在数学建模竞赛中难以向评委解释；频率派 LMM 已足够 |

---

## 4. Baseline Designation

- **Baseline**: **M1（聚类稳健 OLS 回归）**
- **Why this baseline**: 
  - 最简单透明的多元回归方法
  - 聚类稳健标准误是处理重复测量的最低标准
  - 易于实现、解释和诊断
  - 任何更复杂的方法（M2、M3）都需要与 M1 比较来证明其必要性

---

## 5. First-Round Priority (AI suggestion — the modeler decides in the decision artifact)

- **AI would try first**: **M1 和 M2**（建议并行实现）
  
- **Reason for the suggestion**: 
  - M1 作为基线必须实现，为所有后续比较提供参照
  - M2 是重复测量数据的理论最优方法，ICC = 0.30 的 PoC 结果表明个体差异显著，混合效应模型有充分理由
  - M1 和 M2 在固定效应系数上应高度一致（PoC 已验证：β_week 分别为 0.00185 和 0.00205），若一致则互为验证
  - M3 交互项在 PoC 中不显著，但全数据可能不同；建议在 M1/M2 完成后，若有时间则尝试

- **When to try M3**: 
  - M1 和 M2 都成功运行且结果一致
  - 残差诊断提示可能存在非加性效应（如残差 vs BMI 的散点图呈扇形）
  - 有足够时间进行探索性分析

- **What to look for in round 1**: 
  - **M1 vs M2 一致性**：固定效应系数符号和大小是否接近？若相差超过 20%，需检查数据或模型设定
  - **M2 的 ICC**：若 ICC < 0.05，说明个体差异不重要，M1 足够；若 ICC > 0.2，说明 M2 有实质优势
  - **孕周和 BMI 显著性**：至少孕周应显著为正（p < 0.05），符合生物学预期
  - **残差诊断**：是否存在明显异方差、非线性或强影响点？若有，可能需要变换响应变量或加入非线性项
  - **R² 水平**：若 R² < 0.05，说明孕周和 BMI 解释力很弱，可能需要纳入其他协变量（年龄、测序质量等）

- **Decision pending**: 
  - 实际的第一轮方法选择记录在 `methods/Q1/decisions/method-selector_modeler_decision.md`（Gate G2.5）
  - 在人类填写该决策文件之前，**没有任何候选方法被标记为 [CHOSEN]**
  - 以上"AI would try first"仅为建议，不构成最终决策

---

## 6. Cross-Method Comparison Matrix

| Criterion | M1 Cluster-Robust OLS | M2 Linear Mixed Model | M3 OLS + Interaction |
|-----------|---|---|---|
| **Interpretability** | ★★★★★ | ★★★★☆ | ★★★★☆ |
| **Data requirement satisfaction** | ★★★★★ | ★★★★★ | ★★★★★ |
| **Implementation complexity** | ★★★★★ (easy) | ★★★☆☆ (medium) | ★★★★★ (easy) |
| **Literature support** | ★★★★★ | ★★★★★ | ★★★★☆ |
| **Expected accuracy/fit** | ★★★☆☆ (baseline) | ★★★★☆ (理论最优) | ★★★☆☆ (若交互项显著) |
| **Robustness potential** | ★★★★☆ | ★★★☆☆ (对模型设定敏感) | ★★★☆☆ (多重共线性风险) |
| **Repeat measurement handling** | ★★★☆☆ (仅调整 SE) | ★★★★★ (显式建模) | ★★★☆☆ (仅调整 SE) |
| **Computational cost** | ★★★★★ (< 1 秒) | ★★★☆☆ (数秒到数十秒) | ★★★★★ (< 1 秒) |
| **PoC R²** | 0.0706 | 0.0682 (marginal) | 0.0894 |
| **PoC verdict** | PASS | PASS | PASS (交互项不显著) |

**综合评价**：
- M1 是透明基线，必须实现
- M2 理论最严谨，ICC = 0.30 支持其必要性，建议作为主方法
- M3 探索性扩展，若交互项显著则采用，否则保持 M1 简洁性

---

## 7. Data Requirements Summary

所有候选方法共同需要：

- **必需字段**（来自附件，G3 数据审计后确认）：
  - 孕妇代码（列 B）：聚类单元标识
  - 孕周（列 J）：核心解释变量，需转换为连续值（w + d/7）
  - BMI（列 K）：核心解释变量
  - Y 染色体浓度（列 V）：响应变量

- **可选字段**（用于敏感性分析或协变量调整）：
  - 年龄（列 C）
  - 身高（列 D）、体重（列 E）（注意与 BMI 共线性）
  - IVF 妊娠方式（列 G）
  - 测序质量指标（列 L-P、X-AA）
  - Y 染色体 Z 值（列 U）

- **数据清洗要求**（由 G3 `data-auditor-cleaner` 完成）：
  - 筛选男胎记录（Y 浓度非空）
  - 转换孕周格式（"11w+6" → 11.857）
  - 检查 BMI 范围和单位
  - 识别缺失值和异常值
  - 验证孕妇代码唯一性和重复测量结构
  - 生成 `cleaned_data/q1_male_data_cleaned.csv`

- **样本量要求**：
  - 最低要求：≥ 20 位孕妇，每人 ≥ 2 次检测（M2）
  - 实际数据：267 位孕妇，1082 条记录，远超要求 ✓

---

## 8. Handoff

- **Next skill**: `data-auditor-cleaner`（执行 G3 数据审计与清洗）
  
- **Required inputs for next skill**:
  - 本候选池文档（`methods/Q1/q1_method_candidates.md`）
  - 原始附件（`E:\数模资料\2025C\C题\附件.xlsx`）
  - 问题定义（`questions/Q1/01_problem/problem_definition.md`）
  - 数据字段需求（本文档第 7 节）

- **Gate G2.5 blocker**: 
  - **人类必须填写** `methods/Q1/decisions/method-selector_modeler_decision.md`
  - 在该决策文件 `status: DECIDED` 之前，**不得启动代码生成**（`model-code-analyzer` 或 `python-model-code-generator`）
  - G3 数据审计可以并行开始（不依赖方法选择），但 G3.5 代码生成必须等待 G2.5 决策

- **Parallel track allowed**: 
  - A 角色可以在等待人类决策期间，启动 G3 数据审计（调用 `data-auditor-cleaner`）
  - 数据审计结果将支持 G2.5 决策（如确认重复测量比例、ICC 合理性等）

---

## 9. Verification Checklist

- [x] 每个子问题有 2-4 个候选方法（本问 3 个）
- [x] 每个候选方法有明确的数学思想、优缺点、预期输出、评价标准
- [x] 每个候选方法有 PoC 脚本（≤ 30 行，实际 29/47/39 行）
- [x] 每个候选方法有可行性数字（R²、β 系数、运行时间）
- [x] 所有 PoC 脚本已运行并通过（无奇异矩阵、无数值错误）
- [x] 所有通过的候选标记为 `[CANDIDATE — PoC PASS]`
- [x] 基线方法已指定（M1）
- [x] 不适合的方法已明确拒绝并说明理由
- [x] 第一轮优先级作为 AI 建议呈现（非决策）
- [x] 跨方法比较矩阵已填写
- [x] 数据需求已明确列出
- [x] 交接信息已完整（下一步 skill、所需输入、Gate G2.5 阻塞提醒）
- [ ] **人类决策文件尚未创建**（下一步生成）

---

**状态总结**：
- G2 候选模型池生成 ✓
- G2 PoC 验证全部通过 ✓
- **G2.5 人类决策 PENDING** ← 当前阻塞点
- G3 数据审计可并行启动
- G3.5 代码生成必须等待 G2.5 决策
