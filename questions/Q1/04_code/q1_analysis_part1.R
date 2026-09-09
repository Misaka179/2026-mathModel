# Q1 数据分析脚本 - Part 1
# 负责人：B（周小婷）
# 基于：questions/Q1/02_model/model_spec.md
# 日期：2026-09-09
#
# 本脚本执行model_spec.md的阶段0-2：
# - 阶段0: 环境准备
# - 阶段1: BMI前置检查（关键决策点）
# - 阶段2: 创建within-between变量

# ============================================================================
# 阶段0: 环境准备
# ============================================================================

cat("========================================\n")
cat("Q1 数据分析 - 阶段0: 环境准备\n")
cat("========================================\n\n")

# 检查并安装必需包
required_packages <- c(
  "lme4",      # 混合效应模型
  "lmerTest",  # Satterthwaite检验
  "sandwich",  # 聚类稳健SE
  "geepack",   # GEE
  "boot",      # Bootstrap
  "ggplot2",   # 可视化
  "dplyr",     # 数据处理
  "tidyr"      # 数据整理
)

cat("检查必需包...\n")
for (pkg in required_packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    cat(sprintf("安装包: %s\n", pkg))
    install.packages(pkg, repos = "https://cran.rstudio.com/")
  }
}

# 加载包
cat("\n加载包...\n")
library(lme4)
library(lmerTest)
library(sandwich)
library(geepack)
library(boot)
library(ggplot2)
library(dplyr)
library(tidyr)

cat("所有包加载成功!\n\n")

# 读取清洗数据
cat("读取清洗数据...\n")
data_path <- "questions/Q1/03_data/q1_male_data_cleaned.csv"

if (!file.exists(data_path)) {
  stop(sprintf("错误: 数据文件不存在: %s", data_path))
}

data <- read.csv(data_path, fileEncoding = "UTF-8")

cat(sprintf("数据加载成功: %d 行 × %d 列\n", nrow(data), ncol(data)))
cat("\n数据结构:\n")
str(data)

cat("\n数据摘要:\n")
summary(data)

# 确认关键字段存在
required_fields <- c("woman_code", "gestational_week", "bmi", "y_concentration")
missing_fields <- setdiff(required_fields, names(data))
if (length(missing_fields) > 0) {
  stop(sprintf("错误: 缺少必需字段: %s", paste(missing_fields, collapse = ", ")))
}

cat("\n所有必需字段已确认存在!\n")

# ============================================================================
# 阶段1: BMI前置检查（⚠️ 关键决策点）
# ============================================================================

cat("\n========================================\n")
cat("阶段1: BMI前置检查（关键决策点）\n")
cat("========================================\n\n")

cat("目的：确认BMI是否随时间变化，决定使用情况A还是B\n\n")

# 检查BMI时间变异性
bmi_check <- data %>%
  group_by(woman_code) %>%
  summarise(
    n_obs = n(),
    bmi_mean = mean(bmi, na.rm = TRUE),
    bmi_sd = sd(bmi, na.rm = TRUE),
    bmi_range = max(bmi, na.rm = TRUE) - min(bmi, na.rm = TRUE)
  ) %>%
  summarise(
    total_women = n(),
    pct_varying_bmi = mean(bmi_sd > 0, na.rm = TRUE) * 100,
    mean_bmi_sd = mean(bmi_sd, na.rm = TRUE),
    mean_bmi_range = mean(bmi_range, na.rm = TRUE)
  )

cat("BMI时间变异性检查结果:\n")
print(bmi_check)

# 决策规则
pct_varying <- bmi_check$pct_varying_bmi
cat(sprintf("\n孕妇中BMI有变化的比例: %.2f%%\n", pct_varying))

if (pct_varying < 10) {
  cat("\n✅ 决策: 使用情况A（BMI仅个体间变异）\n")
  cat("   继续按情况A执行\n")
  use_case_A <- TRUE
} else {
  cat("\n⚠️ 警告: BMI有变化的孕妇比例 >= 10%\n")
  cat("   需要使用情况B（BMI也需分解）\n")
  cat("   ⚠️ 停止条件触发！必须联系A（宋禹萱）\n")
  stop("停止执行: BMI时间变异性超过10%，需要联系A修改模型公式")
}

# ============================================================================
# 阶段2: 创建within-between变量
# ============================================================================

cat("\n========================================\n")
cat("阶段2: 创建within-between变量\n")
cat("========================================\n\n")

cat("情况A：BMI仅个体间变异\n\n")

# 孕周分解和BMI处理
data <- data %>%
  group_by(woman_code) %>%
  mutate(
    # 孕周分解
    week_mean = mean(gestational_week, na.rm = TRUE),
    week_within = gestational_week - week_mean,
    week_between = week_mean,

    # BMI（个体间，取第一次）
    bmi_between = first(bmi)
  ) %>%
  ungroup()

cat("变量创建完成!\n\n")

# 验证分解正确性
cat("验证分解正确性...\n")
check <- data %>%
  group_by(woman_code) %>%
  summarise(mean_within = mean(week_within))

cat("week_within的组内均值摘要（应接近0）:\n")
print(summary(check$mean_within))

max_abs_mean <- max(abs(check$mean_within))
if (max_abs_mean < 1e-10) {
  cat(sprintf("\n✅ 验证通过: week_within组内均值最大绝对值 = %.2e < 1e-10\n", max_abs_mean))
} else {
  cat(sprintf("\n⚠️ 警告: week_within组内均值最大绝对值 = %.2e，可能存在问题\n", max_abs_mean))
}

# 保存变换后数据
output_path <- "questions/Q1/03_data/q1_data_transformed.csv"
write.csv(data, output_path, row.names = FALSE, fileEncoding = "UTF-8")
cat(sprintf("\n变换后数据已保存至: %s\n", output_path))

cat("\n阶段0-2执行完成!\n")
cat("========================================\n")
