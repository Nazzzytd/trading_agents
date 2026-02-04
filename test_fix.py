import sys
sys.path.insert(0, '.')

print("=== 测试 interface.py 修复 ===")

# 测试1：导入interface模块
try:
    from tradingagents.dataflows.interface import _quant_tools, VENDOR_METHODS
    print("✅ interface模块导入成功")
    
    # 检查量化工具
    if _quant_tools:
        print(f"量化工具数量: {len(_quant_tools)}")
        for name, tool in _quant_tools.items():
            print(f"  {name}: {type(tool).__name__}")
            
            # 测试工具是否能调用
            try:
                if hasattr(tool, 'invoke'):
                    result = tool.invoke({"symbol": "EUR/USD", "periods": 252})
                    print(f"    ✅ 调用成功: {result[:60]}...")
                elif hasattr(tool, 'run'):
                    result = tool.run({"symbol": "EUR/USD", "periods": 252})
                    print(f"    ✅ 调用成功: {result[:60]}...")
                else:
                    print(f"    ⚠️ 没有调用方法")
            except Exception as e:
                print(f"    ❌ 调用失败: {e}")
    else:
        print("⚠️ 量化工具字典为空")
    
    # 检查VENDOR_METHODS中的量化工具
    print("\n检查VENDOR_METHODS中的量化工具:")
    quant_methods = ["get_risk_metrics_data", "get_volatility_data", "simple_forex_data", "calculate_risk_metrics"]
    for method in quant_methods:
        if method in VENDOR_METHODS:
            vendors = VENDOR_METHODS[method]
            print(f"  ✅ {method}: {list(vendors.keys())}")
            
            # 测试calculate_risk_metrics
            if method == "calculate_risk_metrics" and "quant_tools" in vendors:
                quant_func = vendors["quant_tools"]
                try:
                    result = quant_func("EUR/USD", "2024-01-01", 252)
                    print(f"    ✅ calculate_risk_metrics调用成功: {result[:80]}...")
                except Exception as e:
                    print(f"    ❌ calculate_risk_metrics调用失败: {e}")
        else:
            print(f"  ❌ {method}: 不在VENDOR_METHODS中")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 测试完成 ===")
