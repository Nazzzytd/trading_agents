# check_quant_tools.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("检查 quant_data_tools.py 中的实际函数...")

try:
    # 直接导入量化工具模块
    import importlib.util
    
    quant_path = os.path.join(
        os.path.dirname(__file__),
        'tradingagents',
        'agents',
        'utils',
        'quant_data_tools.py'
    )
    
    if os.path.exists(quant_path):
        spec = importlib.util.spec_from_file_location("quant_data_tools", quant_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        print(f"✓ 成功加载 quant_data_tools.py")
        
        # 列出所有函数
        functions = [x for x in dir(module) if not x.startswith('_') and callable(getattr(module, x))]
        print(f"  实际存在的函数: {functions}")
        
        # 检查特定函数
        target_functions = [
            'get_factor_analysis',
            'validate_technical_signal', 
            'calculate_risk_metrics',
            'get_risk_metrics_data',
            'get_volatility_data',
            'simple_forex_data'
        ]
        
        print(f"\n检查目标函数:")
        for func in target_functions:
            if hasattr(module, func):
                print(f"  ✓ {func}: 存在")
            else:
                print(f"  ✗ {func}: 不存在")
                
        # 打印文件内容预览
        print(f"\n文件内容预览:")
        with open(quant_path, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:50]):  # 前50行
                if line.strip().startswith('@tool') or line.strip().startswith('def '):
                    print(f"  第{i+1:3d}行: {line.rstrip()}")
                    
    else:
        print(f"✗ 文件不存在: {quant_path}")
        
except Exception as e:
    print(f"✗ 检查失败: {e}")
    import traceback
    traceback.print_exc()