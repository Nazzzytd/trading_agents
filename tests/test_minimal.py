# tests/test_minimal.py
import sys
import os

# 添加项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("🔬 最小化测试...")

# 最小化测试：只测试核心功能
try:
    # 1. 测试导入
    print("1. 测试导入...")
    import tradingagents.dataflows.interface as interface_module
    
    # 2. 检查 route_to_vendor 是否存在
    print("2. 检查 route_to_vendor...")
    if hasattr(interface_module, 'route_to_vendor'):
        route_func = interface_module.route_to_vendor
        print(f"   ✅ 找到函数: {route_func}")
        
        # 3. 测试简单调用
        print("3. 测试简单调用...")
        # 尝试最简单的调用
        try:
            result = route_func("get_news", "test")
            print(f"   ✅ 调用成功，类型: {type(result)}")
        except TypeError as e:
            # 可能是参数错误，但至少函数存在
            print(f"   ⚠️  参数错误（正常）: {e}")
    else:
        print(f"❌ 没有找到 route_to_vendor")
        print(f"   模块内容: {dir(interface_module)}")
        
except Exception as e:
    print(f"❌ 测试失败: {e}")

# 测试 technical_indicators_tools 中的函数
print("\n4. 测试 get_technical_data...")
try:
    import tradingagents.agents.utils.technical_indicators_tools as tech_module
    
    # 检查函数是否存在
    if hasattr(tech_module, 'get_technical_data'):
        func = tech_module.get_technical_data
        print(f"   ✅ 找到函数: {func}")
        
        # 检查函数源代码中是否有 route_to_vendor
        import inspect
        source = inspect.getsource(func)
        if 'route_to_vendor' in source:
            print(f"   ✅ 源代码中包含 route_to_vendor")
        else:
            print(f"   ❌ 源代码中不包含 route_to_vendor")
            
        # 检查模块中是否有 route_to_vendor 导入
        module_source = inspect.getsource(tech_module)
        if 'from tradingagents.dataflows.interface import route_to_vendor' in module_source:
            print(f"   ✅ 模块中导入了 route_to_vendor")
        else:
            print(f"   ❌ 模块中没有导入 route_to_vendor")
            
    else:
        print(f"❌ 没有找到 get_technical_data")
        
except Exception as e:
    print(f"❌ 测试失败: {e}")

print("\n🎯 最小化测试完成!")