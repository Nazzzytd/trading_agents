# test_adaptive_integration.py
"""
测试自适应系统与现有Graph的集成
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.adaptive_system import AdaptiveSystem
from tradingagents.graph.trading_graph import TradingAgentsGraph

def test_adaptive_graph_integration():
    """
    测试自适应系统与Graph的集成
    """
    print("🚀 测试自适应Graph集成...")
    
    # 1. 初始化自适应系统
    adaptive = AdaptiveSystem()
    
    # 2. 注册Graph中的智能体
    graph_agents = [
        ("Market Analyst", "analyst"),
        ("News Analyst", "analyst"),
        ("Bull Researcher", "researcher"),
        ("Bear Researcher", "researcher"),
        ("Trader", "trader"),
    ]
    
    for agent_name, agent_type in graph_agents:
        adaptive.register_agent(agent_name, agent_type)
    
    # 3. 模拟Graph运行过程
    print("\n📊 模拟Graph决策过程:")
    
    # 模拟各智能体的预测
    predictions = {
        "Market Analyst": 0.7,      # 看涨
        "News Analyst": -0.3,       # 轻微看跌
        "Bull Researcher": 0.9,     # 强烈看涨
        "Bear Researcher": -0.6,    # 看跌
        "Trader": 0.4,             # 看涨
    }
    
    # 记录预测
    for agent, pred in predictions.items():
        adaptive.record_prediction(agent, pred)
    
    # 获取加权决策
    result = adaptive.get_weighted_decision(predictions)
    
    print(f"🤖 智能体预测: {predictions}")
    print(f"⚖️  自适应权重: {result['weights']}")
    print(f"🎯 加权决策: {result['weighted_decision']:.3f}")
    
    # 4. 模拟市场结果和权重更新
    print("\n📈 模拟市场结果更新:")
    actual_market_move = 0.2  # 实际上涨20%
    
    for agent in predictions.keys():
        adaptive.update_with_result(agent, actual_market_move)
    
    # 查看更新后的权重
    print("🔄 权重已更新")
    
    # 5. 第二次决策（使用更新后的权重）
    print("\n🔄 第二次决策（使用学习后的权重）:")
    predictions_round2 = {
        "Market Analyst": 0.6,
        "News Analyst": 0.1,
        "Bull Researcher": 0.8,
        "Bear Researcher": -0.4,
        "Trader": 0.5,
    }
    
    for agent, pred in predictions_round2.items():
        adaptive.record_prediction(agent, pred)
    
    result2 = adaptive.get_weighted_decision(predictions_round2)
    
    print(f"🤖 第二轮预测: {predictions_round2}")
    print(f"⚖️  更新后的权重: {result2['weights']}")
    print(f"🎯 第二轮决策: {result2['weighted_decision']:.3f}")
    
    return adaptive

if __name__ == "__main__":
    adaptive_system = test_adaptive_graph_integration()
    print("\n✅ 自适应Graph集成测试完成!")