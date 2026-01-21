# tests/test_actual_call.py
import sys
import os

# 添加项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("🔧 测试实际调用...")

# 测试1: 直接调用 route_to_vendor
try:
    from tradingagents.dataflows.interface import route_to_vendor
    
    print("🧪 测试1: 直接调用 route_to_vendor")
    result = route_to_vendor("get_news", "EUR/USD", "2024-01-01", "2024-01-31")
    print(f"   ✅ 调用成功，结果类型: {type(result)}")
    if isinstance(result, str):
        print(f"   📄 结果长度: {len(result)} 字符")
        if len(result) > 100:
            print(f"   📝 预览: {result[:100]}...")
except Exception as e:
    print(f"❌ 测试1失败: {e}")

# 测试2: 调用 get_technical_data
try:
    from tradingagents.agents.utils.technical_indicators_tools import get_technical_data
    
    print("\n🧪 测试2: 调用 get_technical_data")
    result = get_technical_data(
        symbol="EUR/USD",
        curr_date="2024-12-02",
        look_back_days=30
    )
    
    print(f"   ✅ 调用成功")
    print(f"   📊 成功状态: {result.get('success')}")
    
    if result.get('success'):
        print(f"   💰 当前价格: {result.get('current_price')}")
        print(f"   📈 数据点数: {result.get('data_points')}")
        print(f"   🎯 技术指标数: {len(result.get('latest_indicators', {}))}")
    else:
        print(f"   ❌ 错误信息: {result.get('error')}")
        
except Exception as e:
    print(f"❌ 测试2失败: {e}")

# 测试3: 调用 get_news 工具
# 在 test_actual_call.py 中修改测试3
try:
    from tradingagents.agents.utils.news_data_tools import get_news
    
    print("\n🧪 测试3: 调用 get_news 工具")
    
    # 检查是否是 StructuredTool
    if hasattr(get_news, 'invoke'):
        print("   ✅ 是 StructuredTool，使用 invoke 方法")
        print(f"   📋 工具名称: {get_news.name}")
        print(f"   📋 工具描述: {get_news.description}")
        
        # 获取 args_schema 查看需要的参数
        if hasattr(get_news, 'args_schema'):
            print("   📋 参数模式可用")
        
        # 测试调用（如果需要）
        # result = get_news.invoke({"ticker": "EUR/USD", "start_date": "2024-01-01", "end_date": "2024-01-31"})
        
    elif callable(get_news):
        print("   ✅ 是普通可调用函数")
    else:
        print(f"   ⚠️  类型: {type(get_news)}")
        
except Exception as e:
    print(f"❌ 测试3失败: {e}")

# 测试4: 测试参数处理
try:
    print("\n🧪 测试4: 参数处理")
    from tradingagents.agents.utils.technical_indicators_tools import get_technical_indicators_data
    
    # 检查这是否是LangChain工具
    if hasattr(get_technical_indicators_data, '__wrapped__'):
        print(f"   ✅ 是LangChain工具装饰器")
        print(f"   📝 工具名称: {get_technical_indicators_data.name}")
        print(f"   📋 工具描述: {get_technical_indicators_data.description}")
    else:
        print(f"   ⚠️  不是LangChain工具")
        
except Exception as e:
    print(f"❌ 测试4失败: {e}")

print("\n🎉 实际调用测试完成!")