"""
宏观经济本地工具函数
"""
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Optional
import pandas as pd
import os
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

def get_central_bank_calendar_local(
    days_ahead: int = 30, 
    **kwargs
) -> str:
    """
    获取央行事件日历 - 本地实现（示例数据）
    """
    try:
        # 首先尝试从本地缓存文件获取
        cache_path = os.path.join(DATA_DIR, "macro_data", "economic_calendar_cache.json")
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cached_data = json.load(f)
                
                # 检查缓存是否过期（1天）
                cache_date = datetime.fromisoformat(cached_data.get('last_updated', '2000-01-01'))
                if (datetime.now() - cache_date).days < 1:
                    return format_calendar_from_cache(cached_data, days_ahead)
            except Exception as e:
                logger.warning(f"Failed to read calendar cache: {e}")
        
        # 如果没有缓存或缓存过期，生成示例数据
        today = datetime.now()
        
        calendar = f"""
# 央行与经济数据日历
**生成时间**: {today.strftime('%Y-%m-%d %H:%M:%S')}
**时间范围**: {today.strftime('%Y-%m-%d')} 至 {(today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')}
**数据状态**: 示例数据（建议集成真实经济日历API）

## 主要央行利率决议
- **美联储 (FOMC)**: 每6-8周会议，关注点阵图和新闻发布会
- **欧洲央行 (ECB)**: 每6周会议，关注拉加德新闻发布会
- **日本央行 (BOJ)**: 每月会议，关注收益率曲线控制调整
- **英国央行 (BOE)**: 每6周会议，关注通胀报告

## 重要经济数据发布（示例时间）
- **美国非农就业数据**: 每月第一个周五 20:30 UTC
- **美国CPI通胀数据**: 每月中旬 12:30 UTC
- **欧元区HICP通胀**: 每月最后工作日 10:00 UTC
- **中国PMI数据**: 每月最后一天 01:00 UTC

## 示例近期事件
"""
        
        # 生成示例事件
        for i in range(min(days_ahead, 15)):
            event_date = today + timedelta(days=i)
            events = []
            
            # 根据日期添加示例事件
            if i % 7 == 0:  # 每周一
                events.append("主要央行官员讲话")
            if i % 14 == 5:  # 每两周的周五
                events.append("美国非农就业数据")
            if i % 30 == 12:  # 每月12号左右
                events.append("美国CPI数据发布")
            if i % 30 == 18:  # 每月18号左右
                events.append("美联储利率决议")
            
            if events:
                calendar += f"- **{event_date.strftime('%Y-%m-%d')}**: {', '.join(events)}\n"
        
        calendar += f"""
## 集成建议
1. **推荐数据源**: 
   - ForexFactory API（专业外汇日历）
   - Investing.com经济日历
   - Bloomberg Terminal（企业级）
   - 各国央行官方网站

2. **实现建议**:
   - 添加经济日历vendor模块
   - 定期爬取或订阅API更新
   - 设置事件提醒和自动刷新

## 当前可用数据源
✅ FRED (美国经济数据) - 实时API
✅ ECB SDW (欧元区经济数据) - 实时API
⏳ 经济日历API (待集成)
✅ 本地缓存支持 (已实现)

## 数据更新频率
- 央行利率决议: 实时更新
- 经济数据: 按发布时间表
- 市场预期: 持续变化
- 突发事件: 实时监控
        """
        
        return calendar.strip()
        
    except Exception as e:
        logger.error(f"Error generating central bank calendar: {e}")
        return f"Error generating central bank calendar: {str(e)}"

def format_calendar_from_cache(cached_data: Dict[str, Any], days_ahead: int) -> str:
    """从缓存数据格式化日历"""
    today = datetime.now()
    
    calendar = f"""
# 央行与经济数据日历（缓存数据）
**数据更新时间**: {cached_data.get('last_updated', 'Unknown')}
**时间范围**: {today.strftime('%Y-%m-%d')} 至 {(today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')}
**数据来源**: {cached_data.get('source', 'Local Cache')}

## 近期重要事件
"""
    
    events = cached_data.get('events', [])
    for event in events[:10]:  # 显示前10个事件
        calendar += f"- **{event.get('date', 'Unknown')}**: {event.get('event', '')} ({event.get('impact', 'Medium')} impact)\n"
    
    calendar += f"""
## 缓存信息
- **事件总数**: {len(events)}
- **缓存有效性**: 24小时
- **下次更新**: {(datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M')}

## 数据说明
缓存数据可能不完全实时，重大事件前建议手动刷新。
"""
    
    return calendar.strip()

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

# 辅助函数：保存日历缓存
def save_calendar_cache(calendar_data: Dict[str, Any]):
    """保存日历数据到缓存"""
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