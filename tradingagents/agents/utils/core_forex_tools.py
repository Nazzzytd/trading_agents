# /tradingagents/agents/utils/core_forex_tools.py
from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor

@tool
def get_forex_data(
    symbol: Annotated[str, "Forex pair symbol, e.g. EUR/USD, GBP/JPY, XAU/USD"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve forex price data (OHLCV) for a given forex pair.
    Uses the configured core_forex_apis vendor (TwelveData for forex).
    
    Supported forex pairs:
    - EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, USD/CAD, NZD/USD
    - EUR/GBP, EUR/JPY, GBP/JPY, XAU/USD (Gold)
    
    Args:
        symbol (str): Forex pair symbol, e.g. EUR/USD, GBP/JPY, XAU/USD
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
        
    Returns:
        str: A formatted dataframe containing the forex OHLCV price data for the specified pair in the specified date range.
    """
    return route_to_vendor("get_forex_data", symbol, start_date, end_date)