#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q1 主运行脚本 - 三步执行流程
解决环境兼容性问题，分步执行数据处理和求解

使用方法:
    python run_q1.py

或分步执行:
    python questions/QC/04_code/step1_data.py
    python questions/QC/04_code/step2_solve.py
    python questions/QC/04_code/step3_deliverables.py
"""

import subprocess
import sys
import os

PYTHON = r"C:\Program Files\Python38\python.exe"
CODE_DIR = "questions/QC/04_code"

def run_step(script_name, description):
    """运行单个步骤"""
    print("\n" + "="*70)
    print(f"Running: {description}")
    print("="*70)

    script_path = os.path.join(CODE_DIR, script_name)

    try:
        result = subprocess.run(
            [PYTHON, script_path],
            capture_output=True,
            text=True,
            timeout=300
        )

        print(result.stdout)

        if result.returncode != 0:
            print(f"\n❌ ERROR in {script_name}:")
            print(result.stderr)
            return False

        return True

    except subprocess.TimeoutExpired:
        print(f"\n❌ TIMEOUT: {script_name} exceeded 300 seconds")
        return False
    except Exception as e:
        print(f"\n❌ EXCEPTION in {script_name}: {e}")
        return False


def main():
    """主执行流程"""
    print("\n" + "🚀"*35)
    print("Q1 Microgrid Optimization - Three-Step Execution")
    print("🚀"*35)

    steps = [
        ("step1_data.py", "Step 1: Data Preparation"),
        ("step2_solve.py", "Step 2: HiGHS Optimization"),
        ("step3_deliverables.py", "Step 3: Generate Deliverables")
    ]

    for i, (script, desc) in enumerate(steps, 1):
        success = run_step(script, desc)

        if not success:
            print("\n" + "❌"*35)
            print(f"FAILED at Step {i}: {desc}")
            print("❌"*35)
            sys.exit(1)

    print("\n" + "🎉"*35)
    print("SUCCESS: All steps completed!")
    print("🎉"*35)
    print("\nDeliverables generated in: questions/QC/05_results/")
    print("  - result1.xlsx")
    print("  - validation_report.txt")
    print("  - result_data.json")
    print()


if __name__ == "__main__":
    main()
