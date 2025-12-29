# 在 TradingAgents-main 目录下创建 simple_test.py
import sys
import os

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 检查 adaptive_system 目录是否存在
adaptive_path = os.path.join('tradingagents', 'adaptive_system')
if not os.path.exists(adaptive_path):
    print(f"❌ 目录不存在: {adaptive_path}")
    print("请确保在 tradingagents/ 目录下创建了 adaptive_system/ 目录")
    exit(1)

print(f"✅ 找到目录: {adaptive_path}")

# 尝试手动导入
try:
    # 先导入模块
    from tradingagents.adaptive_system.weight_manager import AdaptiveWeightManager
    from tradingagents.adaptive_system.layer_manager import LayerManager
    from tradingagents.adaptive_system.visualization import WeightVisualizer
    
    print("✅ 成功导入基础模块")
    
    # 创建一个简化的 AdaptiveSystem 类
    class SimpleAdaptiveSystem:
        def __init__(self):
            self.weight_manager = AdaptiveWeightManager()
            self.layer_manager = LayerManager()
            self.visualizer = WeightVisualizer()
            
        def register_agent(self, name: str, layer: str = "analyst"):
            self.weight_manager.register_agent(name, layer)
            return self
            
        def get_weighted_decision(self, predictions):
            weights = {}
            for agent in predictions.keys():
                weights[agent] = self.weight_manager.get_weight(agent)
            
            total = sum(weights.values())
            if total > 0:
                normalized = {k: v/total for k, v in weights.items()}
            else:
                normalized = {k: 1.0/len(weights) for k in weights.keys()}
            
            weighted_sum = sum(pred * normalized[agent] 
                             for agent, pred in predictions.items())
            
            return {
                "weighted_decision": weighted_sum,
                "weights": normalized
            }
    
    # 测试
    print("\n🚀 测试自适应系统...")
    adaptive = SimpleAdaptiveSystem()
    
    # 注册测试智能体
    adaptive.register_agent("test_analyst_1", "analyst")
    adaptive.register_agent("test_analyst_2", "analyst")
    
    # 模拟预测
    predictions = {
        "test_analyst_1": 0.8,
        "test_analyst_2": 0.3
    }
    
    result = adaptive.get_weighted_decision(predictions)
    print(f"加权决策结果: {result['weighted_decision']:.3f}")
    print(f"权重分布: {result['weights']}")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("\n请检查以下文件是否存在:")
    print("1. tradingagents/adaptive_system/__init__.py")
    print("2. tradingagents/adaptive_system/weight_manager.py")
    print("3. tradingagents/adaptive_system/layer_manager.py")
    print("4. tradingagents/adaptive_system/visualization.py")