# /Users/fr./Downloads/TradingAgents-main/tests/test_graph_integration_real.py
"""
基于真实tradingagents.graph模块的集成测试
"""
import unittest
import sys
import os
from typing import Dict, Any

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# 导入现有Graph模块
from tradingagents.graph import TradingAgentsGraph, GraphSetup, Propagator
from tradingagents.adaptive_system import GraphIntegrator, AdaptiveSystem


class TestRealGraphIntegration(unittest.TestCase):
    """测试与真实Graph模块的集成"""
    
    def setUp(self):
        """设置测试环境"""
        print("\n" + "="*60)
        print("设置真实Graph集成测试环境")
        print("="*60)
        
        # 1. 创建自适应系统
        self.adaptive_system = AdaptiveSystem()
        
        # 注册典型智能体
        self.agents_config = [
            {"name": "technical_analyst", "layer": "analyst", "desc": "技术分析"},
            {"name": "sentiment_analyst", "layer": "analyst", "desc": "情绪分析"},
            {"name": "fundamental_analyst", "layer": "researcher", "desc": "基本面分析"},
            {"name": "risk_analyst", "layer": "debator", "desc": "风险分析"},
            {"name": "execution_agent", "layer": "trader", "desc": "执行交易"}
        ]
        
        for agent in self.agents_config:
            self.adaptive_system.register_agent(agent["name"], agent["layer"])
            print(f"注册智能体: {agent['name']} ({agent['layer']}) - {agent['desc']}")
        
        # 2. 创建真实交易Graph
        print("\n创建TradingAgentsGraph...")
        self.trading_graph = TradingAgentsGraph()
        
        # 检查Graph结构
        print(f"Graph类型: {type(self.trading_graph)}")
        
        # 尝试获取Graph的内部表示（如果可用）
        if hasattr(self.trading_graph, 'graph'):
            self.graph = self.trading_graph.graph
            print(f"获取到内部Graph对象")
        elif hasattr(self.trading_graph, '_graph'):
            self.graph = self.trading_graph._graph
            print(f"获取到内部_graph对象")
        else:
            # 如果无法获取内部Graph，创建networkx Graph模拟
            import networkx as nx
            self.graph = nx.DiGraph()
            print("创建模拟Graph对象")
        
        # 3. 创建Graph集成器
        self.integrator = GraphIntegrator(self.graph)
        
        # 4. 添加一些测试数据
        self._add_test_data()
    
    def _add_test_data(self):
        """添加测试数据到智能体"""
        print("\n添加测试数据...")
        
        # 添加历史预测和实际值
        historical_data = [
            {
                "actual": 1.2580,
                "predictions": {
                    "technical_analyst": 1.2550,
                    "sentiment_analyst": 1.2600,
                    "fundamental_analyst": 1.2620,
                    "risk_analyst": 1.2570,
                    "execution_agent": 1.2590
                }
            },
            {
                "actual": 1.2620,
                "predictions": {
                    "technical_analyst": 1.2600,
                    "sentiment_analyst": 1.2630,
                    "fundamental_analyst": 1.2650,
                    "risk_analyst": 1.2610,
                    "execution_agent": 1.2630
                }
            }
        ]
        
        for i, data in enumerate(historical_data, 1):
            print(f"  周期 {i}:")
            for agent_name, prediction in data["predictions"].items():
                self.adaptive_system.update_with_result(
                    agent_name=agent_name,
                    actual_value=data["actual"],
                    prediction=prediction
                )
        
        # 显示当前权重
        weights = self.adaptive_system.weight_manager.get_normalized_weights()
        print(f"\n当前归一化权重:")
        for agent, weight in weights.items():
            print(f"  {agent}: {weight:.4f}")
    
    def test_graph_structure_examination(self):
        """检查Graph结构"""
        print("\n测试1: 检查Graph结构")
        
        # 检查Graph类型
        self.assertIsNotNone(self.graph)
        
        # 如果使用networkx，检查基本属性
        if hasattr(self.graph, 'nodes'):
            nodes = list(self.graph.nodes())
            edges = list(self.graph.edges())
            
            print(f"  Graph节点数: {len(nodes)}")
            print(f"  Graph边数: {len(edges)}")
            
            # 如果没有节点，添加一些测试节点
            if len(nodes) == 0:
                print("  添加测试节点到Graph...")
                self._add_test_nodes_to_graph()
    
    def _add_test_nodes_to_graph(self):
        """添加测试节点到Graph"""
        # 添加典型交易流程节点
        test_nodes = [
            ("market_data", {"type": "data_source", "function": "提供市场数据"}),
            ("technical_node", {"type": "analyst", "function": "技术分析"}),
            ("sentiment_node", {"type": "analyst", "function": "情绪分析"}),
            ("fundamental_node", {"type": "researcher", "function": "基本面分析"}),
            ("risk_node", {"type": "debator", "function": "风险评估"}),
            ("consensus", {"type": "decision", "function": "生成共识"}),
            ("trade_decision", {"type": "decision", "function": "交易决策"}),
            ("execution", {"type": "action", "function": "执行交易"})
        ]
        
        test_edges = [
            ("market_data", "technical_node"),
            ("market_data", "sentiment_node"),
            ("market_data", "fundamental_node"),
            ("market_data", "risk_node"),
            ("technical_node", "consensus"),
            ("sentiment_node", "consensus"),
            ("fundamental_node", "consensus"),
            ("risk_node", "consensus"),
            ("consensus", "trade_decision"),
            ("trade_decision", "execution")
        ]
        
        for node, attrs in test_nodes:
            self.graph.add_node(node, **attrs)
        
        for u, v in test_edges:
            self.graph.add_edge(u, v)
        
        print(f"  已添加 {len(test_nodes)} 个节点和 {len(test_edges)} 条边")
    
    def test_find_decision_nodes(self):
        """测试查找决策节点"""
        print("\n测试2: 查找决策节点")
        
        # 确保Graph有节点
        if hasattr(self.graph, 'nodes') and len(list(self.graph.nodes())) == 0:
            self._add_test_nodes_to_graph()
        
        decision_nodes = self.integrator.find_decision_nodes()
        print(f"  找到的决策节点: {decision_nodes}")
        
        # 验证找到的节点包含decision类型
        for node in decision_nodes:
            node_data = self.graph.nodes[node]
            self.assertIn(node_data.get('type', ''), ['decision', 'action', 'trade'])
        
        self.assertGreater(len(decision_nodes), 0)
    
    def test_weight_calculator_creation(self):
        """测试权重计算器创建"""
        print("\n测试3: 创建权重计算器")
        
        calculator = self.integrator.create_weight_calculator(
            self.adaptive_system.weight_manager,
            self.adaptive_system.layer_manager
        )
        
        self.assertTrue(callable(calculator))
        print("  ✓ 权重计算器创建成功")
        
        # 测试计算器功能
        test_data = {
            "predictions": {
                "technical_analyst": 1.2670,
                "sentiment_analyst": 1.2690,
                "fundamental_analyst": 1.2710,
                "risk_analyst": 1.2660,
                "execution_agent": 1.2680
            },
            "market_data": {
                "price": 1.2675,
                "volume": 1500000,
                "timestamp": "2024-01-06T14:30:00Z"
            }
        }
        
        result = calculator(test_data)
        
        # 验证结果
        required_keys = ["weighted_predictions", "weighted_decision", "agent_weights", "has_weights"]
        for key in required_keys:
            self.assertIn(key, result)
            print(f"  ✓ 结果包含: {key}")
        
        self.assertTrue(result["has_weights"])
        self.assertIsInstance(result["weighted_decision"], float)
        
        print(f"  加权决策值: {result['weighted_decision']:.6f}")
        print(f"  智能体权重: {result['agent_weights']}")
    
    def test_weight_node_injection(self):
        """测试权重节点注入"""
        print("\n测试4: 权重节点注入")
        
        # 确保Graph有节点
        if hasattr(self.graph, 'nodes') and len(list(self.graph.nodes())) == 0:
            self._add_test_nodes_to_graph()
        
        # 查找目标节点
        decision_nodes = self.integrator.find_decision_nodes()
        if not decision_nodes:
            print("  ⚠ 未找到决策节点，跳过测试")
            return
        
        target_node = decision_nodes[0]
        print(f"  目标节点: {target_node}")
        
        # 创建权重计算器
        calculator = self.integrator.create_weight_calculator(
            self.adaptive_system.weight_manager,
            self.adaptive_system.layer_manager
        )
        
        # 注入权重节点
        weight_node_name = self.integrator.inject_weight_node(
            target_node,
            calculator
        )
        
        self.assertNotEqual(weight_node_name, "")
        self.assertIn(weight_node_name, self.graph.nodes())
        
        # 验证节点属性
        node_data = self.graph.nodes[weight_node_name]
        self.assertEqual(node_data.get("type"), "weight_calculator")
        
        # 验证边连接
        predecessors = list(self.graph.predecessors(weight_node_name))
        successors = list(self.graph.successors(weight_node_name))
        
        print(f"  注入的权重节点: {weight_node_name}")
        print(f"    前驱节点: {predecessors}")
        print(f"    后继节点: {successors}")
        
        self.assertEqual(successors, [target_node])
    
    def test_full_integration_workflow(self):
        """测试完整集成工作流"""
        print("\n测试5: 完整集成工作流")
        
        # 确保Graph有节点
        if hasattr(self.graph, 'nodes') and len(list(self.graph.nodes())) == 0:
            self._add_test_nodes_to_graph()
        
        # 记录初始状态
        initial_nodes = len(list(self.graph.nodes()))
        initial_edges = len(list(self.graph.edges()))
        
        print(f"  初始状态 - 节点: {initial_nodes}, 边: {initial_edges}")
        
        # 执行集成
        injected_nodes = self.integrator.integrate_with_graph(
            self.adaptive_system.weight_manager,
            self.adaptive_system.layer_manager,
            node_names=None  # 自动查找决策节点
        )
        
        # 验证集成结果
        final_nodes = len(list(self.graph.nodes()))
        final_edges = len(list(self.graph.edges()))
        
        print(f"  最终状态 - 节点: {final_nodes}, 边: {final_edges}")
        print(f"  注入的权重节点: {injected_nodes}")
        
        # 应该注入了权重节点
        self.assertGreater(len(injected_nodes), 0)
        self.assertGreater(final_nodes, initial_nodes)
        self.assertGreater(final_edges, initial_edges)
        
        # 验证每个权重节点
        for weight_node in injected_nodes:
            self.assertIn(weight_node, self.graph.nodes())
            node_data = self.graph.nodes[weight_node]
            self.assertEqual(node_data.get("type"), "weight_calculator")
    
    def test_feedback_mechanism(self):
        """测试反馈机制"""
        print("\n测试6: 反馈机制")
        
        # 确保Graph有节点
        if hasattr(self.graph, 'nodes') and len(list(self.graph.nodes())) == 0:
            self._add_test_nodes_to_graph()
        
        # 添加反馈边
        if "execution" in self.graph.nodes() and "trade_decision" in self.graph.nodes():
            success = self.integrator.add_feedback_edge("execution", "trade_decision")
            self.assertTrue(success)
            
            # 验证反馈边存在
            edges = list(self.graph.edges(data=True))
            feedback_edges = [
                (u, v) for u, v, data in edges
                if data.get("type") == "feedback"
            ]
            
            print(f"  添加的反馈边: {feedback_edges}")
            self.assertEqual(len(feedback_edges), 1)
        else:
            print("  ⚠ 缺少必要的节点，跳过反馈测试")
    
    def test_integration_with_actual_trading_flow(self):
        """测试实际交易流程集成"""
        print("\n测试7: 实际交易流程集成")
        
        # 模拟完整的交易决策流程
        trading_flow_data = {
            "step_1": {
                "node": "market_data",
                "data": {"price": 1.2675, "volume": 2000000}
            },
            "step_2": {
                "node": "technical_node",
                "predictions": {"technical_analyst": 1.2670}
            },
            "step_3": {
                "node": "sentiment_node",
                "predictions": {"sentiment_analyst": 1.2690}
            },
            "step_4": {
                "node": "consensus",
                "predictions": {
                    "technical_analyst": 1.2670,
                    "sentiment_analyst": 1.2690,
                    "fundamental_analyst": 1.2710,
                    "risk_analyst": 1.2660,
                    "execution_agent": 1.2680
                },
                "market_data": {"price": 1.2675}
            }
        }
        
        # 创建权重计算器
        calculator = self.integrator.create_weight_calculator(
            self.adaptive_system.weight_manager,
            self.adaptive_system.layer_manager
        )
        
        # 处理共识节点的数据
        consensus_data = trading_flow_data["step_4"]
        result = calculator(consensus_data)
        
        # 验证决策结果
        self.assertIsNotNone(result["weighted_decision"])
        print(f"  交易决策: {result['weighted_decision']:.6f}")
        
        # 验证权重合理性
        weights = result["agent_weights"]
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=5)
        
        print(f"  权重分布: {weights}")
    
    def test_error_handling_scenarios(self):
        """测试错误处理场景"""
        print("\n测试8: 错误处理场景")
        
        # 测试1: 空Graph
        empty_integrator = GraphIntegrator(None)
        with self.assertRaises(ValueError):
            empty_integrator.integrate_with_graph(
                self.adaptive_system.weight_manager,
                self.adaptive_system.layer_manager
            )
        print("  ✓ 空Graph处理正确")
        
        # 测试2: 不存在的节点
        if hasattr(self.graph, 'nodes'):
            non_existent = self.integrator.inject_weight_node(
                "non_existent_node_123",
                lambda x: x
            )
            self.assertEqual(non_existent, "")
            print("  ✓ 不存在的节点处理正确")
        
        # 测试3: 没有预测数据
        calculator = self.integrator.create_weight_calculator(
            self.adaptive_system.weight_manager,
            self.adaptive_system.layer_manager
        )
        
        empty_data = {"market_data": {"price": 1.25}}
        result = calculator(empty_data)
        self.assertIn("predictions", result)
        print("  ✓ 空预测数据处理正确")


def run_trading_agents_graph_test():
    """专门测试TradingAgentsGraph的集成"""
    print("\n" + "="*60)
    print("测试TradingAgentsGraph直接集成")
    print("="*60)
    
    try:
        # 创建TradingAgentsGraph实例
        from tradingagents.graph import TradingAgentsGraph
        tag = TradingAgentsGraph()
        
        # 检查可用方法
        print(f"TradingAgentsGraph可用方法:")
        methods = [m for m in dir(tag) if not m.startswith('_')]
        for method in methods[:10]:  # 显示前10个方法
            print(f"  - {method}")
        
        # 尝试获取Graph结构
        if hasattr(tag, 'get_graph_structure'):
            structure = tag.get_graph_structure()
            print(f"Graph结构: {structure}")
        
        # 创建自适应系统
        adaptive_system = AdaptiveSystem()
        
        # 创建集成器（需要networkx Graph）
        import networkx as nx
        test_graph = nx.DiGraph()
        integrator = GraphIntegrator(test_graph)
        
        # 演示集成
        print("\n演示集成流程:")
        
        # 1. 添加测试节点
        test_graph.add_node("input", type="data")
        test_graph.add_node("processing", type="processor")
        test_graph.add_node("output", type="decision")
        test_graph.add_edge("input", "processing")
        test_graph.add_edge("processing", "output")
        
        # 2. 集成自适应系统
        injected = integrator.integrate_with_graph(
            adaptive_system.weight_manager,
            adaptive_system.layer_manager,
            ["output"]
        )
        
        print(f"注入的权重节点: {injected}")
        print(f"最终Graph: 节点={test_graph.number_of_nodes()}, 边={test_graph.number_of_edges()}")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # 运行单元测试
    print("运行真实Graph集成测试...")
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestRealGraphIntegration)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 运行专门的TradingAgentsGraph测试
    print("\n" + "="*60)
    print("运行TradingAgentsGraph直接测试")
    print("="*60)
    run_trading_agents_graph_test()
    
    # 总结
    print("\n" + "="*60)
    print("测试完成总结")
    print("="*60)
    print(f"总测试数: {result.testsRun}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("✅ 所有测试通过！")
    else:
        print("❌ 有测试失败")