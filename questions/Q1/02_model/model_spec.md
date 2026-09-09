# A→B 交接包：Q1第一问模型规格与执行指南

> 交接时间：2026-09-09  
> 建模手（A）：宋禹萱  
> 编程手（B）：周小婷  
> 状态：MODEL FROZEN（模型已冻结，禁止修改核心结构）

---

## 一、交接文件清单

### ✅ 必需交付物（handoff.md要求）

| 文件 | 路径 | 状态 | 说明 |
|------|------|------|------|
| **问题定义** | `01_problem/problem_definition.md` | ✅ 完成 | 第一问目标、变量、约束 |
| **问题分类** | `01_problem/problem_classification.md` | ✅ 完成 | data-analysis（重复测量） |
| **候选模型池** | `02_model/q1_method_candidates.md` | ✅ 完成 | M1/M2/M3及PoC结果 |
| **模型决策** | `02_model/decisions/method-selector_modeler_decision.md` | ⏸️ 需确认 | 人类决策（G2.5） |
| **⭐模型规格** | `02_model/model_spec.md` | ✅ 完成 | **冻结规格**（本文件） |
| **数据审计** | `03_data/data_audit_report.md` | ✅ 完成 | 数据质量、清洗规则 |
| **清洗数据** | `03_data/q1_male_data_cleaned.csv` | ✅ 完成 | 1082行×12列 |
| **文献分析** | `workspace/papers/related_paper_analysis.md` | ✅ 完成 | 30篇文献支持 |

### 📋 附加参考文件

| 文件 | 路径 | 说明 |
|------|------|------|
| Chorus审查 | `02_model/chorus_judge.md` | Opus+GPT审核意见 |
| 最终修订方案 | `02_model/q1_final_revision.md` | 修正8项问题后的完整方案 |
| P0附件映射 | `p0_attachment_mapping.md` | 附件到子问题映射 |
| PoC样本 | `data_poc_sample.csv` | 50行验证数据 |

---

## 二、MODEL FROZEN 冻结规格

### 🔒 禁止修改的核心结构

根据人类裁决（`q1_final_revision.md`），以下内容已冻结，**编程手B不得修改**：

#### 1. 主模型：M2线性混合效应（within-between分解）

**模型公式（情况A：BMI仅个体间变异）**：
$$Y_{ij} = \beta_0 + \beta_1^W (\text{Week}_{ij} - \overline{\text{Week}}_i) + \beta_2^B \overline{\text{Week}}_i + \beta_3^B \text{BMI}_i + u_i + \epsilon_{ij}$$

- $u_i \sim N(0, \sigma_u^2)$：随机截距
- $\epsilon_{ij} \sim N(0, \sigma_e^2)$：个体内残差

**变量定义**：
- `week_within` = `gestational_week` - `mean(gestational_week) by woman_id`
- `week_between` = `mean(gestational_week) by woman_id`
- `BMI_between` = `first(bmi) by woman_id`（假设BMI不随时间变化）

**估计方法**：
- REML估计
- Satterthwaite或Kenward-Roger自由度近似

#### 2. 对照模型

**M1：聚类稳健OLS**
$$Y_{ij} = \beta_0 + \beta_1 \text{Week}_{ij} + \beta_2 \text{BMI}_{ij} + \epsilon_{ij}$$
- 聚类稳健标准误（cluster by woman_id）

**GEE：可交换相关**
$$Y_{ij} = \beta_0 + \beta_1 \text{Week}_{ij} + \beta_2 \text{BMI}_{ij}$$
- 工作相关矩阵：exchangeable
- 稳健标准误

#### 3. 探索性扩展（M3）

**交互项**（仅当基线模型通过诊断后）：
$$Y_{ij} = \beta_0 + \beta_1^W \text{week\_within}_{ij} + \beta_2^B \text{week\_between}_i + \beta_3^B \text{BMI}_i + \beta_4 (\text{week\_within}_{ij} \times \text{BMI}_i) + u_i + \epsilon_{ij}$$

**决策规则**：
- ML拟合后LRT比较（p<0.05）
- ΔBIC < -2
- 绘图检查实际意义
- 默认放附录，除非三条件全满足

#### 4. 协变量策略（冻结）

| 层级 | 变量 | 处理 |
|------|------|------|
| 核心模型 | week, BMI | 必须纳入 |
| 敏感性分析 | age, IVF | 比较Δβ |
| 排除 | height, weight | 与BMI共线 |
| 技术变量 | 测序质量 | 预设规则纳入 |

**主模型不含协变量**（人类裁决结果）

#### 5. 响应变量处理（冻结）

- **原尺度为主**（不变换）
- 仅当诊断失败（越界>10%或残差严重偏态）才考虑logit变换
- 若变换，两种结果都报告

---

## 三、给编程手B的执行指南

### 阶段0：环境准备（估计30分钟）

#### 安装R包

```r
# 必需包
install.packages(c(
  "lme4",      # 混合效应模型
  "lmerTest",  # Satterthwaite检验
  "sandwich",  # 聚类稳健SE
  "geepack",   # GEE
  "boot",      # Bootstrap
  "ggplot2",   # 可视化
  "dplyr",     # 数据处理
  "tidyr"      # 数据整理
))

# 可选包
install.packages(c(
  "pbkrtest",  # Kenward-Roger检验
  "performance", # 模型诊断
  "sjPlot"     # 表格输出
))
```

#### 读取清洗数据

```r
# 读取A提供的清洗数据
data <- read.csv("E:/数模资料/2026国赛准备/2026-mathModel/questions/Q1/03_data/q1_male_data_cleaned.csv",
                 fileEncoding = "UTF-8")

# 检查数据
str(data)
summary(data)

# 确认关键字段
# woman_code: 孕妇代码（聚类单元）
# gestational_week: 孕周（连续值）
# bmi: BMI
# y_concentration: Y染色体浓度（响应变量）
```

---

### 阶段1：数据前置检查（估计15分钟）⚠️ 关键

**目的**：确认BMI是否随时间变化，决定使用情况A还是B

```r
# 检查BMI时间变异性
library(dplyr)

bmi_check <- data %>% 
  group_by(woman_code) %>% 
  summarise(
    n_obs = n(),
    bmi_mean = mean(bmi, na.rm = TRUE),
    bmi_sd = sd(bmi, na.rm = TRUE),
    bmi_range = max(bmi, na.rm = TRUE) - min(bmi, na.rm = TRUE)
  ) %>%
  summarise(
    pct_varying_bmi = mean(bmi_sd > 0, na.rm = TRUE) * 100,
    mean_bmi_sd = mean(bmi_sd, na.rm = TRUE),
    mean_bmi_range = mean(bmi_range, na.rm = TRUE)
  )

print(bmi_check)

# 决策规则：
# 若 pct_varying_bmi < 10% → 使用情况A（BMI仅个体间）
# 否则 → 使用情况B（BMI也需分解）
```

**⚠️ 检查点**：
- 若 < 10%孕妇BMI有变化 → 继续按情况A执行
- 否则 → **停止，联系A**（需要修改模型公式）

---

### 阶段2：创建within-between变量（估计10分钟）

```r
# 情况A：BMI仅个体间变异
data <- data %>%
  group_by(woman_code) %>%
  mutate(
    # 孕周分解
    week_mean = mean(gestational_week, na.rm = TRUE),
    week_within = gestational_week - week_mean,
    week_between = week_mean,
    
    # BMI（个体间，取第一次或平均）
    bmi_between = first(bmi)  # 若稳定，first()和mean()相等
  ) %>%
  ungroup()

# 验证分解正确
# week_within的组内均值应为0
check <- data %>% 
  group_by(woman_code) %>% 
  summarise(mean_within = mean(week_within))
summary(check$mean_within)  # 应接近0

# 保存变换后数据
write.csv(data, "questions/Q1/03_data/q1_data_transformed.csv", 
          row.names = FALSE, fileEncoding = "UTF-8")
```

---

### 阶段3：拟合三个基线模型（估计30分钟）

#### M1：聚类稳健OLS

```r
library(sandwich)
library(lmtest)

# 拟合OLS
fit_m1 <- lm(y_concentration ~ gestational_week + bmi, data = data)

# 聚类稳健标准误
vcov_cl <- vcovCL(fit_m1, cluster = ~ woman_code, type = "HC1")
coef_m1 <- coeftest(fit_m1, vcov = vcov_cl)

# 保存结果
print(coef_m1)
summary(fit_m1)

# 提取关键结果
m1_results <- data.frame(
  model = "M1_ClusterRobustOLS",
  term = names(coef(fit_m1)),
  estimate = coef(fit_m1),
  se_robust = sqrt(diag(vcov_cl)),
  t_value = coef_m1[, "t value"],
  p_value = coef_m1[, "Pr(>|t|)"]
)
```

#### M2：线性混合效应模型（主模型）

```r
library(lme4)
library(lmerTest)

# 拟合M2（情况A）
fit_m2 <- lmer(y_concentration ~ week_within + week_between + bmi_between + (1 | woman_code), 
               data = data, 
               REML = TRUE)

# 查看结果
summary(fit_m2, ddf = "Satterthwaite")

# 固定效应
fixef_m2 <- summary(fit_m2)$coefficients

# 随机效应方差
vc <- as.data.frame(VarCorr(fit_m2))
sigma_u <- vc$vcov[1]  # 随机截距方差
sigma_e <- vc$vcov[2]  # 残差方差

# 计算ICC
icc <- sigma_u / (sigma_u + sigma_e)
print(paste("ICC =", round(icc, 3)))

# R²
library(performance)
r2_m2 <- r2(fit_m2)
print(r2_m2)
```

#### GEE：可交换相关

```r
library(geepack)

# 拟合GEE
fit_gee <- geeglm(y_concentration ~ gestational_week + bmi, 
                  id = woman_code, 
                  data = data,
                  corstr = "exchangeable",
                  family = gaussian())

# 查看结果
summary(fit_gee)

# 提取系数
coef_gee <- summary(fit_gee)$coefficients
```

**⚠️ 检查点1**：三模型β符号一致性
```r
# 提取关键系数
beta_week_m1 <- coef(fit_m1)["gestational_week"]
beta_week_m2_within <- fixef(fit_m2)["week_within"]
beta_week_m2_between <- fixef(fit_m2)["week_between"]
beta_week_gee <- coef(fit_gee)["gestational_week"]

# 打印比较
cat("孕周系数比较：\n")
cat("M1(混合):", beta_week_m1, "\n")
cat("M2(within):", beta_week_m2_within, "\n")
cat("M2(between):", beta_week_m2_between, "\n")
cat("GEE(混合):", beta_week_gee, "\n")

# ⚠️ 若符号不一致或量级差异巨大，联系A
```

---

### 阶段4：P0诊断清单（估计45分钟）⚠️ 必须全部执行

所有诊断都是**描述性评估**，无硬阈值。

#### 4.1 残差图（异方差检查）

```r
# M2的残差
data$resid_m2 <- residuals(fit_m2)
data$fitted_m2 <- fitted(fit_m2)

# 残差 vs 拟合值
library(ggplot2)
p1 <- ggplot(data, aes(x = fitted_m2, y = resid_m2)) +
  geom_point(alpha = 0.3) +
  geom_hline(yintercept = 0, color = "red", linetype = "dashed") +
  geom_smooth(method = "loess", se = FALSE, color = "blue") +
  labs(title = "M2: Residuals vs Fitted",
       x = "Fitted values", y = "Residuals") +
  theme_minimal()
print(p1)
ggsave("questions/Q1/06_figures/m2_resid_vs_fitted.png", p1, width = 8, height = 6)

# 残差 vs 孕周
p2 <- ggplot(data, aes(x = gestational_week, y = resid_m2)) +
  geom_point(alpha = 0.3) +
  geom_hline(yintercept = 0, color = "red", linetype = "dashed") +
  geom_smooth(method = "loess", se = FALSE, color = "blue") +
  labs(title = "M2: Residuals vs Gestational Week") +
  theme_minimal()
print(p2)
ggsave("questions/Q1/06_figures/m2_resid_vs_week.png", p2, width = 8, height = 6)

# 残差 vs BMI
p3 <- ggplot(data, aes(x = bmi, y = resid_m2)) +
  geom_point(alpha = 0.3) +
  geom_hline(yintercept = 0, color = "red", linetype = "dashed") +
  geom_smooth(method = "loess", se = FALSE, color = "blue") +
  labs(title = "M2: Residuals vs BMI") +
  theme_minimal()
print(p3)
ggsave("questions/Q1/06_figures/m2_resid_vs_bmi.png", p3, width = 8, height = 6)

# ⚠️ 描述性评估：
# - 若有明显扇形或系统趋势 → 记录，考虑加权或变换
# - 若大致随机散布 → 通过
```

#### 4.2 正态性检查

```r
# Q-Q图（残差）
p4 <- ggplot(data, aes(sample = resid_m2)) +
  stat_qq() +
  stat_qq_line(color = "red") +
  labs(title = "M2: Q-Q Plot (Residuals)") +
  theme_minimal()
print(p4)
ggsave("questions/Q1/06_figures/m2_qq_residuals.png", p4, width = 8, height = 6)

# 随机截距Q-Q图
ranef_m2 <- ranef(fit_m2)$woman_code[[1]]
p5 <- ggplot(data.frame(u = ranef_m2), aes(sample = u)) +
  stat_qq() +
  stat_qq_line(color = "red") +
  labs(title = "M2: Q-Q Plot (Random Intercepts)") +
  theme_minimal()
print(p5)
ggsave("questions/Q1/06_figures/m2_qq_ranef.png", p5, width = 8, height = 6)

# ⚠️ 描述性评估：
# - 尾部略偏离可容忍（n=1082）
# - 不用Shapiro-Wilk p值（大样本几乎必拒）
```

#### 4.3 预测越界检查

```r
# 预测值范围
pred_range <- range(data$fitted_m2)
cat("预测值范围: [", pred_range[1], ",", pred_range[2], "]\n")

# 越界比例
n_below_0 <- sum(data$fitted_m2 < 0)
n_above_1 <- sum(data$fitted_m2 > 1)
pct_out <- (n_below_0 + n_above_1) / nrow(data) * 100

cat("越界记录数:", n_below_0 + n_above_1, "\n")
cat("越界比例:", round(pct_out, 2), "%\n")

# ⚠️ 描述性评估：
# - 若越界比例 < 5% → 可接受
# - 若 > 10% → 考虑logit变换
```

#### 4.4 非线性检查

```r
# 部分残差图（孕周二次项）
data$week_sq <- data$gestational_week^2
fit_quad <- lmer(y_concentration ~ week_within + I(week_within^2) + week_between + bmi_between + (1 | woman_code),
                 data = data, REML = FALSE)  # ML拟合

# LRT比较
anova(fit_m2, fit_quad)

# ⚠️ 决策：
# - 若p < 0.05且AIC下降 → 考虑加入二次项
# - 否则 → 线性充分
```

#### 4.5 影响点检查

```r
# 删除单个孕妇重拟合（耗时，仅检查前10位）
unique_women <- unique(data$woman_code)[1:10]

influence_check <- data.frame(
  woman_id = character(),
  beta_week_w = numeric(),
  beta_week_b = numeric(),
  beta_bmi = numeric(),
  stringsAsFactors = FALSE
)

for (w in unique_women) {
  data_minus <- data[data$woman_code != w, ]
  fit_minus <- lmer(y_concentration ~ week_within + week_between + bmi_between + (1 | woman_code),
                    data = data_minus, REML = TRUE)
  influence_check <- rbind(influence_check, data.frame(
    woman_id = w,
    beta_week_w = fixef(fit_minus)["week_within"],
    beta_week_b = fixef(fit_minus)["week_between"],
    beta_bmi = fixef(fit_minus)["bmi_between"]
  ))
}

# 查看变化
print(influence_check)

# ⚠️ 描述性评估：识别变化最大的孕妇
```

---

### 阶段5：随机效应检验（估计30分钟）⚠️ 参数bootstrap

#### 5.1 H0: σ²_u = 0 检验

```r
library(boot)

# 定义bootstrap函数
boot_lrt <- function(data, indices) {
  d <- data[indices, ]
  
  # 拟合混合模型
  fit_alt <- lmer(y_concentration ~ week_within + week_between + bmi_between + (1 | woman_code),
                  data = d, REML = TRUE)
  
  # 拟合固定效应模型
  fit_null <- lm(y_concentration ~ week_within + week_between + bmi_between, data = d)
  
  # LRT统计量
  ll_alt <- logLik(fit_alt)
  ll_null <- logLik(fit_null)
  lrt <- 2 * (as.numeric(ll_alt) - as.numeric(ll_null))
  
  return(lrt)
}

# 运行bootstrap（R=1000，耗时约5-10分钟）
set.seed(123)
boot_res <- boot(data, boot_lrt, R = 1000)

# 观测的LRT统计量
obs_lrt <- 2 * (as.numeric(logLik(fit_m2)) - as.numeric(logLik(lm(y_concentration ~ week_within + week_between + bmi_between, data = data))))

# p值
p_value_ranef <- mean(boot_res$t >= obs_lrt)
cat("随机效应检验 p值:", p_value_ranef, "\n")

# ⚠️ 若p < 0.05 → 随机截距显著，M2有必要
```

#### 5.2 ICC置信区间

```r
# 定义bootstrap函数
boot_icc <- function(data, indices) {
  d <- data[indices, ]
  fit <- lmer(y_concentration ~ week_within + week_between + bmi_between + (1 | woman_code),
              data = d, REML = TRUE)
  vc <- as.data.frame(VarCorr(fit))
  sigma_u <- vc$vcov[1]
  sigma_e <- vc$vcov[2]
  icc <- sigma_u / (sigma_u + sigma_e)
  return(icc)
}

# 运行bootstrap
set.seed(456)
boot_icc_res <- boot(data, boot_icc, R = 1000)

# 95% CI
icc_ci <- boot.ci(boot_icc_res, type = "perc")
print(icc_ci)

# 保存ICC结果
cat("ICC点估计:", icc, "\n")
cat("ICC 95% CI:", icc_ci$percent[4], "-", icc_ci$percent[5], "\n")
```

---

### 阶段6：Within vs Between检验（估计10分钟）

```r
# H0: β^W = β^B（孕周的within和between效应相等）

# 提取协方差矩阵
vcov_m2 <- vcov(fit_m2)

# 系数差异
beta_diff <- fixef(fit_m2)["week_within"] - fixef(fit_m2)["week_between"]

# 差异的方差
var_diff <- vcov_m2["week_within", "week_within"] + 
            vcov_m2["week_between", "week_between"] - 
            2 * vcov_m2["week_within", "week_between"]

# Wald检验
z_stat <- beta_diff / sqrt(var_diff)
p_value_wb <- 2 * (1 - pnorm(abs(z_stat)))

cat("Within vs Between检验:\n")
cat("β^W - β^B =", beta_diff, "\n")
cat("z统计量 =", z_stat, "\n")
cat("p值 =", p_value_wb, "\n")

# ⚠️ 若p < 0.05 → within和between效应显著不同
```

---

### 阶段7：敏感性分析（估计30分钟）

#### 7.1 协变量调整

```r
# 加入age和IVF
fit_m2_adj <- lmer(y_concentration ~ week_within + week_between + bmi_between + age + ivf + (1 | woman_code),
                   data = data, REML = TRUE)

# 比较β变化
fixef_original <- fixef(fit_m2)
fixef_adjusted <- fixef(fit_m2_adj)

delta_beta <- data.frame(
  term = c("week_within", "week_between", "bmi_between"),
  original = fixef_original[c("week_within", "week_between", "bmi_between")],
  adjusted = fixef_adjusted[c("week_within", "week_between", "bmi_between")],
  change = fixef_adjusted[c("week_within", "week_between", "bmi_between")] - 
           fixef_original[c("week_within", "week_between", "bmi_between")],
  pct_change = (fixef_adjusted[c("week_within", "week_between", "bmi_between")] - 
                fixef_original[c("week_within", "week_between", "bmi_between")]) / 
               fixef_original[c("week_within", "week_between", "bmi_between")] * 100
)

print(delta_beta)
```

#### 7.2 信息性复测检查

```r
# 首次检测子集
data_first <- data %>%
  group_by(woman_code) %>%
  filter(row_number() == 1) %>%
  ungroup()

# 首次检测模型（简化，不分解）
fit_first <- lm(y_concentration ~ gestational_week + bmi, data = data_first)
summary(fit_first)

# 比较系数
cat("首次检测 β_week:", coef(fit_first)["gestational_week"], "\n")
cat("全数据混合 β_week:", coef(fit_m1)["gestational_week"], "\n")

# ⚠️ 描述性比较，明确局限性
```

---

### 阶段8：M3交互项（估计20分钟）⚠️ 仅当基线通过诊断

```r
# 交互项模型（ML拟合）
fit_m3 <- lmer(y_concentration ~ week_within + week_between + bmi_between + 
                 week_within:bmi_between + (1 | woman_code),
               data = data, REML = FALSE)  # 必须ML

# LRT比较（M2也需用ML）
fit_m2_ml <- lmer(y_concentration ~ week_within + week_between + bmi_between + (1 | woman_code),
                  data = data, REML = FALSE)

lrt_result <- anova(fit_m2_ml, fit_m3)
print(lrt_result)

# BIC比较
bic_m2 <- BIC(fit_m2_ml)
bic_m3 <- BIC(fit_m3)
delta_bic <- bic_m3 - bic_m2

cat("ΔBIC:", delta_bic, "\n")

# ⚠️ 决策规则：
# - LRT p < 0.05 且 ΔBIC < -2 → 交互显著
# - 需绘图检查实际意义
```

---

### 阶段9：生成主报告表（估计20分钟）

```r
# 提取所有关键结果
results_summary <- data.frame(
  Model = c("M2主模型", "M1对照", "GEE对照"),
  
  beta_week_W = c(
    sprintf("%.5f (%.5f, %.5f)", 
            fixef(fit_m2)["week_within"],
            confint(fit_m2)["week_within", 1],
            confint(fit_m2)["week_within", 2]),
    "—",
    "—"
  ),
  
  p_week_W = c(
    sprintf("%.4f", summary(fit_m2)$coefficients["week_within", "Pr(>|t|)"]),
    "—",
    "—"
  ),
  
  beta_week_B = c(
    sprintf("%.5f (%.5f, %.5f)",
            fixef(fit_m2)["week_between"],
            confint(fit_m2)["week_between", 1],
            confint(fit_m2)["week_between", 2]),
    sprintf("%.5f (%.5f, %.5f)",  # M1混合关联
            coef(fit_m1)["gestational_week"],
            coef_m1["gestational_week", "Estimate"] - 1.96 * sqrt(diag(vcov_cl)["gestational_week"]),
            coef_m1["gestational_week", "Estimate"] + 1.96 * sqrt(diag(vcov_cl)["gestational_week"])),
    sprintf("%.5f", coef(fit_gee)["gestational_week"])
  ),
  
  ICC = c(
    sprintf("%.3f (%.3f, %.3f)", icc, icc_ci$percent[4], icc_ci$percent[5]),
    "—",
    "—"
  ),
  
  R2_marg = c(
    sprintf("%.4f", r2_m2$R2_marginal),
    sprintf("%.4f", summary(fit_m1)$r.squared),
    "—"
  ),
  
  R2_cond = c(
    sprintf("%.4f", r2_m2$R2_conditional),
    "—",
    "—"
  )
)

print(results_summary)

# 保存表格
write.csv(results_summary, "questions/Q1/05_results/q1_main_results_table.csv",
          row.names = FALSE, fileEncoding = "UTF-8")
```

---

### 阶段10：效应量解释（估计15分钟）

```r
# 计算效应量（占均值的百分比）
mean_y <- mean(data$y_concentration)

# Within效应
beta_w <- fixef(fit_m2)["week_within"]
effect_w_pct <- beta_w / mean_y * 100

# Between效应
beta_b_week <- fixef(fit_m2)["week_between"]
effect_b_week_pct <- beta_b_week / mean_y * 100

# BMI效应
beta_bmi <- fixef(fit_m2)["bmi_between"]
effect_bmi_pct <- beta_bmi / mean_y * 100

# 生成解释文本
interpretation <- sprintf(
  "孕周每增加1周，同一孕妇的Y浓度平均增加%.5f (95%% CI: [%.5f, %.5f])，占样本均值的%.2f%%。\n不同孕妇间，平均检测孕周每相差1周，Y浓度平均相差%.5f，占样本均值的%.2f%%。\nBMI每增加1单位，不同孕妇间Y浓度平均相差%.5f，占样本均值的%.2f%%。",
  beta_w, confint(fit_m2)["week_within", 1], confint(fit_m2)["week_within", 2], effect_w_pct,
  beta_b_week, effect_b_week_pct,
  beta_bmi, effect_bmi_pct
)

cat(interpretation)

# 保存
writeLines(interpretation, "questions/Q1/05_results/q1_effect_interpretation.txt")
```

---

## 四、输出文件清单（B需要交付给C）

### 必需产出

| 文件 | 路径 | 说明 |
|------|------|------|
| **⭐主结果表** | `05_results/q1_main_results_table.csv` | M1/M2/GEE对比表 |
| **效应解释** | `05_results/q1_effect_interpretation.txt` | 通俗语言解释 |
| **完整结果报告** | `05_results/q1_verified_results.md` | 包含所有诊断、敏感性分析 |
| **代码** | `04_code/q1_analysis.R` | 完整可复现代码 |
| **诊断图** | `06_figures/m2_*.png` | 残差图、Q-Q图等 |

### 结果验证要求（handoff.md）

B交给C的`verified_results.md`必须满足：
- ✅ **每个数字有来源**（从哪个模型、哪个系数）
- ✅ **经人确认冻结**（B检查后确认无误）
- ✅ **可追溯**（代码行号、数据文件版本）

---

## 五、关键检查点与停止条件

### ⚠️ 必须停止并联系A的情况

| 情况 | 停止原因 | 联系A |
|------|---------|-------|
| BMI有>10%孕妇时间变异 | 需要情况B模型公式 | ✅ |
| M1/M2/GEE系数符号不一致 | 模型设定可能有问题 | ✅ |
| M2不收敛（迭代>1000次） | 需要简化随机效应或调整 | ✅ |
| 残差严重非正态且越界>15% | 可能需要logit变换 | ✅ |
| Within和Between效应符号相反 | Simpson悖论，需讨论 | ✅ |

### ✅ 可以继续的情况（描述性记录）

| 情况 | 处理 |
|------|------|
| 残差略偏态但越界<5% | 记录，继续原尺度 |
| 影响点导致β变化<10% | 记录，敏感性分析 |
| 交互项不显著 | 放附录 |
| 协变量调整β变化<5% | 记录，主模型不变 |

---

## 六、时间估算

| 阶段 | 内容 | 预计时间 |
|------|------|---------|
| 0 | 环境准备 | 30分钟 |
| 1 | BMI前置检查 | 15分钟 |
| 2 | 变量转换 | 10分钟 |
| 3 | 三模型拟合 | 30分钟 |
| 4 | P0诊断 | 45分钟 |
| 5 | Bootstrap检验 | 30分钟 |
| 6 | Within-Between检验 | 10分钟 |
| 7 | 敏感性分析 | 30分钟 |
| 8 | 交互项（可选） | 20分钟 |
| 9 | 主表生成 | 20分钟 |
| 10 | 效应解释 | 15分钟 |
| **总计** | | **约4小时** |

---

## 七、常见问题FAQ

### Q1: 如果M2不收敛怎么办？
**A**: 
1. 检查是否有极端异常值
2. 尝试标准化变量（但需记录转换）
3. 简化随机效应（去掉交互项）
4. **联系A**，考虑用M1为主、M2为对照

### Q2: 随机效应bootstrap太慢怎么办？
**A**: 
1. 先用R=100快速测试
2. 确认代码无误后，用R=1000正式运行
3. 可以晚上运行（约10-15分钟）

### Q3: ICC的bootstrap CI很宽怎么办？
**A**: 
- 这是正常现象（267个簇，不是267×4=1082个独立样本）
- 报告点估计和CI，说明不确定性

### Q4: 交互项该不该放正文？
**A**: 
- 按决策规则：LRT p<0.05 且 ΔBIC<-2 且实际意义明确
- **默认附录**，除非三条件全满足
- 不确定时**联系A**

- 

---

## 八、交接确认

### A的交接承诺

- ✅ 模型结构已冻结（M2 with within-between）
- ✅ 协变量策略已明确（主模型不含）
- ✅ 诊断标准已说明（描述性，无硬阈值）
- ✅ 决策规则已给出（交互项、变换）
- ✅ 数据已清洗且质量优秀（1082行，无缺失）

### B的执行承诺（需确认）

- [ ] 已阅读本指南全文
- [ ] 理解MODEL FROZEN的约束
- [ ] 知道何时停止并联系A
- [ ] 承诺按阶段0-10顺序执行
- [ ] 保证结果可追溯（代码+数据版本）



---

## 九、Git提交要求

### 分支策略
```bash
# B创建自己的分支
git checkout -b q1-analysis-b

# 完成后提交
git add questions/Q1/04_code/*
git add questions/Q1/05_results/*
git add questions/Q1/06_figures/*
git commit -m "Q1: 完成模型拟合和诊断 (B-周小婷)

- M1/M2/GEE三模型拟合
- P0诊断清单全部完成
- Bootstrap检验完成
- 主结果表生成

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"

git push origin q1-analysis-b
```

- [ ] 

---

