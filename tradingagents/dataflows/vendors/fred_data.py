"""
FRED (Federal Reserve Economic Data) API接口
遵循Alpha Vantage vendor的架构模式
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# FRED API配置
FRED_API_KEY = os.getenv("FRED_API_KEY")
FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# 关键指标映射
FRED_SERIES_MAP = {
    # 美国利率相关
    "FEDFUNDS": {"id": "FEDFUNDS", "name": "Federal Funds Effective Rate", "freq": "m", "units": "Percent"},
    "DFF": {"id": "DFF", "name": "Federal Funds Rate (Daily)", "freq": "d", "units": "Percent"},
    "DGS10": {"id": "DGS10", "name": "10-Year Treasury Constant Maturity Rate", "freq": "d", "units": "Percent"},
    "DGS2": {"id": "DGS2", "name": "2-Year Treasury Constant Maturity Rate", "freq": "d", "units": "Percent"},
    "DGS5": {"id": "DGS5", "name": "5-Year Treasury Constant Maturity Rate", "freq": "d", "units": "Percent"},
    "SOFR": {"id": "SOFR", "name": "Secured Overnight Financing Rate", "freq": "d", "units": "Percent"},
    
    # 美国通胀相关
    "CPIAUCSL": {"id": "CPIAUCSL", "name": "Consumer Price Index for All Urban Consumers: All Items", "freq": "m", "units": "Index"},
    "CPILFESL": {"id": "CPILFESL", "name": "Consumer Price Index for All Urban Consumers: All Items Less Food & Energy", "freq": "m", "units": "Index"},
    "PCEPI": {"id": "PCEPI", "name": "Personal Consumption Expenditures: Chain-type Price Index", "freq": "m", "units": "Index"},
    "PCEPILFE": {"id": "PCEPILFE", "name": "PCE less Food and Energy", "freq": "m", "units": "Index"},
    
    # 美国就业相关
    "UNRATE": {"id": "UNRATE", "name": "Civilian Unemployment Rate", "freq": "m", "units": "Percent"},
    "PAYEMS": {"id": "PAYEMS", "name": "All Employees: Total Nonfarm Payrolls", "freq": "m", "units": "Thousands of Persons"},
    "AWHI": {"id": "AWHI", "name": "Average Weekly Hours of All Employees", "freq": "m", "units": "Hours"},
    "CES0500000003": {"id": "CES0500000003", "name": "Average Hourly Earnings of All Employees", "freq": "m", "units": "Dollars per Hour"},
    
    # 美国经济增长相关
    "GDP": {"id": "GDP", "name": "Gross Domestic Product", "freq": "q", "units": "Billions of Dollars"},
    "GDPC1": {"id": "GDPC1", "name": "Real Gross Domestic Product", "freq": "q", "units": "Billions of Chained 2012 Dollars"},
    "INDPRO": {"id": "INDPRO", "name": "Industrial Production Index", "freq": "m", "units": "Index"},
    "RETAIL": {"id": "RETAIL", "name": "Retail Sales", "freq": "m", "units": "Millions of Dollars"},
    "UMCSENT": {"id": "UMCSENT", "name": "University of Michigan: Consumer Sentiment", "freq": "m", "units": "Index"},
    
    # 贸易与财政
    "BOPGSTB": {"id": "BOPGSTB", "name": "Trade Balance: Goods and Services, Balance of Payments Basis", "freq": "m", "units": "Millions of Dollars"},
    "MTS": {"id": "MTS", "name": "Manufacturers' Trade, Inventories, and Orders", "freq": "m", "units": "Millions of Dollars"},
}

def _make_fred_request(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    发送FRED API请求
    """
    if not FRED_API_KEY:
        logger.error("FRED_API_KEY not found in environment variables")
        return {"error": "FRED_API_KEY not configured"}
    
    # 添加API密钥到参数
    params["api_key"] = FRED_API_KEY
    params["file_type"] = "json"
    
    url = f"{FRED_BASE_URL}/{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"FRED API request failed: {e}")
        return {"error": f"FRED API request failed: {str(e)}"}

def get_fred_series(series_id: str, observation_start: Optional[str] = None, 
                   observation_end: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """
    获取FRED数据系列
    
    Args:
        series_id: FRED系列ID
        observation_start: 开始日期 (yyyy-mm-dd)
        observation_end: 结束日期 (yyyy-mm-dd)
        limit: 最大返回数据点数量
    
    Returns:
        包含系列数据和信息的字典
    """
    logger.info(f"Fetching FRED series: {series_id}")
    
    # 构建参数
    params = {
        "series_id": series_id,
        "limit": str(limit)
    }
    
    if observation_start:
        params["observation_start"] = observation_start
    if observation_end:
        params["observation_end"] = observation_end
    
    # 获取系列信息
    series_info = _make_fred_request("series", params)
    if "error" in series_info:
        return series_info
    
    if "seriess" not in series_info or len(series_info["seriess"]) == 0:
        return {"error": f"Series {series_id} not found"}
    
    series_data = series_info["seriess"][0]
    
    # 获取观测数据
    obs_params = params.copy()
    obs_params.pop("limit", None)  # observations接口不支持limit参数
    
    observations_data = _make_fred_request("series/observations", obs_params)
    if "error" in observations_data:
        return observations_data
    
    # 处理观测数据
    if "observations" not in observations_data:
        return {"error": f"No observations found for series {series_id}"}
    
    observations = observations_data["observations"]
    
    # 转换为DataFrame
    df = pd.DataFrame(observations)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
    
    # 准备返回数据
    result = {
        "series_info": series_data,
        "observations": observations,
        "dataframe": df if not df.empty else None,
        "metadata": {
            "series_id": series_id,
            "name": series_data.get("title", series_id),
            "frequency": series_data.get("frequency", "Unknown"),
            "units": series_data.get("units", "Unknown"),
            "seasonal_adjustment": series_data.get("seasonal_adjustment", "Unknown"),
            "last_updated": series_data.get("last_updated", "Unknown"),
            "observation_start": series_data.get("observation_start", "Unknown"),
            "observation_end": series_data.get("observation_end", "Unknown"),
        }
    }
    
    return result

def get_fred_series_list(search_text: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    搜索FRED数据系列
    
    Args:
        search_text: 搜索文本
        limit: 最大返回系列数量
    
    Returns:
        系列列表
    """
    params = {
        "limit": str(limit),
        "order_by": "popularity",
        "sort_order": "desc"
    }
    
    if search_text:
        params["search_text"] = search_text
    
    result = _make_fred_request("series/search", params)
    
    if "error" in result:
        return []
    
    return result.get("seriess", [])

def get_fred_category_series(category_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """
    获取特定类别的FRED系列
    
    Args:
        category_id: FRED类别ID
        limit: 最大返回系列数量
    
    Returns:
        系列列表
    """
    params = {
        "category_id": str(category_id),
        "limit": str(limit)
    }
    
    result = _make_fred_request("category/series", params)
    
    if "error" in result:
        return []
    
    return result.get("seriess", [])

def format_fred_data_for_output(series_data: Dict[str, Any], include_stats: bool = True) -> str:
    """
    格式化FRED数据用于输出
    
    Args:
        series_data: get_fred_series返回的数据
        include_stats: 是否包含统计信息
    
    Returns:
        格式化的字符串
    """
    if "error" in series_data:
        return f"Error: {series_data['error']}"
    
    metadata = series_data.get("metadata", {})
    df = series_data.get("dataframe")
    
    output_lines = []
    
    # 基本信息
    output_lines.append(f"# FRED数据: {metadata.get('name', metadata.get('series_id'))}")
    output_lines.append(f"**系列ID**: {metadata.get('series_id')}")
    output_lines.append(f"**频率**: {metadata.get('frequency')}")
    output_lines.append(f"**单位**: {metadata.get('units')}")
    output_lines.append(f"**季节调整**: {metadata.get('seasonal_adjustment')}")
    output_lines.append(f"**最后更新**: {metadata.get('last_updated')}")
    output_lines.append("")
    
    if df is not None and not df.empty:
        # 最新数据
        latest_date = df["date"].iloc[-1].strftime("%Y-%m-%d")
        latest_value = df["value"].iloc[-1]
        
        output_lines.append(f"## 最新数据")
        output_lines.append(f"- **日期**: {latest_date}")
        output_lines.append(f"- **数值**: {latest_value:.3f} {metadata.get('units', '')}")
        
        # 前值比较
        if len(df) > 1:
            prev_value = df["value"].iloc[-2]
            change = latest_value - prev_value
            change_pct = (change / prev_value * 100) if prev_value != 0 else 0
            
            output_lines.append(f"- **前值**: {prev_value:.3f}")
            output_lines.append(f"- **变化**: {change:+.3f} ({change_pct:+.2f}%)")
        
        output_lines.append("")
        
        if include_stats:
            # 统计信息
            output_lines.append(f"## 统计摘要")
            output_lines.append(f"- **数据点数**: {len(df)}")
            output_lines.append(f"- **时间范围**: {df['date'].iloc[0].strftime('%Y-%m-%d')} 至 {latest_date}")
            output_lines.append(f"- **平均值**: {df['value'].mean():.3f}")
            output_lines.append(f"- **中位数**: {df['value'].median():.3f}")
            output_lines.append(f"- **标准差**: {df['value'].std():.3f}")
            output_lines.append(f"- **最小值**: {df['value'].min():.3f} ({df.loc[df['value'].idxmin(), 'date'].strftime('%Y-%m-%d')})")
            output_lines.append(f"- **最大值**: {df['value'].max():.3f} ({df.loc[df['value'].idxmax(), 'date'].strftime('%Y-%m-%d')})")
            output_lines.append("")
        
        # 最近数据点
        output_lines.append(f"## 最近10个观测值")
        recent_data = df.tail(10)[["date", "value"]].copy()
        recent_data["date"] = recent_data["date"].dt.strftime("%Y-%m-%d")
        recent_data["value"] = recent_data["value"].apply(lambda x: f"{x:.3f}")
        
        for _, row in recent_data.iterrows():
            output_lines.append(f"- {row['date']}: {row['value']}")
    
    else:
        output_lines.append("## 数据")
        output_lines.append("无有效观测数据")
    
    return "\n".join(output_lines)



def format_fred_data_for_output(series_data: Dict[str, Any], include_stats: bool = True) -> str:
    """
    格式化FRED数据用于输出
    
    Args:
        series_data: get_fred_series返回的数据
        include_stats: 是否包含统计信息
    
    Returns:
        格式化的字符串
    """
    if "error" in series_data:
        return f"Error: {series_data['error']}"
    
    metadata = series_data.get("metadata", {})
    df = series_data.get("dataframe")
    
    output_lines = []
    
    # 基本信息
    output_lines.append(f"# FRED数据: {metadata.get('name', metadata.get('series_id'))}")
    output_lines.append(f"**系列ID**: {metadata.get('series_id')}")
    output_lines.append(f"**频率**: {metadata.get('frequency')}")
    output_lines.append(f"**单位**: {metadata.get('units')}")
    output_lines.append(f"**季节调整**: {metadata.get('seasonal_adjustment')}")
    output_lines.append(f"**最后更新**: {metadata.get('last_updated')}")
    output_lines.append("")
    
    if df is not None and not df.empty:
        # 最新数据
        latest_date = df["date"].iloc[-1].strftime("%Y-%m-%d")
        latest_value = df["value"].iloc[-1]
        
        output_lines.append(f"## 最新数据")
        output_lines.append(f"- **日期**: {latest_date}")
        output_lines.append(f"- **数值**: {latest_value:.3f} {metadata.get('units', '')}")
        
        # 前值比较
        if len(df) > 1:
            prev_value = df["value"].iloc[-2]
            change = latest_value - prev_value
            change_pct = (change / prev_value * 100) if prev_value != 0 else 0
            
            output_lines.append(f"- **前值**: {prev_value:.3f}")
            output_lines.append(f"- **变化**: {change:+.3f} ({change_pct:+.2f}%)")
        
        output_lines.append("")
        
        if include_stats:
            # 统计信息
            output_lines.append(f"## 统计摘要")
            output_lines.append(f"- **数据点数**: {len(df)}")
            output_lines.append(f"- **时间范围**: {df['date'].iloc[0].strftime('%Y-%m-%d')} 至 {latest_date}")
            output_lines.append(f"- **平均值**: {df['value'].mean():.3f}")
            output_lines.append(f"- **中位数**: {df['value'].median():.3f}")
            output_lines.append(f"- **标准差**: {df['value'].std():.3f}")
            output_lines.append(f"- **最小值**: {df['value'].min():.3f} ({df.loc[df['value'].idxmin(), 'date'].strftime('%Y-%m-%d')})")
            output_lines.append(f"- **最大值**: {df['value'].max():.3f} ({df.loc[df['value'].idxmax(), 'date'].strftime('%Y-%m-%d')})")
            output_lines.append("")
        
        # 最近数据点
        output_lines.append(f"## 最近10个观测值")
        recent_data = df.tail(10)[["date", "value"]].copy()
        recent_data["date"] = recent_data["date"].dt.strftime("%Y-%m-%d")
        recent_data["value"] = recent_data["value"].apply(lambda x: f"{x:.3f}")
        
        for _, row in recent_data.iterrows():
            output_lines.append(f"- {row['date']}: {row['value']}")
    
    else:
        output_lines.append("## 数据")
        output_lines.append("无有效观测数据")
    
    return "\n".join(output_lines)

def get_fred_data_formatted(series_id: str, **kwargs) -> str:
    """
    获取并格式化FRED数据的便捷函数
    """
    series_data = get_fred_series(series_id=series_id, **kwargs)
    return format_fred_data_for_output(series_data)