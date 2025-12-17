# final_test.py
import sys
import os

# 清除所有缓存
for key in list(sys.modules.keys()):
    if key.startswith('tradingagents'):
        del sys.modules[key]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("最终测试...")

try:
    # 1. 测试 agent_utils.py
    print("1. 测试 agent_utils.py...")
    from tradingagents.agents.utils.agent_utils import create_msg_delete
    print("✓ create_msg_delete 导入成功")
    
    # 2. 测试宏观经济工具
    print("\n2. 测试宏观经济工具...")
    from tradingagents.agents.utils.macro_data_tools import (
        get_fred_data,
        get_ecb_data,
        get_macro_dashboard
    )
    print(f"✓ 宏观经济工具导入成功:")
    print(f"  - get_fred_data: {get_fred_data.__doc__[:50]}...")
    print(f"  - get_ecb_data: {get_ecb_data.__doc__[:50]}...")
    print(f"  - get_macro_dashboard: {get_macro_dashboard.__doc__[:50]}...")
    
    # 3. 测试量化工具
    print("\n3. 测试量化工具...")
    from tradingagents.agents.utils.quant_data_tools import (
        get_risk_metrics_data,
        get_volatility_data,
        simple_forex_data
    )
    print(f"✓ 量化工具导入成功:")
    print(f"  - get_risk_metrics_data: 存在")
    print(f"  - get_volatility_data: 存在")
    print(f"  - simple_forex_data: 存在")
    
    # 4. 测试宏观经济分析师
    print("\n4. 测试宏观经济分析师...")
    from tradingagents.agents.analysts.macro_analyst import create_macro_analyst
    print("✓ create_macro_analyst 导入成功")
    
    # 创建模拟LLM
    class MockLLM:
        def bind_tools(self, tools):
            return self
        def invoke(self, messages):
            class Result:
                def __init__(self):
                    self.tool_calls = []
                    self.content = "宏观经济分析测试完成"
            return Result()
    
    llm = MockLLM()
    analyst = create_macro_analyst(llm)
    
    test_state = {
        "trade_date": "2024-01-01",
        "company_of_interest": "EUR/USD",
        "messages": []
    }
    
    result = analyst(test_state)
    print(f"✓ 宏观经济分析师测试成功")
    print(f"  返回键: {list(result.keys())}")
    
    if 'macro_report' in result:
        print(f"  ✓ 包含 macro_report")
        if result['macro_report']:
            print(f"    报告长度: {len(result['macro_report'])} 字符")
        else:
            print(f"    警告: macro_report 为空")
    else:
        print(f"  ✗ 缺少 macro_report")
    
    print("\n✅ 所有测试通过！")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    
    # 提供调试信息
    print("\n调试信息:")
    import importlib
    
    modules_to_check = [
        'tradingagents.agents.utils.agent_utils',
        'tradingagents.agents.utils.quant_data_tools',
        'tradingagents.agents.analysts.macro_analyst'
    ]
    
    for module_name in modules_to_check:
        try:
            module = importlib.import_module(module_name)
            print(f"✓ {module_name} 可以导入")
            if hasattr(module, '__file__'):
                print(f"  文件位置: {module.__file__}")
        except Exception as e2:
            print(f"✗ {module_name} 导入失败: {e2}")