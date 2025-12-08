"""
Alpha Vantage Economic Calendar API接口
"""
from .alpha_vantage_common import _make_api_request, format_datetime_for_api
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

def get_economic_calendar_av(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    importance: Optional[str] = None,
    countries: Optional[str] = None,
    limit: Optional[int] = 50
) -> Dict[str, Any]:
    """
    获取经济日历数据 - Alpha Vantage版本
    
    Args:
        from_date: 开始日期 yyyy-mm-dd
        to_date: 结束日期 yyyy-mm-dd
        importance: 重要性 (high, medium, low)
        countries: 国家代码，逗号分隔 (US,EU,JP,CN等)
        limit: 限制返回数量
    
    Returns:
        经济日历数据
    """
    params = {}
    
    # 处理时间参数
    if from_date:
        try:
            # Alpha Vantage需要YYYYMMDD格式
            dt = datetime.strptime(from_date, "%Y-%m-%d")
            params["from"] = dt.strftime("%Y%m%d")
        except Exception as e:
            logger.warning(f"Failed to format from_date {from_date}: {e}")
    
    if to_date:
        try:
            dt = datetime.strptime(to_date, "%Y-%m-%d")
            params["to"] = dt.strftime("%Y%m%d")
        except Exception as e:
            logger.warning(f"Failed to format to_date {to_date}: {e}")
    
    # 其他参数
    if importance:
        params["importance"] = importance
    
    if countries:
        params["countries"] = countries
    
    if limit:
        params["limit"] = str(limit)
    
    logger.debug(f"AlphaVantage economic calendar params: {params}")
    
    try:
        # Alpha Vantage的ECONOMIC_CALENDAR函数
        return _make_api_request("ECONOMIC_CALENDAR", params)
    except Exception as e:
        logger.error(f"Error calling Alpha Vantage economic calendar: {e}")
        return {"error": f"Alpha Vantage API error: {str(e)}", "data": []}

def format_economic_calendar_for_display(calendar_data: Dict[str, Any]) -> str:
    """
    格式化经济日历数据用于显示
    
    Args:
        calendar_data: get_economic_calendar_av返回的数据
    
    Returns:
        格式化的字符串报告
    """
    if "error" in calendar_data:
        return f"Error retrieving economic calendar: {calendar_data['error']}"
    
    # Alpha Vantage返回的数据结构
    events = []
    
    # 尝试不同的数据结构
    if "data" in calendar_data and isinstance(calendar_data["data"], list):
        events = calendar_data["data"]
    elif isinstance(calendar_data, list):
        events = calendar_data
    elif "Economic Calendar Data" in calendar_data:
        # 某些情况下返回这种结构
        events = calendar_data.get("Economic Calendar Data", [])
    else:
        # 尝试直接解析为事件列表
        for key, value in calendar_data.items():
            if isinstance(value, list):
                events = value
                break
    
    if not events:
        return "No upcoming economic events found from Alpha Vantage API"
    
    # 按日期分组
    events_by_date = {}
    for event in events:
        # 尝试不同的日期字段
        date = event.get("date") or event.get("Date") or event.get("timestamp") or "Unknown"
        if date not in events_by_date:
            events_by_date[date] = []
        events_by_date[date].append(event)
    
    output_lines = []
    output_lines.append("# 经济日历 - Alpha Vantage API")
    output_lines.append(f"**事件总数**: {len(events)}")
    output_lines.append(f"**数据获取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output_lines.append(f"**数据源**: Alpha Vantage ECONOMIC_CALENDAR API")
    output_lines.append("")
    
    # 按日期排序
    sorted_dates = sorted(events_by_date.keys())
    
    for date in sorted_dates[:15]:  # 显示最近15天的数据
        day_events = events_by_date[date]
        output_lines.append(f"## {date}")
        
        for event in day_events:
            # 尝试不同的字段名
            name = event.get("event") or event.get("Event") or event.get("name") or "Unknown Event"
            country = event.get("country") or event.get("Country") or event.get("region") or "Unknown"
            currency = event.get("currency") or event.get("Currency") or ""
            importance = event.get("importance") or event.get("Importance") or "medium"
            
            # 重要性标记
            if importance == "high" or importance == "High":
                importance_marker = "🔥"
                importance_text = "高影响"
            elif importance == "medium" or importance == "Medium":
                importance_marker = "⚠️"
                importance_text = "中影响"
            else:
                importance_marker = "ℹ️"
                importance_text = "低影响"
            
            # 实际值、预测值、前值
            actual = event.get("actual") or event.get("Actual") or "N/A"
            previous = event.get("previous") or event.get("Previous") or "N/A"
            forecast = event.get("forecast") or event.get("Forecast") or "N/A"
            
            output_lines.append(f"- **{importance_marker} {name}** ({importance_text})")
            output_lines.append(f"  国家: {country} | 货币: {currency}")
            
            # 添加数据值
            data_info = []
            if actual != "N/A" and str(actual) != "None":
                data_info.append(f"实际值: {actual}")
            if forecast != "N/A" and str(forecast) != "None":
                data_info.append(f"预测值: {forecast}")
            if previous != "N/A" and str(previous) != "None":
                data_info.append(f"前值: {previous}")
            
            if data_info:
                output_lines.append(f"  {' | '.join(data_info)}")
            
            # 事件时间
            time_val = event.get("time") or event.get("Time") or event.get("timestamp")
            if time_val and str(time_val) != "None":
                output_lines.append(f"  时间: {time_val}")
            
            output_lines.append("")  # 空行分隔
    
    return "\n".join(output_lines)

def get_economic_calendar_formatted(
    days_ahead: int = 30,
    importance: Optional[str] = None,
    countries: Optional[str] = None,
    limit: Optional[int] = 100,
    **kwargs
) -> str:
    """
    获取并格式化经济日历数据的便捷函数
    
    Args:
        days_ahead: 未来多少天的数据
        importance: 重要性过滤
        countries: 国家过滤
        limit: 限制数量
        **kwargs: 其他参数
    
    Returns:
        格式化的日历报告
    """
    try:
        # 计算日期范围
        today = datetime.now().strftime("%Y-%m-%d")
        future_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        
        logger.info(f"Fetching economic calendar from {today} to {future_date}")
        
        # 获取数据
        calendar_data = get_economic_calendar_av(
            from_date=today,
            to_date=future_date,
            importance=importance,
            countries=countries or "US,EU,JP,CN,GB,CA,AU",  # 主要经济体
            limit=limit
        )
        
        # 格式化输出
        return format_economic_calendar_for_display(calendar_data)
        
    except Exception as e:
        logger.error(f"Error getting economic calendar from Alpha Vantage: {e}")
        return f"Error retrieving economic calendar from Alpha Vantage: {str(e)}"