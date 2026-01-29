# /Users/fr./Downloads/TradingAgents-main/quick_fix_trading_graph.py

import os
import re

def quick_fix():
    """快速修复 trading_graph.py"""
    file_path = "/Users/fr./Downloads/TradingAgents-main/tradingagents/graph/trading_graph.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到导入agent_utils的部分
    old_import_pattern = r'from tradingagents\.agents\.utils\.agent_utils import[\s\S]*?\)'
    old_import_match = re.search(old_import_pattern, content)
    
    if old_import_match:
        print("找到旧的导入语句，正在修复...")
        
        # 新的导入和占位符代码
        new_code = '''# ✅ 修复：直接导入实际存在的函数
from tradingagents.agents.utils.core_forex_tools import get_forex_data
from tradingagents.agents.utils.technical_indicators_tools import get_indicators
from tradingagents.agents.utils.news_data_tools import get_news
from tradingagents.agents.utils.quant_data_tools import (
    get_risk_metrics_data,
    get_volatility_data,
    simple_forex_data
)

# ✅ 尝试导入宏观经济工具
try:
    from tradingagents.agents.utils.macro_data_tools import (
        get_fred_data,
        get_ecb_data,
        get_macro_dashboard
    )
except ImportError:
    # 如果导入失败，创建占位符函数
    def get_fred_data(*args, **kwargs):
        return "FRED data tool not available"
    
    def get_ecb_data(*args, **kwargs):
        return "ECB data tool not available"
    
    def get_macro_dashboard(*args, **kwargs):
        return "Macro dashboard tool not available"

# ✅ 为不存在的函数添加占位符
def get_fundamentals(*args, **kwargs):
    """占位符函数 - fundamentals工具已删除"""
    return {
        "status": "deprecated",
        "message": "Fundamentals tools have been removed. Use macro or technical data instead."
    }

def get_balance_sheet(*args, **kwargs):
    """占位符函数"""
    return {"status": "deprecated", "function": "get_balance_sheet"}

def get_cashflow(*args, **kwargs):
    """占位符函数"""
    return {"status": "deprecated", "function": "get_cashflow"}

def get_income_statement(*args, **kwargs):
    """占位符函数"""
    return {"status": "deprecated", "function": "get_income_statement"}

def get_insider_sentiment(*args, **kwargs):
    """占位符函数"""
    return {"status": "deprecated", "function": "get_insider_sentiment"}

def get_insider_transactions(*args, **kwargs):
    """占位符函数"""
    return {"status": "deprecated", "function": "get_insider_transactions"}

def get_global_news(*args, **kwargs):
    """占位符函数 - 使用本地新闻数据"""
    # 尝试使用现有的get_news函数
    try:
        return get_news(*args, **kwargs)
    except:
        return {"status": "placeholder", "function": "get_global_news"}

# ✅ 从agent_utils导入实际存在的函数
from tradingagents.agents.utils.agent_utils import create_msg_delete'''
        
        # 替换旧的导入
        content = content.replace(old_import_match.group(0), new_code)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ trading_graph.py 已修复")
        return True
    
    # 如果没有找到旧的导入模式，直接添加修复代码在合适的位置
    else:
        print("未找到旧的导入模式，尝试其他方式...")
        
        # 在文件开头附近添加修复代码
        insert_position = content.find('from langgraph.prebuilt import ToolNode')
        if insert_position != -1:
            # 找到下一行的位置
            next_line = content.find('\n', insert_position) + 1
            
            # 构建新内容
            before = content[:next_line]
            after = content[next_line:]
            
            new_content = before + new_code + '\n\n' + after
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ 已添加修复代码")
            return True
    
    return False

if __name__ == "__main__":
    print("快速修复 trading_graph.py")
    print("="*60)
    
    if quick_fix():
        print("\n✅ 修复完成！")
        print("\n现在可以测试: python -m cli.main --help")
    else:
        print("\n❌ 修复失败，可能需要手动编辑")