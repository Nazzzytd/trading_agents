# /Users/fr./Downloads/TradingAgents-main/tradingagents/agents/analysts/quantitative_analyst.py
"""
量化分析师 - 使用LLM分析量化数据
专门分析风险、绩效、相关性等量化指标
"""
from langchain.agents import Tool
from langchain.prompts import PromptTemplate
from typing import Dict, List, Any, Optional
import json

class QuantitativeAnalyst:
    """量化分析师，专门分析量化数据"""
    
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self.system_prompt = self._create_system_prompt()
        
    def _create_system_prompt(self) -> str:
        """创建系统提示"""
        return """你是一个专业的量化分析师，专门分析外汇市场的量化数据。

你的职责：
1. 分析风险指标数据（波动率、最大回撤、夏普比率等）
2. 评估交易策略的表现数据
3. 分析货币对之间的相关性
4. 评估市场波动率特征
5. 基于量化数据提供投资建议

分析要求：
1. 数据驱动：基于提供的量化数据进行分析
2. 专业术语：使用正确的量化金融术语
3. 风险意识：始终考虑风险管理
4. 客观评估：基于数据而非主观判断
5. 实用建议：提供可操作的交易建议

输出格式：
1. 简洁的量化分析总结
2. 关键指标解读
3. 风险评估
4. 具体的交易建议
5. 风险管理提示

记住：你只分析数据，不进行技术指标计算。数据已经由专门的工具计算好了。"""

    def analyze_risk_metrics(self, symbol: str, timeframe: str = "1day") -> str:
        """分析风险指标"""
        prompt = f"""请分析以下货币对的风险指标：

货币对：{symbol}
时间周期：{timeframe}

请提供：
1. 波动率分析：当前波动率水平是否适合交易？
2. 回撤分析：最大回撤是否在可接受范围？
3. 风险调整收益：夏普比率和索提诺比率表现如何？
4. 极端风险：VaR和CVaR揭示了什么风险？
5. 综合风险评估：给出风险评级（低/中/高）
6. 风险管理建议：基于风险指标的交易建议

请基于量化数据分析，不要猜测或假设。"""

        # 使用工具获取数据
        risk_data = self._call_tool("get_risk_metrics_data", 
                                   {"symbol": symbol, "timeframe": timeframe, "periods": 252})
        
        return self._analyze_with_llm(prompt, risk_data)

    def analyze_strategy_performance(self, symbol: str, strategy_type: str, 
                                    parameters: Dict = None) -> str:
        """分析策略表现"""
        if parameters is None:
            parameters = {}
        
        prompt = f"""请分析以下交易策略的表现：

货币对：{symbol}
策略类型：{strategy_type}
策略参数：{parameters}

请评估：
1. 策略盈利能力：平均收益如何？
2. 策略稳定性：胜率是多少？
3. 风险收益比：盈利因子表现如何？
4. 信号质量：信号数量是否足够？
5. 策略有效性：该策略是否有效？
6. 改进建议：如何优化策略？

基于数据说话，不要过度解读。"""

        # 使用工具获取数据
        strategy_data = self._call_tool("get_strategy_performance_data",
                                       {"symbol": symbol, "strategy_type": strategy_type,
                                        "parameters": parameters, "periods": 500})
        
        return self._analyze_with_llm(prompt, strategy_data)

    def analyze_correlation(self, symbols: List[str], timeframe: str = "1day") -> str:
        """分析相关性"""
        prompt = f"""请分析以下货币对之间的相关性：

货币对列表：{', '.join(symbols)}
时间周期：{timeframe}

请分析：
1. 整体相关性特征：哪些货币对相关性高/低？
2. 分散化机会：相关性低的货币对有哪些？
3. 风险集中：相关性高的货币对有哪些风险？
4. 配对交易机会：是否存在高相关性但价差交易的潜力？
5. 投资组合建议：如何构建分散化的投资组合？

基于相关性数据提供实用建议。"""

        # 使用工具获取数据
        correlation_data = self._call_tool("get_correlation_data",
                                          {"symbols": symbols, "timeframe": timeframe, "periods": 90})
        
        return self._analyze_with_llm(prompt, correlation_data)

    def analyze_volatility(self, symbol: str, timeframe: str = "1day") -> str:
        """分析波动率"""
        prompt = f"""请分析以下货币对的波动率特征：

货币对：{symbol}
时间周期：{timeframe}

请分析：
1. 波动率水平：当前波动率处于什么水平？
2. 波动率变化：波动率趋势如何？
3. 日内波动特征：平均日内波幅如何？
4. 波动率聚类：是否存在波动率聚类现象？
5. 交易影响：这样的波动率对交易策略有何影响？
6. 风险管理：基于波动率的头寸管理建议？

基于波动率数据提供专业分析。"""

        # 使用工具获取数据
        volatility_data = self._call_tool("get_volatility_data",
                                         {"symbol": symbol, "timeframe": timeframe, "periods": 60})
        
        return self._analyze_with_llm(prompt, volatility_data)

    def analyze_portfolio_risk(self, symbols: List[str], timeframe: str = "1day") -> str:
        """分析投资组合风险"""
        prompt = f"""请综合分析以下投资组合的风险：

投资组合：{', '.join(symbols)}
时间周期：{timeframe}

请分析：
1. 组合整体风险：投资组合的总体风险特征
2. 相关性风险：各资产相关性带来的风险
3. 分散化效果：投资组合的分散化程度
4. 风险集中度：是否存在风险集中
5. 风险调整收益：投资组合的夏普比率如何？
6. 组合优化建议：如何优化投资组合降低风险？

提供专业的投资组合风险管理建议。"""

        # 获取所有货币对的风险数据
        all_risk_data = {}
        correlation_data = {}
        
        for symbol in symbols:
            risk_data = self._call_tool("get_risk_metrics_data",
                                       {"symbol": symbol, "timeframe": timeframe, "periods": 252})
            all_risk_data[symbol] = risk_data
        
        correlation_data = self._call_tool("get_correlation_data",
                                          {"symbols": symbols, "timeframe": timeframe, "periods": 90})
        
        combined_data = {
            "risk_metrics": all_risk_data,
            "correlation": correlation_data
        }
        
        return self._analyze_with_llm(prompt, json.dumps(combined_data))

    def _call_tool(self, tool_name: str, parameters: Dict) -> str:
        """调用工具获取数据"""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool.func(**parameters)
        return "工具不可用"

    def _analyze_with_llm(self, prompt: str, data: str) -> str:
        """使用LLM分析数据"""
        try:
            # 解析数据
            data_dict = json.loads(data) if isinstance(data, str) else data
            
            if isinstance(data_dict, dict) and not data_dict.get("success", True):
                return f"❌ 数据获取失败: {data_dict.get('error', '未知错误')}"
            
            # 构建完整提示
            full_prompt = f"""{self.system_prompt}

用户请求：
{prompt}

量化数据：
{json.dumps(data_dict, indent=2, ensure_ascii=False)}

请基于以上数据进行分析："""
            
            # 调用LLM
            response = self.llm(full_prompt)
            return response
            
        except Exception as e:
            return f"❌ 分析失败: {str(e)}"

    def create_analysis_report(self, symbol: str, analysis_types: List[str] = None) -> str:
        """创建全面的量化分析报告"""
        if analysis_types is None:
            analysis_types = ["risk", "volatility", "correlation"]
        
        report_parts = [f"# 📊 量化分析报告 - {symbol}", ""]
        
        for analysis_type in analysis_types:
            if analysis_type == "risk":
                analysis = self.analyze_risk_metrics(symbol)
                report_parts.append("## ⚠️ 风险指标分析")
                report_parts.append(analysis)
                
            elif analysis_type == "volatility":
                analysis = self.analyze_volatility(symbol)
                report_parts.append("## 📈 波动率分析")
                report_parts.append(analysis)
                
            elif analysis_type == "correlation":
                # 需要其他货币对作为比较
                default_symbols = ["EUR/USD", "USD/JPY", "GBP/USD"]
                if symbol not in default_symbols:
                    symbols_to_analyze = [symbol] + default_symbols[:2]
                else:
                    symbols_to_analyze = default_symbols
                
                analysis = self.analyze_correlation(symbols_to_analyze)
                report_parts.append("## 🔗 相关性分析")
                report_parts.append(analysis)
        
        report_parts.append("\n## 💡 综合建议")
        report_parts.append("基于以上量化分析，建议：")
        
        # 获取风险数据来做综合建议
        risk_data = self._call_tool("get_risk_metrics_data", 
                                   {"symbol": symbol, "periods": 252})
        
        try:
            risk_dict = json.loads(risk_data)
            if risk_dict.get("success"):
                risk_metrics = risk_dict.get("risk_metrics", {})
                
                sharpe = risk_metrics.get('sharpe_ratio', 0)
                max_dd = risk_metrics.get('max_drawdown', 0)
                vol = risk_metrics.get('annual_volatility', 0)
                
                if sharpe > 1.0 and abs(max_dd) < 0.2 and vol < 0.15:
                    report_parts.append("✅ 适合投资：风险调整收益良好，风险可控")
                elif sharpe > 0.5:
                    report_parts.append("🟢 谨慎投资：有一定盈利潜力，需注意风险管理")
                else:
                    report_parts.append("🔴 避免投资：风险调整收益不佳")
            else:
                report_parts.append("⚠️ 风险评估数据不足，建议保守操作")
                
        except:
            report_parts.append("⚠️ 风险评估数据获取失败，建议谨慎操作")
        
        return "\n".join(report_parts)

# ==================== LangChain工具包装器 ====================

def create_quantitative_tools():
    """创建量化分析工具"""
    from tradingagents.agents.utils.quant_data_tools import (
        get_forex_returns_data,
        get_risk_metrics_data,
        get_correlation_data,
        get_volatility_data,
        get_strategy_performance_data
    )
    
    tools = [
        Tool(
            name="get_forex_returns_data",
            description="获取外汇收益率数据（纯数据）",
            func=get_forex_returns_data.invoke
        ),
        Tool(
            name="get_risk_metrics_data",
            description="获取风险指标数据（纯数据）",
            func=get_risk_metrics_data.invoke
        ),
        Tool(
            name="get_correlation_data",
            description="获取相关性数据（纯数据）",
            func=get_correlation_data.invoke
        ),
        Tool(
            name="get_volatility_data",
            description="获取波动率数据（纯数据）",
            func=get_volatility_data.invoke
        ),
        Tool(
            name="get_strategy_performance_data",
            description="获取策略表现数据（纯数据）",
            func=get_strategy_performance_data.invoke
        )
    ]
    
    return tools

# 使用示例
def create_quantitative_analyst(llm):
    """创建量化分析师实例"""
    tools = create_quantitative_tools()
    analyst = QuantitativeAnalyst(llm, tools)
    return analyst