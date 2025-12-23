"""
Graph系统集成模块
将自适应权重系统集成到现有Graph流程中
"""
from typing import Dict, List, Any, Optional
import networkx as nx


class GraphIntegrator:
    """Graph系统集成器"""
    
    def __init__(self, trading_graph: Optional[nx.DiGraph] = None):
        self.trading_graph = trading_graph
        self.weight_nodes = {}  # 存储添加的权重计算节点
    
    def set_graph(self, trading_graph: nx.DiGraph):
        """设置交易Graph"""
        self.trading_graph = trading_graph
    
    def find_decision_nodes(self) -> List[str]:
        """找到Graph中的决策节点"""
        if not self.trading_graph:
            return []
        
        decision_nodes = []
        for node in self.trading_graph.nodes():
            node_data = self.trading_graph.nodes[node]
            
            # 根据节点属性或名称判断是否为决策节点
            if any(keyword in str(node).lower() for keyword in 
                  ['decision', 'consensus', 'final', 'execute', 'trade']):
                decision_nodes.append(node)
            elif node_data.get('type') in ['decision', 'action', 'trade']:
                decision_nodes.append(node)
        
        return decision_nodes
    
    def inject_weight_node(self, target_node: str, 
                          weight_calculator: callable) -> str:
        """
        在目标节点前注入权重计算节点
        
        Args:
            target_node: 目标节点名称
            weight_calculator: 权重计算函数
        
        Returns:
            创建的权重节点名称
        """
        if not self.trading_graph or target_node not in self.trading_graph:
            return ""
        
        # 创建权重节点
        weight_node_name = f"weight_calc_{target_node}_{len(self.weight_nodes)}"
        
        # 添加权重节点
        self.trading_graph.add_node(
            weight_node_name,
            type="weight_calculator",
            function=weight_calculator,
            description=f"为 {target_node} 计算智能体权重"
        )
        
        # 获取目标节点的所有前驱节点
        predecessors = list(self.trading_graph.predecessors(target_node))
        
        # 重新连接边
        for pred in predecessors:
            # 获取边的属性
            edge_attrs = self.trading_graph.get_edge_data(pred, target_node)
            
            # 移除原边
            self.trading_graph.remove_edge(pred, target_node)
            
            # 添加新边：前驱 -> 权重节点
            self.trading_graph.add_edge(pred, weight_node_name, **edge_attrs)
        
        # 添加边：权重节点 -> 目标节点
        self.trading_graph.add_edge(
            weight_node_name, 
            target_node,
            type="weighted_decision"
        )
        
        # 保存节点信息
        self.weight_nodes[weight_node_name] = {
            "target": target_node,
            "predecessors": predecessors,
            "calculator": weight_calculator
        }
        
        return weight_node_name
    
    def create_weight_calculator(self, weight_manager, layer_manager):
        """创建权重计算函数"""
        def calculate_weights(node_data: Dict[str, Any]) -> Dict[str, Any]:
            """
            权重计算函数，将在Graph节点中调用
            
            Args:
                node_data: 节点数据，包含市场数据和预测
            
            Returns:
                包含权重信息的更新数据
            """
            # 从输入数据中提取预测
            predictions = node_data.get('predictions', {})
            market_data = node_data.get('market_data', {})
            
            if not predictions:
                return node_data
            
            # 获取所有智能体权重
            raw_weights = weight_manager.get_all_weights()
            
            # 使用层级管理器调整权重
            agents_info = {}
            for agent_name, pred in predictions.items():
                error = weight_manager.get_agent_error(agent_name)
                layer = weight_manager.get_agent_layer(agent_name)
                agents_info[agent_name] = {
                    "layer": layer,
                    "error": error,
                    "prediction": pred
                }
            
            # 获取层级调整后的权重
            suggested_weights = layer_manager.get_suggested_weights(agents_info)
            
            # 更新权重管理器中的权重
            for agent_name, new_weight in suggested_weights.items():
                weight_manager.update_weight(agent_name, new_weight)
            
            # 获取归一化权重
            normalized_weights = weight_manager.get_normalized_weights()
            
            # 计算加权预测
            weighted_predictions = {}
            weighted_sum = 0.0
            
            for agent_name, pred in predictions.items():
                weight = normalized_weights.get(agent_name, 0.0)
                weighted_value = pred * weight
                weighted_predictions[agent_name] = weighted_value
                weighted_sum += weighted_value
            
            # 返回更新后的数据
            return {
                **node_data,
                "weighted_predictions": weighted_predictions,
                "weighted_decision": weighted_sum,
                "agent_weights": normalized_weights,
                "raw_weights": raw_weights,
                "has_weights": True
            }
        
        return calculate_weights
    
    def integrate_with_graph(self, weight_manager, layer_manager, 
                           node_names: Optional[List[str]] = None):
        """
        将自适应系统集成到Graph中
        
        Args:
            weight_manager: 权重管理器实例
            layer_manager: 层级管理器实例
            node_names: 要集成的节点列表，为None则自动查找决策节点
        """
        if not self.trading_graph:
            raise ValueError("未设置交易Graph")
        
        # 创建权重计算函数
        weight_calculator = self.create_weight_calculator(
            weight_manager, layer_manager
        )
        
        # 确定要注入的节点
        if node_names:
            target_nodes = node_names
        else:
            target_nodes = self.find_decision_nodes()
        
        # 注入权重节点
        injected_nodes = []
        for target_node in target_nodes:
            weight_node = self.inject_weight_node(target_node, weight_calculator)
            if weight_node:
                injected_nodes.append(weight_node)
        
        return injected_nodes
    
    def add_feedback_edge(self, from_node: str, to_node: str):
        """添加反馈边，用于权重更新"""
        if not self.trading_graph:
            return False
        
        if from_node in self.trading_graph and to_node in self.trading_graph:
            self.trading_graph.add_edge(
                from_node, to_node,
                type="feedback",
                description="权重更新反馈"
            )
            return True
        
        return False
    
    def get_weighted_path(self, start_node: str, end_node: str) -> List[str]:
        """获取包含权重计算的路径"""
        if not self.trading_graph:
            return []
        
        try:
            path = nx.shortest_path(self.trading_graph, start_node, end_node)
            
            # 标记路径中的权重节点
            weighted_path = []
            for node in path:
                if node in self.weight_nodes:
                    weighted_path.append(f"[WEIGHT]{node}")
                else:
                    weighted_path.append(node)
            
            return weighted_path
        except nx.NetworkXNoPath:
            return []
    
    def visualize_integration(self):
        """可视化集成结果"""
        if not self.trading_graph:
            return None
        
        # 创建带颜色标记的Graph可视化
        import matplotlib.pyplot as plt
        
        pos = nx.spring_layout(self.trading_graph, seed=42)
        
        # 节点颜色
        node_colors = []
        for node in self.trading_graph.nodes():
            if node in self.weight_nodes:
                node_colors.append('lightgreen')  # 权重节点
            elif any(keyword in str(node).lower() for keyword in 
                    ['decision', 'consensus', 'final']):
                node_colors.append('lightblue')   # 决策节点
            else:
                node_colors.append('lightgray')   # 普通节点
        
        plt.figure(figsize=(12, 8))
        nx.draw(self.trading_graph, pos, 
               node_color=node_colors,
               with_labels=True,
               node_size=1500,
               font_size=8,
               arrows=True)
        
        plt.title("自适应权重系统集成图")
        plt.tight_layout()
        
        return plt