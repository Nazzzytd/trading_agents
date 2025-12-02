# /Users/fr./Downloads/TradingAgents-main/test_current_config.py

import sys
import os
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_current_config():
    print("测试当前配置...")
    print("=" * 60)
    
    try:
        from tradingagents.dataflows.config import get_config
        from tradingagents.dataflows.interface import get_vendor, get_category_for_method
        
        config = get_config()
        
        print("1. 当前配置:")
        print(f"   data_vendors.news_data: {config.get('data_vendors', {}).get('news_data', '未设置')}")
        print(f"   tool_vendors.get_news: {config.get('tool_vendors', {}).get('get_news', '未设置')}")
        
        print("\n2. 供应商检测逻辑:")
        category = get_category_for_method("get_news")
        print(f"   get_news的类别: {category}")
        
        vendor_config = get_vendor(category, "get_news")
        print(f"   检测到的供应商配置: {vendor_config}")
        print(f"   供应商列表: {[v.strip() for v in vendor_config.split(',')]}")
        
        print("\n3. 测试工具调用...")
        from tradingagents.agents.utils.news_data_tools import get_news
        
        # 观察调试输出
        print("   调用get_news工具（观察供应商顺序）...")
        result = get_news.invoke({
            "ticker": "",
            "start_date": "2024-12-01",
            "end_date": "2024-12-02",
            "limit": 3
        })
        
        print(f"\n   调用成功!")
        print(f"   返回类型: {type(result)}")
        
        if isinstance(result, dict):
            print(f"   供应商: AlphaVantage")
            print(f"   新闻数量: {result.get('items', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("分析:")
        print("=" * 60)
        
        if ',' in vendor_config:
            print("✅ 配置正确: 多个供应商（逗号分隔）")
            print(f"   主要供应商: {vendor_config.split(',')[0].strip()}")
            print(f"   备用供应商: {vendor_config.split(',')[1].strip() if len(vendor_config.split(',')) > 1 else '无'}")
        else:
            print("⚠ 配置需要优化: 单个供应商")
            print("   建议修改为: 'alpha_vantage,openai'")
            print("   这样可以在AlphaVantage失败时自动使用OpenAI")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_current_config()