import os
import requests
import pandas as pd
import json
from datetime import datetime
from io import StringIO

API_BASE_URL = "https://www.alphavantage.co/query"

def get_api_key() -> str:
    """Retrieve the API key for Alpha Vantage from environment variables."""
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise ValueError("ALPHA_VANTAGE_API_KEY environment variable is not set.")
    return api_key

def format_datetime_for_api(date_input) -> str:
    """Convert various date formats to YYYYMMDDTHHMM format required by Alpha Vantage API."""
    if isinstance(date_input, str):
        # If already in correct format, return as-is
        if len(date_input) == 13 and 'T' in date_input:
            return date_input
        # Try to parse common date formats
        try:
            dt = datetime.strptime(date_input, "%Y-%m-%d")
            return dt.strftime("%Y%m%dT0000")
        except ValueError:
            try:
                dt = datetime.strptime(date_input, "%Y-%m-%d %H:%M")
                return dt.strftime("%Y%m%dT%H%M")
            except ValueError:
                raise ValueError(f"Unsupported date format: {date_input}")
    elif isinstance(date_input, datetime):
        return date_input.strftime("%Y%m%dT%H%M")
    else:
        raise ValueError(f"Date must be string or datetime object, got {type(date_input)}")

class AlphaVantageRateLimitError(Exception):
    """Exception raised when Alpha Vantage API rate limit is exceeded."""
    pass

# 在 _make_api_request 函数中添加逻辑处理

def _make_api_request(function_name: str, params: dict) -> dict | str:
    """Helper function to make API requests and handle responses.
    
    Returns:
        dict for JSON responses, str for CSV responses
    """
    # Create a copy of params to avoid modifying the original
    api_params = params.copy()
    api_params.update({
        "function": function_name,
        "apikey": get_api_key(),
        "source": "trading_agents",
    })
    
    # Handle entitlement parameter if present in params or global variable
    current_entitlement = globals().get('_current_entitlement')
    entitlement = api_params.get("entitlement") or current_entitlement
    
    if entitlement:
        api_params["entitlement"] = entitlement
    elif "entitlement" in api_params:
        # Remove entitlement if it's None or empty
        api_params.pop("entitlement", None)
    
    response = requests.get(API_BASE_URL, params=api_params)
    response.raise_for_status()

    response_text = response.text
    
    # 关键修改：根据函数类型决定返回格式
    try:
        # 尝试解析为 JSON
        response_json = json.loads(response_text)
        
        # 检查是否有错误信息
        if "Information" in response_json:
            info_message = response_json["Information"]
            if "rate limit" in info_message.lower() or "api key" in info_message.lower():
                raise AlphaVantageRateLimitError(f"Alpha Vantage rate limit exceeded: {info_message}")
        
        # 对于 NEWS_SENTIMENT 函数，总是返回 JSON
        if function_name == "NEWS_SENTIMENT":
            return response_json
        
        # 对于其他函数，如果响应看起来是 JSON 就返回 JSON，否则返回文本
        # 检查是否是常见的 JSON 响应结构
        if isinstance(response_json, dict) and any(key in response_json for key in 
                                                  ['Meta Data', 'Time Series', 'Technical Analysis', 'feed']):
            return response_json
        else:
            # 如果不是常见的 JSON 结构，返回原始文本（可能是 CSV）
            return response_text
            
    except json.JSONDecodeError:
        # Response is not JSON (likely CSV data), which is normal for some endpoints
        return response_text



def _filter_csv_by_date_range(csv_data: str, start_date: str, end_date: str) -> str:
    """
    Filter CSV data to include only rows within the specified date range.

    Args:
        csv_data: CSV string from Alpha Vantage API
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format

    Returns:
        Filtered CSV string
    """
    if not csv_data or csv_data.strip() == "":
        return csv_data

    try:
        # Parse CSV data
        df = pd.read_csv(StringIO(csv_data))

        # 更好的调试方式：检查列结构来判断数据类型
        if len(df.columns) <= 5 and 'open' in df.columns and 'close' in df.columns:
            print("DEBUG: Processing OHLC data (likely forex or stock prices)")
        
        # 或者通过数值范围判断（外汇价格通常在0.5-2.0范围，股票价格更高）
        if not df.empty and 'close' in df.columns:
            sample_price = df['close'].iloc[0]
            if 0.1 < sample_price < 5.0:
                print("DEBUG: Price range suggests forex data")

        # Assume the first column is the date column (timestamp)
        date_col = df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col])

        # Filter by date range
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        filtered_df = df[(df[date_col] >= start_dt) & (df[date_col] <= end_dt)]

        # Convert back to CSV string
        return filtered_df.to_csv(index=False)

    except Exception as e:
        # If filtering fails, return original data with a warning
        print(f"Warning: Failed to filter CSV data by date range: {e}")
        return csv_data