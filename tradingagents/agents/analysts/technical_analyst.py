from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import logging
from tradingagents.agents.utils.technical_indicators_tools import (
    get_technical_indicators_data,
    get_fibonacci_levels,
    get_technical_data  # 导入数据获取函数供内部使用
)

logger = logging.getLogger(__name__)

def create_technical_analyst(llm):
    """
    创建技术分析师节点
    使用AI对技术指标数据进行深度分析和解读
    """
    def technical_analyst_node(state):
        current_date = state["trade_date"]
        symbol = state.get("currency_pair") or state.get("company_of_interest", "EUR/USD")

        tools = [
            get_technical_indicators_data,  # 获取技术指标数据
            get_fibonacci_levels,           # 获取斐波那契水平
        ]

        system_message = (
            "## 🎯 技术分析师角色说明\n"
            "您是专业的外汇技术分析师，专门对技术指标数据进行深度分析和解读。\n\n"
            
            "## 📊 核心职责\n"
            "1. **技术指标解读** - 使用 get_technical_indicators_data 获取技术指标数据，并进行专业解读\n"
            "2. **斐波那契分析** - 使用 get_fibonacci_levels 分析关键支撑阻力位\n"
            "3. **综合技术分析** - 结合所有技术指标给出专业的交易见解\n\n"
            
            "## 🔧 分析框架\n"
            "- **趋势分析**: 分析移动平均线排列、MACD趋势\n"
            "- **动量分析**: 解读RSI、随机指标的动量状态\n"
            "- **波动分析**: 分析布林带、ATR等波动性指标\n"
            "- **关键价位**: 结合斐波那契水平识别重要支撑阻力\n"
            "- **风险回报**: 基于技术分析评估交易机会的风险回报比\n\n"
            
            "## 📈 输出要求\n"
            "- 提供深度的技术分析结论，而不仅仅是罗列数据\n"
            "- 解释技术指标的含义和市场影响\n"
            "- 给出具体的交易建议和风险提示\n"
            "- 识别关键的技术信号和模式\n"
            "- 如果有明确的交易信号，前缀: **TECHNICAL SIGNAL: BUY/SELL/HOLD**\n\n"
            
            "## 💡 最佳实践\n"
            "- 结合多个技术指标的协同效应\n"
            "- 考虑不同时间框架的技术信号\n"
            "- 提供具体的入场、止损、目标建议\n"
            "- 强调风险管理和资金保护"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "您是专业的技术分析师，负责对技术指标数据进行深度解读和分析。\n"
                    "使用提供的工具获取技术数据，然后运用您的专业知识进行分析。\n"
                    "如果您或其他助手有最终交易建议: **BUY/HOLD/SELL**，请在响应前加上\n"
                    "**FINAL TRANSACTION PROPOSAL: BUY/HOLD/SELL** 以便团队知道停止。\n"
                    "您可以访问以下工具: {tool_names}.\n\n{system_message}\n\n"
                    "参考信息: 当前日期是 {current_date}。我们正在分析 {symbol}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(symbol=symbol)

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content
        else:
            # 如果有工具调用，让图处理执行
            report = "🔄 技术分析进行中..."

        return {
            "messages": [result],
            "technical_report": report,
            "analysis_type": "technical",
            "symbol": symbol
        }

    return technical_analyst_node

def create_advanced_technical_analyst(llm):
    """
    创建高级技术分析师节点
    提供更深入的多维度技术分析
    """
    
    def advanced_technical_analyst_node(state):
        current_date = state["trade_date"]
        symbol = state.get("currency_pair") or state.get("company_of_interest", "EUR/USD")

        tools = [
            get_technical_indicators_data,
            get_fibonacci_levels,
        ]

        system_message = (
            "## 🎯 高级技术分析师角色说明\n"
            "您是资深的外汇技术分析专家，精通多维度技术分析和高级交易策略。\n\n"
            
            "## 📊 高级分析能力\n"
            "1. **多时间框架分析** - 综合分析不同时间框架的技术信号\n"
            "2. **指标协同分析** - 分析多个技术指标之间的协同和背离\n"
            "3. **价格行为分析** - 结合技术指标分析价格行为模式\n"
            "4. **风险管理优化** - 基于技术分析优化交易风险管理\n\n"
            
            "## 🔧 高级分析工具\n"
            "- **艾略特波浪理论** - 识别市场波浪结构\n"
            "- **谐波模式** - 识别蝴蝶、加特利等谐波模式\n"
            "- **市场结构分析** - 分析支撑阻力、趋势线突破\n"
            "- **成交量分析** - 结合成交量确认技术信号\n\n"
            
            "## 📈 专业输出要求\n"
            "- 提供多层次的技术分析视角\n"
            "- 识别高级技术形态和模式\n"
            "- 给出具体的交易计划执行细节\n"
            "- 包含风险回报比计算和仓位管理建议\n"
            "- 前缀明确信号: **ADVANCED TECHNICAL SIGNAL: BUY/SELL/HOLD**\n"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "您是高级技术分析专家，运用专业知识和工具进行深度市场分析。\n"
                    "可用工具: {tool_names}.\n{system_message}\n"
                    "当前日期: {current_date}, 分析标的: {symbol}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(symbol=symbol)

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        return {
            "messages": [result],
            "advanced_technical_report": result.content if len(result.tool_calls) == 0 else "🔬 高级技术分析进行中...",
            "analysis_type": "advanced_technical",
            "symbol": symbol
        }

    return advanced_technical_analyst_node

# 辅助函数：直接获取技术数据供其他组件使用
def get_technical_analysis_data(symbol: str, current_date: str, lookback_days: int = 60) -> dict:
    """
    直接获取技术分析数据
    供其他分析组件使用，不经过LangChain工具
    """
    return get_technical_data(symbol, current_date, lookback_days)