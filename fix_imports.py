# fix_imports.py
import os
import sys

def fix_adaptive_system_init():
    """修复 adaptive_system 的 __init__.py 文件"""
    
    init_path = "tradingagents/adaptive_system/__init__.py"
    
    print(f"📝 修复 {init_path}...")
    
    # 创建新的 __init__.py 内容
    new_content = '''"""
自适应权重误差补偿系统
为外汇交易多智能体系统提供动态权重调整功能
"""

from .weight_manager import AdaptiveWeightManager, AgentRecord
from .layer_manager import LayerManager, LayerConfig
from .graph_integration import GraphIntegrator
from .visualization import WeightVisualizer
from .optimization import WeightOptimizer
from .config import AdaptiveConfig

# 简化的主接口类
class AdaptiveSystem:
    """自适应系统主类 - 简化入口"""
    
    def __init__(self, config=None):
        from .config import AdaptiveConfig
        from .weight_manager import AdaptiveWeightManager
        from .layer_manager import LayerManager
        from .visualization import WeightVisualizer
        
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
    
    def update_with_result(self, agent_name: str, actual_value: float):
        """用实际结果更新智能体权重"""
        layer = self.weight_manager.get_agent_layer(agent_name)
        adjusted_weight = self.layer_manager.adjust_weight(
            agent_name, 
            actual_value,
            self.weight_manager.get_agent_error(agent_name),
            layer
        )
        self.weight_manager.update_weight(agent_name, adjusted_weight)
        return adjusted_weight
    
    def get_weighted_decision(self, predictions):
        """获取加权决策"""
        weights = {}
        for agent in predictions.keys():
            weights[agent] = self.weight_manager.get_weight(agent)
        
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
    "LayerConfig"
]
'''
    
    # 写入文件
    with open(init_path, 'w') as f:
        f.write(new_content)
    
    print("✅ __init__.py 已修复")
    
    # 测试导入
    print("\n🧪 测试导入...")
    try:
        sys.path.append('.')
        from tradingagents.adaptive_system import AdaptiveSystem
        print("✅ AdaptiveSystem 导入成功!")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")

if __name__ == "__main__":
    fix_adaptive_system_init()