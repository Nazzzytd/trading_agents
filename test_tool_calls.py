# test_tool_calls.py
import sys
sys.path.insert(0, '.')

print("=== 测试量化工具调用 ===")

# 测试1：导入工具
print("\n1. 导入工具...")
try:
    from tradingagents.agents.utils.quant_data_tools import (
        get_risk_metrics_data,
        get_volatility_data,
        simple_forex_data
    )
    print("✅ 工具导入成功")
    
    # 检查工具类型
    print(f"\n工具类型检查:")
    print(f"  get_risk_metrics_data: {type(get_risk_metrics_data).__name__}")
    print(f"  get_volatility_data: {type(get_volatility_data).__name__}")
    print(f"  simple_forex_data: {type(simple_forex_data).__name__}")
    
    # 检查是否是 Tool 对象
    from langchain_core.tools import Tool
    for name, tool in [
        ("风险指标", get_risk_metrics_data),
        ("波动率", get_volatility_data),
        ("简化数据", simple_forex_data)
    ]:
        if isinstance(tool, Tool):
            print(f"  {name}: 是 Tool 对象")
            print(f"    名称: {tool.name}")
            print(f"    描述: {tool.description[:50]}...")
        else:
            print(f"  {name}: 不是 Tool 对象 ({type(tool)})")
    
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()

# 测试2：测试工具调用
print("\n2. 测试工具调用...")
try:
    # 方法1：使用 .invoke() 方法
    print("\n方法1: 使用 .invoke()")
    try:
        result = get_risk_metrics_data.invoke({
            "symbol": "EUR/USD",
            "periods": 252,
            "timeframe": "1day"
        })
        print(f"✅ .invoke() 调用成功: {result[:80]}...")
    except Exception as e:
        print(f"❌ .invoke() 失败: {e}")
    
    # 方法2：使用 .run() 方法（如果支持）
    print("\n方法2: 使用 .run()")
    try:
        if hasattr(get_volatility_data, 'run'):
            result = get_volatility_data.run({
                "symbol": "EUR/USD",
                "periods": 60,
                "timeframe": "1day"
            })
            print(f"✅ .run() 调用成功: {result[:80]}...")
        else:
            print("⚠️ 没有 .run() 方法")
    except Exception as e:
        print(f"❌ .run() 失败: {e}")
    
    # 方法3：直接调用（如果支持）
    print("\n方法3: 直接调用")
    try:
        # 有些版本的 @tool 装饰器支持直接调用
        result = simple_forex_data(
            symbol="EUR/USD",
            what="risk",
            periods=100
        )
        print(f"✅ 直接调用成功: {result[:80]}...")
    except Exception as e:
        print(f"⚠️ 直接调用失败（正常）: {e}")
        
except Exception as e:
    print(f"❌ 工具调用测试失败: {e}")

# 测试3：测试量化分析师
print("\n3. 测试量化分析师...")
try:
    from tradingagents.agents.analysts.quantitative_analyst import create_quantitative_analyst
    
    analyst = create_quantitative_analyst()
    print(f"✅ 量化分析师创建成功: {analyst.name}")
    
    tools = analyst.get_tools()
    print(f"✅ 获取到 {len(tools)} 个工具")
    
    # 测试分析师中的工具是否能工作
    if tools:
        print("\n测试分析师中的工具:")
        for i, tool in enumerate(tools):
            print(f"\n  工具 {i+1}: {tool.name}")
            
            try:
                # 使用 .invoke() 测试
                if hasattr(tool, 'invoke'):
                    result = tool.invoke({
                        "symbol": "EUR/USD",
                        "periods": 100,
                        "timeframe": "1day"
                    })
                    print(f"    ✅ 调用成功: {str(result)[:60]}...")
                else:
                    print(f"    ⚠️ 没有 .invoke() 方法")
            except Exception as e:
                print(f"    ❌ 调用失败: {e}")
    
except Exception as e:
    print(f"❌ 量化分析师测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 测试完成 ===")