# /Users/fr./Downloads/TradingAgents-main/tests/test_adaptive_system.py
import unittest
import tempfile
import os
from typing import Dict
import sys

# 直接添加tradingagents的父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # TradingAgents-main
sys.path.insert(0, project_root)

# 现在应该能正确导入
try:
    from tradingagents.adaptive_system import AdaptiveSystem, AdaptiveConfig
    from tradingagents.adaptive_system.weight_manager import AgentRecord
    print(f"成功导入！当前目录: {current_dir}, 项目根目录: {project_root}")
except ImportError as e:
    print(f"导入失败: {e}")
    print(f"Python路径: {sys.path}")
    print(f"检查目录是否存在: {os.path.join(project_root, 'tradingagents', 'adaptive_system', '__init__.py')}")
    print(f"文件存在: {os.path.exists(os.path.join(project_root, 'tradingagents', 'adaptive_system', '__init__.py'))}")
    raise


class TestAdaptiveSystem(unittest.TestCase):
    """测试 AdaptiveSystem 主类"""
    
    def setUp(self):
        self.system = AdaptiveSystem()
    
    def test_initialization(self):
        """测试系统初始化"""
        self.assertIsNotNone(self.system.config)
        self.assertIsNotNone(self.system.weight_manager)
        self.assertIsNotNone(self.system.layer_manager)
        self.assertIsNotNone(self.system.visualizer)
    
    def test_register_agent(self):
        """测试注册智能体"""
        # 测试链式调用
        result = self.system.register_agent("tech_analyst", "analyst")
        self.assertIs(result, self.system)  # 返回self支持链式调用
        
        # 验证智能体已注册
        agents = self.system.weight_manager.get_all_records()
        self.assertIn("tech_analyst", agents)
        self.assertEqual(agents["tech_analyst"].agent_type, "analyst")
    
    def test_record_prediction(self):
        """测试记录预测"""
        self.system.register_agent("tech_analyst", "analyst")
        result = self.system.record_prediction("tech_analyst", 1.25)
        self.assertTrue(result)
        
        # 验证预测已记录
        agents = self.system.weight_manager.get_all_records()
        self.assertEqual(len(agents["tech_analyst"].predictions), 1)
    
    def test_update_with_result_basic(self):
        """测试基本的结果更新"""
        self.system.register_agent("tech_analyst", "analyst")
        
        # 使用预测和实际值更新
        weight = self.system.update_with_result(
            agent_name="tech_analyst",
            actual_value=1.28,
            prediction=1.25,
            market_volatility=1.0
        )
        
        # 验证权重已更新
        self.assertIsInstance(weight, float)
        self.assertGreater(weight, 0)
        
        # 验证预测和实际值已记录
        agent = self.system.weight_manager.agents["tech_analyst"]
        self.assertEqual(len(agent.predictions), 1)
        self.assertEqual(len(agent.actuals), 1)
    
    def test_update_with_result_without_prediction(self):
        """测试没有提供预测值的结果更新"""
        self.system.register_agent("tech_analyst", "analyst")
        
        # 先记录预测
        self.system.record_prediction("tech_analyst", 1.25)
        
        # 然后只提供实际值更新
        weight = self.system.update_with_result(
            agent_name="tech_analyst",
            actual_value=1.28
        )
        
        self.assertIsInstance(weight, float)
    
    def test_update_with_result_missing_agent(self):
        """测试为未注册智能体更新结果"""
        with self.assertRaises(KeyError):
            self.system.update_with_result(
                agent_name="unknown_agent",
                actual_value=1.28,
                prediction=1.25
            )
    
    def test_get_weighted_decision(self):
        """测试获取加权决策"""
        # 注册两个智能体
        self.system.register_agent("analyst1", "analyst")
        self.system.register_agent("analyst2", "analyst")
        
        # 设置不同权重
        self.system.weight_manager.agents["analyst1"].current_weight = 2.0
        self.system.weight_manager.agents["analyst2"].current_weight = 1.0
        
        # 提供预测
        predictions = {
            "analyst1": 1.2,
            "analyst2": 1.4
        }
        
        result = self.system.get_weighted_decision(predictions)
        
        # 验证返回结果
        self.assertIn("weighted_decision", result)
        self.assertIn("weights", result)
        self.assertIn("raw_predictions", result)
        
        # 验证加权决策计算
        weighted_decision = result["weighted_decision"]
        
        # 归一化权重应该是 2/3 和 1/3
        # 加权决策 = 1.2 * 2/3 + 1.4 * 1/3 = 1.2667
        expected = (1.2 * 2/3) + (1.4 * 1/3)
        self.assertAlmostEqual(weighted_decision, expected, places=4)
    
    def test_get_weighted_decision_empty_predictions(self):
        """测试空预测的加权决策"""
        result = self.system.get_weighted_decision({})
        self.assertEqual(result["weighted_decision"], 0.0)
        self.assertEqual(result["weights"], {})
    
    def test_get_weighted_decision_zero_total_weight(self):
        """测试总权重为零的情况"""
        self.system.register_agent("analyst1", "analyst")
        self.system.register_agent("analyst2", "analyst")
        
        # 设置权重为零
        self.system.weight_manager.agents["analyst1"].current_weight = 0.0
        self.system.weight_manager.agents["analyst2"].current_weight = 0.0
        
        predictions = {"analyst1": 1.2, "analyst2": 1.4}
        result = self.system.get_weighted_decision(predictions)
        
        # 当总权重为零时，应该使用等权重
        self.assertAlmostEqual(result["weights"]["analyst1"], 0.5)
        self.assertAlmostEqual(result["weights"]["analyst2"], 0.5)
    
    def test_visualize_weights(self):
        """测试可视化权重"""
        # 注册智能体并设置一些数据
        self.system.register_agent("analyst1", "analyst")
        self.system.register_agent("analyst2", "analyst")
        
        # 设置权重
        self.system.weight_manager.agents["analyst1"].current_weight = 1.5
        self.system.weight_manager.agents["analyst2"].current_weight = 2.5
        
        # 添加一些误差数据
        self.system.weight_manager.agents["analyst1"].errors = [0.1, 0.2, 0.15]
        self.system.weight_manager.agents["analyst2"].errors = [0.3, 0.4, 0.35]
        
        # 测试可视化
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
            filepath = tmp.name
        
        try:
            result = self.system.visualize_weights(save_path=filepath)
            
            # 验证文件已创建
            self.assertTrue(os.path.exists(filepath))
            self.assertGreater(os.path.getsize(filepath), 0)
        finally:
            # 清理临时文件
            if os.path.exists(filepath):
                os.unlink(filepath)
    
    def test_config_serialization(self):
        """测试配置序列化"""
        # 创建自定义配置
        config = AdaptiveConfig(
            initial_weight=1.5,
            min_weight=0.2,
            max_weight=4.0,
            learning_rate=0.2,
            enable_adaptive_learning=False
        )
        
        # 使用自定义配置创建系统
        system = AdaptiveSystem(config)
        
        self.assertEqual(system.config.initial_weight, 1.5)
        self.assertEqual(system.config.min_weight, 0.2)
        self.assertFalse(system.config.enable_adaptive_learning)
    
    def test_error_recovery(self):
        """测试错误恢复"""
        self.system.register_agent("test_agent", "analyst")
        
        # 尝试无效操作
        result = self.system.record_prediction("test_agent", "invalid")
        self.assertFalse(result)  # 应该返回False而不是崩溃
        
        # 系统应该还能正常工作
        valid_result = self.system.record_prediction("test_agent", 1.2)
        self.assertTrue(valid_result)


class TestAdaptiveConfig(unittest.TestCase):
    """测试 AdaptiveConfig 类"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = AdaptiveConfig()
        
        self.assertEqual(config.initial_weight, 1.0)
        self.assertEqual(config.min_weight, 0.1)
        self.assertEqual(config.max_weight, 5.0)
        self.assertEqual(config.learning_rate, 0.3)
        self.assertTrue(config.enable_adaptive_learning)
    
    def test_config_to_dict(self):
        """测试配置转换为字典"""
        config = AdaptiveConfig()
        config_dict = config.to_dict()
        
        self.assertIn("initial_weight", config_dict)
        self.assertIn("layer_configs", config_dict)
        self.assertIsInstance(config_dict, dict)
    
    def test_config_save_load(self):
        """测试配置保存和加载"""
        config = AdaptiveConfig(
            initial_weight=1.5,
            learning_rate=0.4,
            min_weight=0.2
        )
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as tmp:
            filepath = tmp.name
        
        try:
            # 保存配置
            config.save(filepath)
            self.assertTrue(os.path.exists(filepath))
            
            # 加载配置
            loaded_config = AdaptiveConfig.load(filepath)
            
            # 验证加载的配置
            self.assertEqual(loaded_config.initial_weight, 1.5)
            self.assertEqual(loaded_config.learning_rate, 0.4)
            self.assertEqual(loaded_config.min_weight, 0.2)
            
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)


if __name__ == '__main__':
    unittest.main()