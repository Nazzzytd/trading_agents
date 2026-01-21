"""
修复脚本 - 解决测试中发现的问题
"""
import sys
import os
from pathlib import Path

project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

print("🔧 问题修复脚本")
print("=" * 60)

def fix_parameter_names():
    """修复参数名问题"""
    print("\n1️⃣ 修复参数名问题")
    
    try:
        from tradingagents.agents.utils.technical_indicators_tools import get_technical_data
        
        # 获取函数的签名信息
        import inspect
        sig = inspect.signature(get_technical_data)
        params = list(sig.parameters.keys())
        
        print(f"   📋 get_technical_data 参数: {params}")
        
        # 正确调用示例
        result = get_technical_data(
            symbol="EUR/USD",
            curr_date="2024-12-02",
            look_back_days=30  # 正确的参数名
        )
        
        if result and isinstance(result, dict) and result.get("success"):
            print(f"   ✅ 技术数据获取成功!")
            print(f"   📊 数据源: {result.get('data_source', 'unknown')}")
            
            data = result.get("data")
            if isinstance(data, list):
                print(f"   📅 数据条数: {len(data)}")
                if len(data) > 0:
                    print(f"   📋 示例数据: {data[0]}")
            elif isinstance(data, dict):
                print(f"   📊 数据字段: {list(data.keys())}")
        else:
            print(f"   ❌ 技术数据获取失败: {result}")
            
    except Exception as e:
        print(f"   ⚠️  修复失败: {e}")

def fix_macro_data_calls():
    """修复宏观数据调用"""
    print("\n2️⃣ 修复宏观数据调用")
    
    try:
        from tradingagents.agents.utils.macro_data_tools import get_fred_data, get_ecb_data
        
        # 获取FRED工具的参数要求
        if hasattr(get_fred_data, 'args_schema'):
            schema = get_fred_data.args_schema
            print(f"   📋 FRED工具参数要求:")
            if hasattr(schema, 'schema'):
                properties = schema.schema().get('properties', {})
                for key, info in properties.items():
                    print(f"     {key}: {info.get('title', '')}")
                    if 'description' in info:
                        print(f"       {info['description']}")
        
        # 获取ECB工具的参数要求
        if hasattr(get_ecb_data, 'args_schema'):
            schema = get_ecb_data.args_schema
            print(f"   📋 ECB工具参数要求:")
            if hasattr(schema, 'schema'):
                properties = schema.schema().get('properties', {})
                for key, info in properties.items():
                    print(f"     {key}: {info.get('title', '')}")
                    if 'description' in info:
                        print(f"       {info['description']}")
        
        # 尝试使用正确的参数
        print(f"\n   🔄 尝试调用FRED数据...")
        try:
            # 常见的FRED系列ID
            fred_series = {
                "GDP": "GDP",  # 美国GDP
                "CPI": "CPIAUCSL",  # 美国CPI
                "UNRATE": "UNRATE",  # 失业率
                "FEDFUNDS": "FEDFUNDS",  # 联邦基金利率
            }
            
            for series_name, series_id in fred_series.items():
                try:
                    result = get_fred_data.invoke({"series_id": series_id})
                    if result:
                        print(f"     ✅ FRED {series_name}({series_id}): 成功")
                    else:
                        print(f"     ❌ FRED {series_name}({series_id}): 失败")
                except Exception as e:
                    print(f"     ⚠️  FRED {series_name}: {str(e)[:50]}")
                    
        except Exception as e:
            print(f"   ⚠️  FRED调用错误: {e}")
            
    except Exception as e:
        print(f"   ⚠️  修复失败: {e}")

def fix_quantitative_analyst():
    """修复量化分析师导入问题"""
    print("\n3️⃣ 修复量化分析师导入问题")
    
    try:
        # 检查quantitative_analyst.py文件
        quant_file = os.path.join(project_root, "tradingagents", "agents", "analysts", "quantitative_analyst.py")
        
        if os.path.exists(quant_file):
            print(f"   📄 量化分析师文件存在: {quant_file}")
            
            # 读取文件内容
            with open(quant_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查导入语句
            if "from langchain.agents import Tool" in content:
                print(f"   🔍 找到旧的导入语句: from langchain.agents import Tool")
                
                # 建议修复
                print(f"\n   💡 建议修复:")
                print(f"     将 'from langchain.agents import Tool' 替换为:")
                print(f"     'from langchain.tools import Tool'")
                
                # 创建修复版本
                fixed_content = content.replace(
                    "from langchain.agents import Tool",
                    "from langchain.tools import Tool"
                )
                
                # 保存备份
                backup_file = quant_file + ".backup"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   💾 原始文件已备份到: {backup_file}")
                
                # 应用修复
                with open(quant_file, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print(f"   ✅ 文件已修复")
                
        else:
            print(f"   ❌ 量化分析师文件不存在")
            
    except Exception as e:
        print(f"   ⚠️  修复失败: {e}")

def check_api_config():
    """检查API配置"""
    print("\n4️⃣ 检查API配置")
    
    try:
        from tradingagents.dataflows.config import get_config
        config = get_config()
        
        print(f"   📋 当前配置:")
        
        # Alpha Vantage
        alpha_config = config.get('alpha_vantage', {})
        if alpha_config:
            print(f"   🔑 Alpha Vantage: 已配置")
            if alpha_config.get('api_key'):
                print(f"       API密钥: {'*' * 8}{alpha_config['api_key'][-4:] if len(alpha_config['api_key']) > 4 else ''}")
            else:
                print(f"       ⚠️  API密钥未设置")
                
            # 建议的免费API密钥获取
            print(f"\n   💡 获取Alpha Vantage API密钥:")
            print(f"      1. 访问: https://www.alphavantage.co/support/#api-key")
            print(f"      2. 注册免费账号")
            print(f"      3. 获取API密钥")
            print(f"      4. 在配置文件中设置")
        else:
            print(f"   ❌ Alpha Vantage: 未配置")
        
        # OpenAI
        openai_config = config.get('openai', {})
        if openai_config:
            print(f"\n   🔑 OpenAI: 已配置")
            if openai_config.get('api_key'):
                print(f"       API密钥: 已设置")
            else:
                print(f"       ⚠️  API密钥未设置")
        else:
            print(f"\n   ❌ OpenAI: 未配置")
            
    except Exception as e:
        print(f"   ⚠️  配置检查失败: {e}")

def create_working_example():
    """创建可工作的示例"""
    print("\n5️⃣ 创建可工作的示例")
    
    example_code = '''
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

def working_example():
    """可工作的示例"""
    
    print("🚀 可工作的集成示例")
    print("=" * 60)
    
    try:
        # 1. 技术数据
        from tradingagents.agents.utils.technical_indicators_tools import get_technical_data
        
        print("📈 获取技术数据...")
        tech_data = get_technical_data(
            symbol="EUR/USD",
            curr_date="2024-12-02",
            look_back_days=30
        )
        
        if tech_data and isinstance(tech_data, dict) and tech_data.get("success"):
            print(f"   ✅ 技术数据获取成功")
            data = tech_data.get("data", {})
            if isinstance(data, list):
                print(f"   📊 数据条数: {len(data)}")
            elif isinstance(data, dict):
                print(f"   📊 数据字段: {list(data.keys())}")
        else:
            print(f"   ❌ 技术数据获取失败")
    
    except Exception as e:
        print(f"   ⚠️  技术数据错误: {e}")
    
    try:
        # 2. 新闻数据
        from tradingagents.dataflows.interface import route_to_vendor
        
        print("📰 获取新闻数据...")
        news_data = route_to_vendor(
            "get_news",
            ticker="EUR/USD",
            limit=5,
            start_date="2024-11-01",
            end_date="2024-11-30"
        )
        
        if news_data:
            print(f"   ✅ 新闻数据获取成功")
            if isinstance(news_data, dict):
                feed = news_data.get("feed", [])
                print(f"   📊 新闻条数: {len(feed)}")
        else:
            print(f"   ❌ 新闻数据获取失败")
    
    except Exception as e:
        print(f"   ⚠️  新闻数据错误: {e}")
    
    try:
        # 3. 权重管理器
        from tradingagents.adaptive_system.weight_manager import AdaptiveWeightManager
        from tradingagents.adaptive_system.config import AdaptiveConfig
        
        print("⚖️  设置权重管理器...")
        config = AdaptiveConfig()
        weight_manager = AdaptiveWeightManager(config)
        
        # 注册分析师
        analysts = [
            ("macro_analyst", "strategic"),
            ("news_analyst", "operational"),
            ("technical_analyst", "tactical")
        ]
        
        for name, layer in analysts:
            weight_manager.register_agent(name, layer)
            weight_manager.update_weight(name, 1.0)  # 初始权重
        
        print(f"   ✅ 注册了 {len(analysts)} 个分析师")
        
        # 获取权重
        weights = weight_manager.get_normalized_weights()
        print(f"   📊 初始权重分配:")
        for analyst, weight in weights.items():
            print(f"     {analyst}: {weight:.1%}")
    
    except Exception as e:
        print(f"   ⚠️  权重管理器错误: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 示例运行完成!")
    print("=" * 60)

if __name__ == "__main__":
    working_example()
'''
    
    # 保存示例文件
    example_file = os.path.join(project_root, "tests", "working_example.py")
    with open(example_file, 'w', encoding='utf-8') as f:
        f.write(example_code)
    
    print(f"   📄 示例代码已保存到: {example_file}")
    print(f"   💡 运行命令: python tests/working_example.py")

def install_missing_packages():
    """安装缺失的包"""
    print("\n6️⃣ 安装缺失的包")
    
    missing_packages = ["pandas-ta"]
    
    for package in missing_packages:
        print(f"   📦 安装 {package}...")
        os.system(f"pip install {package}")
    
    print(f"   ✅ 包安装完成")

def create_config_template():
    """创建配置模板"""
    print("\n7️⃣ 创建配置模板")
    
    config_template = '''
# API配置模板
# 复制此文件为 config_local.py 并填入您的API密钥

# Alpha Vantage (股票/外汇数据)
ALPHA_VANTAGE_API_KEY = "your_alpha_vantage_api_key_here"

# OpenAI (LLM功能)
OPENAI_API_KEY = "your_openai_api_key_here"

# TwelveData (财经数据，可选)
TWELVEDATA_API_KEY = "your_twelvedata_api_key_here"

# FRED (经济数据，可选)
FRED_API_KEY = "your_fred_api_key_here"

# 其他配置
DATA_DIR = "/path/to/your/data/directory"
RESULTS_DIR = "/path/to/your/results/directory"
'''
    
    config_file = os.path.join(project_root, "tests", "config_template.py")
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_template)
    
    print(f"   📄 配置模板已保存到: {config_file}")
    print(f"   💡 请填入您的API密钥并确保配置文件被正确加载")

def main():
    """主函数"""
    print("开始修复问题...\n")
    
    # 安装缺失的包
    install_missing_packages()
    
    # 修复问题
    fix_parameter_names()
    fix_macro_data_calls()
    fix_quantitative_analyst()
    check_api_config()
    create_working_example()
    create_config_template()
    
    print("\n" + "=" * 60)
    print("✅ 修复步骤完成!")
    print("=" * 60)
    
    print("\n📋 下一步操作:")
    print("1. 🔑 获取并配置API密钥")
    print("2. 🔧 运行: python tests/fix_issues.py (应用修复)")
    print("3. 🚀 运行: python tests/working_example.py (测试修复)")
    print("4. 📊 检查配置是否正确加载")

if __name__ == "__main__":
    main()