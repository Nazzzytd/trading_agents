# tradingagents/agents/utils/tool_helpers.py
"""
工具调用辅助函数
处理StructuredTool对象的正确调用方式
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def call_tool(tool, **kwargs) -> Any:
    """
    统一调用工具，处理StructuredTool和普通函数的差异
    
    Args:
        tool: 工具对象（可能是StructuredTool或普通函数）
        **kwargs: 工具参数
    
    Returns:
        工具调用结果
    """
    try:
        # 检查是否是StructuredTool
        if hasattr(tool, 'invoke'):
            logger.debug(f"调用StructuredTool: {tool.name}")
            return tool.invoke(kwargs)
        elif callable(tool):
            logger.debug(f"调用普通函数: {tool.__name__}")
            return tool(**kwargs)
        else:
            logger.error(f"无法调用的工具类型: {type(tool)}")
            return f"❌ 工具调用失败: 不支持的工具类型 {type(tool)}"
    except Exception as e:
        logger.error(f"工具调用失败: {e}")
        return f"❌ 工具调用失败: {str(e)}"

def call_technical_indicators_tool(symbol: str, curr_date: str, look_back_days: int = 60) -> str:
    """调用技术指标工具"""
    from .technical_indicators_tools import get_technical_indicators_data
    return call_tool(
        get_technical_indicators_data,
        symbol=symbol,
        curr_date=curr_date,
        look_back_days=look_back_days
    )

def call_news_tool(ticker: str = "", start_date: str = None, end_date: str = None, 
                  limit: int = None) -> str:
    """调用新闻工具"""
    from .news_data_tools import get_news
    params = {"ticker": ticker}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if limit:
        params["limit"] = limit
    return call_tool(get_news, **params)

def call_forex_tool(symbol: str, start_date: str, end_date: str) -> str:
    """调用外汇工具"""
    from .core_forex_tools import get_forex_data
    return call_tool(
        get_forex_data,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date
    )