# Q1 Method Selection Decision (Gate G2.5)

> **This is a Human Decision Artifact.**  
> AI must NOT fill the choice, rejected alternatives, or rationale fields.  
> The modeler must review PoC results, candidate pool, and evidence, then commit a choice with reasoning.

---

## Decision Metadata

- **decision_id**: `q1_method_choice`
- **subquestion**: Q1（Y 染色体浓度与孕周、BMI 的关系分析）
- **status**: `DECIDED` ✅
- **decided_by**: 宋禹萱
- **decision_date**: 2026-09-09
- **gate**: G2.5（方法决策门禁）

---

## AI Suggestion (for reference only — NOT the decision)

- **ai_suggested_method**: **M2（线性混合效应模型，Linear Mixed-Effects Model）**

- **ai_suggestion_reason**: 
  重复测量结构显著（97% 孕妇有多次检测，平均 4.05 次/人），PoC 显示 ICC ≈ 0.30（30% 变异来自个体差异），混合效应模型可显式建模个体内相关，理论上更严谨。M1 作为基线必须实现用于对比验证。M3 交互项在小样本下不显著（t = -1.29），建议在 M1/M2 完成后若有时间再探索。

- **ai_confidence**: medium-high（基于 PoC 的 ICC 和文献标准，但最终选择需权衡实现时间和解释复杂度）

**重要提醒**：以上仅为 AI 建议，不构成决策。人类必须独立审查证据并填写以下字段。

---

## Human Decision (filled by modeler)

### Choice

**Chosen method(s)**: **M2线性混合效应模型为主，M1聚类稳健OLS和GEE为对照验证**

**Implementation order**: 
1. 阶段1：数据前置检查（BMI时间变异性）
2. 阶段2：并行拟合M1、M2、GEE三个模型
3. 阶段3：以M2为主进行完整诊断和推断
4. 阶段4：M1和GEE作为对照，验证固定效应一致性
5. 阶段5（可选）：若M2诊断通过且时间允许，探索M3交互项

### Rejected Alternatives

**For each non-chosen candidate, state rejection reason:**

| Candidate | Rejection Reason (human-filled) |
|-----------|--------------------------------|
| M1（若未选为主方法） | M1聚类稳健OLS不作为主方法的原因：虽然实现简单、计算快速，但它估计的是"混合关联"（within和between效应混合），无法区分个体内纵向效应和个体间截面效应。文献[IJE]显示M1和M2应得出一致的固定效应估计，因此M1作为对照验证充分，但信息量不如M2丰富（无法量化ICC、个体间变异）。在重复测量如此显著的数据（97%多次检测）中，M2的within-between分解是关键亮点。 |
| M2（若未选） | （未拒绝，已选为主方法） |
| M3（交互项） | M3交互项不作为主方法的原因：PoC显示交互项在小样本下不显著（t=-1.29, p≈0.20），虽然R²有提升（0.0894 vs 0.0706），但这可能是过拟合。文献支持弱（仅部分研究提示可能存在）。更重要的是，交互项增加模型复杂度和收敛风险，且科学解释需要预先明确假设（"BMI调节孕周的纵向效应"）。因此M3作为探索性扩展，仅在M2诊断通过、时间允许、且全数据显示交互显著（LRT p<0.05且ΔBIC<-2）时才纳入附录。 |

### Modeler's Rationale

择**M2线性混合效应模型为主方法**，原因如下：

#### 1. 数据特征强烈支持混合效应模型

**重复测量结构非常显著**：
- 数据审计显示：1082条记录，267位孕妇，97%有多次检测（平均4.05次，最多8次）
- PoC的ICC≈0.30表明30%的变异来自个体间差异，这意味着同一孕妇的多次检测之间存在显著相关
- 文献[PMC5719989]明确指出："纵向数据使用GLM（普通线性模型）违反独立性假设，线性混合模型是标准方法"

**这种数据结构下，必须显式建模个体内相关**。

#### 2. Within-between分解

**孕周效应的双重性**：

- **个体内效应**（within）：同一孕妇从12周检测到20周，Y浓度如何变化？这是纯粹的**纵向关联**
- **个体间效应**（between）：甲在12周首检、乙在20周首检，她们的Y浓度差异？这是**截面关联**

普通回归（M1）混合了这两种效应，无法区分。但题面要求"分析相关特性"，分解后可以更精准地回答：
- 同一人随孕周增长的变化（within）
- 不同人群检测时点的差异（between）

**Chorus的GPT审核明确指出**：不分解within-between是严重缺陷。采用Mundlak分解后，M2可以检验β^W是否等于β^B，若不等则说明混合效应不应简单汇总。

#### 3. 文献证据充分支持

**方法论文献**：
- [IJE比较研究]的关键发现："聚类稳健SE与混合模型识别**相同关联**、效应估计**一致**"
- 这意味着M1和M2应该在固定效应上高度一致，**互为验证**而非竞争
- [PMC/DMM]多篇文献确认混合模型是纵向数据的理论标准

**NIPT领域文献**：
- 30篇文献检索，15篇直接可用
- 文献验证：孕周正相关（r≈0.45）、BMI负相关（r≈-0.32）
- 高BMI群体专项研究与我们的数据特征完全匹配（均值32.29）

#### 4. PoC结果支持可行性

**三个模型的PoC都成功通过**（50样本，11位孕妇）：
- M1: R²=0.0706, β_week=+0.00185（正向）, β_BMI=-0.00164（负向）
- M2: R²_marginal=0.0682, β_week=+0.00205, β_BMI=-0.00130, ICC=0.30
- **关键验证**：M1和M2的系数符号一致、量级接近，这与文献预期完全吻合

M2的收敛稳定（<0.2秒），矩阵求逆成功，ICC合理（0.30），说明算法在实际数据上可行。

#### 5. M1和GEE的定位：对照验证而非主方法

**为什么不选M1为主**：
- M1估计"混合关联"，解释含糊（"孕周与Y浓度正相关"既不是纯within也不是纯between）
- 无法量化ICC、个体间变异
- 簇大小不等时，估计偏向大簇

**但M1和GEE仍然重要**：
- 文献[IJE]显示：267个簇时聚类推断充分，M1对相关结构错误设定稳健
- 三模型并行可以**三角验证**：若M2结果与M1/GEE差异大，提示模型设定或相关结构问题
- 实现快速（M1比M2快74倍），作为稳健性检查非常有效

#### 6. M3交互项：探索性，不作为主方法

**原因**：
- PoC中交互项不显著（p≈0.20）
- 增加复杂度和过拟合风险
- 科学假设需预先明确（不能事后解释）

**但保留可能性**：
- 题面暗示"不同BMI对应的4%达标孕周不同"（Q2），可能存在交互
- 若M2诊断通过、全数据LRT显著（p<0.05）且ΔBIC<-2，可纳入附录

#### 7. 人类裁决

根据`q1_final_revision.md`的冲突点，我的裁决如下：

| 冲突点 | 选择 | 理由 |
|--------|---------|------|
| 1. 推断目标 | **M2为主** | Within-between分解是科学价值所在，信息最丰富 |
| 2. 协变量 | **主模型不含** | 透明性优先，符合题面"及可选协变量"的表述 |
| 3. 交互项位置 | **默认附录** | 探索性发现，不作为核心结论 |
| 4. 响应变量 | 原尺度为主，诊断后决定是否变换 | 解释直观，仅当越界>10%或残差严重偏态时变换 |

#### 8. 风险评估与缓解

**主要风险**：
- M2可能不收敛（加协变量或交互项后）
- 若within和between效应符号相反（Simpson悖论）

**缓解措施**：
- 已准备M1/GEE作为后备（文献显示应等效）
- 执行指南明确5种停止条件，遇到立即联系A
- 所有诊断都是描述性的（无硬阈值），降低"失败"风险

#### 9. 时间与收益权衡

**M2的额外成本**：
- 实现复杂度：中等（需bootstrap检验，但有完整代码）
- 计算时间：PoC显示<0.2秒，全数据预计<5秒
- 总执行时间：约4小时（含所有诊断）

**M2的额外收益**：
- 科学严谨性：符合统计理论标准
- 信息量：ICC、within/between分解、个体间变异
- 竞赛亮点：within-between分解是高级建模技术

**结论**：收益远大于成本。

## Evidence References (for modeler to cite)

- **Candidate pool**: `questions/Q1/02_model/q1_method_candidates.md`
- **PoC results summary**:
  - M1: R² = 0.0706, β_week = 0.00185 ± 0.00113, β_BMI = -0.00164 ± 0.00223, runtime < 0.1s
  - M2: R²_marginal = 0.0682, β_week = 0.00205, β_BMI = -0.00130, ICC ≈ 0.30, runtime < 0.2s
  - M3: R² = 0.0894, β_interaction = -0.00034 ± 0.00027, t = -1.29 (p ≈ 0.20), runtime < 0.1s
- **PoC scripts**: `questions/Q1/02_model/poc/*.py`
- **Data characteristics**: 1082 条记录，267 位孕妇，平均 4.05 次检测/人，重复测量占 97%
- **Problem definition**: `questions/Q1/01_problem/problem_definition.md`
- **Literature**: 
  - [IJE] 聚类稳健SE vs 混合模型比较：识别相同关联，效应一致，速度快74倍
  - [PMC] 混合模型是纵向数据标准方法
  - [Nature] NIPT建模：孕周正相关、BMI负相关
  - 完整30篇文献：`workspace/papers/related_paper_analysis.md`
- **Chorus审查**: `questions/Q1/02_model/chorus_judge.md`（GPT明确要求within-between分解）
- **数据审计**: `questions/Q1/03_data/data_audit_report.md`（数据质量⭐⭐⭐⭐⭐）

---

## Gate G2.5 Pass Criteria

在 `status` 改为 `DECIDED` 之前，以下条件必须满足：

- [x] `decided_by` 已填写（人类姓名）
- [x] `decision_date` 已填写
- [x] `choice` 已明确填写（方法 ID 或组合）
- [x] `rejected_alternatives` 表格中每个非选方法有拒绝理由
- [x] `Modeler's rationale` 已填写且 ≥ 80 字（中文）或 ≥ 50 words
- [x] Rationale 不是 AI 建议的复制粘贴
- [x] Rationale 引用了至少一项 PoC 证据（R²、ICC、β 系数等）
- [x] `status` 已改为 `DECIDED`

**✅ 所有条件已满足，G3.5 代码生成解除阻塞。**

---

## Next Steps After Decision

一旦本文件 `status: DECIDED`：

1. **✅ 已选择 M2为主 + M1/GEE对照**：
   - 调用 `python-model-code-generator` 或直接按 `model_spec.md` 执行
   - 目标方法：M2（with within-between分解）
   - 对照验证：M1（聚类稳健OLS）、GEE（可交换相关）

2. **实施顺序**：
   - 阶段0-2：环境准备、BMI检查、变量转换
   - 阶段3：并行拟合M1、M2、GEE
   - 阶段4-7：M2完整诊断和敏感性分析
   - 阶段8：M3交互项（可选，条件执行）
   - 阶段9-10：主报告表和效应解释

3. **交接给B（编程手）**：
   - 交付文件：`model_spec.md`（MODEL FROZEN冻结规格+执行指南）
   - Git分支：`q1-modeling-a`
   - 预计执行时间：4小时

并行允许：
- ✅ G3 数据审计已完成，清洗数据已就绪

---

## Modeler Signature

**我已独立审查候选方法池、PoC 结果、文献分析、Chorus审查意见和相关证据，以上决策和理由均为本人判断，而非简单采纳 AI 建议。**

**签名**: 宋禹萱  
**日期**: 2026-09-09

---

**决策状态**: ✅ DECIDED  
**Gate G2.5**: ✅ PASS  
**可进入下一阶段**: ✅ G3.5 代码生成
