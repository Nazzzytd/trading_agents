# /Users/fr./Downloads/TradingAgents-main/tradingagents/agents/utils/news_data_tools.py

from langchain_core.tools import tool
from typing import Annotated, Optional, Dict, Any
from tradingagents.dataflows.interface import route_to_vendor
from datetime import datetime, timedelta

@tool
def get_news(
    ticker: Annotated[Optional[str], "Currency pair (e.g., 'EUR/USD', 'USD/JPY') or empty for general forex news"] = "",
    start_date: Annotated[Optional[str], "Start date in yyyy-mm-dd format (optional)"] = None,
    end_date: Annotated[Optional[str], "End date in yyyy-mm-dd format (optional)"] = None,
    topics: Annotated[Optional[str], "News topics (e.g., 'forex,economy_macro,central_banks')"] = None,
    limit: Annotated[Optional[int], "Maximum number of news items"] = None,
    vendor_aware: Annotated[Optional[bool], "Whether to adjust parameters based on vendor"] = True
) -> str:
    """
    Retrieve forex market news and sentiment data with vendor-aware optimization.
    
    Automatically adjusts parameters:
    - AlphaVantage: Can handle larger date ranges (7+ days)
    - OpenAI: Uses shorter date ranges (1-2 days) to prevent timeout
    
    Args:
        ticker: Currency pair like 'EUR/USD' or empty for general forex news
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
        topics: Optional topics filter
        limit: Maximum number of news items
        vendor_aware: Whether to optimize parameters based on vendor
    
    Returns:
        str: Formatted string containing forex news with sentiment analysis
    """
    
    # 获取当前配置以确定主要供应商
    from tradingagents.dataflows.config import get_config
    config = get_config()
    
    # 确定主要供应商
    primary_vendor = "alpha_vantage"  # 默认
    if config.get('news_data') and 'vendor' in config['news_data']:
        vendor_config = config['news_data']['vendor']
        if isinstance(vendor_config, str):
            primary_vendor = vendor_config.split(',')[0].strip()
    
    # 根据供应商优化参数
    optimized_params = optimize_parameters_for_vendor(
        primary_vendor=primary_vendor,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        topics=topics,
        limit=limit,
        vendor_aware=vendor_aware
    )
    
    # 调用 route_to_vendor
    return route_to_vendor("get_news", **optimized_params)

def optimize_parameters_for_vendor(
    primary_vendor: str,
    ticker: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    topics: Optional[str] = None,
    limit: Optional[int] = None,
    vendor_aware: bool = True
) -> Dict[str, Any]:
    """
    根据供应商优化请求参数
    
    AlphaVantage: 可以处理较长时间范围，返回结构化数据快
    OpenAI: 需要限制数据量，避免超时
    """
    
    params = {}
    
    # 基本参数
    if ticker is not None:
        params['ticker'] = ticker
    
    # 根据供应商调整时间范围和限制
    if vendor_aware:
        if primary_vendor == 'openai':
            # OpenAI: 限制为最近1-2天，少量数据
            if not start_date and not end_date:
                # 如果没有指定日期，默认最近1天
                end_date_obj = datetime.now()
                start_date_obj = end_date_obj - timedelta(days=1)
                params['start_date'] = start_date_obj.strftime("%Y-%m-%d")
                params['end_date'] = end_date_obj.strftime("%Y-%m-%d")
            elif start_date and end_date:
                # 如果指定了日期，确保不超过2天
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                    days_diff = (end_dt - start_dt).days
                    if days_diff > 2:
                        # 如果超过2天，调整为最近2天
                        params['end_date'] = end_date
                        params['start_date'] = (end_dt - timedelta(days=2)).strftime("%Y-%m-%d")
                except:
                    pass
            
            # OpenAI: 限制数量为5-10条
            if limit is None or limit > 10:
                params['limit'] = 10
            elif limit < 3:
                params['limit'] = 3
        
        else:  # AlphaVantage 或其他
            # AlphaVantage: 可以处理更长时间范围
            if not start_date and not end_date:
                # 默认最近7天
                end_date_obj = datetime.now()
                start_date_obj = end_date_obj - timedelta(days=7)
                params['start_date'] = start_date_obj.strftime("%Y-%m-%d")
                params['end_date'] = end_date_obj.strftime("%Y-%m-%d")
            
            # AlphaVantage: 可以返回更多数据
            if limit is None or limit > 50:
                params['limit'] = 50
    
    else:  # 不进行供应商优化
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if limit is not None:
            params['limit'] = limit
    
    # 其他参数
    if topics is not None:
        params['topics'] = topics
    
    return params


def get_news_direct(
    ticker: Optional[str] = "",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    topics: Optional[str] = None,
    limit: Optional[int] = None,
    vendor_aware: bool = True
) -> Dict[str, Any]:
    """
    直接获取新闻数据（不经过工具封装），返回原始结构化数据
    
    用于需要预加载数据的场景
    """
    from tradingagents.dataflows.config import get_config
    
    config = get_config()
    
    # 确定主要供应商
    primary_vendor = "alpha_vantage"
    if config.get('news_data') and 'vendor' in config['news_data']:
        vendor_config = config['news_data']['vendor']
        if isinstance(vendor_config, str):
            primary_vendor = vendor_config.split(',')[0].strip()
    
    # 根据供应商优化参数
    optimized_params = optimize_parameters_for_vendor(
        primary_vendor=primary_vendor,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        topics=topics,
        limit=limit,
        vendor_aware=vendor_aware
    )
    
    # 直接调用底层函数
    try:
        from tradingagents.dataflows.interface import route_to_vendor
        result = route_to_vendor("get_news", **optimized_params)
        
        # 返回结构化数据
        if isinstance(result, dict):
            return result
        elif isinstance(result, str):
            # 尝试解析字符串
            try:
                import json
                return json.loads(result)
            except:
                # 如果解析失败，返回简单结构
                return {"raw_data": result}
        else:
            return {"data": result}
            
    except Exception as e:
        return {"error": str(e)}