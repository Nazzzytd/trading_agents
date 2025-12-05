# TradingAgents/graph/trading_graph.py

import os
from pathlib import Path
import json
from datetime import date
from typing import Dict, Any, Tuple, List, Optional

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.prebuilt import ToolNode

from tradingagents.agents import *
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.memory import FinancialSituationMemory
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)
from tradingagents.dataflows.config import set_config

# Import the new abstract tool methods from agent_utils
from tradingagents.agents.utils.agent_utils import (
    get_forex_data,
    get_indicators,
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement,
    get_news,
    get_insider_sentiment,
    get_insider_transactions,
    get_global_news
)

# 导入新的技术分析和量化分析工具
from tradingagents.agents.utils.technical_indicators_tools import (
    get_technical_indicators_data,
    get_fibonacci_levels,
)

from tradingagents.agents.utils.quant_data_tools import (
    get_factor_analysis,
    validate_technical_signal,
    calculate_risk_metrics
)

from .conditional_logic import ConditionalLogic
from .setup import GraphSetup
from .propagation import Propagator
from .reflection import Reflector
from .signal_processing import SignalProcessor


class TradingAgentsGraph:
    """Main class that orchestrates the trading agents framework."""

    def __init__(
        self,
        selected_analysts=["market", "social", "news", "technical", "quantitative"],
        debug=False,
        config: Dict[str, Any] = None,
    ):
        """Initialize the trading agents graph and components.

        Args:
            selected_analysts: List of analyst types to include
            debug: Whether to run in debug mode
            config: Configuration dictionary. If None, uses default config
        """
        self.debug = debug
        self.config = config or DEFAULT_CONFIG

        # Update the interface's config
        set_config(self.config)

        # Create necessary directories
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        # Initialize LLMs
        if self.config["llm_provider"].lower() == "openai" or self.config["llm_provider"] == "ollama" or self.config["llm_provider"] == "openrouter":
            self.deep_thinking_llm = ChatOpenAI(model=self.config["deep_think_llm"], base_url=self.config["backend_url"])
            self.quick_thinking_llm = ChatOpenAI(model=self.config["quick_think_llm"], base_url=self.config["backend_url"])
        elif self.config["llm_provider"].lower() == "anthropic":
            self.deep_thinking_llm = ChatAnthropic(model=self.config["deep_think_llm"], base_url=self.config["backend_url"])
            self.quick_thinking_llm = ChatAnthropic(model=self.config["quick_think_llm"], base_url=self.config["backend_url"])
        elif self.config["llm_provider"].lower() == "google":
            self.deep_thinking_llm = ChatGoogleGenerativeAI(model=self.config["deep_think_llm"])
            self.quick_thinking_llm = ChatGoogleGenerativeAI(model=self.config["quick_think_llm"])
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config['llm_provider']}")
        
        # Initialize memories
        self.bull_memory = FinancialSituationMemory("bull_memory", self.config)
        self.bear_memory = FinancialSituationMemory("bear_memory", self.config)
        self.trader_memory = FinancialSituationMemory("trader_memory", self.config)
        self.invest_judge_memory = FinancialSituationMemory("invest_judge_memory", self.config)
        self.risk_manager_memory = FinancialSituationMemory("risk_manager_memory", self.config)

        # Create tool nodes
        self.tool_nodes = self._create_tool_nodes()

        # Initialize components
        self.conditional_logic = ConditionalLogic()
        self.graph_setup = GraphSetup(
            self.quick_thinking_llm,
            self.deep_thinking_llm,
            self.tool_nodes,
            self.bull_memory,
            self.bear_memory,
            self.trader_memory,
            self.invest_judge_memory,
            self.risk_manager_memory,
            self.conditional_logic,
        )

        self.propagator = Propagator()
        self.reflector = Reflector(self.quick_thinking_llm)
        self.signal_processor = SignalProcessor(self.quick_thinking_llm)

        # State tracking
        self.curr_state = None
        self.ticker = None
        self.log_states_dict = {}  # date to full state dict

        # Set up the graph
        self.graph = self.graph_setup.setup_graph(selected_analysts)

    def _create_tool_nodes(self) -> Dict[str, ToolNode]:
        """Create tool nodes for different data sources using abstract methods."""
        # 基础工具集合
        base_tools = {
            "market": ToolNode(
                [
                    # Core forex data tools
                    get_forex_data,
                    # Technical indicators
                    get_indicators,
                ]
            ),
            "social": ToolNode(
                [
                    # News tools for social media analysis
                    get_news,
                ]
            ),
            "news": ToolNode(
                [
                    # News and insider information
                    get_news,
                    get_global_news,
                    get_insider_sentiment,
                    get_insider_transactions,
                ]
            ),
        }
        
        # 技术分析工具节点
        technical_tools = [
            get_technical_indicators_data,
            get_fibonacci_levels,
        ]
        
        # 量化分析工具节点
        quant_tools = [
            get_factor_analysis,
            validate_technical_signal,
            calculate_risk_metrics,
        ]
        
        # 更新工具节点字典
        base_tools["technical"] = ToolNode(technical_tools)
        base_tools["quantitative"] = ToolNode(quant_tools)
        
        return base_tools

    def propagate(self, company_name, trade_date):
        """Run the trading agents graph for a company on a specific date."""

        self.ticker = company_name

        # Initialize state
        init_agent_state = self.propagator.create_initial_state(
            company_name, trade_date
        )
        
        # 确保state包含所有新的分析类型
        for analyst_type in ["technical", "quantitative"]:
            if f"{analyst_type}_report" not in init_agent_state:
                init_agent_state[f"{analyst_type}_report"] = ""
        
        args = self.propagator.get_graph_args()

        if self.debug:
            # Debug mode with tracing
            trace = []
            for chunk in self.graph.stream(init_agent_state, **args):
                if len(chunk["messages"]) == 0:
                    pass
                else:
                    chunk["messages"][-1].pretty_print()
                    trace.append(chunk)

            final_state = trace[-1]
        else:
            # Standard mode without tracing
            final_state = self.graph.invoke(init_agent_state, **args)

        # Store current state for reflection
        self.curr_state = final_state

        # Log state
        self._log_state(trade_date, final_state)

        # Return decision and processed signal
        return final_state, self.process_signal(final_state["final_trade_decision"])

    def _log_state(self, trade_date, final_state):
        """Log the final state to a JSON file."""
        # 准备所有可能报告的字段
        report_fields = [
            "market_report", "sentiment_report", "news_report", 
            "technical_report", "quantitative_report"
        ]
        
        # 构建日志字典
        log_dict = {
            "company_of_interest": final_state["company_of_interest"],
            "trade_date": final_state["trade_date"],
        }
        
        # 添加所有存在的报告
        for field in report_fields:
            if field in final_state:
                log_dict[field] = final_state[field]
        
        # 添加辩论状态
        log_dict["investment_debate_state"] = {
            "bull_history": final_state.get("investment_debate_state", {}).get("bull_history", []),
            "bear_history": final_state.get("investment_debate_state", {}).get("bear_history", []),
            "history": final_state.get("investment_debate_state", {}).get("history", []),
            "current_response": final_state.get("investment_debate_state", {}).get("current_response", ""),
            "judge_decision": final_state.get("investment_debate_state", {}).get("judge_decision", ""),
        }
        
        log_dict["trader_investment_decision"] = final_state.get("trader_investment_plan", "")
        log_dict["risk_debate_state"] = {
            "risky_history": final_state.get("risk_debate_state", {}).get("risky_history", []),
            "safe_history": final_state.get("risk_debate_state", {}).get("safe_history", []),
            "neutral_history": final_state.get("risk_debate_state", {}).get("neutral_history", []),
            "history": final_state.get("risk_debate_state", {}).get("history", []),
            "judge_decision": final_state.get("risk_debate_state", {}).get("judge_decision", ""),
        }
        log_dict["investment_plan"] = final_state.get("investment_plan", "")
        log_dict["final_trade_decision"] = final_state.get("final_trade_decision", "")

        # 保存到log字典
        self.log_states_dict[str(trade_date)] = log_dict

        # Save to file
        directory = Path(f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/")
        directory.mkdir(parents=True, exist_ok=True)

        with open(
            f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/full_states_log_{trade_date}.json",
            "w",
        ) as f:
            json.dump(self.log_states_dict, f, indent=4)

    def reflect_and_remember(self, returns_losses):
        """Reflect on decisions and update memory based on returns."""
        # 获取当前状态中所有的分析报告
        reports = {}
        for report_type in ["technical", "quantitative"]:
            if self.curr_state and f"{report_type}_report" in self.curr_state:
                reports[report_type] = self.curr_state[f"{report_type}_report"]
        
        # 更新各个记忆组件，传递分析报告
        self.reflector.reflect_bull_researcher(
            self.curr_state, returns_losses, self.bull_memory, reports
        )
        self.reflector.reflect_bear_researcher(
            self.curr_state, returns_losses, self.bear_memory, reports
        )
        self.reflector.reflect_trader(
            self.curr_state, returns_losses, self.trader_memory, reports
        )
        self.reflector.reflect_invest_judge(
            self.curr_state, returns_losses, self.invest_judge_memory, reports
        )
        self.reflector.reflect_risk_manager(
            self.curr_state, returns_losses, self.risk_manager_memory, reports
        )

    def process_signal(self, full_signal):
        """Process a signal to extract the core decision."""
        return self.signal_processor.process_signal(full_signal)
    
    def get_recommended_analysts(self, strategy_type: str = "forex") -> List[str]:
        """Get recommended analyst configurations based on strategy type.
        
        Args:
            strategy_type: Type of trading strategy. Options: "forex", "equity", "crypto"
        
        Returns:
            List of recommended analyst types
        """
        recommendations = {
            "forex": ["news", "technical", "quantitative"],  # 外汇交易推荐配置
            "equity": ["news", "fundamentals", "technical", "quantitative"],  # 股票交易
            "crypto": ["news", "social", "technical", "quantitative"],  # 加密货币
            "quick": ["technical", "quantitative"],  # 快速分析
            "full": ["market", "social", "news", "technical", "quantitative"],  # 完整分析
        }
        
        return recommendations.get(strategy_type, ["technical", "quantitative"])
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update configuration and reinitialize components.
        
        Args:
            new_config: New configuration dictionary
        """
        self.config.update(new_config)
        set_config(self.config)
        
        # Reinitialize LLMs with new config
        if self.config["llm_provider"].lower() == "openai" or self.config["llm_provider"] == "ollama" or self.config["llm_provider"] == "openrouter":
            self.deep_thinking_llm = ChatOpenAI(model=self.config["deep_think_llm"], base_url=self.config["backend_url"])
            self.quick_thinking_llm = ChatOpenAI(model=self.config["quick_think_llm"], base_url=self.config["backend_url"])
        elif self.config["llm_provider"].lower() == "anthropic":
            self.deep_thinking_llm = ChatAnthropic(model=self.config["deep_think_llm"], base_url=self.config["backend_url"])
            self.quick_thinking_llm = ChatAnthropic(model=self.config["quick_think_llm"], base_url=self.config["backend_url"])
        elif self.config["llm_provider"].lower() == "google":
            self.deep_thinking_llm = ChatGoogleGenerativeAI(model=self.config["deep_think_llm"])
            self.quick_thinking_llm = ChatGoogleGenerativeAI(model=self.config["quick_think_llm"])
        
        # Reinitialize memories
        self.bull_memory = FinancialSituationMemory("bull_memory", self.config)
        self.bear_memory = FinancialSituationMemory("bear_memory", self.config)
        self.trader_memory = FinancialSituationMemory("trader_memory", self.config)
        self.invest_judge_memory = FinancialSituationMemory("invest_judge_memory", self.config)
        self.risk_manager_memory = FinancialSituationMemory("risk_manager_memory", self.config)
        
        # Recreate tool nodes
        self.tool_nodes = self._create_tool_nodes()
        
        # Reinitialize GraphSetup
        self.graph_setup = GraphSetup(
            self.quick_thinking_llm,
            self.deep_thinking_llm,
            self.tool_nodes,
            self.bull_memory,
            self.bear_memory,
            self.trader_memory,
            self.invest_judge_memory,
            self.risk_manager_memory,
            self.conditional_logic,
        )

    def get_analysis_summary(self, state: Dict[str, Any] = None) -> Dict[str, str]:
        """Get a summary of all analysis reports.
        
        Args:
            state: Optional state dictionary. If None, uses current state.
        
        Returns:
            Dictionary with analysis summaries
        """
        if state is None:
            state = self.curr_state
        
        if state is None:
            return {"error": "No analysis state available"}
        
        summary = {}
        report_fields = [
            ("market_report", "市场分析"),
            ("sentiment_report", "情绪分析"), 
            ("news_report", "新闻分析"),
            ("technical_report", "技术分析"),
            ("quantitative_report", "量化分析")
        ]
        
        for field, name in report_fields:
            if field in state and state[field]:
                # 提取前200个字符作为摘要
                content = state[field]
                if len(content) > 200:
                    summary[name] = content[:200] + "..."
                else:
                    summary[name] = content
            else:
                summary[name] = "无数据"
        
        return summary