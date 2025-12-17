# tradingagents/agents/utils/agent_utils.py - 修复版本

from langchain_core.messages import HumanMessage, RemoveMessage

# Import tools from separate utility files
from tradingagents.agents.utils.core_forex_tools import (
    get_forex_data
)

from tradingagents.agents.utils.technical_indicators_tools import (
    get_indicators
)

from tradingagents.agents.utils.news_data_tools import (
    get_news
)

# 量化分析工具 - 只导入实际存在的函数
from tradingagents.agents.utils.quant_data_tools import (
    get_risk_metrics_data,
    get_volatility_data,
    simple_forex_data
)

# ✅ 添加宏观经济工具导入
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


def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility"""
        messages = state["messages"]
        
        # Remove all messages
        removal_operations = [RemoveMessage(id=m.id) for m in messages]
        
        # Add a minimal placeholder message
        placeholder = HumanMessage(content="Continue")
        
        return {"messages": removal_operations + [placeholder]}
    
    return delete_messages