# /Users/fr./Downloads/TradingAgents-main/tests/test_weight_manager.py
import unittest
import numpy as np
from datetime import datetime
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradingagents.adaptive_system.weight_manager import AdaptiveWeightManager, AgentRecord
from tradingagents.adaptive_system.config import AdaptiveConfig


class TestAgentRecord(unittest.TestCase):
    """测试 AgentRecord 类"""
    
    def setUp(self):
        self.record = AgentRecord("test_agent", "analyst")
    
    def test_add_prediction(self):
        """测试添加预测"""
        self.record.add_prediction(1.2)
        self.assertEqual(len(self.record.predictions), 1)
        self.assertEqual(self.record.predictions[0], 1.2)
    
    def test_add_actual_and_calculate_error(self):
        """测试添加实际值并计算误差"""
        self.record.add_prediction(1.2)
        self.record.add_actual(1.0)
        
        self.assertEqual(len(self.record.actuals), 1)
        self.assertEqual(len(self.record.errors), 1)
        self.assertAlmostEqual(self.record.errors[0], 0.2)  # abs(1.2-1.0)/1.0
    
    def test_get_average_error(self):
        """测试获取平均误差"""
        # 添加测试数据
        self.record.errors = [0.1, 0.2, 0.3]
        avg_error = self.record.get_average_error(window=3)
        self.assertAlmostEqual(avg_error, 0.2)
    
    def test_get_average_error_empty(self):
        """测试获取空误差列表的平均误差"""
        avg_error = self.record.get_average_error()
        self.assertEqual(avg_error, 1.0)  # 默认值


class TestAdaptiveWeightManager(unittest.TestCase):
    """测试 AdaptiveWeightManager 类"""
    
    def setUp(self):
        self.config = AdaptiveConfig(
            initial_weight=1.0,
            min_weight=0.1,
            max_weight=5.0,
            learning_rate=0.3,
            error_window_size=5
        )
        self.manager = AdaptiveWeightManager(self.config)
    
    def test_register_agent(self):
        """测试注册智能体"""
        self.manager.register_agent("tech_analyst", "analyst")
        self.assertIn("tech_analyst", self.manager.agents)
        self.assertEqual(self.manager.agents["tech_analyst"].agent_type, "analyst")
    
    def test_get_weight_success(self):
        """测试成功获取权重"""
        self.manager.register_agent("tech_analyst", "analyst")
        weight = self.manager.get_weight("tech_analyst")
        self.assertEqual(weight, 1.0)  # 初始权重
    
    def test_get_weight_agent_not_found(self):
        """测试获取未注册智能体的权重"""
        with self.assertRaises(KeyError):
            self.manager.get_weight("unknown_agent")
    
    def test_record_prediction_success(self):
        """测试成功记录预测"""
        self.manager.register_agent("tech_analyst", "analyst")
        result = self.manager.record_prediction("tech_analyst", 1.25)
        self.assertTrue(result)
        self.assertEqual(len(self.manager.agents["tech_analyst"].predictions), 1)
    
    def test_record_prediction_invalid_agent(self):
        """测试为未注册智能体记录预测"""
        result = self.manager.record_prediction("unknown_agent", 1.25)
        self.assertFalse(result)
    
    def test_record_prediction_invalid_value(self):
        """测试记录无效预测值"""
        self.manager.register_agent("tech_analyst", "analyst")
        result = self.manager.record_prediction("tech_analyst", "invalid")
        self.assertFalse(result)
    
    def test_record_actual_and_calculate_weight(self):
        """测试记录实际值并计算权重"""
        self.manager.register_agent("tech_analyst", "analyst")
        
        # 记录预测和实际值
        self.manager.record_prediction("tech_analyst", 1.2)
        self.manager.record_actual("tech_analyst", 1.0)
        
        # 计算权重
        new_weight = self.manager.calculate_weight("tech_analyst")
        self.assertGreater(new_weight, 1.0)  # 误差为0.2，权重应该增加
    
    def test_get_normalized_weights(self):
        """测试获取归一化权重"""
        self.manager.register_agent("agent1", "analyst")
        self.manager.register_agent("agent2", "researcher")
        
        # 设置不同的权重
        self.manager.agents["agent1"].current_weight = 2.0
        self.manager.agents["agent2"].current_weight = 1.0
        
        normalized = self.manager.get_normalized_weights()
        
        self.assertAlmostEqual(normalized["agent1"], 2.0/3.0)
        self.assertAlmostEqual(normalized["agent2"], 1.0/3.0)
    
    def test_reset_agent(self):
        """测试重置智能体"""
        self.manager.register_agent("tech_analyst", "analyst")
        
        # 添加一些数据
        self.manager.record_prediction("tech_analyst", 1.2)
        self.manager.record_actual("tech_analyst", 1.0)
        self.manager.update_weight("tech_analyst", 2.0)
        
        # 重置
        self.manager.reset_agent("tech_analyst")
        
        agent = self.manager.agents["tech_analyst"]
        self.assertEqual(agent.current_weight, 1.0)  # 恢复初始权重
        self.assertEqual(len(agent.predictions), 0)  # 清空预测
        self.assertEqual(len(agent.actuals), 0)      # 清空实际值
    
    def test_calculate_weight_with_invalid_error(self):
        """测试使用无效误差计算权重"""
        self.manager.register_agent("test_agent", "analyst")
        
        # 设置无效的误差值
        self.manager.agents["test_agent"].errors = [0.0, -1.0]
        
        weight = self.manager.calculate_weight("test_agent")
        self.assertEqual(weight, 1.0)  # 应该返回初始权重
    
    def test_update_all_weights(self):
        """测试更新所有智能体权重"""
        self.manager.register_agent("agent1", "analyst")
        self.manager.register_agent("agent2", "researcher")
        
        # 设置初始权重
        self.manager.agents["agent1"].current_weight = 1.0
        self.manager.agents["agent2"].current_weight = 1.0
        
        # 添加误差数据
        self.manager.agents["agent1"].errors = [0.1]  # 误差小，权重应该增加
        self.manager.agents["agent2"].errors = [0.9]  # 误差大，权重应该减少
        
        self.manager.update_all_weights()
        
        # 验证权重已更新
        self.assertNotEqual(self.manager.agents["agent1"].current_weight, 1.0)
        self.assertNotEqual(self.manager.agents["agent2"].current_weight, 1.0)


if __name__ == '__main__':
    unittest.main()