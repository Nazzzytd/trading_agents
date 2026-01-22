# tradingagents/market_analysis/trend_detector.py
"""
趋势识别模块
基于现有的技术指标进行趋势分析
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import logging
from .config import MarketState, TrendStrength, MarketAnalysisConfig
from tradingagents.agents.utils.technical_indicators_tools import calculate_all_indicators

logger = logging.getLogger(__name__)


class TrendDetector:
    """趋势识别器 - 基于现有技术指标"""
    
    def __init__(self, config: Optional[MarketAnalysisConfig] = None):
        self.config = config or MarketAnalysisConfig()
        self.logger = logging.getLogger(__name__)
    
    def detect_trend(self, technical_data: Dict) -> Dict[str, Any]:
        """
        检测趋势 - 使用现有的技术指标数据
        
        Args:
            technical_data: 从 get_technical_data 返回的技术数据
            
        Returns:
            趋势分析结果
        """
        if not technical_data.get('success'):
            return {
                "success": False,
                "error": technical_data.get('error', '技术数据获取失败'),
                "trend": "unknown",
                "strength": "none",
                "confidence": 0.0
            }
        
        try:
            latest_indicators = technical_data.get('latest_indicators', {})
            price_data = technical_data.get('price_data', {})
            current_price = price_data.get('current', 0)
            
            # 1. 基于移动平均线的趋势分析
            ma_analysis = self._analyze_moving_averages(latest_indicators, current_price)
            
            # 2. 基于价格行为的趋势分析
            price_action_analysis = self._analyze_price_action(technical_data)
            
            # 3. 基于动量的趋势分析
            momentum_analysis = self._analyze_momentum(latest_indicators)
            
            # 4. 综合趋势判断
            trend_result = self._combine_trend_signals(
                ma_analysis, price_action_analysis, momentum_analysis
            )
            
            return {
                "success": True,
                "trend": trend_result["direction"],
                "strength": trend_result["strength"],
                "confidence": trend_result["confidence"],
                "components": {
                    "moving_averages": ma_analysis,
                    "price_action": price_action_analysis,
                    "momentum": momentum_analysis
                },
                "summary": self._generate_trend_summary(trend_result)
            }
            
        except Exception as e:
            self.logger.error(f"趋势检测失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "trend": "unknown",
                "strength": "none",
                "confidence": 0.0
            }
    
    def _analyze_moving_averages(self, indicators: Dict, current_price: float) -> Dict:
        """分析移动平均线趋势"""
        result = {
            "direction": "neutral",
            "strength": 0.0,
            "alignment": "mixed",
            "ma_signals": []
        }
        
        # 检查关键的移动平均线
        ma_keys = ['SMA_20', 'SMA_50', 'SMA_200', 'EMA_20', 'EMA_50', 'EMA_200']
        available_mas = {k: indicators.get(k) for k in ma_keys if k in indicators}
        
        if not available_mas:
            return result
        
        # 计算价格相对于各均线的位置
        above_ma_count = 0
        total_ma_count = 0
        
        for ma_name, ma_value in available_mas.items():
            if ma_value is not None:
                total_ma_count += 1
                if current_price > ma_value:
                    above_ma_count += 1
                    result["ma_signals"].append(f"{ma_name}: 价格在上方 (看涨)")
                else:
                    result["ma_signals"].append(f"{ma_name}: 价格在下方 (看跌)")
        
        # 判断趋势方向
        if total_ma_count > 0:
            above_ratio = above_ma_count / total_ma_count
            
            if above_ratio > 0.7:
                result["direction"] = "bullish"
                result["strength"] = above_ratio
                result["alignment"] = "bullish_alignment"
            elif above_ratio < 0.3:
                result["direction"] = "bearish"
                result["strength"] = 1.0 - above_ratio
                result["alignment"] = "bearish_alignment"
            else:
                result["direction"] = "neutral"
                result["strength"] = 0.5
                result["alignment"] = "mixed_alignment"
        
        # 检查均线排列（如果都有）
        if all(k in available_mas for k in ['EMA_5', 'EMA_10', 'EMA_20', 'EMA_50', 'EMA_200']):
            ema_5 = available_mas['EMA_5']
            ema_10 = available_mas['EMA_10']
            ema_20 = available_mas['EMA_20']
            ema_50 = available_mas['EMA_50']
            ema_200 = available_mas['EMA_200']
            
            # 多头排列
            if ema_5 > ema_10 > ema_20 > ema_50 > ema_200:
                result["alignment"] = "perfect_bullish"
                result["strength"] = max(result["strength"], 0.9)
            # 空头排列
            elif ema_5 < ema_10 < ema_20 < ema_50 < ema_200:
                result["alignment"] = "perfect_bearish"
                result["strength"] = max(result["strength"], 0.9)
        
        return result
    
    def _analyze_price_action(self, technical_data: Dict) -> Dict:
        """分析价格行为趋势"""
        result = {
            "direction": "neutral",
            "strength": 0.0,
            "price_change": 0.0,
            "high_low_analysis": "neutral"
        }
        
        price_change_pct = technical_data.get('price_change_pct', 0)
        result["price_change"] = price_change_pct
        
        # 基于价格变化判断趋势
        abs_change = abs(price_change_pct)
        
        if price_change_pct > self.config.strong_trend_threshold:
            result["direction"] = "bullish"
            result["strength"] = min(abs_change / 0.05, 1.0)  # 归一化到0-1
            result["high_low_analysis"] = "strong_bullish"
        elif price_change_pct > self.config.trending_threshold:
            result["direction"] = "bullish"
            result["strength"] = min(abs_change / 0.03, 1.0)
            result["high_low_analysis"] = "moderate_bullish"
        elif price_change_pct < -self.config.strong_trend_threshold:
            result["direction"] = "bearish"
            result["strength"] = min(abs_change / 0.05, 1.0)
            result["high_low_analysis"] = "strong_bearish"
        elif price_change_pct < -self.config.trending_threshold:
            result["direction"] = "bearish"
            result["strength"] = min(abs_change / 0.03, 1.0)
            result["high_low_analysis"] = "moderate_bearish"
        else:
            result["direction"] = "neutral"
            result["strength"] = 0.3
            result["high_low_analysis"] = "sideways"
        
        return result
    
    def _analyze_momentum(self, indicators: Dict) -> Dict:
        """分析动量指标"""
        result = {
            "direction": "neutral",
            "strength": 0.0,
            "rsi_signal": "neutral",
            "macd_signal": "neutral",
            "stochastic_signal": "neutral"
        }
        
        # RSI分析
        rsi = indicators.get('RSI')
        if rsi is not None:
            if rsi > self.config.rsi_overbought:
                result["rsi_signal"] = "overbought"
                result["direction"] = "bearish"  # 超买可能回调
                result["strength"] = max(result["strength"], 0.7)
            elif rsi > self.config.rsi_neutral_upper:
                result["rsi_signal"] = "bullish"
                if result["direction"] != "bearish":
                    result["direction"] = "bullish"
                    result["strength"] = max(result["strength"], 0.5)
            elif rsi < self.config.rsi_oversold:
                result["rsi_signal"] = "oversold"
                result["direction"] = "bullish"  # 超卖可能反弹
                result["strength"] = max(result["strength"], 0.7)
            elif rsi < self.config.rsi_neutral_lower:
                result["rsi_signal"] = "bearish"
                if result["direction"] != "bullish":
                    result["direction"] = "bearish"
                    result["strength"] = max(result["strength"], 0.5)
        
        # MACD分析
        macd = indicators.get('MACD')
        macd_signal = indicators.get('MACD_Signal')
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                result["macd_signal"] = "bullish"
                if result["direction"] != "bearish":
                    result["direction"] = "bullish"
                    result["strength"] = max(result["strength"], 0.6)
            else:
                result["macd_signal"] = "bearish"
                if result["direction"] != "bullish":
                    result["direction"] = "bearish"
                    result["strength"] = max(result["strength"], 0.6)
        
        # 随机指标分析
        stoch_k = indicators.get('Stoch_K')
        stoch_d = indicators.get('Stoch_D')
        if stoch_k is not None and stoch_d is not None:
            if stoch_k > 80 and stoch_d > 80:
                result["stochastic_signal"] = "overbought"
            elif stoch_k < 20 and stoch_d < 20:
                result["stochastic_signal"] = "oversold"
            elif stoch_k > stoch_d:
                result["stochastic_signal"] = "bullish"
            else:
                result["stochastic_signal"] = "bearish"
        
        return result
    
    def _combine_trend_signals(self, ma_analysis: Dict, 
                               price_action: Dict, 
                               momentum: Dict) -> Dict:
        """综合所有趋势信号"""
        # 权重分配
        weights = {
            'moving_averages': 0.4,
            'price_action': 0.3,
            'momentum': 0.3
        }
        
        # 收集各组件信号
        signals = []
        strengths = []
        
        for component, weight in weights.items():
            if component == 'moving_averages':
                signal = ma_analysis['direction']
                strength = ma_analysis['strength'] * weight
            elif component == 'price_action':
                signal = price_action['direction']
                strength = price_action['strength'] * weight
            else:  # momentum
                signal = momentum['direction']
                strength = momentum['strength'] * weight
            
            signals.append(signal)
            strengths.append(strength)
        
        # 计算综合趋势
        bull_score = sum(strength for signal, strength in zip(signals, strengths) 
                        if signal == 'bullish')
        bear_score = sum(strength for signal, strength in zip(signals, strengths) 
                        if signal == 'bearish')
        
        total_score = bull_score + bear_score
        if total_score == 0:
            return {
                "direction": "neutral",
                "strength": 0.0,
                "confidence": 0.3
            }
        
        # 确定主要趋势
        if bull_score > bear_score * 1.5:  # 牛市信号明显强于熊市
            direction = "bullish"
            strength = bull_score / total_score
        elif bear_score > bull_score * 1.5:  # 熊市信号明显强于牛市
            direction = "bearish"
            strength = bear_score / total_score
        else:
            direction = "neutral"
            strength = 0.5
        
        # 计算置信度
        confidence = min(strength * 1.5, 0.95)  # 不超过0.95
        
        return {
            "direction": direction,
            "strength": strength,
            "confidence": confidence
        }
    
    def _generate_trend_summary(self, trend_result: Dict) -> str:
        """生成趋势摘要"""
        direction = trend_result["direction"]
        strength = trend_result["strength"]
        confidence = trend_result["confidence"]
        
        if direction == "bullish":
            if strength > 0.8:
                trend_desc = "强烈上涨趋势"
            elif strength > 0.6:
                trend_desc = "明确上涨趋势"
            elif strength > 0.4:
                trend_desc = "温和上涨趋势"
            else:
                trend_desc = "轻微上涨倾向"
        elif direction == "bearish":
            if strength > 0.8:
                trend_desc = "强烈下跌趋势"
            elif strength > 0.6:
                trend_desc = "明确下跌趋势"
            elif strength > 0.4:
                trend_desc = "温和下跌趋势"
            else:
                trend_desc = "轻微下跌倾向"
        else:
            if strength > 0.7:
                trend_desc = "明显横盘整理"
            elif strength > 0.5:
                trend_desc = "横盘震荡"
            else:
                trend_desc = "无明确方向"
        
        confidence_desc = "高" if confidence > 0.7 else "中" if confidence > 0.5 else "低"
        
        return f"{trend_desc}，置信度{confidence_desc} (强度: {strength:.2f})"
    
    def identify_trend_strength(self, trend_strength: float) -> TrendStrength:
        """识别趋势强度等级"""
        if trend_strength > 0.8:
            return TrendStrength.STRONG
        elif trend_strength > 0.6:
            return TrendStrength.MODERATE
        elif trend_strength > 0.4:
            return TrendStrength.WEAK
        else:
            return TrendStrength.NONE