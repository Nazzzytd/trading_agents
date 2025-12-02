# /Users/fr./Downloads/TradingAgents-main/set_production_config.py

import sys
import os
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def set_production_config():
    """设置生产环境配置（单供应商）"""
    
    print("设置生产环境配置...")
    print("=" * 60)
    
    config_path = os.path.join(os.path.dirname(__file__), 
                              "tradingagents/default_config.py")
    
    if not os.path.exists(config_path):
        print(f"配置文件不存在: {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        import re
        
        # 更新配置
        changes = []
        
        # 1. 更新 tool_vendors.get_news 为单供应商
        tool_vendors_pattern = r'("tool_vendors"\s*:\s*\{[^}]*"get_news"\s*:\s*)"[^"]*"'
        
        if re.search(tool_vendors_pattern, content, re.DOTALL):
            content = re.sub(tool_vendors_pattern, r'\1"alpha_vantage"', content, flags=re.DOTALL)
            changes.append("tool_vendors.get_news: 'alpha_vantage'")
        
        # 2. 更新 data_vendors.news_data 为单供应商
        data_vendors_pattern = r'("data_vendors"\s*:\s*\{[^}]*"news_data"\s*:\s*)"[^"]*"'
        
        if re.search(data_vendors_pattern, content, re.DOTALL):
            content = re.sub(data_vendors_pattern, r'\1"alpha_vantage"', content, flags=re.DOTALL)
            changes.append("data_vendors.news_data: 'alpha_vantage'")
        
        # 写入更新
        with open(config_path, 'w') as f:
            f.write(content)
        
        if changes:
            print("✅ 配置更新成功!")
            for change in changes:
                print(f"   • {change}")
            
            print("\n生产配置说明:")
            print("   • 主要供应商: AlphaVantage（快速、结构化数据）")
            print("   • 备用机制: 系统自动回退到OpenAI（如果AlphaVantage失败）")
            print("   • 性能优化: 不等待OpenAI响应，除非必要")
            
            return True
        else:
            print("⚠ 未找到需要更新的配置项")
            return False
            
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_production_config():
    """验证生产配置"""
    
    print("\n验证生产配置...")
    print("=" * 60)
    
    try:
        from tradingagents.dataflows.config import get_config
        
        config = get_config()
        
        print("1. 工具供应商配置:")
        tool_news = config.get('tool_vendors', {}).get('get_news', '未设置')
        print(f"   tool_vendors.get_news: {tool_news}")
        
        print("\n2. 数据供应商配置:")
        data_news = config.get('data_vendors', {}).get('news_data', '未设置')
        print(f"   data_vendors.news_data: {data_news}")
        
        print("\n3. 测试工具调用...")
        from tradingagents.agents.utils.news_data_tools import get_news
        
        # 测试调用
        result = get_news.invoke({"limit": 3})
        
        print(f"   返回类型: {type(result)}")
        
        if isinstance(result, dict):
            print("   ✅ 配置正确: 返回结构化数据（字典）")
            print(f"   新闻数量: {result.get('items', 'N/A')}")
        else:
            print("   ⚠ 返回类型异常，可能是配置未生效")
            
        return tool_news == 'alpha_vantage' and isinstance(result, dict)
        
    except Exception as e:
        print(f"验证失败: {e}")
        return False

def test_production_performance():
    """测试生产环境性能"""
    
    print("\n测试生产环境性能...")
    print("=" * 60)
    
    try:
        from tradingagents.agents.utils.news_data_tools import get_news
        
        import time
        
        # 多次测试取平均值
        test_cases = [
            ("少量数据", {"limit": 3}),
            ("中等数据", {"limit": 10}),
            ("指定货币对", {"ticker": "EUR/USD", "limit": 5}),
        ]
        
        for name, params in test_cases:
            print(f"\n测试: {name}")
            print(f"参数: {params}")
            
            times = []
            for i in range(3):  # 测试3次
                start = time.time()
                result = get_news.invoke(params)
                elapsed = time.time() - start
                times.append(elapsed)
                
                if i == 0:  # 第一次显示详细信息
                    print(f"   返回类型: {type(result)}")
                    if isinstance(result, dict):
                        print(f"   新闻数量: {result.get('items', 'N/A')}")
            
            avg_time = sum(times) / len(times)
            print(f"   平均耗时: {avg_time:.2f}秒")
            print(f"   性能: {'优秀' if avg_time < 2 else '良好' if avg_time < 5 else '一般'}")
            
    except Exception as e:
        print(f"性能测试失败: {e}")

if __name__ == "__main__":
    if set_production_config():
        if verify_production_config():
            test_production_performance()