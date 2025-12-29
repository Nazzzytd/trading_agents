# 快速测试脚本 test_adaptive.py
import sys
sys.path.append('.')

from tradingagents.adaptive_system import AdaptiveSystem

# 1. 初始化自适应系统
adaptive = AdaptiveSystem()

# 2. 注册智能体（与您现有系统对应）
adaptive.register_agent("technical_analyst", "analyst")
adaptive.register_agent("news_analyst", "analyst")
adaptive.register_agent("macro_analyst", "analyst")
adaptive.register_agent("bull_researcher", "researcher")
adaptive.register_agent("bear_researcher", "researcher")
adaptive.register_agent("trader", "trader")

# 3. 模拟一个交易周期
# 假设智能体们做出了预测
predictions = {
    "technical_analyst": 0.8,    # 看涨
    "news_analyst": -0.3,        # 轻微看跌
    "macro_analyst": 0.5,        # 看涨
    "bull_researcher": 1.0,      # 强烈看涨
    "bear_researcher": -0.7,     # 看跌
    "trader": 0.2               # 轻微看涨
}

# 4. 获取加权决策
result = adaptive.get_weighted_decision(predictions)
print(f"加权决策: {result['weighted_decision']:.3f}")
print("各智能体权重:", result['weights'])

# 5. 模拟实际市场结果（+0.3表示上涨3%）
actual_market_move = 0.3

# 6. 更新智能体权重（基于预测误差）
for agent_name, prediction in predictions.items():
    # 计算预测误差（绝对误差）
    error = abs(prediction - actual_market_move)
    adaptive.update_with_result(agent_name, actual_market_move)

# 7. 可视化权重
adaptive.visualize_weights("test_weights.html")
print("可视化已保存到 test_weights.html")