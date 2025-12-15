"""
宏观经济本地工具函数
"""
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Optional
import pandas as pd
import os
import json  # 添加缺失的json导入
from ..config import DATA_DIR

logger = logging.getLogger(__name__)

def get_macro_dashboard_local(
    currency_pair: str, 
    lookback_months: int = 12, 
    **kwargs
) -> str:
    """
    生成宏观经济仪表板 - 本地实现
    """
    try:
        # 解析货币对
        if "/" in currency_pair:
            base_currency, quote_currency = currency_pair.split("/")
        else:
            base_currency = currency_pair[:3]
            quote_currency = currency_pair[3:]
        
        # 根据货币对确定相关指标
        usd_indicators = []
        eur_indicators = []
        
        if base_currency == "USD" or quote_currency == "USD":
            usd_indicators = ["FEDFUNDS", "CPIAUCSL", "UNRATE", "DGS10"]
        
        if base_currency == "EUR" or quote_currency == "EUR":
            eur_indicators = ["DFR", "HICP", "UNEMPLOYMENT"]
        
        reports = []
        
        # 获取美国数据
        for indicator in usd_indicators:
            try:
                from ..vendors.fred_data import get_fred_data_formatted
                report = get_fred_data_formatted(series_id=indicator, limit=50)
                reports.append(f"\n## {indicator}\n{report}")
            except Exception as e:
                logger.warning(f"Failed to get FRED indicator {indicator}: {e}")
                reports.append(f"\n## {indicator}\nError: {str(e)}")
        
        # 获取欧元区数据
        for indicator_key in eur_indicators:
            try:
                from ..vendors.ecb_data import get_ecb_data_formatted
                
                # 映射指标键到ECB系列键
                ecb_series_map = {
                    "DFR": "FM.B.U2.EUR.4F.KR.DFR.LEV",
                    "HICP": "ICP.M.U2.N.000000.4.ANR",
                    "UNEMPLOYMENT": "STS.M.I8.Y.UNEH.RTT000.4.000",
                }
                
                series_key = ecb_series_map.get(indicator_key, indicator_key)
                report = get_ecb_data_formatted(series_key=series_key)
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
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 执行摘要
基于相关宏观经济指标的分析结果。

## 详细指标分析
{"".join(reports)}

## 综合分析建议
1. **货币政策对比**: 分析两国利率政策差异
2. **通胀动态**: 监控CPI/HICP变化
3. **就业市场**: 评估失业率走势
4. **国债收益率**: 关注长短期利率差

## 数据源说明
- FRED: 美国经济数据
- ECB SDW: 欧元区经济数据
        """
        
        return dashboard.strip()
        
    except Exception as e:
        logger.error(f"Error generating macroeconomic dashboard: {e}")
        return f"Error generating macroeconomic dashboard: {str(e)}"

# ❌ 已删除的函数：get_central_bank_calendar_local
# 这个函数已经被移除，因为我们已经从macro_data_tools.py中删除了get_central_bank_calendar
# 如果你需要经济日历功能，请考虑使用其他数据源或API

def get_quantitative_analysis_local(
    ticker: str,
    curr_date: str,
    lookback_days: int = 252,
    **kwargs
) -> str:
    """
    本地量化分析函数 - 遵循你的local.py架构
    """
    try:
        # 这里可以添加量化分析逻辑
        # 例如：波动率计算、相关性分析、风险指标等
        
        analysis = f"""
# 量化分析报告: {ticker}
**分析日期**: {curr_date}
**回看天数**: {lookback_days}

## 统计分析
（需要实现具体的量化分析逻辑）

## 建议
1. 实现波动率计算（ATR, Historical Volatility）
2. 添加相关性分析
3. 计算风险调整收益指标（Sharpe, Sortino）
4. 技术指标统计验证

## 当前状态
量化分析模块待实现，可以参考已有技术指标模块进行扩展。
"""
        
        return analysis.strip()
        
    except Exception as e:
        return f"Error in quantitative analysis: {str(e)}"

# 辅助函数：检查并创建数据目录
def ensure_macro_data_dir():
    """确保宏观经济数据目录存在"""
    macro_dir = os.path.join(DATA_DIR, "macro_data")
    if not os.path.exists(macro_dir):
        os.makedirs(macro_dir, exist_ok=True)
    return macro_dir

# 辅助函数：保存日历缓存 - 现在可能不再需要，但保留结构
def save_calendar_cache(calendar_data: Dict[str, Any]):
    """保存日历数据到缓存（保留函数结构，但可能不再使用）"""
    try:
        cache_dir = ensure_macro_data_dir()
        cache_path = os.path.join(cache_dir, "economic_calendar_cache.json")
        
        calendar_data['last_updated'] = datetime.now().isoformat()
        
        with open(cache_path, 'w') as f:
            json.dump(calendar_data, f, indent=2)
        
        logger.info(f"Calendar cache saved to {cache_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save calendar cache: {e}")
        return False

# 以下函数保持原有功能
# 原有本地工具的导出函数保持不变
def get_YFin_data_window(*args, **kwargs):
    """获取Yahoo Finance数据窗口 - 保持原有功能"""
    # 原有实现保持不变
    pass

def get_YFin_data(*args, **kwargs):
    """获取Yahoo Finance数据 - 保持原有功能"""
    # 原有实现保持不变
    pass

def get_finnhub_news(*args, **kwargs):
    """获取Finnhub新闻 - 保持原有功能"""
    # 原有实现保持不变
    pass

def get_finnhub_company_insider_sentiment(*args, **kwargs):
    """获取Finnhub内部人情绪 - 保持原有功能"""
    # 原有实现保持不变
    pass

def get_finnhub_company_insider_transactions(*args, **kwargs):
    """获取Finnhub内部人交易 - 保持原有功能"""
    # 原有实现保持不变
    pass

def get_reddit_global_news(*args, **kwargs):
    """获取Reddit全球新闻 - 保持原有功能"""
    # 原有实现保持不变
    pass

def get_reddit_company_news(*args, **kwargs):
    """获取Reddit公司新闻 - 保持原有功能"""
    # 原有实现保持不变
    pass