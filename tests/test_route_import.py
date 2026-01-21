# tests/test_route_import.py
import sys
import os

# 添加项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"🔍 检查导入路径...")
print(f"项目根目录: {project_root}")
print(f"Python路径: {sys.path[:3]}")

# 测试不同模块的导入
modules_to_test = [
    "tradingagents.dataflows.interface",
    "tradingagents.agents.utils.news_data_tools", 
    "tradingagents.agents.utils.technical_indicators_tools"
]

for module_name in modules_to_test:
    print(f"\n📦 测试导入: {module_name}")
    try:
        module = __import__(module_name, fromlist=['*'])
        print(f"  ✅ 导入成功")
        
        # 检查是否有 route_to_vendor
        if hasattr(module, 'route_to_vendor'):
            print(f"  ✅ 找到 route_to_vendor")
        else:
            print(f"  ⚠️  没有 route_to_vendor 属性")
            
    except ImportError as e:
        print(f"  ❌ 导入失败: {e}")
    except Exception as e:
        print(f"  ⚠️  其他错误: {e}")

print(f"\n🔍 直接测试导入...")
try:
    from tradingagents.dataflows.interface import route_to_vendor
    print(f"✅ 成功直接导入 route_to_vendor")
    print(f"  位置: {route_to_vendor.__module__}")
except ImportError as e:
    print(f"❌ 直接导入失败: {e}")