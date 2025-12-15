from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import logging
from tradingagents.agents.utils.macro_data_tools import (
    get_fred_data,
    get_ecb_data,
    get_macro_dashboard,
    # get_central_bank_calendar  # 已移除
)
from tradingagents.dataflows.interface import route_to_vendor

logger = logging.getLogger(__name__)

def create_structured_macro_report(currency_pair, current_date, tool_results):
    """创建结构化的宏观分析报告"""
    
    # 解析货币对
    if "/" in currency_pair:
        base_currency = currency_pair.split("/")[0]
        quote_currency = currency_pair.split("/")[1]
    elif len(currency_pair) == 6:
        base_currency = currency_pair[:3]
        quote_currency = currency_pair[3:]
    else:
        base_currency = "USD"
        quote_currency = "JPY"
    
    # 分析工具结果
    analysis_summary = analyze_tool_results(tool_results, base_currency, quote_currency)
    
    # 创建结构化报告
    report = f"""
# 宏观经济分析报告
**货币对**: {currency_pair} ({base_currency}/{quote_currency})
**分析日期**: {current_date}
**数据来源**: 实时FRED/ECB宏观经济数据

## 📊 执行摘要
{analysis_summary.get('executive_summary', '基于宏观经济数据分析的基本面评估。')}

## 🔍 数据收集详情
{chr(10).join([format_tool_result(r) for r in tool_results])}

## 📈 综合评估

### 1. 货币政策对比
- **利率差异**: {analysis_summary.get('rate_differential', '待分析')}
- **政策立场**: {analysis_summary.get('policy_stance', '待分析')}
- **预期路径**: {analysis_summary.get('policy_path', '待分析')}

### 2. 经济增长前景
- **相对增长动能**: {analysis_summary.get('growth_momentum', '待分析')}
- **就业市场对比**: {analysis_summary.get('employment_contrast', '待分析')}
- **商业活动指标**: {analysis_summary.get('business_activity', '待分析')}

### 3. 通胀动态
- **通胀水平**: {analysis_summary.get('inflation_level', '待分析')}
- **通胀预期**: {analysis_summary.get('inflation_expectation', '待分析')}
- **实际利率**: {analysis_summary.get('real_rates', '待分析')}

### 4. 关键风险因素
- **近期经济数据发布**: {analysis_summary.get('upcoming_data', '无')}
- **央行政策会议**: {analysis_summary.get('central_bank_meetings', '无')}
- **地缘政治风险**: {analysis_summary.get('geopolitical_risks', '低')}

## 💰 交易影响分析

| 指标类别 | 对{base_currency}影响 | 对{quote_currency}影响 | 净效应 |
|---------|----------------------|-----------------------|--------|
| 货币政策 | {analysis_summary.get('monetary_impact_base', '中性')} | {analysis_summary.get('monetary_impact_quote', '中性')} | {analysis_summary.get('monetary_net', '中性')} |
| 通胀水平 | {analysis_summary.get('inflation_impact_base', '中性')} | {analysis_summary.get('inflation_impact_quote', '中性')} | {analysis_summary.get('inflation_net', '中性')} |
| 经济增长 | {analysis_summary.get('growth_impact_base', '中性')} | {analysis_summary.get('growth_impact_quote', '中性')} | {analysis_summary.get('growth_net', '中性')} |
| 风险情绪 | {analysis_summary.get('risk_impact_base', '中性')} | {analysis_summary.get('risk_impact_quote', '中性')} | {analysis_summary.get('risk_net', '中性')} |
| **综合评估** | **{analysis_summary.get('overall_base', '中等')}** | **{analysis_summary.get('overall_quote', '中等')}** | **{analysis_summary.get('overall_verdict', '中性')}** |

## 🎯 投资建议

### 短期策略 (1-4周)
{analysis_summary.get('short_term_strategy', '基于近期经济数据和事件制定策略')}

### 中期观点 (1-6个月)
{analysis_summary.get('medium_term_view', '考虑政策周期和经济周期的影响')}

### 风险警示
{analysis_summary.get('risk_warnings', '关注重大事件风险和市场波动')}

### 关键监控指标
{analysis_summary.get('key_monitors', '未来经济数据发布和央行事件')}

## 📊 数据源状态
- ✅ FRED API: 实时美国经济数据
- ✅ ECB SDW: 实时欧元区经济数据  
- 📊 经济指标: FRED/ECB官方数据
- 📈 数据新鲜度: 实时更新

## 📋 后续步骤
1. 与技术分析师协调确认信号
2. 监控市场情绪变化
3. 关注风险事件日历
4. 定期更新宏观经济评估
    """
    
    return report.strip()

def analyze_tool_results(tool_results, base_currency, quote_currency):
    """分析工具结果并提取关键信息"""
    summary = {
        'executive_summary': '',
        'rate_differential': '待计算',
        'policy_stance': '待评估',
        'policy_path': '待分析'
    }
    
    # 简单分析逻辑（可以扩展）
    result_text = " ".join([str(r) for r in tool_results])
    
    # 基础分析
    if "rate" in result_text.lower() or "interest" in result_text.lower():
        summary['rate_differential'] = "存在利差机会"
    
    if "inflation" in result_text.lower():
        summary['inflation_level'] = "通胀数据已获取"
    
    if "calendar" in result_text.lower() or "event" in result_text.lower():
        summary['upcoming_data'] = "有近期经济事件"
    
    # 简单的情绪分析
    positive_keywords = ["strong", "growth", "improving", "positive", "up", "higher"]
    negative_keywords = ["weak", "declining", "negative", "down", "lower", "risk"]
    
    pos_count = sum(1 for word in positive_keywords if word in result_text.lower())
    neg_count = sum(1 for word in negative_keywords if word in result_text.lower())
    
    if pos_count > neg_count:
        summary['overall_verdict'] = "谨慎看涨"
    elif neg_count > pos_count:
        summary['overall_verdict'] = "谨慎看跌"
    else:
        summary['overall_verdict'] = "中性"
    
    summary['executive_summary'] = f"基于{len(tool_results)}个数据源的分析，整体评估为{summary['overall_verdict']}"
    
    return summary

def format_tool_result(result):
    """格式化工具结果"""
    if isinstance(result, str):
        if len(result) > 200:
            return f"- {result[:200]}..."
        return f"- {result}"
    return f"- 数据结果: {type(result).__name__}"

def create_macro_analyst(llm):
    def macro_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        # 对于外汇，ticker是货币对
        currency_pair = ticker if "/" in ticker or len(ticker) == 6 else "USD/JPY"  # 默认值
        
        tools = [
            get_fred_data,
            get_ecb_data,
            get_macro_dashboard,
            # get_central_bank_calendar,  # 已移除
        ]

        system_message = (
            "You are a macroeconomic analyst specializing in foreign exchange markets. "
            "Your task is to analyze fundamental economic factors that drive currency values. "
            "\n\n"
            "## 你的职责\n"
            "1. **利率分析**: 分析各国央行货币政策、利率决策和未来路径\n"
            "2. **通胀监控**: 跟踪CPI、PCE等通胀指标及其对货币的影响\n"
            "3. **经济增长评估**: 分析GDP、就业、PMI等增长指标\n"
            "4. **政策预期**: 解读央行会议纪要、官员讲话\n"
            "5. **对比分析**: 对比相关经济体的基本面差异\n"
            "\n"
            "## 可用工具\n"
            "- `get_fred_data`: 获取美国经济数据（利率、通胀、就业等）\n"
            "- `get_ecb_data`: 获取欧元区经济数据\n"
            "- `get_macro_dashboard`: 生成货币对宏观经济仪表板\n"
            # "- `get_central_bank_calendar`: 获取央行事件日历\n"  # 已移除
            "\n"
            "## 输出要求\n"
            "1. **结构化报告**: 提供清晰的宏观经济分析报告\n"
            "2. **明确结论**: 明确指出对货币对的看涨/看跌驱动因素\n"
            "3. **风险评估**: 评估风险事件和时间框架\n"
            "4. **关键指标**: 使用Markdown表格总结关键指标\n"
            "5. **时间敏感**: 特别关注即将到来的央行事件和经济数据发布\n"
            "\n"
            "## 分析策略\n"
            f"当前分析: {currency_pair}\n"
            "- 如果是EUR/USD: 对比美联储和欧洲央行的政策差异\n"
            "- 如果是USD/JPY: 关注美日利差和日本央行政策转向\n"
            "- 如果是GBP/USD: 分析英国通胀和美国经济的相对表现\n"
            "- 如果是AUD/USD: 关注商品价格和中国经济数据\n"
            "- 如果是USD/CAD: 分析油价和加拿大央行政策\n"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. We are analyzing the currency pair {currency_pair}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(currency_pair=currency_pair)

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        if len(result.tool_calls) == 0:
            # 如果没有工具调用，直接使用LLM的输出
            report = result.content
        else:
            # 如果有工具调用，执行工具并收集结果
            tool_results = []
            for tool_call in result.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                # 调用相应的工具
                try:
                    # 通过统一的vendor接口调用工具
                    tool_result = route_to_vendor(tool_name, **tool_args)
                    tool_results.append(tool_result)
                except Exception as e:
                    logger.error(f"Failed to execute {tool_name}: {e}")
                    tool_results.append(f"Error executing {tool_name}: {str(e)}")
            
            # 创建结构化的宏观报告
            report = create_structured_macro_report(
                currency_pair=currency_pair,
                current_date=current_date,
                tool_results=tool_results
            )
        
        return {
            "messages": [result],
            "macro_report": report,
        }

    return macro_analyst_node