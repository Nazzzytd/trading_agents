# tests/test_fixed_imports.py
import sys
import os

# 添加项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("🔧 测试修复后的导入...")

# 测试1: 直接导入 route_to_vendor
try:
    from tradingagents.dataflows.interface import route_to_vendor
    print("✅ 测试1: 直接导入 route_to_vendor 成功")
    
    # 测试调用
    result = route_to_vendor("get_news", "EUR/USD", "2024-01-01", "2024-01-31")
    print(f"   📊 调用结果类型: {type(result)}")
except Exception as e:
    print(f"❌ 测试1失败: {e}")

# 测试2: 导入技术指标工具
try:
    from tradingagents.agents.utils.technical_indicators_tools import get_technical_data
    print("✅ 测试2: 导入 get_technical_data 成功")
    
    # 测试参数
    import inspect
    params = inspect.signature(get_technical_data).parameters
    print(f"   📋 函数参数: {list(params.keys())}")
except Exception as e:
    print(f"❌ 测试2失败: {e}")

# 测试3: 导入新闻工具
try:
    from tradingagents.agents.utils.news_data_tools import get_news
    print("✅ 测试3: 导入 get_news 成功")
except Exception as e:
    print(f"❌ 测试3失败: {e}")

# 测试4: 通过 __init__.py 导入
try:
    from tradingagents.agents.utils import get_technical_indicators_data, get_news
    print("✅ 测试4: 通过 __init__.py 导入成功")
except Exception as e:
    print(f"❌ 测试4失败: {e}")

print("\n🎉 测试完成!")