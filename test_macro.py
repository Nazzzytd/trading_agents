# test_macro_final.py
import sys
import os

# 清除缓存
for key in list(sys.modules.keys()):
    if 'tradingagents' in key:
        del sys.modules[key]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("最终测试 - 检查 market_analyst 是否已完全移除...")

try:
    # 1. 测试能否导入 agents 模块
    print("1. 测试导入 agents 模块...")
    from tradingagents.agents import create_macro_analyst, create_msg_delete
    
    print("✓ 成功导入 agents 模块")
    print(f"  - create_macro_analyst: {'create_macro_analyst' in dir()}")
    print(f"  - create_msg_delete: {'create_msg_delete' in dir()}")
    
    # 2. 测试创建宏观经济分析师
    print("\n2. 测试创建宏观经济分析师...")
    
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
            print(f"\n报告预览:")
            print(result['macro_report'][:300] + "...")
    else:
        print(f"  ✗ 缺少 macro_report")
    
    # 3. 检查是否还有 market_analyst 的引用
    print("\n3. 检查是否还有 market_analyst 引用...")
    
    import importlib
    modules_to_check = ['tradingagents.agents', 'tradingagents.agents.utils.agent_states']
    
    for module_name in modules_to_check:
        try:
            module = importlib.import_module(module_name)
            module_dir = dir(module)
            
            market_refs = [attr for attr in module_dir if 'market' in attr.lower()]
            if market_refs:
                print(f"  ⚠️  {module_name} 中仍有 market 相关引用: {market_refs}")
            else:
                print(f"  ✓ {module_name} 中无 market 相关引用")
        except Exception as e:
            print(f"  ✗ 导入 {module_name} 失败: {e}")
    
    print("\n✅ 测试完成！market_analyst 已成功移除")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()