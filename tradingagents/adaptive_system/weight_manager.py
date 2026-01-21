"""
基础权重管理模块
核心的权重计算、记录和更新逻辑
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple,Any
from datetime import datetime
import logging
from .config import AdaptiveConfig


logger = logging.getLogger(__name__)


@dataclass
class AgentRecord:
    """智能体记录数据类"""
    name: str
    agent_type: str
    current_weight: float = 1.0
    predictions: List[float] = field(default_factory=list)
    actuals: List[float] = field(default_factory=list)
    errors: List[float] = field(default_factory=list)
    weight_history: List[float] = field(default_factory=list)
    last_updated: Optional[datetime] = None
    
    def add_prediction(self, prediction: float):
        """添加预测记录"""
        self.predictions.append(prediction)
    
    def add_actual(self, actual: float):
        """添加实际值记录"""
        self.actuals.append(actual)
        
        # 如果预测和实际值数量匹配，计算误差
        if len(self.predictions) == len(self.actuals):
            latest_pred = self.predictions[-1]
            latest_actual = self.actuals[-1]
            
            # 计算绝对误差
            if latest_actual != 0:
                error = abs(latest_pred - latest_actual) / abs(latest_actual)
            else:
                error = abs(latest_pred)
            
            self.errors.append(error)
            self.last_updated = datetime.now()
    
    def get_recent_errors(self, window: int = 10) -> List[float]:
        """获取最近的误差"""
        return self.errors[-window:] if self.errors else []
    
    def get_average_error(self, window: int = 10) -> float:
        """计算平均误差"""
        recent_errors = self.get_recent_errors(window)
        return np.mean(recent_errors) if recent_errors else 1.0  # 默认误差为1.0


class AdaptiveWeightManager:
    """自适应权重管理器"""
    
    def __init__(self, config: Optional[AdaptiveConfig] = None):
        self.config = config or AdaptiveConfig()
        self.agents: Dict[str, AgentRecord] = {}
        self.history: List[Dict] = []
        
        # 设置日志
        logging.basicConfig(level=getattr(logging, self.config.log_level))
    
    def register_agent(self, name: str, agent_type: str = "analyst"):
        """注册智能体"""
        if name not in self.agents:
            self.agents[name] = AgentRecord(
                name=name, 
                agent_type=agent_type,
                current_weight=self.config.initial_weight
            )
            logger.info(f"注册智能体: {name} ({agent_type})")
        return self
    
    def update_weight(self, agent_name: str, new_weight: Optional[float] = None):
        """更新智能体权重"""
        if agent_name not in self.agents:
            return False
        
        agent = self.agents[agent_name]
        old_weight = agent.current_weight
        
        if new_weight is None:
            new_weight = self.calculate_weight(agent_name)
        
        # 记录权重历史
        agent.weight_history.append(old_weight)
        agent.current_weight = new_weight
        
        # 记录系统历史
        self.history.append({
            "timestamp": datetime.now(),
            "agent": agent_name,
            "old_weight": old_weight,
            "new_weight": new_weight,
            "error": agent.get_average_error() if agent.errors else 0.0
        })
        
        logger.debug(f"更新权重 {agent_name}: {old_weight:.3f} -> {new_weight:.3f}")
        return True
    
    def update_all_weights(self):
        """更新所有智能体权重"""
        for agent_name in self.agents:
            self.update_weight(agent_name)
    
    
    def get_all_weights(self) -> Dict[str, float]:
        """获取所有智能体权重"""
        return {name: agent.current_weight for name, agent in self.agents.items()}
    
    def get_normalized_weights(self) -> Dict[str, float]:
        """获取归一化的权重"""
        weights = self.get_all_weights()
        total = sum(weights.values())
        
        if total > 0 and self.config.enable_weight_normalization:
            return {k: v/total for k, v in weights.items()}
        else:
            # 如果总和为0或禁用归一化，返回等权重
            n = len(weights)
            return {k: 1.0/n for k in weights.keys()}

        
    
    def get_agent_layer(self, agent_name: str) -> str:
        """获取智能体所属层级"""
        if agent_name in self.agents:
            return self.agents[agent_name].agent_type
        return "analyst"  # 默认层级
    
    def get_all_records(self) -> Dict[str, AgentRecord]:
        """获取所有智能体记录"""
        return self.agents.copy()
    
    def reset_agent(self, agent_name: str):
        """重置智能体记录"""
        if agent_name in self.agents:
            agent_type = self.agents[agent_name].agent_type
            self.agents[agent_name] = AgentRecord(
                name=agent_name,
                agent_type=agent_type,
                current_weight=self.config.initial_weight
            )
            logger.info(f"重置智能体: {agent_name}")


    
    def get_weight(self, agent_name: str) -> float:
        """
        获取智能体当前权重
        
        Args:
            agent_name: 智能体名称
            
        Returns:
            智能体的当前权重
            
        Raises:
            KeyError: 如果智能体未注册
            
        Example:
            >>> weight = manager.get_weight("tech_analyst")
            >>> print(f"权重: {weight}")
        """
        if agent_name not in self.agents:
            error_msg = f"智能体 '{agent_name}' 未注册。已注册的智能体: {list(self.agents.keys())}"
            logger.error(error_msg)
            raise KeyError(error_msg)
        
        weight = self.agents[agent_name].current_weight
        logger.debug(f"获取智能体 '{agent_name}' 权重: {weight:.4f}")
        return weight
    
    def get_agent_error(self, agent_name: str, default: float = 1.0) -> float:
        """
        获取智能体误差，带默认值和错误处理
        
        Args:
            agent_name: 智能体名称
            default: 默认误差值，当智能体不存在时返回
            
        Returns:
            智能体的平均误差
        """
        if agent_name not in self.agents:
            logger.warning(f"智能体 '{agent_name}' 未注册，返回默认误差 {default}")
            return default
        
        agent = self.agents[agent_name]
        
        # 检查是否有误差数据
        if not agent.errors:
            logger.debug(f"智能体 '{agent_name}' 暂无误差数据，返回默认误差 {default}")
            return default
        
        error = agent.get_average_error()
        logger.debug(f"智能体 '{agent_name}' 平均误差: {error:.4f}")
        return error
    
    def record_prediction(self, agent_name: str, prediction: float) -> bool:
        """记录智能体预测，增强错误处理"""
        try:
            if agent_name not in self.agents:
                logger.error(f"记录预测失败: 智能体 '{agent_name}' 未注册")
                return False
            
            # 验证预测值
            if not isinstance(prediction, (int, float)):
                logger.error(f"预测值必须是数字，收到: {type(prediction)}")
                return False
            
            self.agents[agent_name].add_prediction(prediction)
            logger.debug(f"记录智能体 '{agent_name}' 预测: {prediction:.4f}")
            return True
            
        except Exception as e:
            logger.error(f"记录预测时发生错误: {str(e)}")
            return False
    
    def record_actual(self, agent_name: str, actual_value: float) -> bool:
        """记录实际值并自动计算误差，增强错误处理"""
        try:
            if agent_name not in self.agents:
                logger.error(f"记录实际值失败: 智能体 '{agent_name}' 未注册")
                return False
            
            # 验证实际值
            if not isinstance(actual_value, (int, float)):
                logger.error(f"实际值必须是数字，收到: {type(actual_value)}")
                return False
            
            # 检查是否有对应的预测
            agent = self.agents[agent_name]
            if not agent.predictions:
                logger.warning(f"智能体 '{agent_name}' 没有预测记录，无法计算误差")
            
            agent.add_actual(actual_value)
            logger.debug(f"记录智能体 '{agent_name}' 实际值: {actual_value:.4f}")
            return True
            
        except Exception as e:
            logger.error(f"记录实际值时发生错误: {str(e)}")
            return False
    
    def calculate_weight(self, agent_name: str) -> float:
        """计算智能体新权重，增强错误处理"""
        try:
            if agent_name not in self.agents:
                logger.warning(f"智能体 '{agent_name}' 未注册，返回默认权重")
                return self.config.initial_weight
            
            agent = self.agents[agent_name]
            avg_error = agent.get_average_error(self.config.error_window_size)
            
            # 防止除零和无效误差
            if avg_error <= 0 or np.isnan(avg_error) or np.isinf(avg_error):
                logger.warning(f"智能体 '{agent_name}' 误差值无效: {avg_error}，使用默认权重")
                return self.config.initial_weight
            
            # 基础权重计算：误差越小，权重越高
            base_weight = 1.0 / avg_error
            
            # 应用学习率
            new_weight = agent.current_weight * (1 - self.config.learning_rate) + \
                        base_weight * self.config.learning_rate
            
            # 验证权重值
            if np.isnan(new_weight) or np.isinf(new_weight):
                logger.error(f"计算出的权重无效: {new_weight}，使用当前权重")
                return agent.current_weight
            
            # 应用权重边界
            new_weight = max(self.config.min_weight, 
                           min(new_weight, self.config.max_weight))
            
            # 应用权重衰减
            new_weight *= self.config.weight_decay
            
            logger.debug(f"智能体 '{agent_name}' 新权重计算: {agent.current_weight:.4f} -> {new_weight:.4f}")
            return new_weight
            
        except Exception as e:
            logger.error(f"计算权重时发生错误: {str(e)}")
            return self.config.initial_weight if agent_name not in self.agents else \
                   self.agents.get(agent_name, AgentRecord("", "")).current_weight
# ==================== 兼容性别名和简单实现 ====================
# 提供兼容性别名以支持现有测试代码

WeightManager = AdaptiveWeightManager

# 简单的兼容性类
class SimpleLayerManager:
    """简化的层管理器（兼容性版本）"""
    def __init__(self, name: str, base_allocation: float = 0.0):
        self.name = name
        self.base_allocation = base_allocation
        self.current_allocation = base_allocation
        self.agents = []

class SimpleAgent:
    """简化的智能体类（兼容性版本）"""
    def __init__(self, name: str, layer: str, base_weight: float = 0.0):
        self.name = name
        self.layer = layer
        self.base_weight = base_weight
        self.current_weight = base_weight
        self.performance_history = []
    
    def record_performance(self, score: float):
        """记录性能"""
        self.performance_history.append(score)
        # 简化权重更新
        if len(self.performance_history) > 5:
            recent_perf = self.performance_history[-5:]
            avg_perf = sum(recent_perf) / len(recent_perf)
            self.current_weight = self.base_weight * avg_perf

# 兼容性导出
LayerManager = SimpleLayerManager
Agent = SimpleAgent

# 导出列表
__all__ = [
    'AdaptiveWeightManager',
    'WeightManager',
    'AgentRecord',
    'LayerManager',
    'Agent',
    'SimpleLayerManager',
    'SimpleAgent'
]
