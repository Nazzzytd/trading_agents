"""
市场分类器模块
综合趋势、波动率和其他指标进行市场状态分类
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
from .config import MarketState, TrendStrength, MarketAnalysisConfig
from .trend_detector import TrendDetector
from .volatility_analyzer import VolatilityAnalyzer

logger = logging.getLogger(__name__)


class MarketClassifier:
    """市场分类器 - 综合各种指标进行市场状态识别"""
    
    def __init__(self, config: Optional[MarketAnalysisConfig] = None):
        self.config = config or MarketAnalysisConfig()
        self.trend_detector = TrendDetector(config)
        self.volatility_analyzer = VolatilityAnalyzer(config)
        self.logger = logging.getLogger(__name__)
        self.state_history = []  # 状态历史记录
    
    def classify_market_state(self, technical_data: Dict) -> Dict[str, Any]:
        """
        分类市场状态
        
        Args:
            technical_data: 从 get_technical_data 返回的技术数据
            
        Returns:
            市场状态分类结果
        """
        if not technical_data.get('success'):
            return {
                "success": False,
                "error": technical_data.get('error', '技术数据获取失败'),
                "market_state": MarketState.UNCERTAIN.value,
                "confidence": 0.0,
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # 1. 趋势分析
            trend_result = self.trend_detector.detect_trend(technical_data)
            
            # 2. 波动率分析
            volatility_result = self.volatility_analyzer.analyze_volatility(technical_data)
            
            # 3. 支撑阻力分析
            support_resistance = self._analyze_support_resistance(technical_data)
            
            # 4. 成交量分析
            volume_analysis = self._analyze_volume(technical_data)
            
            # 5. 综合分类市场状态
            classification = self._classify_market(
                trend_result, 
                volatility_result, 
                support_resistance,
                volume_analysis
            )
            
            # 6. 生成交易信号
            trading_signals = self._generate_trading_signals(
                classification, trend_result, volatility_result
            )
            
            # 7. 更新状态历史
            self._update_state_history(classification)
            
            result = {
                "success": True,
                "market_state": classification["primary_state"].value,
                "state_chinese": classification["primary_state"].value,
                "confidence": classification["confidence"],
                "sub_states": {
                    "trend": classification["trend_state"].value if classification["trend_state"] else "N/A",
                    "volatility": classification["volatility_state"],
                    "pattern": classification["pattern_state"]
                },
                "components": {
                    "trend": trend_result,
                    "volatility": volatility_result,
                    "support_resistance": support_resistance,
                    "volume": volume_analysis
                },
                "trading_signals": trading_signals,
                "summary": classification["summary"],
                "recommendation": classification["recommendation"],
                "timestamp": datetime.now().isoformat(),
                "market_conditions": classification["conditions"]
            }
            
            if self.config.enable_debug_logging:
                self.logger.info(f"市场状态分类完成: {classification['primary_state'].value}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"市场分类失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "market_state": MarketState.UNCERTAIN.value,
                "confidence": 0.0,
                "timestamp": datetime.now().isoformat()
            }
    
    def _analyze_support_resistance(self, technical_data: Dict) -> Dict:
        """分析支撑阻力"""
        result = {
            "near_support": False,
            "near_resistance": False,
            "key_levels": [],
            "breakout_potential": False,
            "signal": "neutral"
        }
        
        price_data = technical_data.get('price_data', {})
        current_price = price_data.get('current', 0)
        
        # 从技术数据中获取关键价格水平（如果有）
        key_levels = technical_data.get('key_levels', [])
        
        if not key_levels and 'price_ranges' in technical_data:
            # 如果没有明确的关键水平，使用价格范围
            ranges = technical_data.get('price_ranges', {})
            if ranges:
                support = ranges.get('support', 0)
                resistance = ranges.get('resistance', 0)
                key_levels = [support, resistance]
        
        for level in key_levels:
            if level > 0:
                # 检查是否接近支撑或阻力
                price_diff_pct = abs(current_price - level) / current_price
                
                if price_diff_pct < 0.02:  # 2%以内视为接近
                    if current_price > level:
                        result["near_support"] = True
                        result["key_levels"].append(f"支撑位附近: {level:.4f}")
                    else:
                        result["near_resistance"] = True
                        result["key_levels"].append(f"阻力位附近: {level:.4f}")
        
        # 判断突破潜力
        if result["near_support"] or result["near_resistance"]:
            result["breakout_potential"] = True
        
        # 设置信号
        if result["near_support"]:
            result["signal"] = "near_support"
        elif result["near_resistance"]:
            result["signal"] = "near_resistance"
        
        return result
    
    def _analyze_volume(self, technical_data: Dict) -> Dict:
        """分析成交量"""
        result = {
            "volume_trend": "neutral",
            "volume_spike": False,
            "volume_signal": "normal",
            "volume_ratio": 1.0
        }
        
        latest_indicators = technical_data.get('latest_indicators', {})
        volume = latest_indicators.get('Volume')
        volume_ma = latest_indicators.get('Volume_MA_20')
        
        if volume is not None and volume_ma is not None and volume_ma > 0:
            volume_ratio = volume / volume_ma
            result["volume_ratio"] = volume_ratio
            
            if volume_ratio > 1.5:
                result["volume_trend"] = "increasing"
                result["volume_spike"] = True
                result["volume_signal"] = "high_volume"
            elif volume_ratio > 1.2:
                result["volume_trend"] = "increasing"
                result["volume_signal"] = "above_average"
            elif volume_ratio < 0.8:
                result["volume_trend"] = "decreasing"
                result["volume_signal"] = "low_volume"
        
        return result
    
    def _classify_market(self, trend_result: Dict, volatility_result: Dict,
                         support_resistance: Dict, volume_analysis: Dict) -> Dict:
        """综合分类市场状态"""
        
        # 提取关键信息
        trend_direction = trend_result.get('trend', 'neutral')
        trend_strength = trend_result.get('confidence', 0.0)
        volatility_level = volatility_result.get('volatility_level', 'normal')
        volatility_score = volatility_result.get('volatility_score', 0.5)
        near_support = support_resistance.get('near_support', False)
        near_resistance = support_resistance.get('near_resistance', False)
        volume_signal = volume_analysis.get('volume_signal', 'normal')
        
        # 初始化状态
        primary_state = MarketState.UNCERTAIN
        trend_state = None
        volatility_state = volatility_level
        pattern_state = "none"
        confidence = 0.5
        conditions = []
        recommendation = ""
        
        # 根据趋势和波动率组合判断
        # 情况1: 明确趋势 + 正常/高波动率
        if trend_direction in ['bullish', 'bearish'] and trend_strength > 0.6:
            if volatility_score > 0.6:
                # 趋势明显且波动率高
                volatility_state = "high_volatility"
                pattern_state = "trending_with_high_vol"
                
                if trend_direction == 'bullish':
                    primary_state = MarketState.TRENDING_BULL
                    conditions.append("强势上涨趋势")
                    conditions.append("高波动率")
                    recommendation = "顺势而为，注意波动风险"
                else:
                    primary_state = MarketState.TRENDING_BEAR
                    conditions.append("强势下跌趋势")
                    conditions.append("高波动率")
                    recommendation = "谨慎做空，设置止损"
                
                confidence = min(trend_strength * 0.8 + volatility_score * 0.2, 0.9)
                
            else:
                # 趋势明显但波动率正常
                volatility_state = "normal_volatility"
                pattern_state = "steady_trend"
                
                if trend_direction == 'bullish':
                    primary_state = MarketState.TRENDING_BULL
                    conditions.append("稳定上涨趋势")
                    recommendation = "逢低买入"
                else:
                    primary_state = MarketState.TRENDING_BEAR
                    conditions.append("稳定下跌趋势")
                    recommendation = "反弹做空"
                
                confidence = min(trend_strength * 0.9 + volatility_score * 0.1, 0.95)
        
        # 情况2: 无明确趋势 + 高波动率
        elif trend_direction == 'neutral' and volatility_score > 0.7:
            primary_state = MarketState.VOLATILE
            trend_state = MarketState.SIDEWAYS
            volatility_state = "high_volatility"
            pattern_state = "choppy_market"
            
            conditions.append("无明确方向")
            conditions.append("高波动震荡")
            recommendation = "区间交易，高抛低吸"
            confidence = volatility_score * 0.8
        
        # 情况3: 无明确趋势 + 低波动率
        elif trend_direction == 'neutral' and volatility_score < 0.3:
            primary_state = MarketState.LOW_VOLATILITY
            trend_state = MarketState.SIDEWAYS
            volatility_state = "low_volatility"
            
            if support_resistance.get('breakout_potential', False):
                pattern_state = "consolidation_before_breakout"
                conditions.append("低波动盘整")
                conditions.append("接近关键价位")
                recommendation = "等待突破方向"
                confidence = 0.6
            else:
                pattern_state = "sideways_consolidation"
                conditions.append("横盘整理")
                conditions.append("低波动率")
                recommendation = "观望或小仓位区间交易"
                confidence = 0.5
        
        # 情况4: 在关键价位附近
        elif near_support or near_resistance:
            if volatility_score < 0.4:
                primary_state = MarketState.CONSOLIDATION
                pattern_state = "consolidation_at_key_level"
                
                if near_support:
                    conditions.append("支撑位附近盘整")
                    recommendation = "观察支撑有效性，准备做多"
                else:
                    conditions.append("阻力位附近盘整")
                    recommendation = "观察阻力有效性，准备做空"
                
                confidence = 0.7
            else:
                primary_state = MarketState.BREAKOUT
                pattern_state = "breakout_attempt"
                conditions.append("关键价位测试")
                conditions.append("波动率上升")
                recommendation = "等待突破确认"
                confidence = 0.6
        
        # 情况5: 其他情况 - 区间震荡
        else:
            price_change_pct = abs(trend_result.get('components', {}).get('price_action', {}).get('price_change', 0))
            
            if price_change_pct < self.config.ranging_threshold:
                primary_state = MarketState.RANGING
                pattern_state = "range_bound"
                conditions.append("区间震荡")
                recommendation = "区间交易策略"
                confidence = 0.7 - volatility_score * 0.2
            else:
                # 不确定状态
                primary_state = MarketState.UNCERTAIN
                conditions.append("市场信号矛盾")
                recommendation = "观望，等待更明确信号"
                confidence = 0.4
        
        # 考虑成交量因素
        if volume_signal == 'high_volume':
            if primary_state in [MarketState.TRENDING_BULL, MarketState.TRENDING_BEAR]:
                confidence = min(confidence * 1.1, 0.95)
                conditions.append("成交量放大确认趋势")
            elif primary_state == MarketState.BREAKOUT:
                confidence = min(confidence * 1.2, 0.95)
                conditions.append("放量突破")
                recommendation = "突破确认，跟随趋势"
        
        # 生成摘要
        summary = self._generate_state_summary(
            primary_state, trend_state, conditions, confidence
        )
        
        return {
            "primary_state": primary_state,
            "trend_state": trend_state,
            "volatility_state": volatility_state,
            "pattern_state": pattern_state,
            "confidence": confidence,
            "conditions": conditions,
            "recommendation": recommendation,
            "summary": summary
        }
    
    def _generate_trading_signals(self, classification: Dict, 
                                  trend_result: Dict, 
                                  volatility_result: Dict) -> List[Dict]:
        """生成交易信号"""
        signals = []
        primary_state = classification["primary_state"]
        confidence = classification["confidence"]
        
        # 基本交易信号
        base_signal = {
            "signal": "neutral",
            "strength": 0.0,
            "action": "hold",
            "reason": ""
        }
        
        # 根据市场状态生成信号
        if primary_state == MarketState.TRENDING_BULL:
            if confidence > 0.7:
                base_signal["signal"] = "bullish"
                base_signal["strength"] = confidence
                base_signal["action"] = "buy"
                base_signal["reason"] = "强势上涨趋势"
                
                # 添加风险管理建议
                if volatility_result.get('volatility_level') == 'high':
                    signals.append({
                        "type": "risk_warning",
                        "message": "高波动率环境，建议轻仓或使用较小止损",
                        "priority": "high"
                    })
        
        elif primary_state == MarketState.TRENDING_BEAR:
            if confidence > 0.7:
                base_signal["signal"] = "bearish"
                base_signal["strength"] = confidence
                base_signal["action"] = "sell"
                base_signal["reason"] = "强势下跌趋势"
        
        elif primary_state == MarketState.RANGING:
            base_signal["signal"] = "neutral"
            base_signal["action"] = "range_trade"
            base_signal["reason"] = "区间震荡市场"
            
            # 区间交易建议
            signals.append({
                "type": "trading_strategy",
                "strategy": "range_trading",
                "description": "在支撑位买入，阻力位卖出",
                "priority": "medium"
            })
        
        elif primary_state == MarketState.BREAKOUT:
            base_signal["signal"] = "breakout_watch"
            base_signal["action"] = "wait_for_confirmation"
            base_signal["reason"] = "等待突破确认"
            
            signals.append({
                "type": "breakout_watch",
                "condition": "等待价格确认突破关键水平",
                "priority": "high"
            })
        
        elif primary_state == MarketState.VOLATILE:
            base_signal["signal"] = "volatile"
            base_signal["action"] = "reduce_position"
            base_signal["reason"] = "高波动市场"
            
            signals.append({
                "type": "risk_management",
                "advice": "减少仓位规模，扩大止损",
                "priority": "high"
            })
        
        # 总是添加基础信号
        signals.insert(0, base_signal)
        
        return signals
    
    def _generate_state_summary(self, primary_state: MarketState, 
                                trend_state: MarketState,
                                conditions: List[str], 
                                confidence: float) -> str:
        """生成状态摘要"""
        state_desc = primary_state.value
        
        confidence_desc = "极高" if confidence > 0.8 else "高" if confidence > 0.7 else "中等" if confidence > 0.6 else "较低"
        
        conditions_str = "，".join(conditions)
        
        if trend_state:
            trend_desc = f"，趋势状态: {trend_state.value}"
        else:
            trend_desc = ""
        
        return f"市场状态: {state_desc}{trend_desc}，置信度: {confidence_desc}。主要特征: {conditions_str}"
    
    def _update_state_history(self, classification: Dict):
        """更新状态历史"""
        history_entry = {
            "timestamp": datetime.now(),
            "state": classification["primary_state"],
            "confidence": classification["confidence"],
            "conditions": classification["conditions"]
        }
        
        self.state_history.append(history_entry)
        
        # 保持历史记录长度
        if len(self.state_history) > 100:
            self.state_history = self.state_history[-100:]
    
    def get_state_transitions(self, lookback: int = 10) -> List[Dict]:
        """获取状态转换历史"""
        if len(self.state_history) < 2:
            return []
        
        recent_history = self.state_history[-lookback:]
        transitions = []
        
        for i in range(1, len(recent_history)):
            prev_state = recent_history[i-1]
            curr_state = recent_history[i]
            
            if prev_state["state"] != curr_state["state"]:
                transitions.append({
                    "from_state": prev_state["state"].value,
                    "to_state": curr_state["state"].value,
                    "timestamp": curr_state["timestamp"],
                    "confidence_change": curr_state["confidence"] - prev_state["confidence"]
                })
        
        return transitions
    
    def get_market_regime(self) -> str:
        """获取当前市场体制"""
        if not self.state_history:
            return "unknown"
        
        # 分析最近的状态模式
        recent_states = [entry["state"] for entry in self.state_history[-20:]]
        
        # 统计各类状态出现频率
        state_counts = {}
        for state in recent_states:
            state_name = state.value
            state_counts[state_name] = state_counts.get(state_name, 0) + 1
        
        if not state_counts:
            return "unknown"
        
        # 找到最频繁的状态
        most_common = max(state_counts.items(), key=lambda x: x[1])
        
        # 判断体制类型
        if "趋势" in most_common[0]:
            return "trending_market"
        elif "震荡" in most_common[0] or "横盘" in most_common[0]:
            return "ranging_market"
        elif "波动" in most_common[0]:
            return "volatile_market"
        else:
            return "transitional_market"