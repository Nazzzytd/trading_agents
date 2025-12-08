"""
宏观经济数据工具 - 遵循news_data_tools.py的架构模式
调用vendor层的FRED和ECB数据服务
"""
from langchain_core.tools import tool
from typing import Annotated, Dict, List, Optional
from tradingagents.dataflows.interface import route_to_vendor
import logging

logger = logging.getLogger(__name__)

@tool
def get_fred_data(
    series_id: Annotated[str, "FRED series ID (e.g., 'FEDFUNDS', 'CPIAUCSL')"],
    observation_start: Annotated[str, "Start date in yyyy-mm-dd format"] = None,
    observation_end: Annotated[str, "End date in yyyy-mm-dd format"] = None,
    limit: Annotated[int, "Maximum number of observations to return"] = 100
) -> str:
    """
    Retrieve macroeconomic data from FRED (Federal Reserve Economic Data).
    
    Args:
        series_id: FRED series identifier
        observation_start: Start date in yyyy-mm-dd format
        observation_end: End date in yyyy-mm-dd format
        limit: Maximum number of observations to return
        
    Returns:
        str: Formatted string containing FRED data with analysis
    """
    return route_to_vendor(
        "get_fred_data",
        series_id=series_id,
        observation_start=observation_start,
        observation_end=observation_end,
        limit=limit
    )

@tool
def get_ecb_data(
    series_key: Annotated[str, "ECB SDW series key (e.g., 'FM.B.U2.EUR.4F.KR.DFR.LEV')"],
    start_period: Annotated[str, "Start period in YYYY-MM format"] = None,
    end_period: Annotated[str, "End period in YYYY-MM format"] = None,
    detail: Annotated[str, "Detail level (full/dataonly)"] = "dataonly"
) -> str:
    """
    Retrieve macroeconomic data from ECB Statistical Data Warehouse.
    
    Args:
        series_key: ECB SDW series key
        start_period: Start period in YYYY-MM format
        end_period: End period in YYYY-MM format
        detail: Detail level for response
        
    Returns:
        str: Formatted string containing ECB data with analysis
    """
    return route_to_vendor(
        "get_ecb_data",
        series_key=series_key,
        start_period=start_period,
        end_period=end_period,
        detail=detail
    )

@tool
def get_macro_dashboard(
    currency_pair: Annotated[str, "Currency pair (e.g., 'EUR/USD', 'USD/JPY')"],
    lookback_months: Annotated[int, "Number of months to look back"] = 12
) -> str:
    """
    Generate a comprehensive macroeconomic dashboard for a currency pair.
    
    Args:
        currency_pair: Currency pair to analyze
        lookback_months: Number of months to look back
        
    Returns:
        str: Comprehensive macroeconomic analysis report
    """
    try:
        # 解析货币对
        if "/" in currency_pair:
            base_currency, quote_currency = currency_pair.split("/")
        else:
            # 假设是6位代码如EURUSD
            base_currency = currency_pair[:3]
            quote_currency = currency_pair[3:]
        
        # 根据货币对确定相关指标
        usd_indicators = []
        eur_indicators = []
        
        if base_currency == "USD" or quote_currency == "USD":
            usd_indicators = ["FEDFUNDS", "CPIAUCSL", "UNRATE", "DGS10"]
        
        if base_currency == "EUR" or quote_currency == "EUR":
            eur_indicators = ["DFR", "HICP", "UNEMPLOYMENT", "GDP"]
        
        # 收集数据
        reports = []
        
        # 获取美国数据
        for indicator in usd_indicators:
            try:
                # 使用route_to_vendor获取数据
                from tradingagents.dataflows.interface import route_to_vendor
                
                report = route_to_vendor(
                    "get_fred_data",
                    series_id=indicator,
                    limit=50
                )
                reports.append(f"\n## {indicator}\n{report}")
            except Exception as e:
                logger.warning(f"Failed to get FRED indicator {indicator}: {e}")
                reports.append(f"\n## {indicator}\nError: {str(e)}")
        
        # 获取欧元区数据
        for indicator_key in eur_indicators:
            try:
                # 映射指标键到ECB系列键
                ecb_series_map = {
                    "DFR": "FM.B.U2.EUR.4F.KR.DFR.LEV",
                    "HICP": "ICP.M.U2.N.000000.4.ANR",
                    "UNEMPLOYMENT": "STS.M.I8.Y.UNEH.RTT000.4.000",
                    "GDP": "MNA.Q.Y.I8.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.N",
                }
                
                series_key = ecb_series_map.get(indicator_key, indicator_key)
                
                report = route_to_vendor(
                    "get_ecb_data",
                    series_key=series_key
                )
                reports.append(f"\n## {indicator_key}\n{report}")
            except Exception as e:
                logger.warning(f"Failed to get ECB indicator {indicator_key}: {e}")
                reports.append(f"\n## {indicator_key}\nError: {str(e)}")
        
        # 生成仪表板
        if not reports:
            return f"No macroeconomic data available for {currency_pair}"
        
        dashboard = f"""
# 宏观经济仪表板: {currency_pair}
**分析货币对**: {base_currency}/{quote_currency}
**数据源**: FRED + ECB SDW
**指标数量**: {len(reports)}

## 执行摘要
基于相关宏观经济指标的分析结果。

## 详细指标分析
{"".join(reports)}

## 综合分析建议
1. **货币政策对比**: 分析两国利率政策差异
2. **经济增长**: 比较GDP增长趋势
3. **通胀动态**: 监控CPI/HICP变化
4. **就业市场**: 评估失业率走势

## 数据源说明
- FRED: 美国经济数据
- ECB SDW: 欧元区经济数据
- 数据通过统一的vendor架构获取
        """
        
        return dashboard.strip()
        
    except Exception as e:
        logger.error(f"Error generating macro dashboard: {e}")
        return f"Error generating macroeconomic dashboard: {str(e)}"

@tool
def get_central_bank_calendar(
    days_ahead: Annotated[int, "Number of days to look ahead"] = 30
) -> str:
    """
    Get upcoming central bank events and economic data releases.
    
    Args:
        days_ahead: Number of days to look ahead
        
    Returns:
        str: Calendar of central bank events
    """
    # 这里可以后续集成经济日历vendor
    # 目前返回示例数据
    from datetime import datetime, timedelta
    
    today = datetime.now()
    
    calendar = f"""
# 央行与经济数据日历
**时间范围**: {today.strftime('%Y-%m-%d')} 至 {(today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')}

## 示例事件（需集成真实数据源）
- **{today.strftime('%Y-%m-%d')}**: 美联储官员讲话
- **{(today + timedelta(days=2)).strftime('%Y-%m-%d')}**: 美国CPI数据发布
- **{(today + timedelta(days=5)).strftime('%Y-%m-%d')}**: 欧洲央行利率决议
- **{(today + timedelta(days=7)).strftime('%Y-%m-%d')}**: 日本央行政策会议
- **{(today + timedelta(days=10)).strftime('%Y-%m-%d')}**: 美国非农就业数据

## 集成建议
1. 添加经济日历vendor（如ForexFactory、Investing.com）
2. 实现get_economic_calendar工具函数
3. 设置事件提醒和实时更新机制

## 当前架构
- ✅ FRED数据vendor
- ✅ ECB数据vendor  
- ⏳ 经济日历vendor（待实现）
        """
        
    return calendar.strip()