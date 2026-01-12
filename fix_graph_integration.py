import re

with open('tradingagents/adaptive_system/graph_integration.py', 'r') as f:
    content = f.read()

# 在create_weight_calculator函数中添加空预测处理
pattern = r'def calculate_weights\(node_data: Dict\[str, Any\]\) -> Dict\[str, Any\]:\s*\n\s*"""\s*\n.*?\s*\n\s*"""\s*\n\s*# 从输入数据中提取预测\s*\n\s*predictions = node_data\.get\(\'predictions\', \{\}\)'

replacement = '''def calculate_weights(node_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        权重计算函数 - 修复版：正确处理空预测数据
        """
        # 从输入数据中提取预测
        predictions = node_data.get('predictions', {})
        market_data = node_data.get('market_data', {})
        actual_value = node_data.get('actual_value')
        
        # ✅ 修复：如果没有预测数据，返回原始数据
        if not predictions:
            # 返回原始数据但标记没有权重计算
            return {
                **node_data,
                "has_weights": False,
                "weighted_decision": None,
                "agent_weights": {},
                "weighted_predictions": {},
                "message": "No predictions provided for weight calculation"
            }'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('tradingagents/adaptive_system/graph_integration.py', 'w') as f:
    f.write(content)

print("修复完成")
