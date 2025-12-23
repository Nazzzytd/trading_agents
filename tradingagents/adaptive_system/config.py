"""
配置管理模块
定义自适应系统的各项参数配置
"""
from dataclasses import dataclass, field
from typing import Dict, Any
import json


@dataclass
class AdaptiveConfig:
    """自适应系统配置类"""
    
    # 基础权重参数
    initial_weight: float = 1.0
    min_weight: float = 0.1
    max_weight: float = 5.0
    
    # 学习率参数
    learning_rate: float = 0.3
    weight_decay: float = 0.99  # 权重衰减因子
    
    # 误差计算窗口
    error_window_size: int = 20  # 计算误差的窗口大小
    recent_weight_factor: float = 2.0  # 近期误差权重因子
    
    # 分层配置
    layer_configs: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "analyst": {
            "adjust_speed": 0.3,
            "min_weight": 0.2,
            "max_weight": 3.0,
            "error_metric": "mape"
        },
        "researcher": {
            "adjust_speed": 0.5,
            "min_weight": 0.1,
            "max_weight": 2.5,
            "error_metric": "binary"
        },
        "debator": {
            "adjust_speed": 0.2,
            "min_weight": 0.3,
            "max_weight": 2.0,
            "error_metric": "consistency"
        },
        "trader": {
            "adjust_speed": 0.1,
            "min_weight": 0.5,
            "max_weight": 4.0,
            "error_metric": "pnl"
        }
    })
    
    # 系统行为
    enable_adaptive_learning: bool = True
    enable_weight_normalization: bool = True
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            k: v for k, v in self.__dict__.items() 
            if not k.startswith('_')
        }
    
    def save(self, filepath: str):
        """保存配置到文件"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'AdaptiveConfig':
        """从文件加载配置"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)