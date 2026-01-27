# adaptive_system/integration_examples.py
"""
集成示例和使用工具
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

from .state_aware_coordinator import StateAwareCoordinator
from .weight_manager import AdaptiveWeightManager

logger = logging.getLogger(__name__)


def create_sample_market_data(days: int = 60) -> pd.DataFrame:
    """创建示例市场数据用于测试"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # 模拟价格数据
    np.random.seed(42)
    base_price = 100.0
    returns = np.random.normal(0.001, 0.02, days)
    prices = base_price * np.exp(np.cumsum(returns))
    
    # 添加一些趋势和震荡模式
    trend = np.linspace(0, 0.1, days)  # 轻微上升趋势
    prices = prices * (1 + trend)
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices * 0.99,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.lognormal(10, 1, days)
    })
    
    df.set_index('date', inplace=True)
    return df


def demonstrate_integration():
    """演示集成功能"""
    print("=" * 60)
    print("市场状态感知自适应系统演示")
    print("=" * 60)
    
    # 1. 创建协调器
    coordinator = StateAwareCoordinator()
    
    # 2. 创建示例数据
    market_data = create_sample_market_data()
    
    # 3. 模拟智能体预测
    agent_predictions = {
        "trend_analyst_1": market_data['close'].iloc[-1] * 1.02,  # 看涨2%
        "reversion_analyst_1": market_data['close'].iloc[-1] * 0.98,  # 看跌2%
        "volatility_analyst_1": market_data['close'].iloc[-1] * 1.01,  # 轻微看涨
        "range_analyst_1": market_data['close'].iloc[-1] * 0.99,  # 轻微看跌
    }
    
    # 4. 执行协调分析
    print("\n📊 执行市场状态感知分析...")
    result = coordinator.analyze_and_adjust(
        symbol="TEST_STOCK",
        market_data=market_data,
        agent_predictions=agent_predictions
    )
    
    # 5. 显示结果
    print(f"\n✅ 分析完成")
    print(f"市场状态: {result['market_state']}")
    print(f"状态置信度: {result['state_confidence']:.2%}")
    print(f"\n📈 智能体权重调整:")
    
    for agent, weight in result['updated_weights'].items():
        normalized = result['normalized_weights'].get(agent, 0)
        print(f"  {agent}: {weight:.3f} (归一化: {normalized:.2%})")
    
    # 6. 模拟后续实际值记录
    print("\n🔄 模拟实际值到达后的权重更新...")
    actual_price = market_data['close'].iloc[-1] * 1.015  # 实际上涨1.5%
    
    for agent_name in agent_predictions.keys():
        coordinator.weight_manager.record_actual(agent_name, actual_price)
    
    # 7. 再次更新权重
    coordinator.weight_manager.update_all_weights_with_state(
        market_state=result['market_state']
    )
    
    print("\n📊 更新后的权重:")
    final_weights = coordinator.weight_manager.get_normalized_weights()
    for agent, weight in final_weights.items():
        print(f"  {agent}: {weight:.2%}")
    
    # 8. 分析性能
    print("\n📋 性能分析:")
    for agent_name in agent_predictions.keys():
        perf = coordinator.get_agent_state_performance(agent_name)
        if perf:
            print(f"\n  {agent_name}:")
            print(f"    全局平均误差: {perf['global_performance']['avg_error']:.4f}")
            
            for state, state_perf in perf['state_performance'].items():
                if state_perf['sample_count'] > 0:
                    print(f"    {state}: 误差={state_perf['avg_error']:.4f} "
                          f"(样本: {state_perf['sample_count']})")
    
    print("\n" + "=" * 60)
    print("演示完成！")
    
    return coordinator, result


class IntegrationTester:
    """集成测试器"""
    
    @staticmethod
    def test_state_weight_interaction():
        """测试状态和权重的交互"""
        # 创建权重管理器
        weight_manager = AdaptiveWeightManager(enable_market_state=True)
        
        # 注册一些测试智能体
        test_agents = [
            ("trend_tracker", "trend_analyst"),
            ("mean_reverter", "reversion_analyst"),
            ("vol_monitor", "risk_analyst"),
            ("range_scanner", "range_analyst")
        ]
        
        for name, agent_type in test_agents:
            weight_manager.register_agent(name, agent_type)
        
        # 测试不同状态下的权重
        test_states = ["上升趋势", "下降趋势", "区间震荡", "高波动"]
        
        results = {}
        for state in test_states:
            weights = weight_manager.get_state_aware_weights(market_state=state)
            results[state] = weights
        
        return results