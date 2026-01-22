# tradingagents/market_analysis/volatility_analyzer.py
"""
波动率分析模块
分析市场波动率状态
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import logging
from .config import MarketAnalysisConfig

logger = logging.getLogger(__name__)


class VolatilityAnalyzer:
    """波动率分析器"""
    
    def __init__(self, config: Optional[MarketAnalysisConfig] = None):
        self.config = config or MarketAnalysisConfig()
        self.logger = logging.getLogger(__name__)
    
    def analyze_volatility(self, technical_data: Dict) -> Dict[str, Any]:
        """
        分析波动率
        
        Args:
            technical_data: 从 get_technical_data 返回的技术数据
            
        Returns:
            波动率分析结果
        """
        if not technical_data.get('success'):
            return {
                "success": False,
                "error": technical_data.get('error', '技术数据获取失败'),
                "volatility_level": "unknown",
                "atr_level": "unknown",
                "bb_squeeze": False,
                "volatility_score": 0.0
            }
        
        try:
            latest_indicators = technical_data.get('latest_indicators', {})
            price_data = technical_data.get('price_data', {})
            
            # 1. ATR分析
            atr_analysis = self._analyze_atr(latest_indicators, price_data)
            
            # 2. 布林带分析
            bb_analysis = self._analyze_bollinger_bands(latest_indicators)
            
            # 3. 价格范围分析
            price_range_analysis = self._analyze_price_range(technical_data)
            
            # 4. 综合波动率判断
            volatility_result = self._combine_volatility_signals(
                atr_analysis, bb_analysis, price_range_analysis
            )
            
            return {
                "success": True,
                "volatility_level": volatility_result["level"],
                "volatility_score": volatility_result["score"],
                "atr_level": atr_analysis["level"],
                "atr_value": atr_analysis["value"],
                "bb_squeeze": bb_analysis["is_squeeze"],
                "bb_width": bb_analysis["width"],
                "price_range": price_range_analysis["range_pct"],
                "components": {
                    "atr": atr_analysis,
                    "bollinger_bands": bb_analysis,
                    "price_range": price_range_analysis
                },
                "summary": self._generate_volatility_summary(volatility_result)
            }
            
        except Exception as e:
            self.logger.error(f"波动率分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "volatility_level": "unknown",
                "atr_level": "unknown",
                "bb_squeeze": False,
                "volatility_score": 0.0
            }
    
    def _analyze_atr(self, indicators: Dict, price_data: Dict) -> Dict:
        """分析ATR波动率"""
        result = {
            "level": "normal",
            "value": 0.0,
            "relative_value": 0.0,
            "signal": "neutral"
        }
        
        atr = indicators.get('ATR')
        current_price = price_data.get('current', 1.0)
        
        if atr is not None and current_price > 0:
            result["value"] = atr
            atr_pct = atr / current_price
            
            # ATR相对水平
            if atr_pct > 0.015:  # 1.5%
                result["level"] = "high"
                result["relative_value"] = atr_pct
                result["signal"] = "high_volatility"
            elif atr_pct > 0.008:  # 0.8%
                result["level"] = "medium"
                result["relative_value"] = atr_pct
                result["signal"] = "moderate_volatility"
            else:
                result["level"] = "low"
                result["relative_value"] = atr_pct
                result["signal"] = "low_volatility"
        
        return result
    
    def _analyze_bollinger_bands(self, indicators: Dict) -> Dict:
        """分析布林带"""
        result = {
            "is_squeeze": False,
            "width": 0.0,
            "position": 0.5,
            "signal": "normal"
        }
        
        bb_width = indicators.get('BB_Width')
        bb_position = indicators.get('BB_Position')
        
        if bb_width is not None:
            result["width"] = bb_width
            
            # 判断挤压状态
            if bb_width < 0.02:  # 宽度小于2%为挤压
                result["is_squeeze"] = True
                result["signal"] = "squeeze"
            elif bb_width > 0.05:  # 宽度大于5%为扩张
                result["signal"] = "expansion"
        
        if bb_position is not None:
            result["position"] = bb_position
            
            # 位置信号
            if bb_position > 0.8:
                result["signal"] = "near_upper_band"
            elif bb_position < 0.2:
                result["signal"] = "near_lower_band"
        
        return result
    
    def _analyze_price_range(self, technical_data: Dict) -> Dict:
        """分析价格范围"""
        result = {
            "range_pct": 0.0,
            "level": "normal",
            "signal": "normal_range"
        }
        
        price_change_pct = abs(technical_data.get('price_change_pct', 0))
        result["range_pct"] = price_change_pct
        
        # 根据价格变化范围判断波动率
        if price_change_pct > 0.03:  # 3%
            result["level"] = "high"
            result["signal"] = "wide_range"
        elif price_change_pct > 0.015:  # 1.5%
            result["level"] = "medium"
            result["signal"] = "moderate_range"
        elif price_change_pct < 0.005:  # 0.5%
            result["level"] = "low"
            result["signal"] = "narrow_range"
        
        return result
    
    def _combine_volatility_signals(self, atr_analysis: Dict, 
                                    bb_analysis: Dict, 
                                    price_range: Dict) -> Dict:
        """综合波动率信号"""
        # 各指标权重
        weights = {
            'atr': 0.4,
            'bollinger': 0.3,
            'price_range': 0.3
        }
        
        # 转换各指标等级为分数
        atr_score = self._volatility_level_to_score(atr_analysis['level'])
        bb_score = 0.8 if bb_analysis['is_squeeze'] else 0.3 if bb_analysis['width'] > 0.04 else 0.5
        range_score = self._volatility_level_to_score(price_range['level'])
        
        # 加权平均
        total_score = (
            atr_score * weights['atr'] +
            bb_score * weights['bollinger'] +
            range_score * weights['price_range']
        )
        
        # 确定波动率等级
        if total_score > 0.7:
            level = "high"
        elif total_score > 0.5:
            level = "medium_high"
        elif total_score > 0.3:
            level = "medium"
        elif total_score > 0.2:
            level = "low"
        else:
            level = "very_low"
        
        return {
            "level": level,
            "score": total_score
        }
    
    def _volatility_level_to_score(self, level: str) -> float:
        """将波动率等级转换为分数"""
        level_map = {
            "high": 0.9,
            "medium_high": 0.7,
            "medium": 0.5,
            "low": 0.3,
            "very_low": 0.1,
            "normal": 0.5
        }
        return level_map.get(level, 0.5)
    
    def _generate_volatility_summary(self, volatility_result: Dict) -> str:
        """生成波动率摘要"""
        level = volatility_result["level"]
        score = volatility_result["score"]
        
        level_map = {
            "high": "高波动率",
            "medium_high": "中高波动率",
            "medium": "中等波动率",
            "low": "低波动率",
            "very_low": "极低波动率"
        }
        
        level_desc = level_map.get(level, "正常波动率")
        
        # 波动率建议
        if level in ["high", "medium_high"]:
            advice = "市场波动较大，注意风险管理"
        elif level in ["low", "very_low"]:
            advice = "市场波动较小，可能即将突破"
        else:
            advice = "市场波动正常"
        
        return f"{level_desc} (得分: {score:.2f}) - {advice}"