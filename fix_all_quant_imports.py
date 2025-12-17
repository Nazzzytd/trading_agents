# fix_all_quant_imports.py
import os
import sys
import re

def fix_file(file_path, old_imports, new_content):
    """修复文件中的导入"""
    if os.path.exists(file_path):
        print(f"检查 {file_path}...")
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        modified = False
        
        for old_import in old_imports:
            if old_import in content:
                print(f"  ⚠️  找到需要修复的导入")
                content = content.replace(old_import, new_content)
                modified = True
        
        if modified:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"  ✓ 已修复")
        else:
            print(f"  ✓ 无需修复")
    else:
        print(f"  ❌ 文件不存在: {file_path}")

def fix_all_files():
    """修复所有文件中的量化工具导入"""
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. 修复 agent_utils.py
    agent_utils_path = os.path.join(base_dir, 'tradingagents', 'agents', 'utils', 'agent_utils.py')
    
    old_imports = [
        """from tradingagents.agents.utils.quant_data_tools import (
    get_factor_analysis,
    validate_technical_signal,
    calculate_risk_metrics
)""",
        "from tradingagents.agents.utils.quant_data_tools import (",
        "from tradingagents.agents.utils.quant_data_tools import get_factor_analysis",
        "from tradingagents.agents.utils.quant_data_tools import validate_technical_signal",
        "from tradingagents.agents.utils.quant_data_tools import calculate_risk_metrics"
    ]
    
    new_content = """# 量化分析工具 - 只导入实际存在的函数
from tradingagents.agents.utils.quant_data_tools import (
    get_risk_metrics_data,
    get_volatility_data,
    simple_forex_data
)"""
    
    fix_file(agent_utils_path, old_imports, new_content)
    
    # 2. 修复 setup.py
    setup_path = os.path.join(base_dir, 'tradingagents', 'graph', 'setup.py')
    
    old_setup_imports = [
        """from tradingagents.agents.utils.quant_data_tools import (
                    get_factor_analysis,
                    validate_technical_signal,
                    calculate_risk_metrics
                )""",
        """from tradingagents.agents.utils.quant_data_tools import (
    get_factor_analysis,
    validate_technical_signal,
    calculate_risk_metrics
)"""
    ]
    
    new_setup_content = """from tradingagents.agents.utils.quant_data_tools import (
    get_risk_metrics_data,
    get_volatility_data,
    simple_forex_data
)"""
    
    # 读取并修复 setup.py
    if os.path.exists(setup_path):
        print(f"\n检查 {setup_path}...")
        
        with open(setup_path, 'r') as f:
            content = f.read()
        
        # 修复导入语句
        for old_import in old_setup_imports:
            if old_import in content:
                print(f"  ⚠️  找到需要修复的导入")
                content = content.replace(old_import, new_setup_content)
        
        # 修复工具列表
        if "quant_tools = [get_factor_analysis, validate_technical_signal, calculate_risk_metrics]" in content:
            print(f"  ⚠️  修复工具列表")
            content = content.replace(
                "quant_tools = [get_factor_analysis, validate_technical_signal, calculate_risk_metrics]",
                "quant_tools = [get_risk_metrics_data, get_volatility_data, simple_forex_data]"
            )
        
        # 保存修改
        with open(setup_path, 'w') as f:
            f.write(content)
        print(f"  ✓ 已修复")
    
    # 3. 修复 __init__.py（如果需要）
    init_path = os.path.join(base_dir, 'tradingagents', 'agents', '__init__.py')
    
    # 检查是否导入了不存在的函数
    if os.path.exists(init_path):
        print(f"\n检查 {init_path}...")
        
        with open(init_path, 'r') as f:
            content = f.read()
        
        # 检查是否导入了不存在的函数
        if 'get_factor_analysis' in content or 'validate_technical_signal' in content or 'calculate_risk_metrics' in content:
            print(f"  ⚠️  可能需要修复 __init__.py")
            # 这里可能需要根据实际情况修复
        else:
            print(f"  ✓ 无需修复")
    
    # 4. 修复其他可能的地方
    other_files = [
        'tradingagents/agents/analysts/quantitative_analyst.py',
        'tradingagents/dataflows/interface.py'
    ]
    
    for file in other_files:
        file_path = os.path.join(base_dir, file)
        if os.path.exists(file_path):
            print(f"\n检查 {file}...")
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # 检查是否有不存在的函数引用
            if any(func in content for func in ['get_factor_analysis', 'validate_technical_signal', 'calculate_risk_metrics']):
                print(f"  ⚠️  可能包含不存在的函数引用")
                # 显示相关行
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if any(func in line for func in ['get_factor_analysis', 'validate_technical_signal', 'calculate_risk_metrics']):
                        print(f"    第{i+1}行: {line.strip()}")
            else:
                print(f"  ✓ 无需修复")
    
    print("\n修复完成！")

if __name__ == '__main__':
    fix_all_files()