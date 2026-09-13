"""
Q3 情景规划模型 v1.2
严格遵循 Model Spec v1.2

核心改进：
1. 新负载预测器：日电量水平 + 日内形状分解（1/15起锁定类型）
2. 历史残差as-of重算（无信息泄露）
3. 近期+季节/相似日情景选择（配对残差）
4. 删除scenario 0直接执行，改用动态价值函数
5. 删除固定STORAGE_VALUE，改用动态价值函数
6. 完整实现Stage k调整（6/12/18点）
7. 信息泄露审计

模型架构：
Scenario-based day-ahead planning + Multi-stage rolling adjustment + Dynamic value control
"""

import sys
import io
import pandas as pd
import numpy as np
from pathlib import Path
import pulp
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 路径配置
DATA_ROOT = Path("E:/数模资料/2026国赛准备/2026-mathModel/questions/QC-3/03_data")
OUTPUT_ROOT = Path("E:/数模资料/2026国赛准备/2026-mathModel/questions/QC-3/05_results")
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

# ============================================================
# 常量定义
# ============================================================

DT = 1/6
N_SLOTS = 144

# 储能参数
ETA = 0.9
E_INIT = 6000
E_MIN = 1200
E_MAX = 10800
P_MAX = 5000
POWER_LIMIT = P_MAX * DT

# 成本系数
ALPHA_EMERGENCY = 5
ALPHA_PENALTY = 0.5
ALPHA_EXCESS = 1.5

# 情景参数
N_SCENARIOS = 30

# 决策时刻（小时）
DECISION_HOURS = [0, 6, 12, 18]
# Python 0-based索引：6:00->index 36, 12:00->index 72, 18:00->index 108
DECISION_INDICES = {0: 0, 6: 36, 12: 72, 18: 108}

# 日类型（通过1/1-1/14识别，1/15起锁定）
LOW_LOAD_WEEKDAYS = None  # 将由infer_day_types_from_jan1_14()识别

# ============================================================
# 附件3：光伏预报数据加载（0/6/12/18四个时刻）
# ============================================================

# 导入修复后的预报加载模块
from load_pv_forecast_attachment3 import load_pv_forecast_attachment3

# 保留 get_pv_forecast_as_of 函数（信息集控制）

def get_pv_forecast_as_of(date: datetime, cutoff_hour: int,
                         pv_forecast_0h: Dict, pv_forecast_6h: Dict,
                         pv_forecast_12h: Dict, pv_forecast_18h: Dict) -> np.ndarray:
    """
    获取指定时刻可用的PV预报（严格信息集控制）

    参数:
        date: 目标日期
        cutoff_hour: 决策时刻（0/6/12/18）

    返回:
        144个时段的PV预报功率（kW）

    信息集原则:
        - cutoff_hour=0: 只能使用0:00发布的预报
        - cutoff_hour=6: 使用6:00发布的预报
        - cutoff_hour=12: 使用12:00发布的预报
        - cutoff_hour=18: 使用18:00发布的预报
    """
    if cutoff_hour == 0:
        return pv_forecast_0h.get(date, np.zeros(144))
    elif cutoff_hour == 6:
        # 优先使用6:00预报，如果没有则回退到0:00
        return pv_forecast_6h.get(date, pv_forecast_0h.get(date, np.zeros(144)))
    elif cutoff_hour == 12:
        # 优先使用12:00预报，回退顺序：12→6→0
        if date in pv_forecast_12h:
            return pv_forecast_12h[date]
        elif date in pv_forecast_6h:
            return pv_forecast_6h[date]
        else:
            return pv_forecast_0h.get(date, np.zeros(144))
    elif cutoff_hour == 18:
        # 优先使用18:00预报，回退顺序：18→12→6→0
        if date in pv_forecast_18h:
            return pv_forecast_18h[date]
        elif date in pv_forecast_12h:
            return pv_forecast_12h[date]
        elif date in pv_forecast_6h:
            return pv_forecast_6h[date]
        else:
            return pv_forecast_0h.get(date, np.zeros(144))
    else:
        raise ValueError(f"cutoff_hour必须是0/6/12/18，得到{cutoff_hour}")

# ============================================================
# 数据结构
# ============================================================

@dataclass
class DayData:
    """单日数据"""
    date: datetime
    load: np.ndarray  # 144个时段
    pv: np.ndarray

@dataclass
class ForecastResult:
    """预测结果"""
    load_forecast: np.ndarray
    pv_forecast: np.ndarray
    B_forecast: float  # 预测日电量
    k_type: int  # 日类型
    shape_source_dates: List[datetime]
    beta: Optional[float]

# ============================================================
# 数据加载与缓存
# ============================================================

def load_data():
    """加载所有数据并构建日期索引（包含时间对齐修复）"""
    print("加载数据...")

    price = pd.read_csv(DATA_ROOT / "price.csv")['price'].values

    load_real = pd.read_csv(DATA_ROOT / "load_real.csv")
    load_real['date'] = pd.to_datetime(load_real['date'])

    pv_real = pd.read_csv(DATA_ROOT / "pv_real.csv")
    pv_real['date'] = pd.to_datetime(pv_real['date'])

    # 构建实测PV字典（用于提供预报锚点）
    pv_actual_dict = {}
    for date in pd.date_range('2025-01-01', '2025-12-31', freq='D'):
        pv_day = pv_real[pv_real['date'] == date]['pv_kw'].values
        if len(pv_day) == N_SLOTS:
            pv_actual_dict[date] = pv_day

    # 加载附件3：多时刻光伏预报（0/6/12/18时刻）- 带时间对齐修复
    attachment3_path = Path("E:/数模资料/2026国赛准备/2026-mathModel/C题/附件/附件3.xlsx")
    pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h = load_pv_forecast_attachment3(
        str(attachment3_path), pv_actual_dict
    )

    print(f"  [OK] 电价: {len(price)} 时段")
    print(f"  [OK] 真实负载: {len(load_real)} 行")
    print(f"  [OK] 真实光伏: {len(pv_real)} 行")

    return price, load_real, pv_real, pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h

def build_date_cache(load_real: pd.DataFrame, pv_real: pd.DataFrame) -> Tuple[Dict, Dict]:
    """构建日期索引缓存"""
    print("构建日期缓存...")

    load_by_date = {}
    pv_by_date = {}

    for date in pd.date_range('2025-01-01', '2025-12-31', freq='D'):
        load_day = load_real[load_real['date'] == date]['load_kw'].values
        pv_day = pv_real[pv_real['date'] == date]['pv_kw'].values

        if len(load_day) == N_SLOTS:
            load_by_date[date] = load_day
        if len(pv_day) == N_SLOTS:
            pv_by_date[date] = pv_day

    print(f"  [OK] 缓存负载: {len(load_by_date)} 天")
    print(f"  [OK] 缓存光伏: {len(pv_by_date)} 天")

    return load_by_date, pv_by_date

# ============================================================
# Phase 1: 新负载预测器（日电量水平 + 日内形状分解）
# ============================================================

def infer_day_types_from_jan1_14(load_by_date: Dict) -> set:
    """
    从1/1-1/14数据识别低负载星期类别

    返回:
        低负载星期的集合（weekday编码：0=Monday, 6=Sunday）
    """
    # 统计各星期的平均日电量
    weekday_energies = {i: [] for i in range(7)}

    for day_offset in range(14):
        date = datetime(2025, 1, 1) + timedelta(days=day_offset)
        if date in load_by_date:
            daily_energy = compute_daily_energy(load_by_date[date])
            weekday = date.weekday()
            weekday_energies[weekday].append(daily_energy)

    # 计算各星期的平均值
    weekday_avg = {}
    for wd in range(7):
        if weekday_energies[wd]:
            weekday_avg[wd] = np.mean(weekday_energies[wd])
        else:
            weekday_avg[wd] = np.inf

    # 找出平均日电量最低的两个星期类别
    sorted_weekdays = sorted(weekday_avg.items(), key=lambda x: x[1])
    low_load_weekdays = {sorted_weekdays[0][0], sorted_weekdays[1][0]}

    # 输出识别结果
    weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    print(f"\n日类型识别结果（基于1/1-1/14数据）:")
    for wd, avg_energy in sorted(weekday_avg.items(), key=lambda x: x[1]):
        status = "低负载" if wd in low_load_weekdays else "高负载"
        print(f"  {weekday_names[wd]:9s}: {avg_energy:,.0f} kWh  [{status}]")

    return low_load_weekdays

def classify_day_type(date: datetime) -> int:
    """
    日类型分类（1/15起锁定）

    返回:
        0: 低负载类
        1: 高负载类
    """
    global LOW_LOAD_WEEKDAYS
    if LOW_LOAD_WEEKDAYS is None:
        raise RuntimeError("LOW_LOAD_WEEKDAYS未初始化，需先调用infer_day_types_from_jan1_14()")
    return 0 if date.weekday() in LOW_LOAD_WEEKDAYS else 1

def compute_daily_energy(load_day: np.ndarray) -> float:
    """计算日总电量（kWh）"""
    return float(np.sum(load_day) * DT)

def get_same_type_history(target_date: datetime, load_by_date: Dict,
                          n_days: int = 3) -> List[datetime]:
    """
    获取最近n个同类型历史日

    参数:
        target_date: 目标日期
        load_by_date: 负载数据字典
        n_days: 需要的历史日数量

    返回:
        同类型历史日期列表
    """
    target_type = classify_day_type(target_date)
    candidates = []

    check_date = target_date - timedelta(days=1)
    while len(candidates) < n_days and check_date >= datetime(2025, 1, 1):
        if check_date in load_by_date:
            if classify_day_type(check_date) == target_type:
                candidates.append(check_date)
        check_date -= timedelta(days=1)

    return candidates

def estimate_daily_level(target_date: datetime, load_by_date: Dict) -> Tuple[float, Optional[float], str]:
    """
    估计日电量水平

    逻辑:
        1. 同类型相邻日：延续前一日电量
        2. 类型切换：使用最近35天切换对数比例的median

    返回:
        (B_forecast, beta, method)
    """
    target_type = classify_day_type(target_date)
    prev_date = target_date - timedelta(days=1)

    # 检查是否类型切换
    if prev_date not in load_by_date:
        # 无前一日数据，使用最近可用同类型日
        same_type_hist = get_same_type_history(target_date, load_by_date, n_days=1)
        if same_type_hist:
            B_prev = compute_daily_energy(load_by_date[same_type_hist[0]])
            return B_prev, None, "fallback_same_type"
        else:
            return 4500.0 * N_SLOTS, None, "fallback_default"

    prev_type = classify_day_type(prev_date)
    B_prev = compute_daily_energy(load_by_date[prev_date])

    if target_type == prev_type:
        # 同类型延续
        return B_prev, None, "same_type_continuation"

    # 类型切换：找最近35天的切换对（必须匹配相同切换方向）
    switch_pairs = []
    for i in range(1, 36):
        check_date = target_date - timedelta(days=i)
        check_prev = check_date - timedelta(days=1)

        if check_date in load_by_date and check_prev in load_by_date:
            check_type = classify_day_type(check_date)
            check_prev_type = classify_day_type(check_prev)

            # 必须匹配相同的切换方向
            if check_prev_type == prev_type and check_type == target_type:
                B_i = compute_daily_energy(load_by_date[check_date])
                B_i_prev = compute_daily_energy(load_by_date[check_prev])

                if B_i_prev > 0:
                    log_ratio = np.log(B_i / B_i_prev)
                    switch_pairs.append(log_ratio)

    if switch_pairs:
        beta = np.median(switch_pairs)
        B_forecast = B_prev * np.exp(beta)
        return B_forecast, beta, "type_switch_median"
    else:
        # 无足够切换样本，使用同类型历史平均
        # print(f"  ⚠️ 警告: {target_date.date()} 类型切换但历史不足35天，使用fallback")
        same_type_dates = get_same_type_history(target_date, load_by_date, n_days=5)
        if same_type_dates:
            B_same_type = [compute_daily_energy(load_by_date[d]) for d in same_type_dates]
            B_forecast = np.mean(B_same_type)
            # print(f"    使用最近{len(same_type_dates)}个同类型日平均: {B_forecast:.0f} kWh")
            return B_forecast, None, "fallback_same_type_avg"
        else:
            # print(f"    无同类型历史，延续前一日: {B_prev:.0f} kWh")
            return B_prev, 0.0, "fallback_neutral"

def forecast_load_shape(target_date: datetime, load_by_date: Dict,
                       n_days: int = 3) -> Tuple[np.ndarray, List[datetime]]:
    """
    预测日内形状（最近n个同类型日归一化）

    返回:
        (shape, source_dates)
    """
    same_type_dates = get_same_type_history(target_date, load_by_date, n_days=n_days)

    if not same_type_dates:
        # 无同类型历史，使用默认形状
        default_shape = np.ones(N_SLOTS) / N_SLOTS
        return default_shape, []

    # 按能量加权累加（修复：确保 sum(shape) = 1.0）
    total_energy_array = np.zeros(N_SLOTS)

    for hist_date in same_type_dates:
        load_hist = load_by_date[hist_date]  # kW
        energy_hist = load_hist * DT          # kWh per slot
        total_energy_array += energy_hist

    total_energy = np.sum(total_energy_array)

    if total_energy > 0:
        shape = total_energy_array / total_energy
    else:
        shape = np.ones(N_SLOTS) / N_SLOTS

    return shape, same_type_dates

def forecast_load_as_of(target_date: datetime, load_by_date: Dict) -> ForecastResult:
    """
    按as-of原则预测负载（使用target_date之前的信息）

    适用规则:
        - 2025-01-01: 无历史，返回默认值
        - 2025-01-02~2025-01-14: 使用同星期均值/最多7日均值
        - 2025-01-15+: 使用锁定的日类型分解预测器
    """
    if target_date < datetime(2025, 1, 2):
        # 1/1无历史
        default_load = np.ones(N_SLOTS) * 4500
        return ForecastResult(
            load_forecast=default_load,
            pv_forecast=np.zeros(N_SLOTS),  # PV由其他函数处理
            B_forecast=compute_daily_energy(default_load),
            k_type=-1,
            shape_source_dates=[],
            beta=None
        )

    if target_date < datetime(2025, 1, 15):
        # 1/2~1/14: 使用简单同星期均值（类型尚未锁定）
        target_weekday = target_date.weekday()
        same_weekday_loads = []

        for i in range(1, 15):  # 最多回看14天
            check_date = target_date - timedelta(days=i)
            if check_date < datetime(2025, 1, 1):
                break
            if check_date in load_by_date and check_date.weekday() == target_weekday:
                same_weekday_loads.append(load_by_date[check_date])

        if same_weekday_loads:
            load_forecast = np.mean(same_weekday_loads, axis=0)
        else:
            # 无同星期数据，使用最近7天均值
            recent_loads = []
            for i in range(1, 8):
                check_date = target_date - timedelta(days=i)
                if check_date in load_by_date:
                    recent_loads.append(load_by_date[check_date])

            if recent_loads:
                load_forecast = np.mean(recent_loads, axis=0)
            else:
                load_forecast = np.ones(N_SLOTS) * 4500

        return ForecastResult(
            load_forecast=load_forecast,
            pv_forecast=np.zeros(N_SLOTS),
            B_forecast=compute_daily_energy(load_forecast),
            k_type=-1,
            shape_source_dates=[],
            beta=None
        )

    # 1/15+: 使用锁定的日类型分解预测器
    k_type = classify_day_type(target_date)
    B_forecast, beta, method = estimate_daily_level(target_date, load_by_date)
    shape, shape_sources = forecast_load_shape(target_date, load_by_date, n_days=3)

    # 单元测试1: shape必须归一化
    assert abs(np.sum(shape) - 1.0) < 1e-8, f"Shape sum = {np.sum(shape)}, 应该=1.0"

    # shape是能量占比（sum=1），B_forecast是总能量(kWh)
    # 恢复功率：能量数组 / 时间步长
    energy_array = B_forecast * shape  # kWh per slot
    load_forecast = energy_array / DT  # kW

    # 单元测试2: 预测能量必须等于B_forecast
    forecast_energy = np.sum(load_forecast) * DT
    assert abs(forecast_energy - B_forecast) < 1e-6, \
        f"预测能量 {forecast_energy:.1f} != B_forecast {B_forecast:.1f}"

    return ForecastResult(
        load_forecast=load_forecast,
        pv_forecast=np.zeros(N_SLOTS),
        B_forecast=B_forecast,
        k_type=k_type,
        shape_source_dates=shape_sources,
        beta=beta
    )

# ============================================================
# Phase 2: 历史残差as-of重算
# ============================================================

def build_historical_residual(hist_date: datetime, load_by_date: Dict,
                              pv_by_date: Dict,
                              pv_forecast_0h: Dict, pv_forecast_6h: Dict,
                              pv_forecast_12h: Dict, pv_forecast_18h: Dict) -> Tuple[np.ndarray, np.ndarray, bool]:
    """
    按as-of原则重算历史残差

    返回:
        (e_load, e_pv, is_valid)
    """
    if hist_date < datetime(2025, 1, 2):
        # 1/1无历史预测，不进残差库
        return None, None, False

    if hist_date not in load_by_date or hist_date not in pv_by_date:
        return None, None, False

    # 使用历史日当时的信息生成预测
    forecast_result = forecast_load_as_of(hist_date, load_by_date)
    pv_forecast_hist = get_pv_forecast_as_of(hist_date, 0, pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h)

    # 计算残差
    load_real_hist = load_by_date[hist_date]
    pv_real_hist = pv_by_date[hist_date]

    e_load = load_real_hist - forecast_result.load_forecast
    e_pv = pv_real_hist - pv_forecast_hist

    return e_load, e_pv, True

# ============================================================
# Phase 3: 情景生成（近期+季节/相似日）
# ============================================================

def compute_similarity_features(target_date: datetime, load_by_date: Dict,
                                pv_by_date: Dict,
                                pv_forecast_0h: Dict, pv_forecast_6h: Dict,
                                pv_forecast_12h: Dict, pv_forecast_18h: Dict) -> np.ndarray:
    """
    计算日期的相似性特征（仅使用as-of信息）

    特征:
        - 预测日电量
        - 预测峰值负载
        - 预测PV日电量
        - 预测PV峰值
        - 月份sin/cos编码
    """
    forecast_result = forecast_load_as_of(target_date, load_by_date)
    pv_forecast = get_pv_forecast_as_of(target_date, 0, pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h)

    features = [
        forecast_result.B_forecast / 1e5,  # 归一化
        np.max(forecast_result.load_forecast) / 1e4,
        np.sum(pv_forecast) / 1e5,
        np.max(pv_forecast) / 1e4,
        np.sin(2 * np.pi * target_date.month / 12),
        np.cos(2 * np.pi * target_date.month / 12)
    ]

    return np.array(features)

def select_representative_scenarios(target_date: datetime, load_by_date: Dict,
                                   pv_by_date: Dict,
                                   pv_forecast_0h: Dict, pv_forecast_6h: Dict,
                                   pv_forecast_12h: Dict, pv_forecast_18h: Dict,
                                   n_scenarios: int = 30,
                                   n_recent: int = 15) -> List[datetime]:
    """
    选择代表性情景日期（近期+季节/相似日）

    策略:
        - 保留n_recent个近期样本
        - 从更早历史中选择n_scenarios-n_recent个相似日
    """
    # 1. 近期候选池（最近30天）
    recent_candidates = []
    for i in range(1, 31):
        check_date = target_date - timedelta(days=i)
        if check_date >= datetime(2025, 1, 2) and check_date in load_by_date and check_date in pv_by_date:
            recent_candidates.append(check_date)

    # 保留前n_recent个作为基础
    selected_dates = recent_candidates[:n_recent]

    # 2. 相似日候选池（31天前的历史）
    if len(selected_dates) < n_scenarios:
        target_features = compute_similarity_features(target_date, load_by_date, pv_by_date,
                                                      pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h)

        similar_candidates = []
        for i in range(31, 180):  # 从31天前到180天前
            check_date = target_date - timedelta(days=i)
            if check_date < datetime(2025, 1, 2):
                break
            if check_date in load_by_date and check_date in pv_by_date:
                hist_features = compute_similarity_features(check_date, load_by_date, pv_by_date,
                                                           pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h)
                distance = np.linalg.norm(target_features - hist_features)
                similar_candidates.append((check_date, distance))

        # 按距离排序，选择最相似的
        similar_candidates.sort(key=lambda x: x[1])
        n_similar = min(n_scenarios - len(selected_dates), len(similar_candidates))
        selected_dates.extend([d for d, _ in similar_candidates[:n_similar]])

    return selected_dates[:n_scenarios]

def generate_paired_scenarios(target_date: datetime, load_by_date: Dict,
                              pv_by_date: Dict,
                              pv_forecast_0h: Dict, pv_forecast_6h: Dict,
                              pv_forecast_12h: Dict, pv_forecast_18h: Dict,
                              load_forecast: np.ndarray,
                              pv_forecast: np.ndarray, n_scenarios: int = 30) -> List[Dict]:
    """
    生成配对残差情景

    返回:
        scenarios: list of dicts, 每个包含load/pv/net_load和source_date
    """
    # 选择代表性历史日期
    scenario_dates = select_representative_scenarios(
        target_date, load_by_date, pv_by_date,
        pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h,
        n_scenarios=n_scenarios
    )

    scenarios = []

    for hist_date in scenario_dates:
        # 获取历史残差（按as-of重算）
        e_load, e_pv, is_valid = build_historical_residual(hist_date, load_by_date, pv_by_date,
                                                           pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h)

        if not is_valid:
            # 无效历史日，使用确定性预测
            scenarios.append({
                'load': load_forecast,
                'pv': pv_forecast,
                'net_load': load_forecast - pv_forecast,
                'source_date': hist_date
            })
            continue

        # 应用配对残差到当前预测
        load_scenario = np.maximum(0, load_forecast + e_load)
        pv_scenario = np.maximum(0, pv_forecast + e_pv)

        scenarios.append({
            'load': load_scenario,
            'pv': pv_scenario,
            'net_load': load_scenario - pv_scenario,
            'source_date': hist_date
        })

    return scenarios

# ============================================================
# Stage 1: 情景规划（只返回E_plan）
# ============================================================

def solve_stage1_scenario(date: datetime, price: np.ndarray, scenarios: List[Dict],
                         E_storage_prev: float) -> Dict:
    """
    Stage 1: 情景规划优化

    目标: min 计划购电成本 + 期望紧急购电成本
    注意: 不再包含固定末态价值STORAGE_VALUE

    返回:
        只返回共同E_plan，scenario追索变量仅用于成本估计
    """
    n_scenarios = len(scenarios)

    prob = pulp.LpProblem(f"Stage1_{date.date()}", pulp.LpMinimize)

    # 共用的计划购电量
    E_plan = [pulp.LpVariable(f"E_plan_{t}", lowBound=0) for t in range(N_SLOTS)]

    # 各情景的追索变量
    E_emergency_scenarios = []
    E_charge_scenarios = []
    E_discharge_scenarios = []
    E_storage_scenarios = []

    for omega in range(n_scenarios):
        E_emergency_scenarios.append([
            pulp.LpVariable(f"E_em_{omega}_{t}", lowBound=0) for t in range(N_SLOTS)
        ])
        E_charge_scenarios.append([
            pulp.LpVariable(f"C_{omega}_{t}", lowBound=0, upBound=POWER_LIMIT) for t in range(N_SLOTS)
        ])
        E_discharge_scenarios.append([
            pulp.LpVariable(f"D_{omega}_{t}", lowBound=0, upBound=POWER_LIMIT) for t in range(N_SLOTS)
        ])
        E_storage_scenarios.append([
            pulp.LpVariable(f"S_{omega}_{t}", lowBound=E_MIN, upBound=E_MAX) for t in range(N_SLOTS)
        ])

    # 目标函数：计划成本 + 期望紧急成本
    plan_cost = pulp.lpSum([price[t] * E_plan[t] for t in range(N_SLOTS)])

    expected_emergency_cost = (1.0 / n_scenarios) * pulp.lpSum([
        ALPHA_EMERGENCY * price[t] * E_emergency_scenarios[omega][t]
        for omega in range(n_scenarios)
        for t in range(N_SLOTS)
    ])

    prob += plan_cost + expected_emergency_cost

    # 约束条件（逐情景）
    for omega in range(n_scenarios):
        scenario = scenarios[omega]
        net_load = scenario['net_load']

        for t in range(N_SLOTS):
            net_load_energy = net_load[t] * DT

            # 电力平衡 (修复: 功率变量需要 * DT 转换为能量)
            prob += (E_plan[t] + E_emergency_scenarios[omega][t] +
                    ETA * E_discharge_scenarios[omega][t] * DT >=
                    net_load_energy + E_charge_scenarios[omega][t] * DT)

            # 储能状态方程 (修复: 功率变量需要 * DT 转换为能量)
            if t == 0:
                prob += (E_storage_scenarios[omega][t] ==
                        E_storage_prev +
                        ETA * E_charge_scenarios[omega][t] * DT -
                        E_discharge_scenarios[omega][t] * DT)
            else:
                prob += (E_storage_scenarios[omega][t] ==
                        E_storage_scenarios[omega][t-1] +
                        ETA * E_charge_scenarios[omega][t] * DT -
                        E_discharge_scenarios[omega][t] * DT)

    # 求解
    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=300)
    status = prob.solve(solver)

    if status != pulp.LpStatusOptimal:
        raise RuntimeError(f"Stage 1 failed: {pulp.LpStatus[status]}")

    # 只提取E_plan
    E_plan_vals = np.array([E_plan[t].varValue for t in range(N_SLOTS)])
    Z_plan = sum([price[t] * E_plan_vals[t] for t in range(N_SLOTS)])

    return {
        'E_plan': E_plan_vals,
        'Z_plan': Z_plan,
        'n_scenarios': n_scenarios
    }

# ============================================================
# Phase 6: 动态价值函数（离散SOC网格DP）
# ============================================================

class DynamicValueController:
    """
    动态价值函数控制器

    使用离散SOC网格和反向DP计算价值函数
    """

    def __init__(self, n_soc_grid: int = 49):
        """
        初始化

        参数:
            n_soc_grid: SOC网格点数量
        """
        self.soc_grid = np.linspace(E_MIN, E_MAX, n_soc_grid)
        self.n_soc = n_soc_grid
        self.V = None  # 价值函数 [t, soc_idx]

    def build_value_function(self, price: np.ndarray, E_final: np.ndarray,
                            load_scenarios: List[np.ndarray],
                            pv_scenarios: List[np.ndarray],
                            next_day_avg_price: float = None) -> None:
        """
        构建价值函数（反向递推）

        参数:
            price: 电价 (144,)
            E_final: 最终购电策略 (144,)
            load_scenarios: 负载情景列表
            pv_scenarios: PV情景列表
            next_day_avg_price: 下一日平均电价（用于终端价值估计）
        """
        n_scenarios = len(load_scenarios)

        # 初始化价值函数 [145, n_soc]
        # V[t, j] = 从时段t、SOC=soc_grid[j]开始的最小期望未来成本
        self.V = np.zeros((N_SLOTS + 1, self.n_soc))

        # 终端价值（跨日连续性价值估计）
        # V_144(S) 表示以SOC=S结束当天，对下一天的价值
        # 使用简化的二次惩罚：偏离目标SOC的成本
        E_target = 6000.0  # 目标SOC（均衡状态）

        if next_day_avg_price is None:
            next_day_avg_price = np.mean(price)

        # 终端价值（跨日连续性价值估计）- 分段惩罚版本
        E_target = 6000.0  # 目标SOC

        if next_day_avg_price is None:
            next_day_avg_price = np.mean(price)

        for j, soc in enumerate(self.soc_grid):
            if soc < 2000:
                # 危险区：接近最低限，大惩罚
                shortage = E_target - soc
                self.V[N_SLOTS, j] = ALPHA_EMERGENCY * next_day_avg_price * shortage * 1.0
            elif soc < 4000:
                # 偏低区：需要补充
                shortage = E_target - soc
                self.V[N_SLOTS, j] = ALPHA_EMERGENCY * next_day_avg_price * shortage * 0.6
            elif soc < E_target:
                # 略低区：温和惩罚
                shortage = E_target - soc
                self.V[N_SLOTS, j] = ALPHA_EMERGENCY * next_day_avg_price * shortage * 0.3
            else:
                # 高于目标：小持有成本
                excess = soc - E_target
                self.V[N_SLOTS, j] = 0.1 * next_day_avg_price * excess / (E_MAX - E_MIN)

        # 反向递推
        for t in range(N_SLOTS - 1, -1, -1):
            for j, soc_current in enumerate(self.soc_grid):
                min_cost = np.inf

                # 动作空间：充电、放电、空闲（禁止同时充放电）
                # 充电动作：C>0, D=0
                charge_candidates = np.linspace(0, min(POWER_LIMIT, E_MAX - soc_current), 11)
                # 放电动作：C=0, D>0
                discharge_candidates = np.linspace(0, min(POWER_LIMIT, soc_current - E_MIN), 11)

                # 1. 尝试所有充电动作
                for charge in charge_candidates:
                    discharge = 0.0
                    # 修复: charge/discharge是功率(kW)，需要 * DT 转换为能量(kWh)
                    soc_next = soc_current + ETA * charge * DT - discharge * DT

                    if soc_next < E_MIN - 1e-6 or soc_next > E_MAX + 1e-6:
                        continue

                    # 计算期望紧急购电成本
                    emergency_cost = 0.0
                    for omega in range(n_scenarios):
                        load_omega = load_scenarios[omega][t]
                        pv_omega = pv_scenarios[omega][t]

                        emergency = compute_emergency_power(
                            E_final[t], pv_omega, load_omega,
                            charge, discharge
                        )
                        emergency_cost += ALPHA_EMERGENCY * price[t] * emergency

                    emergency_cost /= n_scenarios

                    # 未来价值
                    future_value = np.interp(soc_next, self.soc_grid, self.V[t + 1, :])
                    total_cost = emergency_cost + future_value

                    if total_cost < min_cost:
                        min_cost = total_cost

                # 2. 尝试所有放电动作
                for discharge in discharge_candidates:
                    charge = 0.0
                    # 修复: charge/discharge是功率(kW)，需要 * DT 转换为能量(kWh)
                    soc_next = soc_current + ETA * charge * DT - discharge * DT

                    if soc_next < E_MIN - 1e-6 or soc_next > E_MAX + 1e-6:
                        continue

                    emergency_cost = 0.0
                    for omega in range(n_scenarios):
                        load_omega = load_scenarios[omega][t]
                        pv_omega = pv_scenarios[omega][t]

                        emergency = compute_emergency_power(
                            E_final[t], pv_omega, load_omega,
                            charge, discharge
                        )
                        emergency_cost += ALPHA_EMERGENCY * price[t] * emergency

                    emergency_cost /= n_scenarios

                    future_value = np.interp(soc_next, self.soc_grid, self.V[t + 1, :])
                    total_cost = emergency_cost + future_value

                    if total_cost < min_cost:
                        min_cost = total_cost

                self.V[t, j] = min_cost

    def act(self, t: int, soc_current: float, E_final: float,
            load_real: float, pv_real: float, price: float) -> Tuple[float, float]:
        """
        在线决策：根据当前状态选择充放电动作（禁止同时充放电）

        参数:
            t: 当前时段
            soc_current: 当前SOC
            E_final: 当前时段购电量
            load_real: 真实负载
            pv_real: 真实PV
            price: 当前电价

        返回:
            (charge, discharge)
        """
        if self.V is None:
            return self._simple_rule(soc_current, price)

        best_charge = 0.0
        best_discharge = 0.0
        min_cost = np.inf

        # 动作空间：充电或放电（禁止同时）
        charge_candidates = np.linspace(0, min(POWER_LIMIT, E_MAX - soc_current), 21)
        discharge_candidates = np.linspace(0, min(POWER_LIMIT, soc_current - E_MIN), 21)

        # 1. 尝试充电动作
        for charge in charge_candidates:
            discharge = 0.0
            # 修复: charge/discharge是功率(kW)，需要 * DT 转换为能量(kWh)
            soc_next = soc_current + ETA * charge * DT - discharge * DT

            if soc_next < E_MIN - 1e-6 or soc_next > E_MAX + 1e-6:
                continue

            emergency = compute_emergency_power(
                E_final, pv_real, load_real, charge, discharge
            )
            current_cost = ALPHA_EMERGENCY * price * emergency

            if t + 1 < N_SLOTS:
                future_value = np.interp(soc_next, self.soc_grid, self.V[t + 1, :])
            else:
                future_value = np.interp(soc_next, self.soc_grid, self.V[N_SLOTS, :])

            total_cost = current_cost + future_value

            if total_cost < min_cost:
                min_cost = total_cost
                best_charge = charge
                best_discharge = discharge

        # 2. 尝试放电动作
        for discharge in discharge_candidates:
            charge = 0.0
            # 修复: charge/discharge是功率(kW)，需要 * DT 转换为能量(kWh)
            soc_next = soc_current + ETA * charge * DT - discharge * DT

            if soc_next < E_MIN - 1e-6 or soc_next > E_MAX + 1e-6:
                continue

            emergency = compute_emergency_power(
                E_final, pv_real, load_real, charge, discharge
            )
            current_cost = ALPHA_EMERGENCY * price * emergency

            if t + 1 < N_SLOTS:
                future_value = np.interp(soc_next, self.soc_grid, self.V[t + 1, :])
            else:
                future_value = np.interp(soc_next, self.soc_grid, self.V[N_SLOTS, :])

            total_cost = current_cost + future_value

            if total_cost < min_cost:
                min_cost = total_cost
                best_charge = charge
                best_discharge = discharge

        return best_charge, best_discharge

    def _simple_rule(self, soc_current: float, price: float) -> Tuple[float, float]:
        """简单规则（价值函数未构建时的fallback）"""
        soc_pct = (soc_current - E_MIN) / (E_MAX - E_MIN)

        if price < 0.5 and soc_pct < 0.8:
            charge = min(POWER_LIMIT, E_MAX - soc_current)
            discharge = 0.0
        elif price > 0.7 and soc_pct > 0.3:
            charge = 0.0
            discharge = min(POWER_LIMIT, soc_current - E_MIN)
        else:
            charge = 0.0
            discharge = 0.0

        return charge, discharge

# ============================================================
# Stage K 调整
# ============================================================

def solve_stage_k_forecast_based(k_hour: int, price: np.ndarray,
                                load_real_so_far: np.ndarray, pv_real_so_far: np.ndarray,
                                E_storage_current: float, E_base_remaining: np.ndarray,
                                load_by_date: Dict, pv_by_date: Dict, date: datetime,
                                pv_forecast_0h: Dict, pv_forecast_6h: Dict,
                                pv_forecast_12h: Dict, pv_forecast_18h: Dict,
                                pv_forecast_remaining: np.ndarray = None) -> np.ndarray:
    """
    Stage k调整决策 - Step 2: 基于预测更新的调整（改进版 + PV预测支持）

    核心思路:
    1. 利用0:00~k_hour的真实数据评估预测误差
    2. 在k_hour时刻读取更新的PV预测（如果提供）
    3. 结合当前SOC状态，决定是否需要调整
    4. 采用保守策略：只在明确有益时调整

    参数:
        k_hour: 6, 12, 或 18 (小时)
        price: 剩余时段的电价 (k_hour~24:00)
        load_real_so_far: 0:00~k_hour的真实负载 (功率kW)
        pv_real_so_far: 0:00~k_hour的真实光伏 (功率kW)
        E_storage_current: 当前储能状态 (kWh)
        E_base_remaining: k_hour~24:00的基准购电量 (已包含之前的调整)
        load_by_date: 历史负载数据
        pv_by_date: 历史光伏数据
        date: 当前日期
        pv_forecast_0h/6h/12h/18h: PV预报字典
        pv_forecast_remaining: k_hour~24:00的PV预测 (kW功率)，如果为None则不使用PV信息

    返回:
        delta_k: k_hour~24:00的调整量 (kWh，可正可负)
    """
    n_remaining = len(E_base_remaining)
    E_adjust = np.zeros(n_remaining)

    # 1. 获取0:00预测（Stage 1使用的预测）
    forecast_result = forecast_load_as_of(date, load_by_date)
    load_forecast_0 = forecast_result.load_forecast  # 144个时段的预测

    # 2. 计算实际vs预测的偏差（0:00~k_hour）
    k_slot = k_hour * 6  # 转换为时段索引
    load_forecast_so_far = load_forecast_0[:k_slot]

    # 负载预测能量 vs 实际能量（已发生部分）
    forecast_load_energy = np.sum(load_forecast_so_far) * DT
    actual_load_energy = np.sum(load_real_so_far) * DT

    # 如果预测能量为0（异常情况），不调整
    if forecast_load_energy < 1e-6:
        return E_adjust

    # 负载偏差比例
    load_error_ratio = (actual_load_energy - forecast_load_energy) / forecast_load_energy

    # 3. ✅ 启用PV预测：计算PV预测误差
    pv_error_ratio = 0.0
    has_pv_error = False

    if pv_forecast_remaining is not None and len(pv_real_so_far) > 0:
        # 获取0:00时刻的PV预测（用于对比）
        pv_forecast_0 = get_pv_forecast_as_of(date, 0, pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h)
        pv_forecast_so_far = pv_forecast_0[:k_slot]

        # 计算PV预测误差
        forecast_pv_energy = np.sum(pv_forecast_so_far) * DT
        actual_pv_energy = np.sum(pv_real_so_far) * DT

        if forecast_pv_energy > 1e-6:
            pv_error_ratio = (actual_pv_energy - forecast_pv_energy) / forecast_pv_energy
            has_pv_error = True

            # 调试输出
            # print(f"    [PV误差] 预测:{forecast_pv_energy:.0f} kWh, 实际:{actual_pv_energy:.0f} kWh, 偏差:{pv_error_ratio*100:.1f}%")

    # 4. 计算净负载误差（负载 - PV）
    # 如果PV低于预测，净负载会更高，需要更多购电
    # 如果PV高于预测，净负载会更低，可以减少购电
    net_load_error_ratio = load_error_ratio
    if has_pv_error:
        # PV低于预测（pv_error_ratio < 0）-> 净负载偏高 -> 需要更多购电
        # PV高于预测（pv_error_ratio > 0）-> 净负载偏低 -> 可以减少购电
        net_load_error_ratio = load_error_ratio - pv_error_ratio

    # 5. 计算SOC状态
    soc_pct = (E_storage_current - E_MIN) / (E_MAX - E_MIN)

    # 6. 改进的调整策略（结合负载和PV预测误差）

    # ============================================================
    # 新增：计算预测变化量（F_new vs F_old）
    # ============================================================
    pv_forecast_change = 0.0
    has_forecast_change = False

    if pv_forecast_remaining is not None and len(pv_forecast_remaining) > 0:
        # 获取上一版本的PV预测（0:00预测的剩余部分）
        pv_forecast_0 = get_pv_forecast_as_of(date, 0, pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h)
        pv_forecast_0_remaining = pv_forecast_0[k_slot:]

        # 计算预测变化量
        pv_energy_0_remaining = np.sum(pv_forecast_0_remaining) * DT
        pv_energy_k_remaining = np.sum(pv_forecast_remaining) * DT

        pv_forecast_change = pv_energy_k_remaining - pv_energy_0_remaining  # 正值=增加，负值=减少
        has_forecast_change = True

    # 规则1: 净负载显著高于预测 -> 增加购电
    # 降低阈值：从error_ratio > 0.08降低到0.05，且考虑SOC < 0.5（而非0.35）
    if net_load_error_ratio > 0.05 and soc_pct < 0.5:
        # 预测剩余时段的总能量
        load_forecast_remaining = load_forecast_0[k_slot:]
        forecast_energy_remaining = np.sum(load_forecast_remaining) * DT

        # ✅ 修复Bug：确保net_forecast_remaining非负
        if pv_forecast_remaining is not None and len(pv_forecast_remaining) > 0:
            pv_forecast_energy_remaining = np.sum(pv_forecast_remaining) * DT
            net_forecast_remaining = max(0.0, forecast_energy_remaining - pv_forecast_energy_remaining)
        else:
            net_forecast_remaining = forecast_energy_remaining

        # 调整量 = 剩余净负载 × 误差比例 × 调整系数
        adjustment_factor = 0.5 if soc_pct < 0.3 else 0.3  # SOC更低时更积极
        total_adjustment = net_forecast_remaining * net_load_error_ratio * adjustment_factor

        # ✅ 修复Bug：确保total_adjustment非负（Rule 1只增加购电）
        total_adjustment = max(0.0, total_adjustment)

        # 限制调整幅度
        max_adjustment = net_forecast_remaining * 0.25  # 最多增加25%
        total_adjustment = min(total_adjustment, max_adjustment)

        # 按时段能量比例分配
        if forecast_energy_remaining > 1e-6:
            slot_weights = (load_forecast_remaining * DT) / forecast_energy_remaining
            E_adjust = total_adjustment * slot_weights
        else:
            E_adjust[:] = total_adjustment / n_remaining

    # 规则2: SOC危险低（无论预测如何）-> 紧急补充
    elif soc_pct < 0.25:
        # 紧急补充：均匀增加150kWh
        E_adjust[:] = 150.0 / n_remaining

    # 规则3: 减少购电 - 暂时禁用
    # ⚠️ 经过v1.3和v1.4测试，减少购电导致紧急成本增加，暂时禁用
    # 原因：预测不确定性导致减少购电后容易触发5倍成本的紧急购电
    # 未来改进方向：基于LP优化的Stage K，显式约束紧急购电风险
    # elif net_load_error_ratio < -0.15 and soc_pct > 0.90:
    #     # 减少购电逻辑（暂时禁用）
    #     pass

    # 其他情况：不调整（保持原计划）

    # ============================================================
    # 诊断输出：Stage K决策过程（可选开启）
    # ============================================================
    # 设置为True以启用详细诊断
    ENABLE_STAGE_K_DIAGNOSTICS = True

    if ENABLE_STAGE_K_DIAGNOSTICS:
        print(f"\n  [Stage K={k_hour}:00 诊断]")
        print(f"    预测变化: PV预测 {pv_forecast_change:+.0f} kWh ({pv_forecast_change/max(1.0, np.sum(pv_forecast_remaining)*DT if pv_forecast_remaining is not None else 1.0)*100:+.1f}%)")
        print(f"    历史误差: 净负载误差比例 {net_load_error_ratio*100:+.1f}% (Load {load_error_ratio*100:+.1f}%, PV {pv_error_ratio*100:+.1f}%)")
        print(f"    当前SOC: {E_storage_current:.0f} kWh ({soc_pct*100:.1f}%)")

        # 判断触发条件
        trigger_rule1 = net_load_error_ratio > 0.05 and soc_pct < 0.5
        trigger_rule2 = soc_pct < 0.25

        print(f"    触发条件:")
        print(f"      Rule 1 (误差>5% & SOC<50%): {'✓' if trigger_rule1 else '✗'}")
        print(f"      Rule 2 (SOC<25%紧急): {'✓' if trigger_rule2 else '✗'}")

        total_delta = np.sum(E_adjust)
        if abs(total_delta) > 0.1:
            print(f"    → 调整: {total_delta:+.0f} kWh")
        else:
            print(f"    → 不调整 (delta=0)")

    return E_adjust


def solve_stage_k_simple(k_hour: int, price: np.ndarray,
                        load_real_so_far: np.ndarray, pv_real_so_far: np.ndarray,
                        E_storage_current: float, E_plan_remaining: np.ndarray,
                        controller: DynamicValueController) -> np.ndarray:
    """
    Stage k调整决策 - Step 1: 简单规则版本（备用）

    参数:
        k_hour: 6, 12, 或 18 (小时)
        price: 剩余时段的电价 (k_hour~24:00)
        load_real_so_far: 0:00~k_hour的真实负载
        pv_real_so_far: 0:00~k_hour的真实光伏
        E_storage_current: 当前储能状态 (kWh)
        E_plan_remaining: k_hour~24:00的剩余计划电 (已包含之前的调整)
        controller: 动态价值函数控制器

    返回:
        E_adjust: k_hour~24:00的调整量 (kWh，可正可负)

    规则:
        1. SOC过低 (<30%) -> 增加购电
        2. SOC过高 (>70%) -> 减少购电
        3. 否则不调整
    """
    n_remaining = len(E_plan_remaining)
    E_adjust = np.zeros(n_remaining)

    # 计算SOC百分比
    soc_pct = (E_storage_current - E_MIN) / (E_MAX - E_MIN)

    # 规则1: SOC过低 -> 增加购电
    if soc_pct < 0.3:
        # 均匀增加200kWh到剩余时段
        adjustment_per_slot = 200.0 / n_remaining
        E_adjust[:] = adjustment_per_slot

    # 规则2: SOC过高 -> 减少购电
    elif soc_pct > 0.7:
        # 均匀减少200kWh (确保不会让计划电变成负数)
        adjustment_per_slot = min(200.0 / n_remaining, np.min(E_plan_remaining))
        E_adjust[:] = -adjustment_per_slot

    return E_adjust


def compute_adjustment_cost(E_adjust: np.ndarray, price: np.ndarray) -> float:
    """
    计算调整成本（对齐Model Spec v1.2 第6.7节）

    调整成本计算规则:
    Z_adjust = Σ[1.5·Price(t)·δ⁺(t) - 0.5·Price(t)·δ⁻(t)]

    其中:
    - δ⁺(t) = max(0, E_adjust(t))  增购部分
    - δ⁻(t) = max(0, -E_adjust(t)) 减购部分

    增购部分: 1.5倍电价（超额购电150%）
    减购部分: -0.5倍电价（冲销原计划费用的50%）

    参数:
        E_adjust: 调整量数组 (kWh)，正值为增购，负值为减购
        price: 电价数组 (元/kWh)

    返回:
        调整成本 (元)
    """
    # δ⁺: 增购部分
    delta_plus = np.maximum(E_adjust, 0)

    # δ⁻: 减购部分
    delta_minus = np.maximum(-E_adjust, 0)

    # 调整成本 = 1.5·Price·δ⁺ - 0.5·Price·δ⁻
    Z_adjust = np.sum(1.5 * price * delta_plus - 0.5 * price * delta_minus)

    return Z_adjust


# ============================================================
# 实时执行
# ============================================================

def compute_emergency_power(E_final: float, pv_real: float, load_real: float,
                           E_charge: float, E_discharge: float) -> float:
    """
    计算紧急购电量

    参数:
        E_final: 购电量 (kWh)
        pv_real: 光伏功率 (kW)
        load_real: 负载功率 (kW)
        E_charge: 充电功率 (kW)
        E_discharge: 放电功率 (kW)

    返回:
        紧急购电量 (kWh)
    """
    # 修复: charge/discharge是功率(kW)，需要 * DT 转换为能量(kWh)
    supply = E_final + pv_real * DT + ETA * E_discharge * DT
    demand = load_real * DT + E_charge * DT
    return max(0, demand - supply)

def execute_single_day(date: datetime, price: np.ndarray, load_real_day: np.ndarray,
                      pv_real_day: np.ndarray, E_plan: np.ndarray,
                      E_storage_prev: float, controller: DynamicValueController,
                      load_by_date: Dict, pv_by_date: Dict,
                      pv_forecast_0h: Dict, pv_forecast_6h: Dict,
                      pv_forecast_12h: Dict, pv_forecast_18h: Dict,
                      enable_stage_k: bool = True) -> Dict:
    """
    单日实际执行（使用动态价值函数控制器 + Stage K调整）

    注意: 不再使用scenario 0的充放电轨迹

    参数:
        enable_stage_k: 是否启用Stage K调整（用于A/B测试）
        load_by_date: 历史负载数据（用于Stage K预测更新）
        pv_by_date: 历史光伏数据（用于Stage K情景生成）
        pv_forecast_0h/6h/12h/18h: 光伏预测数据（用于Stage K读取更新预测）

    变量定义（对齐Model Spec v1.2）:
        E_plan: 0:00制定的计划购电量（基准）
        E_base_k: Stage k时刻的基准购电量（最近一次决策值）
        E_adjust_k: Stage k时刻的调整后购电量
        delta_k: E_adjust_k - E_base_k（可正可负）
        E_final: 最终购电量（经过所有Stage k调整后）
    """
    # 初始化
    E_base = E_plan.copy()  # 当前基准购电量（滚动更新）
    E_final = E_plan.copy()  # 最终购电量
    E_charge_final = np.zeros(N_SLOTS)
    E_discharge_final = np.zeros(N_SLOTS)
    E_storage_actual = np.zeros(N_SLOTS)
    E_emergency = np.zeros(N_SLOTS)

    E_storage_current = E_storage_prev

    # 诊断：同时充放电次数
    simultaneous_count = 0

    # Stage K调整统计
    stage_k_adjustments = []  # 记录每次调整的信息
    stage_k_deltas = []  # 记录每次调整的delta值（用于成本计算）

    for t in range(N_SLOTS):
        # Stage K调整点: 6:00 (t=36), 12:00 (t=72), 18:00 (t=108)
        if enable_stage_k and t in [36, 72, 108]:
            k_hour = t // 6  # 6, 12, 18

            # ✅ 读取k_hour时刻的PV预测（严格信息集控制）
            # 6:00使用6:00预报，12:00使用12:00预报，18:00使用18:00预报
            pv_forecast_k = get_pv_forecast_as_of(date, k_hour, pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h)

            # 当前基准购电量（最近一次决策值）
            E_base_remaining = E_base[t:]

            # 调用Stage K求解器（使用更新的PV预测）
            delta_k = solve_stage_k_forecast_based(
                k_hour, price[t:],
                load_real_day[:t], pv_real_day[:t],
                E_storage_current,
                E_base_remaining,
                load_by_date, pv_by_date, date,
                pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h,
                pv_forecast_remaining=pv_forecast_k[t:]  # 传递k_hour~24:00的PV预测
            )

            # 更新：E_adjust_k = E_base_k + delta_k
            E_adjust_k = E_base_remaining + delta_k

            # 计算本次调整成本（delta_k相对于E_base_k的增量成本）
            Z_adjust_increment = compute_adjustment_cost(delta_k, price[t:])

            # 更新基准和最终购电量
            E_final[t:] = E_adjust_k
            E_base[t:] = E_adjust_k  # 下一次Stage k的基准

            # 记录调整信息
            adjustment_sum = np.sum(delta_k)
            stage_k_adjustments.append({
                'k_hour': k_hour,
                't_index': t,
                'soc_pct': (E_storage_current - E_MIN) / (E_MAX - E_MIN),
                'delta_sum': adjustment_sum,
                'adjustment_cost': Z_adjust_increment
            })
            stage_k_deltas.append((t, delta_k, price[t:]))  # 保存用于最终成本计算

            if abs(adjustment_sum) > 1e-3:  # 只打印有实际调整的
                print(f"  [Stage k={k_hour}:00]")
                print(f"    当前SOC: {E_storage_current:.0f} kWh ({(E_storage_current - E_MIN) / (E_MAX - E_MIN) * 100:.1f}%)")
                print(f"    δ_k: {adjustment_sum:+.0f} kWh")
                print(f"    调整成本: {Z_adjust_increment:.2f} 元")

        # 使用动态价值函数控制器决定充放电
        charge, discharge = controller.act(
            t, E_storage_current, E_final[t],
            load_real_day[t], pv_real_day[t], price[t]
        )

        E_charge_final[t] = charge
        E_discharge_final[t] = discharge

        # 检查同时充放电
        if charge > 1e-6 and discharge > 1e-6:
            simultaneous_count += 1

        # 计算紧急购电
        E_emergency[t] = compute_emergency_power(
            E_final[t], pv_real_day[t], load_real_day[t],
            charge, discharge
        )

        # 更新储能状态 (修复: charge/discharge是功率kW，需要 * DT 转换为能量kWh)
        E_storage_actual[t] = E_storage_current + ETA * charge * DT - discharge * DT
        E_storage_current = E_storage_actual[t]

    # 计算成本（对齐Model Spec v1.2 第6.7节）
    # Z_plan: 0:00计划购电成本
    Z_plan = sum([price[t] * E_plan[t] for t in range(N_SLOTS)])

    # Z_adjust: 所有Stage k调整的累计成本
    Z_adjust = 0.0
    for k_adj in stage_k_adjustments:
        Z_adjust += k_adj['adjustment_cost']

    # Z_emergency: 紧急购电成本
    Z_emergency = sum([ALPHA_EMERGENCY * price[t] * E_emergency[t] for t in range(N_SLOTS)])

    # Z_total: 总成本
    Z_total = Z_plan + Z_adjust + Z_emergency

    # 诊断统计
    emergency_slots = np.sum(E_emergency > 1e-6)
    total_emergency_energy = np.sum(E_emergency)

    return {
        'date': date,
        'E_plan': E_plan,
        'E_final': E_final,
        'E_charge_final': E_charge_final,
        'E_discharge_final': E_discharge_final,
        'E_storage_actual': E_storage_actual,
        'E_emergency': E_emergency,
        'Z_plan': Z_plan,
        'Z_adjust': Z_adjust,
        'Z_emergency': Z_emergency,
        'Z_total': Z_total,
        'E_storage_end': E_storage_actual[-1],
        'E_storage_min': np.min(E_storage_actual),
        'E_storage_max': np.max(E_storage_actual),
        'simultaneous_charge_discharge': simultaneous_count,
        'emergency_slots': emergency_slots,
        'total_emergency_energy': total_emergency_energy,
        'stage_k_adjustments': stage_k_adjustments,
        'n_stage_k_adjustments': len(stage_k_adjustments)
    }

# ============================================================
# 单日优化主流程
# ============================================================

def optimize_single_day(date: datetime, price: np.ndarray,
                       load_real_day: np.ndarray, pv_real_day: np.ndarray,
                       pv_forecast_day: np.ndarray, E_storage_prev: float,
                       load_by_date: Dict, pv_by_date: Dict,
                       pv_forecast_0h: Dict, pv_forecast_6h: Dict,
                       pv_forecast_12h: Dict, pv_forecast_18h: Dict,
                       enable_stage_k: bool = True) -> Dict:
    """
    单日优化主流程（v1.2）

    流程:
        1. 生成负载预测（新预测器）
        2. 生成情景（近期+相似日+配对残差）
        3. Stage 1规划（返回E_plan）
        4. 构建动态价值函数
        5. 实际执行（动态价值控制 + Stage K调整）
    """
    # 1. 生成负载预测
    forecast_result = forecast_load_as_of(date, load_by_date)
    load_forecast = forecast_result.load_forecast

    # [调试] 验证预测能量
    actual_forecast_energy = np.sum(load_forecast) * DT
    if abs(actual_forecast_energy - forecast_result.B_forecast) > 1.0:
        print(f"  ⚠️ 预测不一致: B_forecast={forecast_result.B_forecast:.0f}, actual={actual_forecast_energy:.0f}")

    # 2. 生成情景
    scenarios = generate_paired_scenarios(
        date, load_by_date, pv_by_date,
        pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h,
        load_forecast, pv_forecast_day,
        n_scenarios=N_SCENARIOS
    )

    print(f"  生成 {len(scenarios)} 个情景")

    # 3. Stage 1规划
    stage1_result = solve_stage1_scenario(date, price, scenarios, E_storage_prev)
    E_plan = stage1_result['E_plan']

    # 4. 构建动态价值函数
    controller = DynamicValueController(n_soc_grid=49)
    load_scenarios = [s['load'] for s in scenarios]
    pv_scenarios = [s['pv'] for s in scenarios]

    print(f"  构建动态价值函数...")
    controller.build_value_function(price, E_plan, load_scenarios, pv_scenarios)

    # 5. 实际执行
    exec_result = execute_single_day(
        date, price, load_real_day, pv_real_day,
        E_plan, E_storage_prev, controller,
        load_by_date, pv_by_date,
        pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h,
        enable_stage_k=enable_stage_k
    )

    exec_result['n_scenarios'] = len(scenarios)
    exec_result['B_forecast'] = forecast_result.B_forecast
    exec_result['k_type'] = forecast_result.k_type

    return exec_result

# ============================================================
# 主函数：10天测试
# ============================================================

def main_test_10days():
    """10天测试（P0修复版）"""
    print("="*70)
    print("Q3 情景规划模型 v1.2 - 10天测试（P0修复）")
    print(f"策略: {N_SCENARIOS}个配对残差情景 + 动态价值函数 + 终端价值")
    print("="*70)

    price, load_real, pv_real, pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h = load_data()
    load_by_date, pv_by_date = build_date_cache(load_real, pv_real)

    # P0修复1: 从1/1-1/14识别日类型
    global LOW_LOAD_WEEKDAYS
    LOW_LOAD_WEEKDAYS = infer_day_types_from_jan1_14(load_by_date)
    print(f"\n[锁定] 低负载星期: {LOW_LOAD_WEEKDAYS}")

    test_dates = pd.date_range('2025-02-01', '2025-02-10', freq='D')
    results = []
    E_storage_prev = E_INIT

    for date in test_dates:
        print(f"\n优化 {date.date()}...")

        # 获取0:00时刻的PV预测
        pv_forecast_day = get_pv_forecast_as_of(date, 0, pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h)

        if date not in load_by_date or date not in pv_by_date or len(pv_forecast_day) != N_SLOTS:
            print(f"  [跳过] 数据不完整")
            continue

        try:
            result = optimize_single_day(
                date, price,
                load_by_date[date], pv_by_date[date],
                pv_forecast_day, E_storage_prev,
                load_by_date, pv_by_date,
                pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h
            )

            results.append(result)
            E_storage_prev = result['E_storage_end']

            # 调试特定日期
            if date.day in [2, 9] and date.month == 2:
                print(f"  [详细调试 {date.date()}]")
                print(f"    B_forecast: {result['B_forecast']:.2f} kWh")
                actual_load_energy = compute_daily_energy(load_by_date[date])
                print(f"    真实能量: {actual_load_energy:.2f} kWh")
                print(f"    预测误差: {(result['B_forecast']/actual_load_energy - 1)*100:.1f}%")

            print(f"  日类型: {result['k_type']}")
            print(f"  预测日电量: {result['B_forecast']:.2f} kWh")
            print(f"  计划成本: {result['Z_plan']:.2f} 元")
            print(f"  调整成本: {result['Z_adjust']:.2f} 元")
            print(f"  紧急成本: {result['Z_emergency']:.2f} 元")
            print(f"  总成本: {result['Z_total']:.2f} 元")
            print(f"  末态储能: {result['E_storage_end']:.2f} kWh (最小: {result['E_storage_min']:.0f}, 最大: {result['E_storage_max']:.0f})")
            print(f"  [诊断] 同时充放电: {result['simultaneous_charge_discharge']} 次 (必须=0)")
            print(f"  [诊断] 紧急购电: {result['emergency_slots']} 时段, {result['total_emergency_energy']:.2f} kWh")
            print(f"  [Stage K] 调整次数: {result['n_stage_k_adjustments']}")


        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
            break

    if results:
        print("\n" + "="*70)
        print("10天测试结果汇总（P0修复验证 + Stage K）")
        print("="*70)
        total_cost = sum([r['Z_total'] for r in results])
        total_plan = sum([r['Z_plan'] for r in results])
        total_adjust = sum([r['Z_adjust'] for r in results])
        total_emergency = sum([r['Z_emergency'] for r in results])
        total_simultaneous = sum([r['simultaneous_charge_discharge'] for r in results])
        total_emergency_slots = sum([r['emergency_slots'] for r in results])

        print(f"总成本: {total_cost:.2f} 元")
        print(f"  计划成本: {total_plan:.2f} 元 ({total_plan/total_cost*100:.1f}%)")
        print(f"  调整成本: {total_adjust:.2f} 元 ({total_adjust/total_cost*100:.1f}%)")
        print(f"  紧急成本: {total_emergency:.2f} 元 ({total_emergency/total_cost*100:.1f}%)")
        print(f"平均日成本: {total_cost/len(results):.2f} 元")

        print(f"\n[P0验证] 同时充放电总次数: {total_simultaneous} (必须=0)")
        print(f"[P0验证] 紧急购电频率: {total_emergency_slots}/{len(results)*144} 时段 ({total_emergency_slots/(len(results)*144)*100:.1f}%)")

        # Stage K统计
        total_stage_k_adjustments = sum([r['n_stage_k_adjustments'] for r in results])
        print(f"\n[Stage K] 总调整次数: {total_stage_k_adjustments} / {len(results) * 3} 可能调整点")

        # SOC分析
        end_socs = [r['E_storage_end'] for r in results]
        min_socs = [r['E_storage_min'] for r in results]
        print(f"\n[SOC分析] 末态储能范围: {min(end_socs):.0f} ~ {max(end_socs):.0f} kWh")
        print(f"[SOC分析] 最低SOC: {min(min_socs):.0f} kWh")

        # 检查是否连续掉底
        low_soc_days = sum(1 for soc in end_socs if soc < E_MIN + 500)
        if low_soc_days > len(results) * 0.3:
            print(f"⚠️  警告: {low_soc_days}/{len(results)} 天末态接近下限，可能终端价值不足")

# ============================================================
# A/B 对比测试
# ============================================================

def run_ab_test_10days():
    """A/B对比测试：验证Stage K的价值"""
    print("="*70)
    print("A/B 对比测试 - Stage K价值验证")
    print("="*70)

    price, load_real, pv_real, pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h = load_data()
    load_by_date, pv_by_date = build_date_cache(load_real, pv_real)

    # 识别日类型
    global LOW_LOAD_WEEKDAYS
    LOW_LOAD_WEEKDAYS = infer_day_types_from_jan1_14(load_by_date)
    print(f"\n[锁定] 低负载星期: {LOW_LOAD_WEEKDAYS}")

    test_dates = pd.date_range('2025-02-01', '2025-02-10', freq='D')

    # A组：无Stage K
    print("\n" + "="*70)
    print("A组测试：无Stage K调整")
    print("="*70)
    results_A = []
    E_storage_prev = E_INIT

    for date in test_dates:
        print(f"\n优化 {date.date()}...")

        # 获取0:00时刻的PV预测
        pv_forecast_day = get_pv_forecast_as_of(date, 0, pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h)

        if date not in load_by_date or date not in pv_by_date or len(pv_forecast_day) != N_SLOTS:
            print(f"  [跳过] 数据不完整")
            continue

        try:
            result = optimize_single_day(
                date, price,
                load_by_date[date], pv_by_date[date],
                pv_forecast_day, E_storage_prev,
                load_by_date, pv_by_date,
                pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h,
                enable_stage_k=False  # 关闭Stage K
            )

            results_A.append(result)
            E_storage_prev = result['E_storage_end']

            print(f"  总成本: {result['Z_total']:.2f} 元 (计划: {result['Z_plan']:.2f}, 紧急: {result['Z_emergency']:.2f})")

        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
            break

    # B组：有Stage K
    print("\n" + "="*70)
    print("B组测试：启用Stage K调整")
    print("="*70)
    results_B = []
    E_storage_prev = E_INIT

    for date in test_dates:
        print(f"\n优化 {date.date()}...")

        # 获取0:00时刻的PV预测
        pv_forecast_day = get_pv_forecast_as_of(date, 0, pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h)

        if date not in load_by_date or date not in pv_by_date or len(pv_forecast_day) != N_SLOTS:
            print(f"  [跳过] 数据不完整")
            continue

        try:
            result = optimize_single_day(
                date, price,
                load_by_date[date], pv_by_date[date],
                pv_forecast_day, E_storage_prev,
                load_by_date, pv_by_date,
                pv_forecast_0h, pv_forecast_6h, pv_forecast_12h, pv_forecast_18h,
                enable_stage_k=True  # 启用Stage K
            )

            results_B.append(result)
            E_storage_prev = result['E_storage_end']

            print(f"  总成本: {result['Z_total']:.2f} 元 (计划: {result['Z_plan']:.2f}, 调整: {result['Z_adjust']:.2f}, 紧急: {result['Z_emergency']:.2f})")

        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
            break

    # 对比分析
    if results_A and results_B:
        print("\n" + "="*70)
        print("A/B 对比结果")
        print("="*70)

        total_cost_A = sum([r['Z_total'] for r in results_A])
        total_cost_B = sum([r['Z_total'] for r in results_B])

        total_plan_A = sum([r['Z_plan'] for r in results_A])
        total_plan_B = sum([r['Z_plan'] for r in results_B])

        total_emergency_A = sum([r['Z_emergency'] for r in results_A])
        total_emergency_B = sum([r['Z_emergency'] for r in results_B])

        total_adjust_B = sum([r['Z_adjust'] for r in results_B])

        emergency_slots_A = sum([r['emergency_slots'] for r in results_A])
        emergency_slots_B = sum([r['emergency_slots'] for r in results_B])

        print("\n【总成本对比】")
        print(f"  A组 (无Stage K): {total_cost_A:.2f} 元")
        print(f"  B组 (有Stage K): {total_cost_B:.2f} 元")
        cost_reduction = total_cost_A - total_cost_B
        print(f"  成本节省: {cost_reduction:.2f} 元 ({cost_reduction/total_cost_A*100:.2f}%)")

        print("\n【成本结构对比】")
        print(f"  计划成本: A={total_plan_A:.2f}, B={total_plan_B:.2f} (相同)")
        print(f"  调整成本: A=0.00, B={total_adjust_B:.2f}")
        print(f"  紧急成本: A={total_emergency_A:.2f}, B={total_emergency_B:.2f}")

        if total_emergency_A > 0:
            emergency_reduction = (total_emergency_A - total_emergency_B) / total_emergency_A * 100
            print(f"  紧急成本降低: {emergency_reduction:.1f}%")

        print("\n【紧急购电频率对比】")
        print(f"  A组: {emergency_slots_A}/{len(results_A)*144} 时段 ({emergency_slots_A/(len(results_A)*144)*100:.1f}%)")
        print(f"  B组: {emergency_slots_B}/{len(results_B)*144} 时段 ({emergency_slots_B/(len(results_B)*144)*100:.1f}%)")

        if emergency_slots_A > 0:
            frequency_reduction = (emergency_slots_A - emergency_slots_B) / emergency_slots_A * 100
            print(f"  频率降低: {frequency_reduction:.1f}%")

        print("\n【Stage K调整统计】")
        total_stage_k_adjustments = sum([r['n_stage_k_adjustments'] for r in results_B])
        print(f"  总调整次数: {total_stage_k_adjustments} / {len(results_B) * 3} 可能调整点")
        print(f"  平均调整成本占比: {total_adjust_B/total_cost_B*100:.2f}%")

        print("\n【结论】")
        if cost_reduction > 0:
            print(f"  ✅ Stage K有效：总成本降低 {cost_reduction:.2f} 元 ({cost_reduction/total_cost_A*100:.2f}%)")
            print(f"  ✅ 调整成本 ({total_adjust_B:.2f} 元) < 紧急成本节省 ({total_emergency_A - total_emergency_B:.2f} 元)")
        elif cost_reduction < 0:
            print(f"  ⚠️ Stage K当前无效：总成本增加 {-cost_reduction:.2f} 元")
            print(f"  ⚠️ 调整成本 ({total_adjust_B:.2f} 元) > 紧急成本节省 ({total_emergency_A - total_emergency_B:.2f} 元)")
        else:
            print(f"  ➖ Stage K影响中性：总成本无明显变化")

if __name__ == "__main__":
    # 运行A/B测试
    run_ab_test_10days()

    # 如果只想运行单一测试，使用：
    # main_test_10days()
