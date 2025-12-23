"""
分层权重管理模块
不同层级的智能体使用不同的权重调整策略
"""
from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum
import numpy as np


class AgentLayer(Enum):
    """智能体层级枚举"""
    ANALYST = "analyst"      # 分析师：技术、新闻、宏观等
    RESEARCHER = "researcher" # 研究员：多方、空方
    DEBATOR = "debator"     # 辩论者：风险讨论
    TRADER = "trader"       # 交易员：最终执行
    MANAGER = "manager"     # 管理器：协调决策


@dataclass
class LayerConfig:
    """层级配置"""
    name: str
    adjust_speed: float      # 调整速度：0-1，越高调整越快
    min_weight: float       # 最小权重
    max_weight: float       # 最大权重
    error_metric: str       # 误差衡量标准
    volatility_tolerance: float = 1.0  # 波动容忍度


class LayerManager:
    """分层管理器"""
    
    def __init__(self):
        # 默认层级配置
        self.layers: Dict[str, LayerConfig] = {
            "analyst": LayerConfig(
                name="analyst",
                adjust_speed=0.3,
                min_weight=0.2,
                max_weight=3.0,
                error_metric="mape",  # 平均绝对百分比误差
                volatility_tolerance=0.8
            ),
            "researcher": LayerConfig(
                name="researcher",
                adjust_speed=0.5,    # 研究员调整更快
                min_weight=0.1,
                max_weight=2.5,
                error_metric="binary",  # 二分类正确率
                volatility_tolerance=1.2
            ),
            "debator": LayerConfig(
                name="debator",
                adjust_speed=0.2,    # 辩论者调整更谨慎
                min_weight=0.3,
                max_weight=2.0,
                error_metric="consistency",  # 一致性评分
                volatility_tolerance=0.5
            ),
            "trader": LayerConfig(
                name="trader",
                adjust_speed=0.1,    # 交易员调整最慢
                min_weight=0.5,
                max_weight=4.0,
                error_metric="pnl",  # 盈亏指标
                volatility_tolerance=1.0
            ),
            "manager": LayerConfig(
                name="manager",
                adjust_speed=0.4,
                min_weight=0.8,
                max_weight=2.0,
                error_metric="composite",  # 综合指标
                volatility_tolerance=1.0
            )
        }
    
    def get_layer_config(self, layer_name: str) -> LayerConfig:
        """获取层级配置"""
        return self.layers.get(layer_name, self.layers["analyst"])
    
    def calculate_layer_adjusted_weight(self, 
                                     base_weight: float,
                                     error: float,
                                     layer_name: str,
                                     market_volatility: float = 1.0) -> float:
        """根据层级计算调整后的权重"""
        config = self.get_layer_config(layer_name)
        
        # 基于层级和误差调整权重
        if config.error_metric == "mape":
            # 平均绝对百分比误差：误差越小权重越高
            adjustment = 1.0 / (error + 0.001)
        elif config.error_metric == "binary":
            # 二分类：正确率高权重高
            adjustment = 2.0 if error < 0.5 else 0.5
        elif config.error_metric == "pnl":
            # 盈亏：盈利时权重增加
            adjustment = 1.0 + (1.0 - error) * 2.0
        else:
            # 默认调整
            adjustment = 1.0 / (error + 0.1)
        
        # 应用层级调整速度
        adjusted_weight = base_weight * (1 - config.adjust_speed) + \
                         adjustment * config.adjust_speed
        
        # 考虑市场波动性
        volatility_factor = market_volatility / config.volatility_tolerance
        adjusted_weight *= (1.0 / volatility_factor)
        
        # 应用层级权重边界
        adjusted_weight = max(config.min_weight, 
                            min(adjusted_weight, config.max_weight))
        
        return adjusted_weight
    
    def adjust_weight(self, 
                     agent_name: str,
                     actual_value: float,
                     current_error: float,
                     layer_name: str) -> float:
        """调整智能体权重（简化接口）"""
        config = self.get_layer_config(layer_name)
        
        # 基于误差计算新权重
        if current_error <= 0:
            current_error = 0.001
        
        new_weight = 1.0 / (current_error + 0.01)  # 基础计算
        
        # 应用层级调整
        new_weight = self.calculate_layer_adjusted_weight(
            new_weight, current_error, layer_name
        )
        
        return new_weight
    
    def get_suggested_weights(self, agents_info: Dict[str, Dict]) -> Dict[str, float]:
        """为多个智能体建议权重"""
        suggested = {}
        
        for agent_name, info in agents_info.items():
            layer = info.get("layer", "analyst")
            error = info.get("error", 1.0)
            volatility = info.get("volatility", 1.0)
            
            suggested[agent_name] = self.calculate_layer_adjusted_weight(
                1.0, error, layer, volatility
            )
        
        return suggested