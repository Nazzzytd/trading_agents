# adaptive_system/state_aware_coordinator.py
"""
市场状态感知协调器 - 连接现有系统和市场状态识别
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .weight_manager import AdaptiveWeightManager
from ..market_analysis.state_recognizer import MarketStateRecognizer

logger = logging.getLogger(__name__)


class StateAwareCoordinator:
    """
    市场状态感知协调器
    负责集成市场状态识别和权重管理
    """
    
    def __init__(self, weight_manager: Optional[AdaptiveWeightManager] = None):
        # 使用现有权重管理器或创建新的
        self.weight_manager = weight_manager or AdaptiveWeightManager(
            enable_market_state=True
        )
        
        # 市场状态识别器
        self.state_recognizer = MarketStateRecognizer()
        
        # 状态历史
        self.state_history = []
        
        logger.info("市场状态感知协调器初始化完成")
    
    def analyze_and_adjust(self, symbol: str, market_data: pd.DataFrame, 
                          agent_predictions: Dict[str, float]) -> Dict[str, Any]:
        """
        完整分析流程：识别状态 → 记录预测 → 调整权重
        
        Args:
            symbol: 交易品种
            market_data: 市场数据DataFrame
            agent_predictions: 智能体预测字典 {agent_name: prediction}
            
        Returns:
            协调结果
        """
        try:
            # 1. 识别市场状态
            market_state_result = self._analyze_market_state(symbol, market_data)
            current_state = market_state_result.get('market_state', '未知')
            state_confidence = market_state_result.get('confidence', 0.0)
            
            # 2. 为每个智能体记录预测
            for agent_name, prediction in agent_predictions.items():
                self.weight_manager.register_agent(agent_name, self._infer_agent_type(agent_name))
                self.weight_manager.record_prediction(agent_name, prediction)
            
            # 3. 等待实际值后记录（这里需要实际调用时传入实际值）
            # 在实际使用中，您需要稍后调用 record_actual 方法
            
            # 4. 基于市场状态更新权重
            updated_weights = {}
            for agent_name in agent_predictions.keys():
                new_weight = self.weight_manager.update_weight(
                    agent_name, 
                    market_state=current_state
                )
                updated_weights[agent_name] = self.weight_manager.get_weight(agent_name)
            
            # 5. 生成协调结果
            result = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "market_state": current_state,
                "state_confidence": state_confidence,
                "state_analysis": market_state_result,
                "agent_count": len(agent_predictions),
                "updated_weights": updated_weights,
                "normalized_weights": self.weight_manager.get_normalized_weights(),
                "performance_summary": self._generate_summary(current_state, updated_weights)
            }
            
            logger.info(f"协调完成: {symbol} - {current_state}, "
                       f"调整了 {len(updated_weights)} 个智能体的权重")
            
            return result
            
        except Exception as e:
            logger.error(f"协调过程失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _analyze_market_state(self, symbol: str, market_data: pd.DataFrame) -> Dict:
        """分析市场状态"""
        try:
            result = self.state_recognizer.analyze_market(symbol, market_data)
            
            # 记录状态历史
            state_entry = {
                "timestamp": datetime.now(),
                "symbol": symbol,
                "state": result.get('market_state', '未知'),
                "confidence": result.get('confidence', 0.0)
            }
            self.state_history.append(state_entry)
            
            # 限制历史长度
            if len(self.state_history) > 1000:
                self.state_history = self.state_history[-1000:]
            
            return result
            
        except Exception as e:
            logger.error(f"市场状态分析失败: {e}")
            return {
                "market_state": "未知",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _infer_agent_type(self, agent_name: str) -> str:
        """从智能体名称推断类型"""
        name_lower = agent_name.lower()
        
        if any(keyword in name_lower for keyword in ['trend', 'momentum']):
            return "trend_analyst"
        elif any(keyword in name_lower for keyword in ['reversion', 'mean']):
            return "reversion_analyst"
        elif any(keyword in name_lower for keyword in ['volatility', 'risk']):
            return "risk_analyst"
        elif any(keyword in name_lower for keyword in ['range', 'channel']):
            return "range_analyst"
        else:
            return "analyst"  # 默认类型
    
    def _generate_summary(self, market_state: str, weights: Dict[str, float]) -> str:
        """生成执行摘要"""
        if not weights:
            return "暂无智能体权重信息"
        
        # 找出权重最高的智能体
        top_agent = max(weights.items(), key=lambda x: x[1])
        
        # 计算权重分布
        weight_values = list(weights.values())
        weight_mean = np.mean(weight_values) if weight_values else 0
        weight_std = np.std(weight_values) if len(weight_values) > 1 else 0
        
        return (f"市场状态: {market_state} | "
                f"顶级智能体: {top_agent[0]}({top_agent[1]:.2f}) | "
                f"平均权重: {weight_mean:.2f}±{weight_std:.2f}")
    
    def get_state_transitions(self, lookback: int = 20) -> List[Dict]:
        """获取状态转换历史"""
        if len(self.state_history) < 2:
            return []
        
        recent_history = self.state_history[-lookback:]
        transitions = []
        
        for i in range(1, len(recent_history)):
            prev = recent_history[i-1]
            curr = recent_history[i]
            
            if prev["state"] != curr["state"]:
                transitions.append({
                    "from": prev["state"],
                    "to": curr["state"],
                    "timestamp": curr["timestamp"],
                    "symbol": curr["symbol"]
                })
        
        return transitions
    
    def get_agent_state_performance(self, agent_name: str) -> Dict:
        """获取智能体在不同状态下的表现分析"""
        return self.weight_manager.analyze_state_performance(agent_name)