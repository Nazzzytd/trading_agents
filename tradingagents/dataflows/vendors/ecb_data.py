"""
ECB (European Central Bank) Statistical Data Warehouse接口
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any, List
import json

logger = logging.getLogger(__name__)

# ECB SDW配置
ECB_BASE_URL = "https://sdw-wsrest.ecb.europa.eu/service/data"

# 关键指标映射
ECB_SERIES_MAP = {
    # 欧元区利率
    "DFR": {"id": "FM.B.U2.EUR.4F.KR.DFR.LEV", "name": "Deposit facility rate", "freq": "m", "units": "Percent"},
    "MRR": {"id": "FM.B.U2.EUR.4F.KR.MRR_FR.LEV", "name": "Main refinancing operations rate", "freq": "m", "units": "Percent"},
    "MLR": {"id": "FM.B.U2.EUR.4F.KR.MLR_FR.LEV", "name": "Marginal lending facility rate", "freq": "m", "units": "Percent"},
    
    # 欧元区通胀
    "HICP": {"id": "ICP.M.U2.N.000000.4.ANR", "name": "HICP - Overall index, annual rate of change", "freq": "m", "units": "Percent"},
    "HICP_ENERGY": {"id": "ICP.M.U2.N.XEF000.4.ANR", "name": "HICP - Energy, annual rate of change", "freq": "m", "units": "Percent"},
    "HICP_FOOD": {"id": "ICP.M.U2.N.XEFOOD.4.ANR", "name": "HICP - Food, annual rate of change", "freq": "m", "units": "Percent"},
    "HICP_CORE": {"id": "ICP.M.U2.N.XEF0000.4.ANR", "name": "HICP - All-items excluding energy, food, alcohol and tobacco", "freq": "m", "units": "Percent"},
    
    # 欧元区经济增长
    "GDP": {"id": "MNA.Q.Y.I8.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.N", "name": "Gross domestic product at market prices", "freq": "q", "units": "Euro"},
    "INDUSTRIAL_PROD": {"id": "STS.M.I8.Y.PROD.NS0010.4.000", "name": "Industrial production index", "freq": "m", "units": "Index"},
    "UNEMPLOYMENT": {"id": "STS.M.I8.Y.UNEH.RTT000.4.000", "name": "Unemployment rate", "freq": "m", "units": "Percent"},
    "RETAIL_SALES": {"id": "STS.M.I8.Y.RTL.SP000.4.000", "name": "Retail trade", "freq": "m", "units": "Index"},
    
    # 欧洲央行资产负债表
    "BALANCE_SHEET_TOTAL": {"id": "BSI.M.U2.Y.V.M10.X.1.U2.2300.Z01.E", "name": "Eurosystem balance sheet total", "freq": "m", "units": "Euro"},
    "ASSET_PURCHASES": {"id": "BSI.M.U2.Y.V.M10.X.1.U2.2320.Z01.E", "name": "Asset purchase programmes holdings", "freq": "m", "units": "Euro"},
    
    # 货币供应量
    "M3": {"id": "BSI.M.U2.Y.V.M30.X.1.U2.2300.Z01.E", "name": "M3", "freq": "m", "units": "Euro"},
}

def _make_ecb_request(series_key: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    发送ECB API请求
    """
    url = f"{ECB_BASE_URL}/{series_key}"
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"ECB API request failed: {e}")
        return {"error": f"ECB API request failed: {str(e)}"}

def get_ecb_series(series_key: str, start_period: Optional[str] = None, 
                  end_period: Optional[str] = None, detail: str = "dataonly") -> Dict[str, Any]:
    """
    获取ECB数据系列
    
    Args:
        series_key: ECB系列键
        start_period: 开始期间 (YYYY-MM)
        end_period: 结束期间 (YYYY-MM)
        detail: 详细程度 (full/dataonly)
    
    Returns:
        包含系列数据和信息的字典
    """
    logger.info(f"Fetching ECB series: {series_key}")
    
    # 构建参数
    params = {
        "format": "jsondata",
        "detail": detail
    }
    
    if start_period:
        params["startPeriod"] = start_period
    if end_period:
        params["endPeriod"] = end_period
    
    # 获取数据
    data = _make_ecb_request(series_key, params)
    if "error" in data:
        return data
    
    # 解析ECB数据格式
    if "dataSets" not in data or len(data["dataSets"]) == 0:
        return {"error": f"No data found for ECB series {series_key}"}
    
    dataset = data["dataSets"][0]
    series_data = dataset.get("series", {})
    
    if not series_data:
        return {"error": f"No series data found for {series_key}"}
    
    # 获取第一个系列的数据
    first_key = next(iter(series_data.keys()))
    series_info = series_data[first_key]
    observations = series_info.get("observations", {})
    
    # 解析维度信息
    dimensions = data.get("structure", {}).get("dimensions", {}).get("observation", [])
    time_dim = None
    for dim in dimensions:
        if dim.get("id") == "TIME_PERIOD":
            time_dim = dim
            break
    
    # 提取数据点
    data_points = []
    time_values = time_dim.get("values", []) if time_dim else []
    
    for idx, (obs_key, obs_value) in enumerate(observations.items()):
        if idx < len(time_values):
            time_period = time_values[idx].get("name", f"Period_{idx}")
            value = obs_value[0] if isinstance(obs_value, list) and len(obs_value) > 0 else obs_value
            
            try:
                numeric_value = float(value) if value is not None else None
            except (ValueError, TypeError):
                numeric_value = None
            
            data_points.append({
                "period": time_period,
                "value": numeric_value,
                "raw_value": value
            })
    
    # 转换为DataFrame
    df = pd.DataFrame(data_points)
    if not df.empty:
        # 尝试转换日期
        df["date"] = pd.to_datetime(df["period"], errors="coerce")
        df = df.dropna(subset=["value"])
    
    # 准备返回数据
    result = {
        "observations": observations,
        "data_points": data_points,
        "dataframe": df if not df.empty else None,
        "metadata": {
            "series_key": series_key,
            "name": ECB_SERIES_MAP.get(series_key, {}).get("name", series_key),
            "frequency": ECB_SERIES_MAP.get(series_key, {}).get("freq", "Unknown"),
            "units": ECB_SERIES_MAP.get(series_key, {}).get("units", "Unknown"),
            "data_points_count": len(data_points),
            "valid_data_points": len(df) if df is not None else 0,
        }
    }
    
    return result

def format_ecb_data_for_output(series_data: Dict[str, Any], include_stats: bool = True) -> str:
    """
    格式化ECB数据用于输出
    
    Args:
        series_data: get_ecb_series返回的数据
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
    output_lines.append(f"# ECB数据: {metadata.get('name', metadata.get('series_key'))}")
    output_lines.append(f"**系列键**: {metadata.get('series_key')}")
    output_lines.append(f"**频率**: {metadata.get('frequency')}")
    output_lines.append(f"**单位**: {metadata.get('units')}")
    output_lines.append(f"**数据点数**: {metadata.get('data_points_count')}")
    output_lines.append(f"**有效数据点**: {metadata.get('valid_data_points')}")
    output_lines.append("")
    
    if df is not None and not df.empty:
        # 最新数据
        latest_row = df.iloc[-1]
        latest_period = latest_row["period"]
        latest_value = latest_row["value"]
        
        output_lines.append(f"## 最新数据")
        output_lines.append(f"- **期间**: {latest_period}")
        output_lines.append(f"- **数值**: {latest_value:.3f} {metadata.get('units', '')}")
        
        # 前值比较
        if len(df) > 1:
            prev_row = df.iloc[-2]
            prev_value = prev_row["value"]
            change = latest_value - prev_value
            change_pct = (change / prev_value * 100) if prev_value != 0 else 0
            
            output_lines.append(f"- **前值**: {prev_value:.3f} ({prev_row['period']})")
            output_lines.append(f"- **变化**: {change:+.3f} ({change_pct:+.2f}%)")
        
        output_lines.append("")
        
        if include_stats:
            # 统计信息
            output_lines.append(f"## 统计摘要")
            output_lines.append(f"- **数据点数**: {len(df)}")
            
            if "date" in df.columns and not df["date"].isnull().all():
                start_date = df["date"].min()
                end_date = df["date"].max()
                output_lines.append(f"- **时间范围**: {start_date.strftime('%Y-%m')} 至 {end_date.strftime('%Y-%m')}")
            
            output_lines.append(f"- **平均值**: {df['value'].mean():.3f}")
            output_lines.append(f"- **中位数**: {df['value'].median():.3f}")
            output_lines.append(f"- **标准差**: {df['value'].std():.3f}")
            output_lines.append(f"- **最小值**: {df['value'].min():.3f} ({df.loc[df['value'].idxmin(), 'period']})")
            output_lines.append(f"- **最大值**: {df['value'].max():.3f} ({df.loc[df['value'].idxmax(), 'period']})")
            output_lines.append("")
        
        # 最近数据点
        output_lines.append(f"## 最近10个观测值")
        recent_data = df.tail(10)[["period", "value"]].copy()
        recent_data["value"] = recent_data["value"].apply(lambda x: f"{x:.3f}")
        
        for _, row in recent_data.iterrows():
            output_lines.append(f"- {row['period']}: {row['value']}")
    
    else:
        output_lines.append("## 数据")
        output_lines.append("无有效观测数据")
    
    return "\n".join(output_lines)



def format_ecb_data_for_output(series_data: Dict[str, Any], include_stats: bool = True) -> str:
    """
    格式化ECB数据用于输出
    
    Args:
        series_data: get_ecb_series返回的数据
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
    output_lines.append(f"# ECB数据: {metadata.get('name', metadata.get('series_key'))}")
    output_lines.append(f"**系列键**: {metadata.get('series_key')}")
    output_lines.append(f"**频率**: {metadata.get('frequency')}")
    output_lines.append(f"**单位**: {metadata.get('units')}")
    output_lines.append(f"**数据点数**: {metadata.get('data_points_count')}")
    output_lines.append(f"**有效数据点**: {metadata.get('valid_data_points')}")
    output_lines.append("")
    
    if df is not None and not df.empty:
        # 最新数据
        latest_period = df["period"].iloc[-1]
        latest_value = df["value"].iloc[-1]
        
        output_lines.append(f"## 最新数据")
        output_lines.append(f"- **期间**: {latest_period}")
        output_lines.append(f"- **数值**: {latest_value:.3f} {metadata.get('units', '')}")
        
        # 前值比较
        if len(df) > 1:
            prev_row = df.iloc[-2]
            prev_value = prev_row["value"]
            change = latest_value - prev_value
            change_pct = (change / prev_value * 100) if prev_value != 0 else 0
            
            output_lines.append(f"- **前值**: {prev_value:.3f} ({prev_row['period']})")
            output_lines.append(f"- **变化**: {change:+.3f} ({change_pct:+.2f}%)")
        
        output_lines.append("")
        
        if include_stats:
            # 统计信息
            output_lines.append(f"## 统计摘要")
            output_lines.append(f"- **数据点数**: {len(df)}")
            
            if "date" in df.columns and not df["date"].isnull().all():
                start_date = df["date"].min()
                end_date = df["date"].max()
                output_lines.append(f"- **时间范围**: {start_date.strftime('%Y-%m')} 至 {end_date.strftime('%Y-%m')}")
            
            output_lines.append(f"- **平均值**: {df['value'].mean():.3f}")
            output_lines.append(f"- **中位数**: {df['value'].median():.3f}")
            output_lines.append(f"- **标准差**: {df['value'].std():.3f}")
            output_lines.append(f"- **最小值**: {df['value'].min():.3f} ({df.loc[df['value'].idxmin(), 'period']})")
            output_lines.append(f"- **最大值**: {df['value'].max():.3f} ({df.loc[df['value'].idxmax(), 'period']})")
            output_lines.append("")
        
        # 最近数据点
        output_lines.append(f"## 最近10个观测值")
        recent_data = df.tail(10)[["period", "value"]].copy()
        recent_data["value"] = recent_data["value"].apply(lambda x: f"{x:.3f}")
        
        for _, row in recent_data.iterrows():
            output_lines.append(f"- {row['period']}: {row['value']}")
    
    else:
        output_lines.append("## 数据")
        output_lines.append("无有效观测数据")
    
    return "\n".join(output_lines)

def get_ecb_data_formatted(series_key: str, **kwargs) -> str:
    """
    获取并格式化ECB数据的便捷函数
    """
    series_data = get_ecb_series(series_key=series_key, **kwargs)
    return format_ecb_data_for_output(series_data)