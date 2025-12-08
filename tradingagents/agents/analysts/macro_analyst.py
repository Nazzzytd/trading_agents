from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.agents.utils.macro_data_tools import (
    get_fred_data,
    get_ecb_data,
    get_macro_dashboard,
    get_central_bank_calendar
)
from tradingagents.dataflows.config import get_config

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
            get_central_bank_calendar,
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
            "- `get_central_bank_calendar`: 获取央行事件日历（优先使用API数据）\n"
            "\n"
            "## 数据来源说明\n"
            "✅ **实时数据源**:\n"
            "1. FRED API - 美联储经济数据（实时）\n"
            "2. ECB SDW - 欧洲央行统计数据（实时）\n"
            "3. 经济日历 - 尝试使用API数据，失败则使用本地缓存\n"
            "\n"
            "## 输出要求\n"
            "1. 提供结构化的宏观经济分析报告\n"
            "2. 明确指出对货币对的看涨/看跌驱动因素\n"
            "3. 评估风险事件和时间框架\n"
            "4. 在报告末尾添加Markdown表格总结关键指标\n"
            "5. 特别关注即将到来的央行事件和经济数据发布\n"
            "\n"
            "## 货币对分析示例\n"
            f"当前分析: {currency_pair}\n"
            "- 如果是EUR/USD: 对比美联储和欧洲央行的政策\n"
            "- 如果是USD/JPY: 关注美日利差和日本央行政策\n"
            "- 如果是GBP/USD: 分析英国通胀和美国经济的相对表现\n"
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

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content
        else:
            # 如果有工具调用，收集工具结果
            tool_results = []
            for tool_call in result.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                # 调用相应的工具
                if tool_name == "get_fred_data":
                    tool_result = get_fred_data.invoke(tool_args)
                elif tool_name == "get_ecb_data":
                    tool_result = get_ecb_data.invoke(tool_args)
                elif tool_name == "get_macro_dashboard":
                    tool_result = get_macro_dashboard.invoke(tool_args)
                elif tool_name == "get_central_bank_calendar":
                    # 对于日历，默认尝试使用API
                    if "use_api" not in tool_args:
                        tool_args["use_api"] = True
                    tool_result = get_central_bank_calendar.invoke(tool_args)
                else:
                    tool_result = f"Unknown tool: {tool_name}"
                
                tool_results.append(tool_result)
            
            # 创建综合报告
            report = f"""
# 宏观经济分析报告
**货币对**: {currency_pair}
**分析日期**: {current_date}
**数据新鲜度**: 实时FRED/ECB数据 + 智能日历数据

## 执行摘要
基于宏观经济数据分析，以下是{currency_pair}的基本面评估。

## 数据收集结果
{chr(10).join([str(r) for r in tool_results])}

## 综合评估
基于以上数据，提供对{currency_pair}的宏观经济展望：

1. **货币政策对比**:
   - 利率差异分析
   - 央行政策立场（鹰派/鸽派）
   - 未来政策路径预期

2. **经济增长前景**:
   - 相对增长动能
   - 就业市场状况
   - 商业活动指标

3. **通胀动态**:
   - 通胀水平比较
   - 通胀预期差异
   - 实际利率计算

4. **风险因素**:
   - 即将到来的经济数据发布
   - 央行政策会议
   - 地缘政治风险

## 交易影响分析
分析这些宏观经济因素对{currency_pair}的潜在影响方向。

| 指标类别 | 对{currency_pair.split('/')[0] if '/' in currency_pair else currency_pair[:3]}影响 | 对{currency_pair.split('/')[1] if '/' in currency_pair else currency_pair[3:]}影响 | 净效应 |
|---------|-----------------------------------|-----------------------------------|--------|
| 货币政策 | | | |
| 通胀水平 | | | |
| 经济增长 | | | |
| 风险情绪 | | | |
| **综合评估** | | | **看涨/看跌/中性** |

## 建议
1. **短期策略**: 基于近期经济数据和事件
2. **中期观点**: 考虑政策周期和经济周期
3. **风险警示**: 关注重大事件风险
4. **关键监控**: 未来经济数据发布和央行事件

## 数据源状态
- ✅ FRED API: 实时美国经济数据
- ✅ ECB SDW: 实时欧元区经济数据  
- 📊 经济日历: 智能获取（优先API，失败则本地）
- 📅 下次更新: 建议定期刷新获取最新数据
            """

        return {
            "messages": [result],
            "macro_report": report,
        }

    return macro_analyst_node