# adaptive_lightweight_integration.py
"""
轻量级自适应系统集成 - 绕过项目中的导入问题
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from typing import Dict, Any, List, Optional
from tradingagents.adaptive_system import AdaptiveSystem


class LightweightAdaptiveIntegrator:
    """
    轻量级自适应系统集成器
    不依赖有问题的模块，直接与现有功能集成
    """
    
    def __init__(self):
        self.adaptive = AdaptiveSystem()
        self.agent_mapping = {}
    
    def register_existing_agents(self, agent_info: List[tuple]):
        """
        注册现有智能体
        
        Args:
            agent_info: [(agent_name, agent_type), ...] 列表
        """
        for agent_name, agent_type in agent_info:
            self.adaptive.register_agent(agent_name, agent_type)
            self.agent_mapping[agent_name] = agent_type
        
        print(f"✅ 已注册 {len(agent_info)} 个智能体")
    
    def process_agent_predictions(self, predictions: Dict[str, float], 
                                 context: str = "") -> Dict[str, Any]:
        """
        处理智能体预测，返回加权决策
        
        Args:
            predictions: {agent_name: prediction_value}
            context: 可选的上下文信息
        
        Returns:
            包含加权决策和权重的字典
        """
        if not predictions:
            return {"error": "No predictions provided"}
        
        print(f"\n{'='*50}")
        print(f"🔄 自适应权重处理 - {context}")
        print(f"{'='*50}")
        
        # 1. 记录预测
        for agent_name, prediction in predictions.items():
            if agent_name not in self.agent_mapping:
                # 如果未注册，自动注册为分析师
                self.adaptive.register_agent(agent_name, "analyst")
                self.agent_mapping[agent_name] = "analyst"
                print(f"⚠️  自动注册新智能体: {agent_name} (analyst)")
            
            self.adaptive.record_prediction(agent_name, prediction)
        
        # 2. 计算加权决策
        result = self.adaptive.get_weighted_decision(predictions)
        
        # 3. 显示结果
        print(f"\n📊 预测输入:")
        for agent, pred in predictions.items():
            print(f"   {agent:20s}: {pred:7.3f}")
        
        print(f"\n⚖️  自适应权重:")
        for agent, weight in result["weights"].items():
            print(f"   {agent:20s}: {weight:7.3f}")
        
        print(f"\n🎯 加权决策: {result['weighted_decision']:.4f}")
        
        return result
    
    def update_with_market_result(self, actual_change: float, 
                                 agent_names: Optional[List[str]] = None):
        """
        用实际市场结果更新智能体权重
        
        Args:
            actual_change: 实际市场变动 (如 0.01 表示 1% 上涨)
            agent_names: 要更新的智能体列表，None表示更新所有
        """
        if agent_names is None:
            agent_names = list(self.agent_mapping.keys())
        
        print(f"\n📈 更新权重 - 市场实际变动: {actual_change:.2%}")
        
        updated_count = 0
        for agent_name in agent_names:
            if agent_name in self.agent_mapping:
                self.adaptive.update_with_result(agent_name, actual_change)
                updated_count += 1
        
        print(f"✅ 已更新 {updated_count} 个智能体权重")
    
    def simulate_learning_cycle(self, num_cycles: int = 5):
        """
        模拟学习周期，展示自适应系统如何学习
        
        Args:
            num_cycles: 模拟周期数
        """
        print(f"\n{'='*60}")
        print(f"🧠 模拟自适应学习 ({num_cycles} 个周期)")
        print(f"{'='*60}")
        
        # 定义模拟的智能体
        agents = ["Technical", "News", "Macro", "Bull", "Bear"]
        
        # 注册智能体
        agent_info = [(f"{agent} Analyst", "analyst") for agent in agents[:3]]
        agent_info += [(f"{agent} Researcher", "researcher") for agent in agents[3:]]
        self.register_existing_agents(agent_info)
        
        # 模拟多个周期
        for cycle in range(num_cycles):
            print(f"\n📅 周期 {cycle + 1}/{num_cycles}:")
            
            # 生成随机预测（模拟不同智能体的观点）
            import random
            predictions = {}
            for agent in agents:
                agent_name = f"{agent} Analyst" if agent in ["Technical", "News", "Macro"] else f"{agent} Researcher"
                
                # 每个智能体有特定的预测偏差
                if agent == "Technical":
                    base = 0.6 + random.uniform(-0.3, 0.3)
                elif agent == "News":
                    base = 0.2 + random.uniform(-0.4, 0.4)
                elif agent == "Macro":
                    base = 0.4 + random.uniform(-0.3, 0.3)
                elif agent == "Bull":
                    base = 0.8 + random.uniform(-0.2, 0.2)
                else:  # Bear
                    base = -0.3 + random.uniform(-0.3, 0.3)
                
                predictions[agent_name] = max(-1.0, min(1.0, base))
            
            # 处理预测
            result = self.process_agent_predictions(predictions, f"模拟周期 {cycle+1}")
            
            # 模拟实际市场结果（有一定随机性）
            actual_change = random.uniform(-0.05, 0.05)
            
            # 更新权重
            self.update_with_market_result(actual_change)
        
        print(f"\n{'='*60}")
        print(f"✅ 模拟完成！系统已进行 {num_cycles} 轮学习")
        print(f"{'='*60}")
    
    def get_system_summary(self) -> Dict[str, Any]:
        """获取系统摘要"""
        summary = {
            "total_agents": len(self.agent_mapping),
            "agent_types": {},
            "average_weight": 0.0,
            "weight_std": 0.0,
        }
        
        # 统计各类型智能体
        for agent_type in self.agent_mapping.values():
            summary["agent_types"][agent_type] = summary["agent_types"].get(agent_type, 0) + 1
        
        # 计算权重统计
        weights = []
        for agent_name in self.agent_mapping.keys():
            weight = self.adaptive.weight_manager.get_weight(agent_name)
            weights.append(weight)
        
        if weights:
            import numpy as np
            summary["average_weight"] = np.mean(weights)
            summary["weight_std"] = np.std(weights)
            summary["min_weight"] = min(weights)
            summary["max_weight"] = max(weights)
        
        return summary


def create_standalone_adaptive_system():
    """
    创建独立的自适应系统，不依赖有问题的模块
    """
    integrator = LightweightAdaptiveIntegrator()
    
    # 注册您项目中的智能体（根据您的实际智能体调整）
    agent_info = [
        # 分析师团队
        ("Market Analyst", "analyst"),
        ("Social Analyst", "analyst"),
        ("News Analyst", "analyst"),
        ("Technical Analyst", "analyst"),
        ("Quantitative Analyst", "analyst"),
        ("Macro Analyst", "analyst"),
        
        # 研究团队
        ("Bull Researcher", "researcher"),
        ("Bear Researcher", "researcher"),
        
        # 风险管理团队
        ("Risky Analyst", "debator"),
        ("Neutral Analyst", "debator"),
        ("Safe Analyst", "debator"),
        
        # 交易和管理
        ("Trader", "trader"),
        ("Research Manager", "manager"),
        ("Portfolio Manager", "manager"),
    ]
    
    integrator.register_existing_agents(agent_info)
    
    return integrator


# 使用示例
if __name__ == "__main__":
    print("🚀 创建轻量级自适应集成系统...")
    
    try:
        # 创建集成器
        integrator = create_standalone_adaptive_system()
        
        # 选项1：模拟学习周期
        print("\n1. 模拟学习周期演示:")
        integrator.simulate_learning_cycle(num_cycles=3)
        
        # 选项2：手动测试
        print("\n2. 手动测试:")
        print("-" * 40)
        
        # 模拟一次实际预测
        test_predictions = {
            "Technical Analyst": 0.7,
            "News Analyst": -0.2,
            "Macro Analyst": 0.4,
            "Bull Researcher": 0.9,
            "Bear Researcher": -0.5,
            "Trader": 0.3,
        }
        
        result = integrator.process_agent_predictions(
            test_predictions, 
            "手动测试场景"
        )
        
        # 模拟市场结果
        integrator.update_with_market_result(0.02)  # 2% 上涨
        
        # 显示系统摘要
        summary = integrator.get_system_summary()
        print(f"\n📋 系统摘要:")
        print(f"   总智能体数: {summary['total_agents']}")
        print(f"   智能体类型分布: {summary['agent_types']}")
        print(f"   平均权重: {summary['average_weight']:.3f}")
        print(f"   权重标准差: {summary['weight_std']:.3f}")
        
        print("\n✅ 轻量级集成测试完成!")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()