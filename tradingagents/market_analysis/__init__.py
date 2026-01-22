"""
市场状态识别系统
整合趋势检测、波动率分析和市场分类功能
"""

__version__ = "1.0.0"
__author__ = "TradingAgents Team"

from .config import (
    MarketState,
    TrendStrength,
    MarketAnalysisConfig
)

from .trend_detector import TrendDetector
from .volatility_analyzer import VolatilityAnalyzer
from .market_classifier import MarketClassifier
from .state_recognizer import MarketStateRecognizer

# 导出主要类
__all__ = [
    # 配置
    'MarketState',
    'TrendStrength',
    'MarketAnalysisConfig',
    
    # 组件
    'TrendDetector',
    'VolatilityAnalyzer',
    'MarketClassifier',
    
    # 主类
    'MarketStateRecognizer',
]

# 便捷函数
def create_recognizer(config=None):
    """创建市场状态识别器实例"""
    return MarketStateRecognizer(config)

def analyze_market_state(symbol, df, config=None, lookback_days=None):
    """
    便捷函数：分析市场状态
    
    Args:
        symbol: 交易品种
        df: 包含OHLCV的DataFrame
        config: 配置对象
        lookback_days: 回看天数
        
    Returns:
        分析结果字典
    """
    recognizer = create_recognizer(config)
    return recognizer.analyze_market(symbol, df, lookback_days)

# 初始化日志
import logging

# 设置模块日志级别
logging.getLogger(__name__).addHandler(logging.NullHandler())

def setup_logging(level=logging.INFO):
    """设置日志级别"""
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger