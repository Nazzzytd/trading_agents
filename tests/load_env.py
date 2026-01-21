"""
加载环境变量并测试配置
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

print("🔧 加载环境变量")
print("=" * 60)

def load_environment_variables():
    """加载环境变量"""
    
    # 可能的.env文件路径
    env_paths = [
        os.path.join(project_root, ".env"),
        os.path.join(project_root, ".env.local"),
        os.path.join(project_root, "config", ".env"),
    ]
    
    loaded = False
    for env_path in env_paths:
        if os.path.exists(env_path):
            print(f"📄 找到.env文件: {env_path}")
            load_dotenv(env_path, override=True)
            loaded = True
            break
    
    if not loaded:
        print("⚠️  未找到.env文件，将使用系统环境变量")
        # 尝试从当前目录加载
        load_dotenv()
    
    return loaded

def test_environment_variables():
    """测试环境变量"""
    print("\n🔑 检查环境变量:")
    
    # 关键API密钥
    api_keys = [
        ("OPENAI_API_KEY", "OpenAI API密钥"),
        ("OPENAI_BASE_URL", "OpenAI基础URL"),
        ("ALPHA_VANTAGE_API_KEY", "Alpha Vantage API密钥"),
        ("NEWSAPI_KEY", "NewsAPI密钥"),
        ("TWELVEDATA_API_KEY", "TwelveData API密钥"),
        ("FRED_API_KEY", "FRED API密钥"),
        ("MYFXBOOK_EMAIL", "MyFXBook邮箱"),
        ("MYFXBOOK_PASSWORD", "MyFXBook密码"),
    ]
    
    all_present = True
    for key, description in api_keys:
        value = os.getenv(key)
        if value:
            # 显示部分密钥（保护隐私）
            display_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            print(f"  ✅ {description}: {display_value}")
        else:
            print(f"  ❌ {description}: 未设置")
            all_present = False
    
    return all_present

def test_imports():
    """测试导入"""
    print("\n📦 测试模块导入:")
    
    modules = [
        ("tradingagents.dataflows.interface", "数据流接口"),
        ("tradingagents.dataflows.config", "配置模块"),
        ("tradingagents.agents.utils.technical_indicators_tools", "技术指标工具"),
        ("tradingagents.adaptive_system.weight_manager", "权重管理器"),
    ]
    
    for module_path, description in modules:
        try:
            __import__(module_path)
            print(f"  ✅ {description}: 导入成功")
        except Exception as e:
            print(f"  ❌ {description}: 导入失败 - {str(e)[:50]}")
            import traceback
            traceback.print_exc()

def test_config_loading():
    """测试配置加载"""
    print("\n⚙️  测试配置加载:")
    
    try:
        from tradingagents.dataflows.config import get_config
        config = get_config()
        
        if config:
            print(f"  ✅ 配置加载成功")
            
            # 检查关键配置
            print(f"  📋 配置项:")
            for key in ['alpha_vantage', 'openai', 'llm_provider']:
                if key in config:
                    value = config[key]
                    if isinstance(value, dict):
                        has_key = 'api_key' in value and value['api_key']
                        print(f"    {key}: {'✅ 已配置API密钥' if has_key else '⚠️  API密钥未配置'}")
                    else:
                        print(f"    {key}: {type(value).__name__}")
                else:
                    print(f"    {key}: ❌ 不存在")
        else:
            print(f"  ❌ 配置加载失败")
            
    except Exception as e:
        print(f"  ❌ 配置测试失败: {e}")

def test_route_to_vendor():
    """测试route_to_vendor函数"""
    print("\n🔄 测试route_to_vendor:")
    
    try:
        from tradingagents.dataflows.interface import route_to_vendor
        
        # 测试一个简单的调用
        print("  测试新闻数据...")
        result = route_to_vendor(
            "get_news",
            ticker="EUR/USD",
            limit=2,
            start_date="2024-11-01",
            end_date="2024-11-30"
        )
        
        if result:
            print(f"  ✅ route_to_vendor调用成功")
            if isinstance(result, dict):
                print(f"  📋 结果类型: dict, 键: {list(result.keys())}")
        else:
            print(f"  ⚠️  route_to_vendor返回空结果")
            
    except Exception as e:
        print(f"  ❌ route_to_vendor测试失败: {e}")
        import traceback
        traceback.print_exc()

def create_pythonpath_fix():
    """创建Python路径修复"""
    print("\n🔧 创建Python路径修复:")
    
    fix_code = '''
# 修复Python路径问题
import sys
import os
from pathlib import Path

# 添加项目根目录
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)

# 加载环境变量
from dotenv import load_dotenv
env_path = os.path.join(project_root, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
    print(f"✅ 从 {env_path} 加载环境变量")
else:
    print(f"⚠️  未找到.env文件: {env_path}")

# 测试导入
try:
    from tradingagents.dataflows.interface import route_to_vendor
    print("✅ route_to_vendor导入成功")
except ImportError as e:
    print(f"❌ route_to_vendor导入失败: {e}")

print("✅ Python路径修复完成")
'''
    
    fix_file = os.path.join(project_root, "tests", "pythonpath_fix.py")
    with open(fix_file, 'w', encoding='utf-8') as f:
        f.write(fix_code)
    
    print(f"  📄 修复脚本保存到: {fix_file}")
    print(f"  💡 在需要时导入此脚本: from tests.pythonpath_fix import *")

def main():
    """主函数"""
    print("开始加载和测试环境配置...\n")
    
    # 1. 加载环境变量
    env_loaded = load_environment_variables()
    
    if not env_loaded:
        print("⚠️  警告：未加载到.env文件")
    
    # 2. 测试环境变量
    env_ok = test_environment_variables()
    
    # 3. 测试导入
    test_imports()
    
    # 4. 测试配置
    test_config_loading()
    
    # 5. 测试route_to_vendor
    if env_ok:
        test_route_to_vendor()
    
    # 6. 创建修复
    create_pythonpath_fix()
    
    print("\n" + "=" * 60)
    if env_ok:
        print("✅ 环境配置测试完成！")
    else:
        print("⚠️  环境配置存在问题")
    
    print("=" * 60)
    
    print("\n💡 建议:")
    if env_ok:
        print("1. ✅ 环境变量已正确加载")
        print("2. 🚀 现在可以运行集成测试")
        print("3. 📊 运行: python tests/working_example.py")
    else:
        print("1. 🔧 需要手动设置环境变量")
        print("2. 💻 运行: source .env (Linux/Mac) 或 set / .env (Windows)")
        print("3. 🔄 或者在代码开始处添加: from dotenv import load_dotenv; load_dotenv()")

if __name__ == "__main__":
    main()