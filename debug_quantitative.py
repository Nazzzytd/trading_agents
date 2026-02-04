# debug_quantitative.py
import sys
sys.path.insert(0, '.')

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# 创建一个简化的配置
config = DEFAULT_CONFIG.copy()
config.update({
    'project_dir': '/tmp/test',
    'llm_provider': 'openai',
    'deep_think_llm': 'gpt-3.5-turbo',
    'quick_think_llm': 'gpt-3.5-turbo',
    'backend_url': None,
    'results_dir': './results'
})

print("=== 调试量化分析师 ===")

# 1. 检查量化工具函数
print("\n1. 检查量化工具函数:")
try:
    from tradingagents.agents.utils.quant_data_tools import (
        get_risk_metrics_data,
        get_volatility_data,
        simple_forex_data
    )
    print(f"  get_risk_metrics_data: {'可用' if callable(get_risk_metrics_data) else '不可用'}")
    print(f"  get_volatility_data: {'可用' if callable(get_volatility_data) else '不可用'}")
    print(f"  simple_forex_data: {'可用' if callable(simple_forex_data) else '不可用'}")
except Exception as e:
    print(f"  导入失败: {e}")

# 2. 检查量化分析师类
print("\n2. 检查量化分析师类:")
try:
    from tradingagents.agents.analysts.quantitative_analyst import create_quantitative_analyst
    print("  量化分析师类可用")
except Exception as e:
    print(f"  量化分析师类不可用: {e}")

# 3. 尝试创建包含量化分析师的图
print("\n3. 尝试创建图:")
try:
    graph = TradingAgentsGraph(
        selected_analysts=['quantitative'], 
        config=config, 
        debug=False
    )
    print("  ✅ 图创建成功")
    
    # 检查工具节点
    print(f"  工具节点字典: {list(graph.tool_nodes.keys())}")
    
    if 'quantitative' in graph.tool_nodes:
        quant_node = graph.tool_nodes['quantitative']
        print(f"  量化工具节点: {quant_node}")
        print(f"  工具数量: {len(quant_node.tools) if hasattr(quant_node, 'tools') else '未知'}")
    else:
        print("  ❌ 量化工具节点不存在于 tool_nodes 中")
        
except Exception as e:
    print(f"  ❌ 图创建失败: {e}")
    import traceback
    traceback.print_exc()

# 4. 检查图结构
print("\n4. 检查图结构:")
try:
    graph = TradingAgentsGraph(
        selected_analysts=['news', 'quantitative'], 
        config=config, 
        debug=False
    )
    
    print("  图节点:")
    for node_name, node in graph.graph.nodes.items():
        print(f"    {node_name}: {type(node).__name__}")
        
    # 检查是否有 tools_quantitative 节点
    if 'tools_quantitative' in graph.graph.nodes:
        print("  ✅ 'tools_quantitative' 节点存在")
    else:
        print("  ❌ 'tools_quantitative' 节点不存在")
        
except Exception as e:
    print(f"  检查图结构失败: {e}")