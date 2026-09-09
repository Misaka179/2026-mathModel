# Q1 关键文献下载清单

> 用于队友交接或离线阅读  
> 优先级：⭐⭐⭐⭐⭐ = 必读，⭐⭐⭐ = 建议读

---

## 高优先级文献（强烈推荐下载）

### 1. 方法论关键文献

**[必读] 聚类稳健SE vs 混合模型比较**
- 优先级：⭐⭐⭐⭐⭐
- URL: http://oxfordjournals.org/ije/article-pdf/47/2/516/25088258/dyy012.pdf
- 文件名建议：`01_cluster_robust_vs_mixed_models_IJE.pdf`
- 为什么重要：证明M1和M2应得出一致结果，是决策的关键依据

**[必读] 稳健标准误解释**
- 优先级：⭐⭐⭐⭐⭐
- URL: https://academic.oup.com/ije/article/50/1/346/6044447
- 文件名建议：`02_robust_standard_errors_demystified_IJE.pdf`
- 为什么重要：M1方法的理论基础

**[必读] 纵向数据混合模型**
- 优先级：⭐⭐⭐⭐⭐
- URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC5719989/
- 文件名建议：`03_longitudinal_linear_mixed_models_PMC.pdf`
- 为什么重要：M2方法的理论基础

---

### 2. NIPT建模直接相关文献

**[必读] 多因素NIPT时点模型**
- 优先级：⭐⭐⭐⭐⭐
- URL: https://www.nature.com/articles/s41598-026-48094-1.pdf
- 文件名建议：`04_NIPT_BMI_stratification_Nature.pdf`
- 为什么重要：直接验证孕周正相关、BMI负相关

**[必读] 高BMI群体研究**
- 优先级：⭐⭐⭐⭐⭐
- URL: http://www.scitepress.org/Papers/2026/151072/151072.pdf
- 文件名建议：`05_high_BMI_cohorts_SCITEPRESS.pdf`
- 为什么重要：我们的数据是高BMI群体（均值32.29），完全匹配

**[必读] 胎儿游离DNA影响因素**
- 优先级：⭐⭐⭐⭐⭐
- URL: https://pubmed.ncbi.nlm.nih.gov/28514925/
- 文件名建议：`06_cell_free_DNA_factors_PubMed.pdf`
- 为什么重要：BMI效应量参考（每↑1单位，浓度显著下降）

---

## 中等优先级文献（建议阅读）

**多项式回归模型**
- 优先级：⭐⭐⭐
- URL: http://www.scitepress.org/Papers/2025/148482/148482.pdf
- 文件名建议：`07_polynomial_regression_BMI_optimization.pdf`
- 为什么重要：支持交互项和非线性扩展（M3参考）

**GAM建模Y染色体浓度**
- 优先级：⭐⭐⭐
- URL: http://www.scitepress.org/Papers/2025/147907/147907.pdf
- 文件名建议：`08_GAM_Y_chromosome_factors.pdf`
- 为什么重要：非线性探索的参考

**相关分析研究**
- 优先级：⭐⭐⭐
- URL: https://ijphmr.org/pdf/2026/10.62051-ijphmr.v6n2.01.pdf
- 文件名建议：`09_correlation_gestational_age_BMI.pdf`
- 为什么重要：预期效应量（r=0.45, r=-0.32）

---

## 下载步骤

### 方法1：手动下载（推荐）

1. 打开 `related_paper_analysis.md`
2. 按优先级依次点击URL链接
3. 下载PDF并按建议文件名重命名
4. 保存到统一文件夹

### 方法2：使用下载工具

如果文献较多，可以使用：
- 浏览器扩展（如 Zotero Connector）
- 文献管理软件（如 Zotero、Mendeley）
- 批量下载工具

---

## 交接文件夹结构建议

```
E:\数模资料\2026国赛准备\2026-mathModel\workspace\papers\
├── related_paper_analysis.md          # 文献分析报告（必交接）
├── download_checklist.md              # 本文件（下载清单）
└── pdfs\                               # PDF原文文件夹（可选）
    ├── 01_cluster_robust_vs_mixed_models_IJE.pdf
    ├── 02_robust_standard_errors_demystified_IJE.pdf
    ├── 03_longitudinal_linear_mixed_models_PMC.pdf
    ├── 04_NIPT_BMI_stratification_Nature.pdf
    ├── 05_high_BMI_cohorts_SCITEPRESS.pdf
    ├── 06_cell_free_DNA_factors_PubMed.pdf
    ├── 07_polynomial_regression_BMI_optimization.pdf
    ├── 08_GAM_Y_chromosome_factors.pdf
    └── 09_correlation_gestational_age_BMI.pdf
```

---

## 快速交接方案

### 最小交接（10秒）
```
只发送：related_paper_analysis.md
说明：文件包含所有文献链接和分析，队友可在线阅读
```

### 标准交接（需要时间下载）
```
发送：
1. related_paper_analysis.md
2. pdfs/ 文件夹（包含6篇⭐⭐⭐⭐⭐必读PDF）
说明：核心文献已下载，可离线阅读
```

### 完整交接（可选）
```
发送：
1. related_paper_analysis.md
2. pdfs/ 文件夹（包含所有9篇PDF）
3. download_checklist.md（本文件）
说明：完整文献库，支持深度研究
```

---

## 需要知道的关键信息

```
📚 Q1 文献分析已完成

关键发现：
1. 找到30篇相关文献，15篇直接可用
2. 文献验证：孕周正相关（r≈0.45）、BMI负相关（r≈-0.32）
3. 关键证据：聚类稳健SE与混合模型应得出一致结果
4. 高BMI群体研究与我们的数据完全匹配（均值32.29）

文献支持的决策建议：
- M1（聚类稳健OLS）：⭐⭐⭐⭐⭐ 基线必须
- M2（混合模型）：⭐⭐⭐⭐⭐ 理论最优
- 推荐：M1+M2并行实现，互为验证

文件位置：
- 文献分析报告：workspace/papers/related_paper_analysis.md
- PDF原文（可选）：workspace/papers/pdfs/

快速开始：
1. 阅读 related_paper_analysis.md（15分钟）
2. 重点看第8-9节（文献支持评级和决策依据）
3. 需要深入研究时点击链接阅读原文
```

---

## 注意事项

1. **版权**：部分文献可能需要机构访问权限或付费
2. **时效性**：Web搜索结果中有2025-2026年的文献，可能是预印本
3. **可访问性**：如果某些链接失效，可在分析报告中找到文献标题后自行搜索
4. **引用格式**：若需要正式引用，建议从原文获取完整引用信息

---

**交接状态**：✅ 文献分析报告已完成，可立即交接
