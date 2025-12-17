# tradingagents/dataflows/interface.py

from typing import Annotated
import logging

# 导入vendor模块
from .vendors.twelvedata_data import TwelveDataForex
from .vendors.alpha_vantage import get_forex as get_alpha_vantage_forex
from .vendors.alpha_vantage_common import AlphaVantageRateLimitError

# 导入宏观经济数据vendor
from .vendors.fred_data import get_fred_data_formatted
from .vendors.ecb_data import get_ecb_data_formatted

# 导入openai新闻vendor
from .vendors.openai import get_forex_news_openai

# 修正：从 local.py 导入，而不是 local.macro_tools
from .local import (
    get_macro_dashboard_local,  # 从 local.py 导入
    get_quantitative_analysis_local  # 从 local.py 导入
)

# 导入原有的本地工具
from .local import (
    get_YFin_data_window,
    get_YFin_data,
    get_finnhub_news,
    get_finnhub_company_insider_sentiment,
    get_finnhub_company_insider_transactions,
    get_reddit_global_news,
    get_reddit_company_news
)

# 配置和路由逻辑
from .config import get_config

logger = logging.getLogger(__name__)

# 初始化vendor实例
twelvedata_forex = TwelveDataForex()

# ⚠️ 修改：将量化分析工具的导入移到后面或函数内部
# 原因：quant_data_tools 可能导入 interface，造成循环依赖

# 工具类别定义 - 简化量化分析部分
TOOLS_CATEGORIES = {
    "core_forex_apis": {
        "description": "OHLCV forex price data",
        "tools": [
            "get_forex_data"
        ]
    },
    "technical_indicators": {
        "description": "Technical analysis indicators",
        "tools": [
            "get_indicators"
        ]
    },
    "quantitative_analysis": {
        "description": "Quantitative analysis and risk metrics",
        "tools": [
            "get_risk_metrics_data",       # 核心：风险指标数据
            "get_volatility_data",         # 核心：波动率数据
            "simple_forex_data",           # 简化数据获取（多合一）
            "calculate_risk_metrics"       # 向后兼容的别名
        ]
    },
    "news_data": {
        "description": "Forex news and sentiment data",
        "tools": [
            "get_news"
        ]
    },
    "macroeconomic_data": {
        "description": "Macroeconomic indicators and central bank data",
        "tools": [
            "get_fred_data",        # FRED数据
            "get_ecb_data",         # ECB数据
            "get_macro_dashboard",  # 宏观仪表板
        ]
    }
}

VENDOR_LIST = [
    "local",
    "twelvedata",
    "alpha_vantage",
    "openai",
    "fred",
    "ecb",
    "quant_tools"  # 量化工具vendor
]

# ⚠️ 修改：延迟导入量化工具
_quant_data_tools_imported = False
_quant_tools = {}

def _import_quant_data_tools():
    """延迟导入量化数据工具，避免循环依赖"""
    global _quant_data_tools_imported, _quant_tools
    
    if not _quant_data_tools_imported:
        try:
            from tradingagents.agents.utils.quant_data_tools import (
                get_risk_metrics_data,
                get_volatility_data,
                simple_forex_data
            )
            _quant_tools = {
                "get_risk_metrics_data": get_risk_metrics_data,
                "get_volatility_data": get_volatility_data,
                "simple_forex_data": simple_forex_data,
            }
            _quant_data_tools_imported = True
            logger.info("✓ 成功延迟导入量化数据工具")
        except ImportError as e:
            logger.error(f"导入量化数据工具失败: {e}")
            # 创建占位符函数
            def placeholder_func(*args, **kwargs):
                return f"量化工具导入失败: {e}"
            
            _quant_tools = {
                "get_risk_metrics_data": placeholder_func,
                "get_volatility_data": placeholder_func,
                "simple_forex_data": placeholder_func,
            }
            _quant_data_tools_imported = True

# Vendor方法映射 - 简化版本
VENDOR_METHODS = {
    # core_forex_apis
    "get_forex_data": {
        "twelvedata": twelvedata_forex.get_forex_ohlc,
        "alpha_vantage": get_alpha_vantage_forex,
    },
    
    # technical_indicators
    "get_indicators": {
        "local": lambda *args, **kwargs: "技术指标计算 - 请使用 technical_indicators_tools.py 模块"
    },
    
    # news_data
    "get_news": {
        "openai": get_forex_news_openai,
        "alpha_vantage": lambda ticker, start_date, end_date, **kwargs: 
            f"外汇新闻数据 - {ticker}\n（AlphaVantage新闻API）"
    },
    
    # macroeconomic_data
    "get_fred_data": {
        "fred": get_fred_data_formatted,
    },
    "get_ecb_data": {
        "ecb": get_ecb_data_formatted,
    },
    "get_macro_dashboard": {
        "local": get_macro_dashboard_local,
    },
}

def _initialize_vendor_methods():
    """初始化VENDOR_METHODS，包含延迟导入的量化工具"""
    global VENDOR_METHODS
    
    # 延迟导入量化工具
    _import_quant_data_tools()
    
    # 添加量化分析工具到VENDOR_METHODS
    if _quant_tools:
        VENDOR_METHODS.update({
            # quantitative_analysis - 只保留核心工具
            "get_risk_metrics_data": {
                "quant_tools": _quant_tools.get("get_risk_metrics_data"),
            },
            "get_volatility_data": {
                "quant_tools": _quant_tools.get("get_volatility_data"),
            },
            "simple_forex_data": {
                "quant_tools": _quant_tools.get("simple_forex_data"),
            },
            "calculate_risk_metrics": {
                "quant_tools": lambda ticker, curr_date, lookback_days=252, **kwargs: 
                    _quant_tools.get("get_risk_metrics_data")(ticker, lookback_days, "1day"),
                "local": lambda ticker, curr_date, lookback_days=252, **kwargs: 
                    get_quantitative_analysis_local(ticker, curr_date, lookback_days, **kwargs)
            },
        })

# 初始化VENDOR_METHODS
_initialize_vendor_methods()

# 其余函数保持不变...

def get_category_for_method(method: str) -> str:
    """获取方法所属的类别"""
    for category, info in TOOLS_CATEGORIES.items():
        if method in info["tools"]:
            return category
    raise ValueError(f"Method '{method}' not found in any category")

def get_vendor(category: str, method: str = None) -> str:
    """获取配置的vendor"""
    config = get_config()

    # 首先检查工具级别的配置
    if method:
        tool_vendors = config.get("tool_vendors", {})
        if method in tool_vendors:
            return tool_vendors[method]

    # 回退到类别级别的配置
    return config.get("data_vendors", {}).get(category, "default")

def route_to_vendor(method: str, *args, **kwargs):
    """路由方法调用到相应的vendor实现"""
    try:
        category = get_category_for_method(method)
    except ValueError:
        # 如果找不到方法，可能是因为我们移除了get_central_bank_calendar
        # 处理这个特定情况
        if method == "get_central_bank_calendar":
            logger.warning(f"Method '{method}' has been removed. Returning empty calendar information.")
            return "经济日历功能已移除。如需经济日历数据，请使用其他数据源。"
        else:
            raise
    
    vendor_config = get_vendor(category, method)

    # 处理逗号分隔的vendor配置
    primary_vendors = [v.strip() for v in vendor_config.split(',')]

    if method not in VENDOR_METHODS:
        # 处理被移除的get_central_bank_calendar方法
        if method == "get_central_bank_calendar":
            logger.warning(f"Method '{method}' is no longer supported. Returning placeholder.")
            return "⚠️ 经济日历功能暂时不可用。该功能已被移除，请更新您的代码。"
        raise ValueError(f"Method '{method}' not supported")

    # 获取所有可用的vendor用于回退
    all_available_vendors = list(VENDOR_METHODS[method].keys())
    
    # 创建回退vendor列表：首选vendor在前，其他vendor作为回退
    fallback_vendors = primary_vendors.copy()
    for vendor in all_available_vendors:
        if vendor not in fallback_vendors:
            fallback_vendors.append(vendor)

    # 调试信息
    logger.debug(f"{method} - Primary: {primary_vendors} | Fallback: {fallback_vendors}")

    # 跟踪结果和执行状态
    results = []
    vendor_attempt_count = 0
    successful_vendor = None

    for vendor in fallback_vendors:
        if vendor not in VENDOR_METHODS[method]:
            if vendor in primary_vendors:
                logger.info(f"Vendor '{vendor}' not supported for method '{method}', falling back")
            continue

        vendor_impl = VENDOR_METHODS[method][vendor]
        is_primary_vendor = vendor in primary_vendors
        vendor_attempt_count += 1
        
        vendor_type = "primary" if is_primary_vendor else "fallback"
        logger.debug(f"Attempting {vendor_type} vendor '{vendor}' for {method} (attempt #{vendor_attempt_count})")

        try:
            logger.debug(f"Calling {method} from vendor '{vendor}'...")
            
            # 直接调用vendor实现函数
            result = vendor_impl(*args, **kwargs)
            
            results.append(result)
            successful_vendor = vendor
            logger.info(f"{method} from vendor '{vendor}' completed successfully")
            
            # 单vendor配置时在第一个成功的vendor后停止
            if len(primary_vendors) == 1:
                logger.debug(f"Stopping after successful vendor '{vendor}' (single-vendor config)")
                break
                
        except AlphaVantageRateLimitError as e:
            if vendor == "alpha_vantage":
                logger.warning(f"Alpha Vantage rate limit exceeded, falling back")
            continue
        except Exception as e:
            logger.error(f"{method} from vendor '{vendor}' failed: {e}")
            continue

    # 最终结果汇总
    if not results:
        logger.error(f"All {vendor_attempt_count} vendor attempts failed for method '{method}'")
        raise RuntimeError(f"All vendor implementations failed for method '{method}'")
    else:
        logger.info(f"{method} completed with {len(results)} result(s) from {vendor_attempt_count} vendor attempt(s)")

    # 如果只有一个结果，直接返回；否则拼接成字符串
    if len(results) == 1:
        return results[0]
    else:
        return '\n'.join(str(result) for result in results)