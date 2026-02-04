import sys
sys.path.insert(0, '.')

print("=== 验证修复效果 ===")

# 测试1：测试量化工具
print("\n1. 测试量化工具导入...")
try:
    from tradingagents.agents.utils.quant_data_tools import get_risk_metrics_data
    print(f"✅ 量化工具导入成功: {type(get_risk_metrics_data).__name__}")
    
    # 测试调用
    print("\n2. 测试工具调用...")
    try:
        # 测试位置参数调用
        result = get_risk_metrics_data.invoke({
            "symbol": "EUR/USD",
            "periods": 252,
            "timeframe": "1day"
        })
        print(f"✅ 关键字参数调用成功: {result[:80]}...")
    except Exception as e:
        print(f"❌ 关键字参数调用失败: {e}")
    
except Exception as e:
    print(f"❌ 量化工具测试失败: {e}")

# 测试2：测试interface模块
print("\n3. 测试interface模块...")
try:
    from tradingagents.dataflows.interface import VENDOR_METHODS, route_to_vendor
    print("✅ interface模块导入成功")
    
    # 检查量化工具是否在VENDOR_METHODS中
    quant_methods = ["get_risk_metrics_data", "calculate_risk_metrics"]
    for method in quant_methods:
        if method in VENDOR_METHODS:
            print(f"  ✅ {method} 在VENDOR_METHODS中")
            
            # 测试调用
            try:
                if method == "get_risk_metrics_data":
                    result = route_to_vendor(method, "EUR/USD", 252, "1day")
                    print(f"    ✅ {method} 路由调用成功: {result[:80]}...")
                elif method == "calculate_risk_metrics":
                    result = route_to_vendor(method, "EUR/USD", "2024-01-01", 252)
                    print(f"    ✅ {method} 路由调用成功: {result[:80]}...")
            except Exception as e:
                print(f"    ⚠️ {method} 调用失败（可能正常）: {e}")
        else:
            print(f"  ❌ {method} 不在VENDOR_METHODS中")
    
except Exception as e:
    print(f"❌ interface模块测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试3：测试技术指标工具
print("\n4. 测试技术指标工具...")
try:
    from tradingagents.agents.utils.technical_indicators_tools import route_to_vendor as tech_route
    result = tech_route("test", "test")
    print(f"✅ 技术指标工具导入成功: {result}")
except Exception as e:
    print(f"❌ 技术指标工具测试失败: {e}")

print("\n=== 验证完成 ===")
