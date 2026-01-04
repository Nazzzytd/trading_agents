"""
自适应权重误差补偿系统
为外汇交易多智能体系统提供动态权重调整功能
"""

from typing import Dict, Any, Optional
from .config import AdaptiveConfig
from .weight_manager import AdaptiveWeightManager, AgentRecord
from .layer_manager import LayerManager, AgentLayer
from .graph_integration import GraphIntegrator
from .visualization import WeightVisualizer
from .optimization import WeightOptimizer

# 版本信息
__version__ = "1.0.0"
__author__ = "TradingAgents Adaptive System"

# 简化的主接口
class AdaptiveSystem:
    """自适应系统主类 - 简化入口"""
    
    def __init__(self, config=None):
        self.config = config or AdaptiveConfig()
        self.weight_manager = AdaptiveWeightManager(config=self.config)
        self.layer_manager = LayerManager()
        self.visualizer = WeightVisualizer()
        
    def register_agent(self, name: str, layer: str = "analyst"):
        """注册一个智能体"""
        self.weight_manager.register_agent(name, layer)
        return self
    
    def record_prediction(self, agent_name: str, prediction: float):
        """记录智能体预测"""
        return self.weight_manager.record_prediction(agent_name, prediction)
    

    def update_with_result(self, 
                          agent_name: str, 
                          actual_value: float,
                          prediction: Optional[float] = None,
                          market_volatility: float = 1.0) -> float:
        """
        用实际结果更新智能体权重（修复版）
        
        Args:
            agent_name: 智能体名称
            actual_value: 实际的市场值
            prediction: 预测值（可选，如果之前已记录可省略）
            market_volatility: 市场波动率因子，默认1.0
        
        Returns:
            调整后的权重
            
        注意：
            1. 如果提供了prediction参数，会先记录预测值
            2. 然后记录实际值并自动计算误差
            3. 最后使用误差调整权重
        """
        # 如果提供了预测值，先记录预测
        if prediction is not None:
            self.weight_manager.record_prediction(agent_name, prediction)
        
        # 记录实际值（这会触发误差计算）
        self.weight_manager.record_actual(agent_name, actual_value)
        
        # 获取最新的误差和层级
        current_error = self.weight_manager.get_agent_error(agent_name)
        layer = self.weight_manager.get_agent_layer(agent_name)
        
        if current_error <= 0:
            current_error = 0.001  # 防止除零
        
        # 使用层级管理器调整权重
        adjusted_weight = self.layer_manager.adjust_weight(
            agent_name, 
            current_error,  # 传递误差而不是实际值
            layer,
            market_volatility
        )
        
        # 更新权重管理器中的权重
        self.weight_manager.update_weight(agent_name, adjusted_weight)
        
        # 记录更新日志
        # print(f"权重更新 - 智能体: {agent_name}, 误差: {current_error:.4f}, "
        #       f"新权重: {adjusted_weight:.4f}")
        
        return adjusted_weight
    
    # ... 其他方法保持不变 ...
    def get_weighted_decision(self, predictions: Dict[str, float]) -> Dict:
        """获取加权决策"""
        weights = {}
        for agent, pred in predictions.items():
            weight = self.weight_manager.get_weight(agent)
            weights[agent] = weight
        
        # 归一化权重
        total = sum(weights.values())
        if total > 0:
            normalized = {k: v/total for k, v in weights.items()}
        else:
            normalized = {k: 1.0/len(weights) for k in weights.keys()}
        
        # 计算加权结果
        weighted_sum = sum(pred * normalized[agent] 
                          for agent, pred in predictions.items())
        
        return {
            "weighted_decision": weighted_sum,
            "weights": normalized,
            "raw_predictions": predictions
        }
    
    def visualize_weights(self, save_path: str = "weights_plot.html"):
        """可视化权重"""
        return self.visualizer.plot_weights(self.weight_manager.get_all_records())

__all__ = [
    "AdaptiveSystem",
    "AdaptiveConfig",
    "AdaptiveWeightManager",
    "LayerManager",
    "GraphIntegrator",
    "WeightVisualizer",
    "WeightOptimizer",
    "AgentRecord",
    "AgentLayer"
]