from .utils.agent_utils import create_msg_delete
from .utils.agent_states import AgentState, InvestDebateState, RiskDebateState
from .utils.memory import FinancialSituationMemory

# 导入实际存在的分析师模块（不包含 market_analyst）
try:
    from .analysts.news_analyst import create_news_analyst
except ImportError:
    def create_news_analyst(*args, **kwargs):
        def placeholder(state):
            return {"messages": [], "news_report": "新闻分析师模块不存在"}
        return placeholder

try:
    from .analysts.technical_analyst import create_technical_analyst
except ImportError:
    def create_technical_analyst(*args, **kwargs):
        def placeholder(state):
            return {"messages": [], "technical_report": "技术分析师模块不存在"}
        return placeholder

try:
    from .analysts.quantitative_analyst import create_quantitative_analyst, create_llm_enhanced_quantitative_analyst
except ImportError:
    def create_quantitative_analyst(*args, **kwargs):
        def placeholder(state):
            return {"messages": [], "quantitative_report": "量化分析师模块不存在"}
        return placeholder
    
    def create_llm_enhanced_quantitative_analyst(*args, **kwargs):
        def placeholder(state):
            return {"messages": [], "quantitative_report": "增强量化分析师模块不存在"}
        return placeholder

# ✅ 导入宏观经济分析师
try:
    from .analysts.macro_analyst import create_macro_analyst
except ImportError:
    def create_macro_analyst(*args, **kwargs):
        def placeholder(state):
            return {"messages": [], "macro_report": "宏观经济分析师模块不存在"}
        return placeholder

# 其他模块保持不变
from .researchers.bear_researcher import create_bear_researcher
from .researchers.bull_researcher import create_bull_researcher

from .risk_mgmt.aggresive_debator import create_risky_debator
from .risk_mgmt.conservative_debator import create_safe_debator
from .risk_mgmt.neutral_debator import create_neutral_debator

from .managers.research_manager import create_research_manager
from .managers.risk_manager import create_risk_manager

from .trader.trader import create_trader

__all__ = [
    "FinancialSituationMemory",
    "AgentState",
    "create_msg_delete",
    "InvestDebateState",
    "RiskDebateState",
    "create_bear_researcher",
    "create_bull_researcher",
    "create_research_manager",
    "create_technical_analyst",
    "create_macro_analyst",    # ✅ 添加宏观经济分析师
    "create_neutral_debator",
    "create_news_analyst",
    "create_quantitative_analyst",
    "create_llm_enhanced_quantitative_analyst",
    "create_risky_debator",
    "create_risk_manager",
    "create_safe_debator",
    "create_trader",
]
