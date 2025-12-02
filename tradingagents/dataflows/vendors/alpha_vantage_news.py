# /Users/fr./Downloads/TradingAgents-main/tradingagents/dataflows/vendors/alpha_vantage_news.py

from .alpha_vantage_common import _make_api_request, format_datetime_for_api
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def get_news(
    ticker: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    topics: Optional[str] = None,
    limit: Optional[int] = None
):
    """Returns live and historical forex market news & sentiment data.
    
    Modified for forex trading - automatically filters by 'forex' topic.
    
    Args:
        ticker: Currency pair (e.g., "EURUSD", "USDJPY") or empty for general forex news.
        start_date: Start date for news search (optional).
        end_date: End date for news search (optional).
        topics: News topics to filter (defaults to "forex" for forex trading).
        limit: Maximum number of news items to return.

    Returns:
        Dictionary containing forex news sentiment data.
    """
    
    params = {}
    
    # 处理时间参数
    if start_date:
        try:
            params["time_from"] = format_datetime_for_api(start_date)
        except Exception as e:
            logger.warning(f"Failed to format start_date {start_date}: {e}")
    
    if end_date:
        try:
            params["time_to"] = format_datetime_for_api(end_date)
        except Exception as e:
            logger.warning(f"Failed to format end_date {end_date}: {e}")
    
    # 设置默认的topics为forex
    params["topics"] = topics if topics else "forex"
    
    # 排序和限制
    params["sort"] = "LATEST"
    params["limit"] = str(limit) if limit else "50"
    
    # 处理货币对格式
    if ticker and str(ticker).strip():
        # 移除斜杠，转换为AlphaVantage格式
        formatted_ticker = str(ticker).replace("/", "").upper()
        params["tickers"] = formatted_ticker
    
    logger.debug(f"AlphaVantage news params: {params}")
    return _make_api_request("NEWS_SENTIMENT", params)