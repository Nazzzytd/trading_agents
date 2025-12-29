import sys
import os
sys.path.append('.')

try:
    from tradingagents.adaptive_system import AdaptiveSystem
    print("✅ 成功导入 AdaptiveSystem!")
    
    # 简单测试
    adaptive = AdaptiveSystem()
    adaptive.register_agent("test_agent", "analyst")
    adaptive.record_prediction("test_agent", 0.5)
    
    result = adaptive.get_weighted_decision({"test_agent": 0.5})
    print(f"✅ 测试成功! 加权决策: {result}")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
