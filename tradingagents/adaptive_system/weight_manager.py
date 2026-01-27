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
from ..market_analysis.state_recognizer import MarketStateRecognizer


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
    state_performance: Dict[str, Dict] = field(default_factory=dict)
    
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

    def get_state_specific_error(self, state: str, window: int = 10) -> float:
        """获取特定市场状态下的误差"""
        if state not in self.state_performance:
            return self.get_average_error(window)  # 回退到全局误差
        
        state_errors = self.state_performance[state].get("errors", [])
        if not state_errors:
            return self.get_average_error(window)
        
        recent_errors = state_errors[-window:]
        return np.mean(recent_errors) if recent_errors else 1.0


class AdaptiveWeightManager:
    """自适应权重管理器（带市场状态感知）"""
    
    def __init__(self, config: Optional[AdaptiveConfig] = None, 
                 enable_market_state: bool = True):
        self.config = config or AdaptiveConfig()
        self.agents: Dict[str, AgentRecord] = {}
        self.history: List[Dict] = []
        
        # 新增：市场状态识别器
        self.enable_market_state = enable_market_state
        self.market_state_recognizer = None
        self.current_market_state = "未知"
        self.state_confidence = 0.0
        
        if enable_market_state:
            try:
                self.market_state_recognizer = MarketStateRecognizer()
                logger.info("市场状态识别器已启用")
            except Exception as e:
                logger.warning(f"市场状态识别器初始化失败: {e}, 将继续使用基础权重计算")
                self.enable_market_state = False
        
        # 状态权重调整配置
        self.state_weight_config = {
            "上升趋势": {
                "trend_analyst": 1.5,
                "momentum_analyst": 1.3,
                "reversion_analyst": 0.7,
                "default": 1.0
            },
            "下降趋势": {
                "trend_analyst": 1.4,
                "reversion_analyst": 0.8,
                "default": 1.0
            },
            "区间震荡": {
                "reversion_analyst": 1.6,
                "range_analyst": 1.4,
                "trend_analyst": 0.6,
                "default": 1.0
            },
            "高波动": {
                "volatility_analyst": 1.5,
                "risk_analyst": 1.3,
                "trend_analyst": 0.8,
                "default": 0.9
            },
            "低波动": {
                "reversion_analyst": 1.2,
                "default": 1.0
            }
        }
        
        logging.basicConfig(level=getattr(logging, self.config.log_level))


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

    # 还需要添加以下基础方法（如果还没有的话）
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
    
    # 4. 新增方法：基于市场状态计算权重
    def calculate_weight_with_state(self, agent_name: str, 
                                   market_state: Optional[str] = None) -> float:
        """
        考虑市场状态的权重计算
        
        Args:
            agent_name: 智能体名称
            market_state: 当前市场状态，如果为None则自动检测
            
        Returns:
            考虑市场状态的新权重
        """
        try:
            # 基础权重计算（使用原有逻辑）
            base_weight = self.calculate_weight(agent_name)
            
            # 如果未启用市场状态或无法获取，返回基础权重
            if not self.enable_market_state or agent_name not in self.agents:
                return base_weight
            
            # 获取或检测市场状态
            if market_state is None and self.market_state_recognizer:
                # 注意：这里需要实际的market_data参数
                # 在实际使用时需要传入数据
                market_state = self.current_market_state
            
            # 获取状态调整因子
            state_factor = self._get_state_factor(agent_name, market_state)
            
            # 应用状态调整（考虑置信度）
            adjusted_weight = base_weight * state_factor
            
            # 记录状态性能
            self._record_state_performance(agent_name, market_state, state_factor)
            
            logger.debug(f"状态感知权重 {agent_name}: "
                        f"基础={base_weight:.3f}, "
                        f"状态因子={state_factor:.3f}, "
                        f"最终={adjusted_weight:.3f} "
                        f"(状态: {market_state})")
            
            return adjusted_weight
            
        except Exception as e:
            logger.error(f"状态感知权重计算失败 {agent_name}: {e}")
            return self.calculate_weight(agent_name)  # 回退到基础计算
    
    def _get_state_factor(self, agent_name: str, market_state: str) -> float:
        """获取状态调整因子"""
        if market_state not in self.state_weight_config:
            return 1.0  # 未知状态，无调整
        
        agent = self.agents[agent_name]
        agent_type = agent.agent_type
        
        # 优先使用智能体类型匹配
        if agent_type in self.state_weight_config[market_state]:
            return self.state_weight_config[market_state][agent_type]
        
        # 使用智能体名称匹配（如果名称包含类型信息）
        for state_agent_type in self.state_weight_config[market_state]:
            if state_agent_type in agent_name.lower():
                return self.state_weight_config[market_state][state_agent_type]
        
        # 使用默认值
        return self.state_weight_config[market_state].get("default", 1.0)
    
    def _record_state_performance(self, agent_name: str, market_state: str, factor: float):
        """记录状态特定的性能"""
        if agent_name not in self.agents:
            return
        
        agent = self.agents[agent_name]
        
        if market_state not in agent.state_performance:
            agent.state_performance[market_state] = {
                "errors": [],
                "weight_multiplier": factor,
                "usage_count": 0
            }
        
        # 记录最近误差
        if agent.errors:
            recent_error = agent.errors[-1] if agent.errors else 1.0
            agent.state_performance[market_state]["errors"].append(recent_error)
            
            # 限制历史记录长度
            max_state_errors = 50
            if len(agent.state_performance[market_state]["errors"]) > max_state_errors:
                agent.state_performance[market_state]["errors"] = \
                    agent.state_performance[market_state]["errors"][-max_state_errors:]
        
        agent.state_performance[market_state]["usage_count"] += 1
    
    # 5. 扩展 update_weight 方法以支持状态感知
    def update_weight(self, agent_name: str, new_weight: Optional[float] = None,
                     market_state: Optional[str] = None) -> bool:
        """更新智能体权重（支持市场状态）"""
        if agent_name not in self.agents:
            return False
        
        agent = self.agents[agent_name]
        old_weight = agent.current_weight
        
        if new_weight is None:
            # 使用状态感知的权重计算
            new_weight = self.calculate_weight_with_state(agent_name, market_state)
        
        # 记录权重历史
        agent.weight_history.append(old_weight)
        agent.current_weight = new_weight
        
        # 记录系统历史
        history_entry = {
            "timestamp": datetime.now(),
            "agent": agent_name,
            "old_weight": old_weight,
            "new_weight": new_weight,
            "error": agent.get_average_error() if agent.errors else 0.0,
            "market_state": market_state or self.current_market_state
        }
        self.history.append(history_entry)
        
        logger.debug(f"更新权重 {agent_name}: {old_weight:.3f} -> {new_weight:.3f} "
                    f"(状态: {market_state or 'N/A'})")
        return True
    
    # 6. 新增方法：批量更新带市场状态
    def update_all_weights_with_state(self, market_state: Optional[str] = None):
        """基于市场状态更新所有智能体权重"""
        if market_state:
            self.current_market_state = market_state
        
        for agent_name in self.agents:
            self.update_weight(agent_name, market_state=market_state)
    
    # 7. 新增方法：获取状态感知的权重
    def get_state_aware_weights(self, market_state: Optional[str] = None) -> Dict[str, float]:
        """获取考虑市场状态的权重"""
        if not self.enable_market_state or market_state is None:
            return self.get_all_weights()
        
        state_weights = {}
        for agent_name in self.agents:
            weight = self.calculate_weight_with_state(agent_name, market_state)
            state_weights[agent_name] = weight
        
        return state_weights
    
    # 8. 新增方法：分析智能体在不同状态下的表现
    def analyze_state_performance(self, agent_name: str) -> Dict:
        """分析智能体在不同市场状态下的表现"""
        if agent_name not in self.agents:
            return {}
        
        agent = self.agents[agent_name]
        analysis = {
            "agent": agent_name,
            "type": agent.agent_type,
            "global_performance": {
                "avg_error": agent.get_average_error(),
                "prediction_count": len(agent.predictions)
            },
            "state_performance": {}
        }
        
        for state, perf_data in agent.state_performance.items():
            errors = perf_data.get("errors", [])
            analysis["state_performance"][state] = {
                "avg_error": np.mean(errors) if errors else None,
                "sample_count": len(errors),
                "weight_multiplier": perf_data.get("weight_multiplier", 1.0),
                "usage_count": perf_data.get("usage_count", 0)
            }
        
        return analysis

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
