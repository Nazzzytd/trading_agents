# TradingAgents/graph/setup.py

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode

from tradingagents.agents import *
from tradingagents.agents.utils.agent_states import AgentState

from .conditional_logic import ConditionalLogic


class GraphSetup:
    """Handles the setup and configuration of the agent graph."""

    def __init__(
        self,
        quick_thinking_llm: ChatOpenAI,
        deep_thinking_llm: ChatOpenAI,
        tool_nodes: Dict[str, ToolNode],
        bull_memory,
        bear_memory,
        trader_memory,
        invest_judge_memory,
        risk_manager_memory,
        conditional_logic: ConditionalLogic,
    ):
        """Initialize with required components."""
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.tool_nodes = tool_nodes
        self.bull_memory = bull_memory
        self.bear_memory = bear_memory
        self.trader_memory = trader_memory
        self.invest_judge_memory = invest_judge_memory
        self.risk_manager_memory = risk_manager_memory
        self.conditional_logic = conditional_logic

    def _default_should_continue(self, state: AgentState):
        """默认的继续逻辑"""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return "Msg Clear"

    def setup_graph(
        self, 
        selected_analysts=["social", "news", "technical", "quantitative", "macroeconomic"]  # ❌ 移除 market
    ):
        """Set up and compile the agent workflow graph.

        Args:
            selected_analysts (list): List of analyst types to include. Options are:
                - "social": Social media analyst
                - "news": News analyst
                - "technical": Technical analyst
                - "quantitative": Quantitative analyst
                - "macroeconomic": Macroeconomic analyst
                # "market": Market analyst - ❌ 已移除
        """
        if len(selected_analysts) == 0:
            raise ValueError("Trading Agents Graph Setup Error: no analysts selected!")

        # Create analyst nodes
        analyst_nodes = {}
        delete_nodes = {}
        tool_nodes = {}

        # ❌ 移除市场分析师部分
        
        # 基础分析师
        if "social" in selected_analysts:
            try:
                from tradingagents.agents.analysts.social_media_analyst import create_social_media_analyst
                analyst_nodes["social"] = create_social_media_analyst(
                    self.quick_thinking_llm
                )
                delete_nodes["social"] = create_msg_delete()
                tool_nodes["social"] = self.tool_nodes.get("social", ToolNode([]))
                print("✓ 已加载社交媒体分析师")
            except ImportError as e:
                print(f"警告: 无法导入社交媒体分析师: {e}")

        if "news" in selected_analysts:
            analyst_nodes["news"] = create_news_analyst(
                self.quick_thinking_llm
            )
            delete_nodes["news"] = create_msg_delete()
            tool_nodes["news"] = self.tool_nodes.get("news", ToolNode([]))

        # 新增宏观经济分析师
        if "macroeconomic" in selected_analysts:
            try:
                from tradingagents.agents.analysts.macro_analyst import create_macro_analyst
                analyst_nodes["macroeconomic"] = create_macro_analyst(
                    self.quick_thinking_llm
                )
                delete_nodes["macroeconomic"] = create_msg_delete()
                # 创建宏观经济工具节点
                from tradingagents.agents.utils.macro_data_tools import (
                    get_fred_data,
                    get_ecb_data,
                    get_macro_dashboard,
                )
                macro_tools = [get_fred_data, get_ecb_data, get_macro_dashboard]
                tool_nodes["macroeconomic"] = ToolNode(macro_tools)
                print("✓ 已加载宏观经济分析师")
            except ImportError as e:
                print(f"警告: 无法导入宏观经济分析师: {e}")

        # 新增技术分析师
        if "technical" in selected_analysts:
            try:
                from tradingagents.agents.analysts.technical_analyst import create_technical_analyst
                analyst_nodes["technical"] = create_technical_analyst(
                    self.quick_thinking_llm
                )
                delete_nodes["technical"] = create_msg_delete()
                # 创建技术分析工具节点
                from tradingagents.agents.utils.technical_indicators_tools import (
                    get_technical_indicators_data,
                    get_fibonacci_levels,
                )
                technical_tools = [get_technical_indicators_data, get_fibonacci_levels]
                tool_nodes["technical"] = ToolNode(technical_tools)
                print("✓ 已加载技术分析师")
            except ImportError as e:
                print(f"警告: 无法导入技术分析师: {e}")

        # 新增量化分析师
        if "quantitative" in selected_analysts:
            try:
                from tradingagents.agents.analysts.quantitative_analyst import create_quantitative_analyst
                analyst_nodes["quantitative"] = create_quantitative_analyst(
                    self.quick_thinking_llm
                )
                delete_nodes["quantitative"] = create_msg_delete()
                # 创建量化分析工具节点 - 只使用实际存在的函数
                from tradingagents.agents.utils.quant_data_tools import (
                    get_risk_metrics_data,
                    get_volatility_data,
                    simple_forex_data
                )
                quant_tools = [get_risk_metrics_data, get_volatility_data, simple_forex_data]
                tool_nodes["quantitative"] = ToolNode(quant_tools)
                print("✓ 已加载量化分析师")
            except ImportError as e:
                print(f"警告: 无法导入量化分析师: {e}")

        # Create researcher and manager nodes
        bull_researcher_node = create_bull_researcher(
            self.quick_thinking_llm, self.bull_memory
        )
        bear_researcher_node = create_bear_researcher(
            self.quick_thinking_llm, self.bear_memory
        )
        research_manager_node = create_research_manager(
            self.deep_thinking_llm, self.invest_judge_memory
        )
        trader_node = create_trader(self.quick_thinking_llm, self.trader_memory)

        # Create risk analysis nodes
        risky_analyst = create_risky_debator(self.quick_thinking_llm)
        neutral_analyst = create_neutral_debator(self.quick_thinking_llm)
        safe_analyst = create_safe_debator(self.quick_thinking_llm)
        risk_manager_node = create_risk_manager(
            self.deep_thinking_llm, self.risk_manager_memory
        )

        # Create workflow
        workflow = StateGraph(AgentState)

        # Add analyst nodes to the graph
        for analyst_type, node in analyst_nodes.items():
            workflow.add_node(f"{analyst_type.capitalize()} Analyst", node)
            workflow.add_node(
                f"Msg Clear {analyst_type.capitalize()}", delete_nodes[analyst_type]
            )
            workflow.add_node(f"tools_{analyst_type}", tool_nodes.get(analyst_type, ToolNode([])))

        # Add other nodes
        workflow.add_node("Bull Researcher", bull_researcher_node)
        workflow.add_node("Bear Researcher", bear_researcher_node)
        workflow.add_node("Research Manager", research_manager_node)
        workflow.add_node("Trader", trader_node)
        workflow.add_node("Risky Analyst", risky_analyst)
        workflow.add_node("Neutral Analyst", neutral_analyst)
        workflow.add_node("Safe Analyst", safe_analyst)
        workflow.add_node("Risk Judge", risk_manager_node)

        # Define edges
        # Start with the first analyst
        if not selected_analysts:
            raise ValueError("必须至少选择一个分析师")
        first_analyst = selected_analysts[0]
        workflow.add_edge(START, f"{first_analyst.capitalize()} Analyst")

        # Connect analysts in sequence
        for i, analyst_type in enumerate(selected_analysts):
            current_analyst = f"{analyst_type.capitalize()} Analyst"
            current_tools = f"tools_{analyst_type}"
            current_clear = f"Msg Clear {analyst_type.capitalize()}"

            # 为不同的分析师类型使用相应的条件逻辑
            method_name = f"should_continue_{analyst_type}"
            if hasattr(self.conditional_logic, method_name):
                workflow.add_conditional_edges(
                    current_analyst,
                    getattr(self.conditional_logic, method_name),
                    {
                        current_tools: current_tools,
                        current_clear: current_clear
                    },
                )
            else:
                # 如果没有特定方法，使用默认逻辑
                workflow.add_conditional_edges(
                    current_analyst,
                    self._default_should_continue,
                    {
                        current_tools: current_tools,
                        current_clear: current_clear
                    },
                )
            
            workflow.add_edge(current_tools, current_analyst)

            # Connect to next analyst or to Bull Researcher if this is the last analyst
            if i < len(selected_analysts) - 1:
                next_analyst = f"{selected_analysts[i+1].capitalize()} Analyst"
                workflow.add_edge(current_clear, next_analyst)
            else:
                # 最后一个分析师完成后进入研究员阶段
                workflow.add_edge(current_clear, "Bull Researcher")

        # Add remaining edges
        workflow.add_conditional_edges(
            "Bull Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bear Researcher": "Bear Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_conditional_edges(
            "Bear Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bull Researcher": "Bull Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_edge("Research Manager", "Trader")
        workflow.add_edge("Trader", "Risky Analyst")
        workflow.add_conditional_edges(
            "Risky Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Safe Analyst": "Safe Analyst",
                "Risk Judge": "Risk Judge",
            },
        )
        workflow.add_conditional_edges(
            "Safe Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Neutral Analyst": "Neutral Analyst",
                "Risk Judge": "Risk Judge",
            },
        )
        workflow.add_conditional_edges(
            "Neutral Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Risky Analyst": "Risky Analyst",
                "Risk Judge": "Risk Judge",
            },
        )

        workflow.add_edge("Risk Judge", END)

        # Compile and return
        return workflow.compile()
