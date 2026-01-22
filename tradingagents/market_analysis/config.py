# tradingagents/market_analysis/config.py
"""
市场状态识别配置
扩展现有技术指标
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MarketState(Enum):
    """市场状态枚举"""
    TRENDING_BULL = "上升趋势"
    TRENDING_BEAR = "下降趋势"
    RANGING = "区间震荡"
    VOLATILE = "高波动"
    BREAKOUT = "突破"
    REVERSAL = "反转"
    SIDEWAYS = "横盘整理"
    LOW_VOLATILITY = "低波动"
    CONSOLIDATION = "盘整"
    UNCERTAIN = "不确定"


class TrendStrength(Enum):
    """趋势强度"""
    STRONG = "强势"
    MODERATE = "温和"
    WEAK = "弱势"
    NONE = "无趋势"


@dataclass
class MarketAnalysisConfig:
    """市场分析配置 - 扩展现有技术指标"""
    
    # 数据获取
    default_lookback_days: int = 60
    min_data_points: int = 20
    
    # 状态识别阈值
    trending_threshold: float = 0.015  # 1.5% 变化视为趋势
    strong_trend_threshold: float = 0.03  # 3% 为强趋势
    ranging_threshold: float = 0.01  # 1% 以内视为震荡
    
    # 波动率阈值
    high_volatility_multiplier: float = 1.5  # 高于平均1.5倍为高波动
    low_volatility_multiplier: float = 0.5   # 低于平均0.5倍为低波动
    
    # RSI阈值
    rsi_overbought: float = 70
    rsi_oversold: float = 30
    rsi_neutral_upper: float = 60
    rsi_neutral_lower: float = 40
    
    # 布林带阈值
    bb_squeeze_threshold: float = 0.7  # 布林带宽度小于平均的70%为挤压
    
    # 移动平均线权重
    short_term_ma_weight: float = 0.3  # 短期均线权重
    medium_term_ma_weight: float = 0.4  # 中期均线权重
    long_term_ma_weight: float = 0.3   # 长期均线权重
    
    # 状态转换平滑
    state_change_smoothing: int = 3  # 状态变化平滑周期
    
    # 输出配置
    enable_debug_logging: bool = True
    generate_summary: bool = True
    
    def validate(self):
        """验证配置"""
        if self.trending_threshold <= 0:
            raise ValueError("trending_threshold 必须大于0")
        if self.high_volatility_multiplier <= 1:
            raise ValueError("high_volatility_multiplier 必须大于1")
        if not (0 < self.low_volatility_multiplier < 1):
            raise ValueError("low_volatility_multiplier 必须在0和1之间")
        
        logger.info(f"市场分析配置已加载: {self}")
        return self