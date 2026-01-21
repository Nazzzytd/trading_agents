"""
工具模块统一导出
避免循环导入问题
"""

import logging

logger = logging.getLogger(__name__)

# 使用延迟导入避免循环依赖
# 不在这里导入 route_to_vendor，而是让每个模块自己导入

# 导出技术指标工具
from .technical_indicators_tools import (
    get_technical_data,
    get_technical_indicators_data,
    get_fibonacci_levels,
    get_indicators
)

# 导出新闻工具
from .news_data_tools import (
    get_news,
    get_news_direct,
    optimize_parameters_for_vendor
)

# 导出外汇工具
from .core_forex_tools import (
    get_forex_data
)

# 导出量化工具（如果可用）
try:
    from .quant_data_tools import (
        get_risk_metrics_data,
        get_volatility_data,
        simple_forex_data
    )
except ImportError:
    logger.warning("量化数据工具导入失败，可能是循环导入问题")

# 导出宏观经济工具（如果可用）
try:
    from .macro_data_tools import (
        get_fred_data,
        get_ecb_data,
        get_macro_dashboard
    )
except ImportError:
    logger.warning("宏观经济工具导入失败")

# 导出 agent_utils
from .agent_utils import (
    create_msg_delete
)

# 提供导入帮助函数
def import_route_to_vendor():
    """帮助导入 route_to_vendor，避免循环依赖"""
    try:
        from tradingagents.dataflows.interface import route_to_vendor
        return route_to_vendor
    except ImportError as e:
        logger.error(f"导入 route_to_vendor 失败: {e}")
        raise

# 提供常用工具列表
TOOLS = {
    "technical": [get_technical_indicators_data, get_fibonacci_levels, get_indicators],
    "news": [get_news],
    "forex": [get_forex_data],
    "macro": [],  # 根据实际导入情况填充
    "quant": []   # 根据实际导入情况填充
}