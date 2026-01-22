"""
市场状态识别主类
整合所有组件提供统一接口
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
import logging
from datetime import datetime, timedelta
from .config import MarketState, MarketAnalysisConfig
from .trend_detector import TrendDetector
from .volatility_analyzer import VolatilityAnalyzer
from .market_classifier import MarketClassifier
from tradingagents.agents.utils.technical_indicators_tools import calculate_all_indicators

logger = logging.getLogger(__name__)


class MarketStateRecognizer:
    """
    市场状态识别器
    主要入口类，整合趋势、波动率、分类等所有功能
    """
    
    def __init__(self, config: Optional[MarketAnalysisConfig] = None):
        """
        初始化市场状态识别器
        
        Args:
            config: 配置对象，如果为None则使用默认配置
        """
        self.config = config or MarketAnalysisConfig()
        self.config.validate()
        
        # 初始化组件
        self.trend_detector = TrendDetector(self.config)
        self.volatility_analyzer = VolatilityAnalyzer(self.config)
        self.market_classifier = MarketClassifier(self.config)
        
        self.logger = logging.getLogger(__name__)
        
        # 缓存最近的分析结果
        self._recent_analyses = []
        self._max_cache_size = 50
        
        self.logger.info("市场状态识别器初始化完成")
    
    def analyze_market(self, symbol: str, df: pd.DataFrame, 
                       lookback_days: Optional[int] = None) -> Dict[str, Any]:
        """
        分析市场状态 - 主要入口方法
        
        Args:
            symbol: 交易品种/股票代码
            df: 包含OHLCV数据的DataFrame，必须有以下列：
                'open', 'high', 'low', 'close', 'volume'
            lookback_days: 回看天数，如果为None则使用配置中的默认值
            
        Returns:
            完整的市场分析结果
        """
        try:
            start_time = datetime.now()
            
            # 验证数据
            if df.empty or len(df) < self.config.min_data_points:
                return self._create_error_result(
                    f"数据不足，至少需要{self.config.min_data_points}个数据点"
                )
            
            # 计算技术指标
            technical_data = self._get_technical_data(symbol, df, lookback_days)
            
            if not technical_data.get('success'):
                return self._create_error_result(technical_data.get('error', '技术指标计算失败'))
            
            # 分析市场状态
            classification_result = self.market_classifier.classify_market_state(technical_data)
            
            # 合并结果
            full_result = self._compile_full_analysis(
                symbol, technical_data, classification_result, start_time
            )
            
            # 缓存结果
            self._cache_analysis(full_result)
            
            # 生成日志
            if self.config.enable_debug_logging:
                self._log_analysis_result(full_result)
            
            return full_result
            
        except Exception as e:
            self.logger.error(f"市场分析失败: {e}", exc_info=True)
            return self._create_error_result(f"分析过程出错: {str(e)}")
    
    def _get_technical_data(self, symbol: str, df: pd.DataFrame, 
                           lookback_days: Optional[int]) -> Dict:
        """
        获取技术数据
        使用现有的技术指标计算工具
        """
        try:
            # 准备数据
            data = df.copy()
            
            # 确保数据格式正确
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in data.columns:
                    return {
                        "success": False,
                        "error": f"缺少必要列: {col}",
                        "symbol": symbol
                    }
            
            # 使用现有的技术指标计算工具
            indicator_results = calculate_all_indicators(data)
            
            if not indicator_results or 'indicators' not in indicator_results:
                return {
                    "success": False,
                    "error": "技术指标计算失败",
                    "symbol": symbol
                }
            
            # 提取最新指标值
            latest_indicators = {}
            indicators_df = indicator_results['indicators']
            
            if not indicators_df.empty:
                latest_row = indicators_df.iloc[-1]
                for col in indicators_df.columns:
                    if col not in ['open', 'high', 'low', 'close', 'volume']:
                        latest_indicators[col] = latest_row[col]
            
            # 计算价格变化
            price_data = {
                'current': data['close'].iloc[-1],
                'open': data['open'].iloc[-1],
                'high': data['high'].iloc[-1],
                'low': data['low'].iloc[-1],
                'volume': data['volume'].iloc[-1]
            }
            
            if len(data) >= 2:
                prev_close = data['close'].iloc[-2]
                current_close = data['close'].iloc[-1]
                price_change_pct = (current_close - prev_close) / prev_close
            else:
                price_change_pct = 0
            
            # 识别关键价格水平（简化版）
            key_levels = self._identify_key_levels(data)
            
            return {
                "success": True,
                "symbol": symbol,
                "latest_indicators": latest_indicators,
                "price_data": price_data,
                "price_change_pct": price_change_pct,
                "key_levels": key_levels,
                "data_points": len(data),
                "timeframe": f"{len(data)}个周期"
            }
            
        except Exception as e:
            self.logger.error(f"获取技术数据失败: {e}")
            return {
                "success": False,
                "error": f"技术数据处理错误: {str(e)}",
                "symbol": symbol
            }
    
    def _identify_key_levels(self, df: pd.DataFrame) -> List[float]:
        """识别关键价格水平"""
        try:
            prices = df['close'].values
            
            if len(prices) < 20:
                return []
            
            # 简单实现：使用近期高低点
            recent_prices = prices[-20:]
            support = np.min(recent_prices)
            resistance = np.max(recent_prices)
            
            # 添加一些中间水平
            levels = [
                support,
                np.percentile(recent_prices, 25),
                np.median(recent_prices),
                np.percentile(recent_prices, 75),
                resistance
            ]
            
            # 去重并排序
            unique_levels = sorted(list(set(round(level, 4) for level in levels if level > 0)))
            
            return unique_levels
            
        except Exception:
            return []
    
    def _compile_full_analysis(self, symbol: str, technical_data: Dict,
                              classification_result: Dict, start_time: datetime) -> Dict:
        """编译完整分析结果"""
        
        analysis_time = datetime.now() - start_time
        
        result = {
            "success": classification_result.get("success", True),
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "analysis_time_ms": analysis_time.total_seconds() * 1000,
            
            # 市场状态
            "market_state": classification_result.get("market_state", MarketState.UNCERTAIN.value),
            "state_chinese": classification_result.get("state_chinese", MarketState.UNCERTAIN.value),
            "confidence": classification_result.get("confidence", 0.0),
            
            # 详细状态
            "sub_states": classification_result.get("sub_states", {}),
            
            # 组件分析
            "components": classification_result.get("components", {}),
            
            # 交易信号
            "trading_signals": classification_result.get("trading_signals", []),
            
            # 摘要和建议
            "summary": classification_result.get("summary", ""),
            "recommendation": classification_result.get("recommendation", ""),
            "market_conditions": classification_result.get("market_conditions", []),
            
            # 元数据
            "metadata": {
                "data_points": technical_data.get("data_points", 0),
                "timeframe": technical_data.get("timeframe", "unknown"),
                "config": {
                    "trending_threshold": self.config.trending_threshold,
                    "rsi_overbought": self.config.rsi_overbought,
                    "rsi_oversold": self.config.rsi_oversold
                }
            },
            
            # 技术数据引用
            "technical_data": {
                "price": technical_data.get("price_data", {}).get("current", 0),
                "price_change_pct": technical_data.get("price_change_pct", 0),
                "key_levels": technical_data.get("key_levels", [])
            }
        }
        
        # 如果有错误
        if not result["success"]:
            result["error"] = classification_result.get("error", "未知错误")
        
        return result
    
    def _create_error_result(self, error_message: str) -> Dict:
        """创建错误结果"""
        return {
            "success": False,
            "error": error_message,
            "timestamp": datetime.now().isoformat(),
            "market_state": MarketState.UNCERTAIN.value,
            "state_chinese": MarketState.UNCERTAIN.value,
            "confidence": 0.0,
            "summary": f"分析失败: {error_message}",
            "recommendation": "无法分析，请检查数据"
        }
    
    def _cache_analysis(self, analysis_result: Dict):
        """缓存分析结果"""
        self._recent_analyses.append(analysis_result)
        
        # 限制缓存大小
        if len(self._recent_analyses) > self._max_cache_size:
            self._recent_analyses = self._recent_analyses[-self._max_cache_size:]
    
    def _log_analysis_result(self, result: Dict):
        """记录分析结果日志"""
        symbol = result.get('symbol', 'Unknown')
        state = result.get('state_chinese', '未知状态')
        confidence = result.get('confidence', 0.0)
        
        self.logger.info(
            f"市场分析完成: {symbol} - {state} (置信度: {confidence:.2f})"
        )
    
    def get_recent_analyses(self, count: int = 10) -> List[Dict]:
        """获取最近的分析结果"""
        return self._recent_analyses[-count:] if self._recent_analyses else []
    
    def get_market_regime(self) -> str:
        """获取当前市场体制"""
        return self.market_classifier.get_market_regime()
    
    def get_state_transitions(self, lookback: int = 10) -> List[Dict]:
        """获取状态转换历史"""
        return self.market_classifier.get_state_transitions(lookback)
    
    def batch_analyze(self, symbols_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """
        批量分析多个品种
        
        Args:
            symbols_data: 字典，key为品种代码，value为DataFrame
            
        Returns:
            字典，key为品种代码，value为分析结果
        """
        results = {}
        
        for symbol, df in symbols_data.items():
            try:
                result = self.analyze_market(symbol, df)
                results[symbol] = result
            except Exception as e:
                self.logger.error(f"批量分析失败 {symbol}: {e}")
                results[symbol] = self._create_error_result(f"批量分析失败: {str(e)}")
        
        return results
    
    def generate_report(self, result: Dict) -> str:
        """生成分析报告"""
        if not result.get('success', False):
            return f"分析失败: {result.get('error', '未知错误')}"
        
        report_lines = []
        report_lines.append("=" * 50)
        report_lines.append(f"市场分析报告 - {result.get('symbol', 'Unknown')}")
        report_lines.append(f"时间: {result.get('timestamp', 'N/A')}")
        report_lines.append("=" * 50)
        
        # 市场状态
        report_lines.append(f"市场状态: {result.get('state_chinese', '未知')}")
        report_lines.append(f"置信度: {result.get('confidence', 0.0):.2f}")
        
        # 子状态
        sub_states = result.get('sub_states', {})
        if sub_states:
            report_lines.append("\n子状态:")
            for key, value in sub_states.items():
                report_lines.append(f"  {key}: {value}")
        
        # 市场条件
        conditions = result.get('market_conditions', [])
        if conditions:
            report_lines.append("\n市场特征:")
            for condition in conditions:
                report_lines.append(f"  • {condition}")
        
        # 交易信号
        signals = result.get('trading_signals', [])
        if signals:
            report_lines.append("\n交易信号:")
            for i, signal in enumerate(signals[:3]):  # 只显示前3个
                action = signal.get('action', 'N/A')
                reason = signal.get('reason', '')
                report_lines.append(f"  {i+1}. {action} - {reason}")
        
        # 建议
        recommendation = result.get('recommendation', '')
        if recommendation:
            report_lines.append(f"\n建议: {recommendation}")
        
        # 摘要
        summary = result.get('summary', '')
        if summary:
            report_lines.append(f"\n摘要: {summary}")
        
        report_lines.append("\n" + "=" * 50)
        
        return "\n".join(report_lines)
    
    def get_statistics(self) -> Dict:
        """获取分析统计信息"""
        if not self._recent_analyses:
            return {"total_analyses": 0}
        
        # 统计各种状态的出现频率
        state_counts = {}
        total_success = 0
        
        for analysis in self._recent_analyses:
            if analysis.get('success', False):
                total_success += 1
                state = analysis.get('market_state', 'unknown')
                state_counts[state] = state_counts.get(state, 0) + 1
        
        total_analyses = len(self._recent_analyses)
        success_rate = total_success / total_analyses if total_analyses > 0 else 0
        
        return {
            "total_analyses": total_analyses,
            "successful_analyses": total_success,
            "success_rate": success_rate,
            "state_distribution": state_counts,
            "cache_size": len(self._recent_analyses)
        }