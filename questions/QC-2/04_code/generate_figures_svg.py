"""
统一图表生成脚本 - SVG格式
包含基础图表和深度分析图表
"""
import json
from pathlib import Path
from figure_generators import (
    generate_figure1,
    generate_figure2,
    generate_figure3,
    generate_figure4,
    generate_figure5,
    generate_table1,
)
from figure_generators_advanced import (
    generate_figure6_cost_breakdown,
    generate_figure7_seasonal_comparison,
    generate_figure8_battery_cycle_analysis,
    generate_figure9_temporal_heatmap,
)

def load_data():
    """加载所有需要的数据"""
    print("加载数据...")

    with open('full_year_backtest_results.json', encoding='utf-8') as f:
        backtest = json.load(f)

    with open('no_storage_baseline_results.json', encoding='utf-8') as f:
        baseline = json.load(f)

    with open('energy_balance_verified.json', encoding='utf-8') as f:
        energy_data = json.load(f)

    return {
        'backtest': backtest,
        'baseline': baseline,
        'energy_data': energy_data,
    }


def main():
    """主函数：生成所有图表（SVG格式）"""
    print("=" * 70)
    print("QC-2 论文图表生成 (SVG)")
    print("=" * 70)

    # 加载数据
    data = load_data()

    # 输出目录
    output_dir = Path('../06_figures')

    # ========== 基础图表 ==========
    print("\n[基础图表]")

    print("\n[1/10] 生成图1：成本与能量分析...")
    generate_figure1(data, output_dir / '图1_成本与能量分析.svg', fmt='svg')
    print("  [OK] 保存: 图1_成本与能量分析.svg")

    print("\n[2/10] 生成图2：储能经济性对比...")
    generate_figure2(data, output_dir / '图2_储能经济性对比.svg', fmt='svg')
    print("  [OK] 保存: 图2_储能经济性对比.svg")

    print("\n[3/10] 生成图3：典型日SOC轨迹...")
    generate_figure3(data, output_dir / '图3_典型日SOC轨迹.svg', fmt='svg')
    print("  [OK] 保存: 图3_典型日SOC轨迹.svg")

    print("\n[4/10] 生成图4：跨日连续性验证...")
    generate_figure4(data, output_dir / '图4_跨日连续性验证.svg', fmt='svg')
    print("  [OK] 保存: 图4_跨日连续性验证.svg")

    print("\n[5/10] 生成图5：全年SOC轨迹...")
    generate_figure5(data, output_dir / '图5_全年SOC轨迹.svg', fmt='svg')
    print("  [OK] 保存: 图5_全年SOC轨迹.svg")

    print("\n[6/10] 生成表1：边界触碰统计...")
    generate_table1(data, output_dir / '表1_边界触碰统计.svg', fmt='svg')
    print("  [OK] 保存: 表1_边界触碰统计.svg")

    # ========== 深度分析图表 ==========
    print("\n[深度分析图表]")

    print("\n[7/10] 生成图6：成本节省来源分解...")
    generate_figure6_cost_breakdown(data, output_dir / '图6_成本节省来源分解.svg', fmt='svg')
    print("  [OK] 保存: 图6_成本节省来源分解.svg")

    print("\n[8/10] 生成图7：季节性运行模式对比...")
    generate_figure7_seasonal_comparison(data, output_dir / '图7_季节性运行模式对比.svg', fmt='svg')
    print("  [OK] 保存: 图7_季节性运行模式对比.svg")

    print("\n[9/10] 生成图8：电池寿命分析...")
    generate_figure8_battery_cycle_analysis(data, output_dir / '图8_电池寿命分析.svg', fmt='svg')
    print("  [OK] 保存: 图8_电池寿命分析.svg")

    print("\n[10/10] 生成图9：SOC时空热力图...")
    generate_figure9_temporal_heatmap(data, output_dir / '图9_SOC时空热力图.svg', fmt='svg')
    print("  [OK] 保存: 图9_SOC时空热力图.svg")

    print("\n" + "=" * 70)
    print("所有图表生成完成！")
    print("=" * 70)
    print("\n生成的图表：")
    print("  基础图表（6张）：图1-5 + 表1")
    print("  深度分析（4张）：图6-9")
    print("\nSVG优势：矢量图，无损缩放，可用Illustrator/Inkscape精细调整")
    print("\n保存位置: ../06_figures/")


if __name__ == '__main__':
    main()
