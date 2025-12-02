# /Users/fr./Downloads/TradingAgents-main/test_fixed_import.py

import sys
import os
from dotenv import load_dotenv
load_dotenv()
# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_import_fix():
    print("测试导入修复...")
    print("=" * 60)
    
    try:
        # 1. 测试从 __init__.py 导入
        print("1. 测试从 agents.__init__ 导入...")
        from tradingagents.agents import create_news_analyst
        print("   ✓ 成功导入 create_news_analyst")
        
        # 2. 测试直接导入
        print("\n2. 测试直接导入 news_analyst...")
        from tradingagents.agents.analysts.news_analyst import create_news_analyst as direct_import
        print("   ✓ 成功直接导入")
        
        # 3. 测试工具导入
        print("\n3. 测试工具导入...")
        from tradingagents.agents.utils.news_data_tools import get_news
        print("   ✓ 成功导入 get_news 工具")
        
        # 4. 测试配置
        print("\n4. 测试配置导入...")
        from tradingagents.dataflows.config import get_config
        config = get_config()
        print(f"   ✓ 配置加载成功")
        print(f"   新闻供应商: {config.get('news_data', {}).get('vendor', '未设置')}")
        
        print("\n" + "=" * 60)
        print("✅ 所有导入测试通过！")
        
        return True
        
    except ImportError as e:
        print(f"✗ 导入错误: {e}")
        print("\n可能的解决方案:")
        print("1. 检查 __init__.py 文件是否存在且内容正确")
        print("2. 检查 news_analyst.py 文件是否存在且包含 create_news_analyst 函数")
        print("3. 检查文件路径和Python路径")
        
        # 显示详细错误
        import traceback
        traceback.print_exc()
        
        return False
        
    except Exception as e:
        print(f"✗ 其他错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tool_functionality():
    print("\n\n测试工具功能...")
    print("=" * 60)
    
    try:
        from tradingagents.agents.utils.news_data_tools import get_news
        
        print("调用 get_news 工具...")
        result = get_news.invoke({
            "ticker": "",
            "start_date": "2024-12-01",
            "end_date": "2024-12-02",
            "limit": 3,
            "vendor_aware": True
        })
        
        print(f"✓ 工具调用成功")
        print(f"返回类型: {type(result)}")
        
        if isinstance(result, dict):
            print(f"供应商: AlphaVantage")
            print(f"新闻数量: {result.get('items', 'N/A')}")
            if 'feed' in result:
                feed = result['feed']
                if isinstance(feed, list):
                    print(f"实际条数: {len(feed)}")
                    if len(feed) > 0:
                        print(f"第一条新闻标题: {feed[0].get('title', 'N/A')[:50]}...")
        else:
            print(f"响应预览: {str(result)[:200]}...")
            
    except Exception as e:
        print(f"✗ 工具测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if test_import_fix():
        test_tool_functionality()