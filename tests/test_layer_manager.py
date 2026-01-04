# /Users/fr./Downloads/TradingAgents-main/tests/test_layer_manager.py
import unittest
import numpy as np
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradingagents.adaptive_system.layer_manager import LayerManager, LayerConfig, AgentLayer


class TestLayerManager(unittest.TestCase):
    """测试 LayerManager 类"""
    
    def setUp(self):
        self.manager = LayerManager()
    
    def test_get_layer_config(self):
        """测试获取层级配置"""
        config = self.manager.get_layer_config("analyst")
        self.assertIsInstance(config, LayerConfig)
        self.assertEqual(config.name, "analyst")
    
    def test_get_layer_config_default(self):
        """测试获取不存在的层级配置"""
        config = self.manager.get_layer_config("unknown_layer")
        self.assertEqual(config.name, "analyst")  # 应该返回默认配置
    
    def test_calculate_layer_adjusted_weight_analyst(self):
        """测试分析师层级权重调整"""
        # 误差小，权重应该高
        weight = self.manager.calculate_layer_adjusted_weight(
            1.0, 0.1, "analyst", 1.0
        )
        self.assertGreater(weight, 1.0)
        
        # 误差大，权重应该低
        weight = self.manager.calculate_layer_adjusted_weight(
            1.0, 0.9, "analyst", 1.0
        )
        self.assertLess(weight, 1.0)
    
    def test_calculate_layer_adjusted_weight_trader(self):
        """测试交易员层级权重调整"""
        # 交易员层级有更高的最小权重
        weight = self.manager.calculate_layer_adjusted_weight(
            1.0, 0.9, "trader", 1.0
        )
        config = self.manager.get_layer_config("trader")
        self.assertGreaterEqual(weight, config.min_weight)
    
    def test_adjust_weight_method(self):
        """测试adjust_weight方法"""
        # 测试有效的输入
        weight = self.manager.adjust_weight(
            agent_name="test_agent",
            current_error=0.2,
            layer_name="analyst",
            market_volatility=1.0
        )
        
        config = self.manager.get_layer_config("analyst")
        self.assertGreaterEqual(weight, config.min_weight)
        self.assertLessEqual(weight, config.max_weight)
    
    def test_adjust_weight_with_zero_error(self):
        """测试零误差情况"""
        weight = self.manager.adjust_weight(
            "test_agent", 0.0, "analyst", 1.0
        )
        self.assertIsInstance(weight, float)
        self.assertGreater(weight, 0)
    
    def test_get_suggested_weights(self):
        """测试为多个智能体建议权重"""
        agents_info = {
            "agent1": {"layer": "analyst", "error": 0.1, "volatility": 1.0},
            "agent2": {"layer": "researcher", "error": 0.5, "volatility": 1.0},
            "agent3": {"layer": "trader", "error": 0.3, "volatility": 1.0}
        }
        
        suggested_weights = self.manager.get_suggested_weights(agents_info)
        
        self.assertEqual(len(suggested_weights), 3)
        
        # 误差小的智能体应该有更高的权重
        self.assertGreater(suggested_weights["agent1"], suggested_weights["agent2"])
    
    def test_volatility_tolerance(self):
        """测试市场波动性容忍度"""
        # 高波动性市场应该降低权重
        weight_high_vol = self.manager.calculate_layer_adjusted_weight(
            1.0, 0.2, "analyst", 2.0  # 高波动性
        )
        
        weight_low_vol = self.manager.calculate_layer_adjusted_weight(
            1.0, 0.2, "analyst", 0.5  # 低波动性
        )
        
        self.assertLess(weight_high_vol, weight_low_vol)
    
    def test_layer_boundaries(self):
        """测试层级权重边界"""
        # 测试最小权重边界
        weight = self.manager.calculate_layer_adjusted_weight(
            0.01,  # 非常小的基础权重
            0.9,   # 大误差
            "analyst",
            1.0
        )
        config = self.manager.get_layer_config("analyst")
        self.assertGreaterEqual(weight, config.min_weight)
        
        # 测试最大权重边界
        weight = self.manager.calculate_layer_adjusted_weight(
            10.0,  # 非常大的基础权重
            0.01,  # 小误差
            "analyst",
            1.0
        )
        self.assertLessEqual(weight, config.max_weight)
    
    def test_agent_layer_enum(self):
        """测试AgentLayer枚举"""
        self.assertEqual(AgentLayer.ANALYST.value, "analyst")
        self.assertEqual(AgentLayer.TRADER.value, "trader")
        
        # 测试枚举值转换
        layer = AgentLayer("analyst")
        self.assertEqual(layer, AgentLayer.ANALYST)


if __name__ == '__main__':
    unittest.main()