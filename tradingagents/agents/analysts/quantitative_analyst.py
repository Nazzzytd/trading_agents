"""
量化分析师
"""
from langchain_core.tools import Tool
from typing import List
import logging

logger = logging.getLogger(__name__)

class QuantitativeAnalyst:
    """量化分析师"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.name = "Quantitative Analyst"
        self.description = "专门负责量化分析和风险建模的分析师"
        
    def get_tools(self) -> List[Tool]:
        """获取量化分析工具"""
        tools = []
        
        try:
            from tradingagents.agents.utils.quant_data_tools import (
                get_risk_metrics_data,
                get_volatility_data,
                simple_forex_data
            )
            
            # 注意：@tool 装饰器已经将函数转换为 Tool 对象
            # 直接添加这些工具对象
            
            # 检查并添加工具
            tool_list = [
                (get_risk_metrics_data, "风险指标工具"),
                (get_volatility_data, "波动率工具"),
                (simple_forex_data, "简化数据工具")
            ]
            
            for tool_obj, tool_name in tool_list:
                if tool_obj:
                    # 确保是 Tool 对象
                    if isinstance(tool_obj, Tool):
                        tools.append(tool_obj)
                        print(f'✓ 添加 {tool_name}: {tool_obj.name}')
                    else:
                        print(f'⚠️ {tool_name} 不是 Tool 对象: {type(tool_obj)}')
            
            logger.info(f"量化分析师加载了 {len(tools)} 个工具")
            
        except ImportError as e:
            logger.warning(f"量化数据工具导入失败: {e}")
            # 创建占位符工具
            placeholder = Tool(
                name="quantitative_placeholder",
                func=lambda *args, **kwargs: f"量化工具不可用: {e}",
                description="量化分析占位符工具"
            )
            tools.append(placeholder)
            print(f'⚠️ 使用占位符工具: {placeholder.name}')
        
        return tools
    
    def get_description(self) -> str:
        return self.description
    
    def get_name(self) -> str:
        return self.name

def create_quantitative_analyst(config=None):
    """创建量化分析师工厂函数"""
    return QuantitativeAnalyst(config)
