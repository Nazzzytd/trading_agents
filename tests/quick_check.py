"""
快速检查脚本
"""
import sys
import os
from pathlib import Path

project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

print("🔍 快速系统检查")
print("=" * 60)

def check_packages():
    """检查关键包"""
    print("📦 检查关键包:")
    
    packages = [
        ("pandas", "数据处理"),
        ("numpy", "数值计算"),
        ("plotly", "数据可视化"),
        ("yfinance", "财经数据"),
        ("pandas_ta", "技术分析"),
        ("requests", "HTTP请求"),
        ("langchain", "LLM框架"),
        ("networkx", "图分析"),
    ]
    
    for package, description in packages:
        try:
            __import__(package)
            print(f"  ✅ {package}: {description} - 已安装")
        except ImportError:
            print(f"  ❌ {package}: {description} - 未安装")

def check_config():
    """检查配置"""
    print("\n⚙️  检查配置:")
    
    try:
        from tradingagents.dataflows.config import get_config
        config = get_config()
        
        print(f"  ✅ 配置加载成功")
        print(f"    项目目录: {config.get('project_dir', '未设置')}")
        print(f"    数据目录: {config.get('data_dir', '未设置')}")
        
        # 检查API密钥
        print(f"\n  🔑 API密钥检查:")
        apis = ['alpha_vantage', 'openai', 'twelvedata']
        for api in apis:
            api_config = config.get(api, {})
            if api_config.get('api_key'):
                print(f"    ✅ {api}: 已配置")
            else:
                print(f"    ⚠️  {api}: 未配置")
                
    except Exception as e:
        print(f"  ❌ 配置检查失败: {e}")

def check_data_tools():
    """检查数据工具"""
    print("\n🔧 检查数据工具:")
    
    tools = [
        ("technical_indicators_tools", "get_technical_data"),
        ("macro_data_tools", "get_fred_data"),
        ("macro_data_tools", "get_ecb_data"),
    ]
    
    for module_name, func_name in tools:
        try:
            module_path = f"tradingagents.agents.utils.{module_name}"
            module = __import__(module_path, fromlist=[''])
            
            if hasattr(module, func_name):
                func = getattr(module, func_name)
                print(f"  ✅ {func_name}: 存在 (类型: {type(func).__name__})")
                
                # 检查是否可调用
                if callable(func):
                    print(f"      可调用: 是")
                elif hasattr(func, 'invoke'):
                    print(f"      可调用: 通过.invoke()方法")
                else:
                    print(f"      可调用: 否")
            else:
                print(f"  ❌ {func_name}: 不存在")
                
        except Exception as e:
            print(f"  ❌ {module_name}.{func_name}: 检查失败 - {str(e)[:50]}")

def check_analysts():
    """检查分析师"""
    print("\n🤖 检查分析师模块:")
    
    analysts = ["macro_analyst", "news_analyst", "technical_analyst", "quantitative_analyst"]
    
    for analyst in analysts:
        try:
            module_path = f"tradingagents.agents.analysts.{analyst}"
            module = __import__(module_path, fromlist=[''])
            print(f"  ✅ {analyst}: 模块存在")
            
            # 检查创建函数
            create_func = f"create_{analyst}"
            if hasattr(module, create_func):
                print(f"      {create_func}: 存在")
            else:
                # 列出可用函数
                funcs = [f for f in dir(module) if not f.startswith('_')]
                print(f"      可用函数: {funcs[:5]}{'...' if len(funcs) > 5 else ''}")
                
        except Exception as e:
            print(f"  ❌ {analyst}: 模块不存在 - {e}")

def check_adaptive_system():
    """检查自适应系统"""
    print("\n⚡ 检查自适应系统:")
    
    try:
        from tradingagents.adaptive_system.weight_manager import AdaptiveWeightManager
        from tradingagents.adaptive_system.config import AdaptiveConfig
        from tradingagents.adaptive_system.layer_manager import LayerManager
        
        print(f"  ✅ AdaptiveWeightManager: 可用")
        print(f"  ✅ AdaptiveConfig: 可用")
        print(f"  ✅ LayerManager: 可用")
        
        # 测试创建实例
        config = AdaptiveConfig()
        weight_manager = AdaptiveWeightManager(config)
        layer_manager = LayerManager()
        
        print(f"  ✅ 实例创建成功")
        print(f"     权重管理器: {len(weight_manager.agents)}个智能体")
        
    except Exception as e:
        print(f"  ❌ 自适应系统检查失败: {e}")

def main():
    """主函数"""
    print("开始快速系统检查...\n")
    
    check_packages()
    check_config()
    check_data_tools()
    check_analysts()
    check_adaptive_system()
    
    print("\n" + "=" * 60)
    print("✅ 快速检查完成!")
    print("=" * 60)
    
    print("\n💡 建议:")
    print("1. 如果有❌标记的项目，请先安装相应包")
    print("2. 检查API密钥配置")
    print("3. 运行修复版测试: python tests/test_integration_fixed.py")

if __name__ == "__main__":
    main()