"""
改进版层管理器 - 直接集成您的数据流
"""
import sys
import os

# 添加您的项目路径
sys.path.append('/Users/fr./Downloads/TradingAgents-main')

from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class DirectDataIntegratedLayerManager:
    """直接数据集成层管理器"""
    
    def __init__(self):
        # 尝试导入您的数据接口
        try:
            from tradingagents.dataflows.interface import route_to_vendor
            from tradingagents.agents.utils.technical_indicators_tools import get_technical_data
            from tradingagents.agents.utils.macro_data_tools import get_fred_data, get_ecb_data
            from tradingagents.agents.utils.quant_data_tools import get_risk_metrics_data
            
            self.route_to_vendor = route_to_vendor
            self.get_technical_data = get_technical_data
            self.get_fred_data = get_fred_data
            self.get_ecb_data = get_ecb_data
            self.get_risk_metrics_data = get_risk_metrics_data
            
            self.data_access_available = True
            print("✅ 成功集成您的数据接口")
            
        except ImportError as e:
            print(f"⚠️  无法导入数据接口: {e}")
            self.data_access_available = False
        
        # 初始化状态检测器
        self.regime_detector = DirectDataRegimeDetector(self)
        
    def get_market_data(self, symbol: str, lookback_days: int = 60) -> Optional[pd.DataFrame]:
        """直接获取市场数据 - 使用您的数据接口"""
        if not self.data_access_available:
            return None
        
        try:
            # 使用您的技术数据工具
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            data_result = self.get_technical_data(
                symbol=symbol,
                current_date=current_date,
                lookback_days=lookback_days
            )
            
            if isinstance(data_result, dict) and data_result.get("success"):
                # 解析数据为DataFrame
                df = self._parse_technical_data(data_result)
                return df
            else:
                print(f"⚠️  技术数据获取失败: {data_result}")
                return None
                
        except Exception as e:
            print(f"❌ 获取市场数据失败: {e}")
            return None
    
    def get_macro_data(self, currency_pair: str) -> Dict:
        """获取宏观经济数据"""
        if not self.data_access_available:
            return {}
        
        try:
            # 解析货币对
            if "/" in currency_pair:
                base_currency, quote_currency = currency_pair.split("/")
            else:
                base_currency = currency_pair[:3]
                quote_currency = currency_pair[3:]
            
            macro_data = {}
            
            # 获取美国数据（如果涉及USD）
            if base_currency == "USD" or quote_currency == "USD":
                us_data = self.get_fred_data({"currency": "USD"})
                if us_data:
                    macro_data["us"] = us_data
            
            # 获取欧元区数据（如果涉及EUR）
            if base_currency == "EUR" or quote_currency == "EUR":
                eur_data = self.get_ecb_data({"currency": "EUR"})
                if eur_data:
                    macro_data["eu"] = eur_data
            
            return macro_data
            
        except Exception as e:
            print(f"❌ 获取宏观数据失败: {e}")
            return {}
    
    def get_risk_data(self, symbol: str) -> Dict:
        """获取风险数据"""
        if not self.data_access_available:
            return {}
        
        try:
            risk_data = self.get_risk_metrics_data({"symbol": symbol, "periods": 252})
            
            if isinstance(risk_data, dict) and risk_data.get("success"):
                return risk_data.get("risk_metrics", {})
            else:
                return {}
                
        except Exception as e:
            print(f"❌ 获取风险数据失败: {e}")
            return {}
    
    def detect_regime_from_data(self, symbol: str) -> Dict:
        """直接从数据检测市场状态"""
        # 1. 获取市场数据
        market_data = self.get_market_data(symbol)
        
        # 2. 获取宏观数据
        macro_data = self.get_macro_data(symbol)
        
        # 3. 获取风险数据
        risk_data = self.get_risk_data(symbol)
        
        # 4. 综合检测
        regime_result = self.regime_detector.detect(
            market_data=market_data,
            macro_data=macro_data,
            risk_data=risk_data,
            symbol=symbol
        )
        
        return regime_result
    
    def _parse_technical_data(self, data_result: Dict) -> pd.DataFrame:
        """解析技术数据为DataFrame"""
        try:
            if "data" in data_result:
                # 假设数据在"data"字段中
                data_dict = data_result["data"]
                
                # 转换为DataFrame
                df = pd.DataFrame(data_dict)
                
                # 确保有必要的列
                required_columns = ['close', 'high', 'low']
                if all(col in df.columns for col in required_columns):
                    return df
                else:
                    # 尝试其他可能的列名
                    column_mapping = {
                        'Close': 'close',
                        'High': 'high', 
                        'Low': 'low',
                        'Open': 'open',
                        'Volume': 'volume'
                    }
                    
                    for old_col, new_col in column_mapping.items():
                        if old_col in df.columns:
                            df[new_col] = df[old_col]
                    
                    return df
            
            return pd.DataFrame()
            
        except Exception as e:
            print(f"❌ 解析技术数据失败: {e}")
            return pd.DataFrame()


class DirectDataRegimeDetector:
    """直接数据驱动的状态检测器"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
    
    def detect(self, market_data: Optional[pd.DataFrame], 
              macro_data: Dict, 
              risk_data: Dict,
              symbol: str) -> Dict:
        """基于原始数据检测市场状态"""
        
        regime_scores = {}
        
        # 1. 技术面检测（如果有市场数据）
        if market_data is not None and len(market_data) > 20:
            technical_regime = self._detect_from_technical(market_data)
            regime_scores.update(technical_regime)
        
        # 2. 基本面检测（如果有宏观数据）
        if macro_data:
            fundamental_regime = self._detect_from_fundamental(macro_data, symbol)
            regime_scores.update(fundamental_regime)
        
        # 3. 风险面检测
        if risk_data:
            risk_regime = self._detect_from_risk(risk_data)
            regime_scores.update(risk_regime)
        
        # 4. 如果没有数据，返回默认状态
        if not regime_scores:
            return {
                "dominant_regime": "uncertain",
                "confidence": 0.3,
                "detection_method": "no_data",
                "recommendation": "等待更多数据"
            }
        
        # 5. 确定主导状态
        dominant_regime = max(regime_scores.items(), key=lambda x: x[1])[0]
        confidence = regime_scores[dominant_regime]
        
        # 6. 生成建议
        recommendation = self._generate_recommendation(dominant_regime, confidence, symbol)
        
        return {
            "dominant_regime": dominant_regime,
            "regime_scores": regime_scores,
            "confidence": confidence,
            "detection_method": "data_driven",
            "recommendation": recommendation,
            "data_sources": {
                "market_data": market_data is not None,
                "macro_data": len(macro_data) > 0,
                "risk_data": len(risk_data) > 0
            }
        }
    
    def _detect_from_technical(self, df: pd.DataFrame) -> Dict[str, float]:
        """从技术数据检测"""
        scores = {}
        
        try:
            # 计算基本技术指标
            close = df['close'].values
            high = df['high'].values
            low = df['low'].values
            
            # 1. 趋势检测
            trend_score = self._calculate_trend_score(close)
            
            # 2. 波动率检测
            volatility_score = self._calculate_volatility_score(close)
            
            # 3. 动量检测
            momentum_score = self._calculate_momentum_score(close)
            
            # 4. 范围检测
            range_score = self._calculate_range_score(high, low)
            
            # 根据分数判断状态
            if trend_score > 0.7:
                scores["trending_bull"] = trend_score
            elif trend_score < -0.7:
                scores["trending_bear"] = abs(trend_score)
            
            if volatility_score > 0.7:
                scores["high_volatility"] = volatility_score
            elif volatility_score < 0.3:
                scores["low_volatility"] = 1 - volatility_score
            
            if range_score > 0.6:
                scores["ranging"] = range_score
            
            if momentum_score > 0.7:
                scores["breakout_up"] = momentum_score
            elif momentum_score < -0.7:
                scores["breakout_down"] = abs(momentum_score)
            
        except Exception as e:
            print(f"❌ 技术检测失败: {e}")
        
        return scores
    
    def _calculate_trend_score(self, prices: np.ndarray) -> float:
        """计算趋势分数"""
        if len(prices) < 50:
            return 0
        
        # 简单趋势计算：近期价格与均线的关系
        recent = prices[-20:]
        sma = np.mean(prices[-50:])
        
        current_price = recent[-1]
        price_20 = recent[0]
        
        # 趋势强度
        price_change = (current_price - price_20) / price_20
        ma_distance = (current_price - sma) / sma
        
        # 综合趋势分数
        trend_score = (price_change * 0.6 + ma_distance * 0.4) * 10  # 放大到-1到1范围
        
        return max(min(trend_score, 1), -1)
    
    def _calculate_volatility_score(self, prices: np.ndarray) -> float:
        """计算波动率分数"""
        if len(prices) < 20:
            return 0.5
        
        returns = np.diff(np.log(prices))
        
        # 近期波动率
        recent_vol = np.std(returns[-10:]) * np.sqrt(252)
        
        # 历史波动率
        historical_vol = np.std(returns) * np.sqrt(252)
        
        if historical_vol > 0:
            vol_ratio = recent_vol / historical_vol
            return min(vol_ratio, 2.0) / 2.0  # 归一化到0-1
        else:
            return 0.5
    
    def _calculate_momentum_score(self, prices: np.ndarray) -> float:
        """计算动量分数"""
        if len(prices) < 30:
            return 0
        
        # 近期动量
        recent_return = (prices[-1] - prices[-10]) / prices[-10]
        
        # 动量变化
        earlier_return = (prices[-10] - prices[-30]) / prices[-30]
        
        momentum_acceleration = recent_return - earlier_return
        
        return max(min(momentum_acceleration * 5, 1), -1)  # 归一化
    
    def _calculate_range_score(self, high: np.ndarray, low: np.ndarray) -> float:
        """计算范围分数"""
        if len(high) < 20 or len(low) < 20:
            return 0
        
        # 近期价格范围
        recent_high = np.max(high[-10:])
        recent_low = np.min(low[-10:])
        recent_range = (recent_high - recent_low) / recent_low
        
        # 历史价格范围
        historical_high = np.max(high)
        historical_low = np.min(low)
        historical_range = (historical_high - historical_low) / historical_low
        
        if historical_range > 0:
            range_ratio = recent_range / historical_range
            return min(range_ratio, 1.5) / 1.5
        else:
            return 0.5
    
    def _detect_from_fundamental(self, macro_data: Dict, symbol: str) -> Dict[str, float]:
        """从基本面检测"""
        scores = {}
        
        try:
            # 简单的宏观信号检测
            has_us_data = "us" in macro_data
            has_eu_data = "eu" in macro_data
            
            if "/" in symbol:
                base_currency, quote_currency = symbol.split("/")
            else:
                base_currency = symbol[:3]
                quote_currency = symbol[3:]
            
            # 检查是否有重要宏观事件
            event_signals = self._extract_macro_events(macro_data)
            
            if event_signals.get("has_important_event", False):
                scores["macro_event"] = 0.8
            
            # 检查是否有新闻驱动
            if event_signals.get("has_news_impact", False):
                scores["news_driven"] = 0.7
            
        except Exception as e:
            print(f"❌ 基本面检测失败: {e}")
        
        return scores
    
    def _extract_macro_events(self, macro_data: Dict) -> Dict:
        """提取宏观事件信号"""
        signals = {
            "has_important_event": False,
            "has_news_impact": False,
            "event_count": 0
        }
        
        # 简单的事件检测逻辑
        # 实际中需要更复杂的逻辑来解析宏观数据
        
        return signals
    
    def _detect_from_risk(self, risk_data: Dict) -> Dict[str, float]:
        """从风险数据检测"""
        scores = {}
        
        try:
            # 检查关键风险指标
            volatility = risk_data.get("annual_volatility", 0)
            max_drawdown = abs(risk_data.get("max_drawdown", 0))
            sharpe_ratio = risk_data.get("sharpe_ratio", 0)
            
            # 高波动率
            if volatility > 0.15:  # 15%年化波动率
                scores["high_volatility"] = min(volatility / 0.3, 1.0)
            
            # 高风险（大回撤）
            if max_drawdown > 0.20:  # 20%最大回撤
                scores["crisis"] = min(max_drawdown / 0.5, 1.0)
            
            # 量化异常（夏普比率异常）
            if abs(sharpe_ratio) > 3.0:
                scores["quant_shock"] = 0.6
            
        except Exception as e:
            print(f"❌ 风险检测失败: {e}")
        
        return scores
    
    def _generate_recommendation(self, regime: str, confidence: float, symbol: str) -> str:
        """生成交易建议"""
        recommendations = {
            "trending_bull": f"{symbol}处于上涨趋势，建议逢低买入",
            "trending_bear": f"{symbol}处于下跌趋势，建议逢高卖出",
            "ranging": f"{symbol}处于震荡整理，建议区间操作",
            "high_volatility": f"{symbol}波动率高，建议谨慎操作，严格止损",
            "low_volatility": f"{symbol}波动率低，适合套利策略",
            "breakout_up": f"{symbol}向上突破，可考虑追涨",
            "breakout_down": f"{symbol}向下突破，可考虑追空",
            "macro_event": f"{symbol}受宏观事件影响，关注基本面变化",
            "news_driven": f"{symbol}受新闻驱动，注意事件风险",
            "quant_shock": f"{symbol}出现量化异常，模型可能失效",
            "crisis": f"{symbol}处于危机模式，建议大幅减仓或对冲",
            "uncertain": f"{symbol}状态不确定，建议观望"
        }
        
        base_recommendation = recommendations.get(regime, "建议谨慎操作")
        
        # 根据置信度调整建议
        if confidence > 0.7:
            confidence_level = "高置信度"
        elif confidence > 0.5:
            confidence_level = "中等置信度"
        else:
            confidence_level = "低置信度"
        
        return f"{confidence_level}: {base_recommendation}"