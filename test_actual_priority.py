# /Users/fr./Downloads/TradingAgents-main/test_actual_priority.py

import sys
import os
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_actual_call_order():
    """测试实际的调用顺序"""
    
    print("=" * 60)
    print("测试新闻获取的实际调用顺序")
    print("=" * 60)
    
    # 临时修改日志级别以查看调试信息
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        from tradingagents.agents.utils.news_data_tools import get_news
        
        print("调用 get_news 工具...")
        print("（观察控制台输出，应该显示供应商调用顺序）")
        print("-" * 40)
        
        # 进行一个简单的调用
        result = get_news.invoke({
            "ticker": "",
            "start_date": "2024-12-01",
            "end_date": "2024-12-02",
            "limit": 3
        })
        
        print("\n" + "-" * 40)
        print("调用完成！")
        
        if isinstance(result, dict):
            print(f"成功获取新闻，供应商: AlphaVantage")
            print(f"新闻数量: {result.get('items', 'N/A')}")
        elif isinstance(result, str) and "OpenAI" in result:
            print(f"备用供应商: OpenAI")
            print(f"响应类型: 文本分析")
        else:
            print(f"返回类型: {type(result)}")
            
    except Exception as e:
        print(f"调用失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_actual_call_order()