# tradingagents/agents/analysts/quantitative_analyst.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import json
from datetime import datetime
from tradingagents.dataflows.interface import route_to_vendor

def create_quantitative_analyst(llm=None):
    """
    创建量化分析师节点
    注意：这个版本更注重数据计算，减少LLM依赖
    """
    def quantitative_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state.get("company_of_interest") or state.get("currency_pair", "EUR/USD")
        
        # 从state中获取技术分析报告（如果有）
        technical_report = state.get("technical_report", "")
        
        # 直接从接口获取量化分析数据（不经过LLM工具调用）
        try:
            # 方法1：直接调用量化分析
            quant_report = route_to_vendor(
                "get_quantitative_analysis", 
                ticker, 
                current_date,
                lookback_days=365
            )
            
            # 方法2：计算风险指标
            risk_report = route_to_vendor(
                "calculate_risk_metrics",
                ticker,
                current_date,
                lookback_days=252
            )
            
            # 综合报告
            combined_report = f"""
# 📊 量化分析报告 - {ticker}
**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析日期**: {current_date}

## 📈 量化分析结果
{quant_report}

## ⚠️ 风险评估
{risk_report}

## 🎯 技术信号验证
{_validate_technical_signals(technical_report, ticker, current_date)}

## 💡 综合建议
{_generate_final_recommendation(quant_report, risk_report, technical_report)}
"""
            
        except Exception as e:
            combined_report = f"量化分析失败: {str(e)}"
        
        return {
            "messages": [{"role": "assistant", "content": combined_report}],
            "quantitative_report": combined_report,
            "analysis_type": "quantitative",
            "ticker": ticker
        }
    
    return quantitative_analyst_node

def _validate_technical_signals(technical_report, ticker, current_date):
    """验证技术分析报告中的信号"""
    if not technical_report:
        return "⚠️ 无技术分析报告可供验证"
    
    # 简单的信号提取（可以根据需要扩展）
    signals = []
    
    if "买入" in technical_report or "BUY" in technical_report.upper():
        signals.append("买入信号")
    if "卖出" in technical_report or "SELL" in technical_report.upper():
        signals.append("卖出信号")
    if "持有" in technical_report or "HOLD" in technical_report.upper():
        signals.append("持有信号")
    
    if signals:
        return f"检测到技术信号: {', '.join(signals)}\n📊 建议通过历史数据进行进一步验证"
    else:
        return "未检测到明确的技术交易信号"

def _generate_final_recommendation(quant_report, risk_report, technical_report):
    """生成综合建议"""
    recommendations = []
    
    # 基于量化报告的简单判断
    if "夏普比率" in quant_report:
        if "夏普比率: 0.00" in quant_report or "夏普比率: -" in quant_report:
            recommendations.append("⚠️ 夏普比率不佳，建议谨慎操作")
        elif "夏普比率: 0.5" in quant_report:
            recommendations.append("✅ 夏普比率良好，可考虑交易")
    
    if "波动率较高" in quant_report or "年化波动率: 0.12" in quant_report:
        recommendations.append("📊 波动率较高，建议减小头寸规模")
    
    if "最大回撤超过" in quant_report:
        recommendations.append("🔥 历史回撤较大，需设置严格止损")
    
    # 结合技术分析
    if technical_report and ("强烈买入" in technical_report or "强烈建议" in technical_report):
        recommendations.append("🎯 技术面支持交易，可结合量化分析确定仓位")
    
    if not recommendations:
        recommendations = [
            "📋 建议进行更深入的分析",
            "💡 考虑市场宏观环境",
            "⚖️ 平衡技术面与量化分析结果"
        ]
    
    return "\n".join(f"- {rec}" for rec in recommendations)

# ==================== 如果需要LLM增强版本 ====================

def create_llm_enhanced_quantitative_analyst(llm):
    """
    如果需要LLM来增强分析，使用这个版本
    """
    def llm_quantitative_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state.get("company_of_interest") or state.get("currency_pair", "EUR/USD")
        
        # 先获取量化数据
        try:
            quant_data = route_to_vendor("get_quantitative_analysis", ticker, current_date)
            risk_data = route_to_vendor("calculate_risk_metrics", ticker, current_date)
        except Exception as e:
            return {
                "messages": [{"role": "assistant", "content": f"数据获取失败: {str(e)}"}],
                "quantitative_report": f"量化分析失败: {str(e)}",
                "analysis_type": "quantitative",
                "ticker": ticker
            }
        
        # 使用LLM分析数据
        system_message = """您是一个量化分析师，需要根据提供的量化数据给出专业分析。
        
数据包括：
1. 量化指标（波动率、夏普比率等）
2. 风险评估（VaR、最大回撤等）

请基于这些数据：
1. 解释每个指标的含义
2. 评估交易风险
3. 给出具体的交易建议
4. 提供风险管理策略

格式要求：
- 使用专业但易懂的语言
- 包含具体数字
- 给出明确建议（BUY/HOLD/SELL）
- 包含仓位管理建议
"""
        
        user_message = f"""
请分析以下数据：

量化指标：
{quant_data}

风险评估：
{risk_data}

货币对：{ticker}
分析日期：{current_date}

请给出完整的量化分析报告。
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", user_message)
        ])
        
        chain = prompt | llm
        result = chain.invoke({})
        
        return {
            "messages": [{"role": "assistant", "content": result.content}],
            "quantitative_report": result.content,
            "quantitative_data": {
                "raw_quant": quant_data,
                "raw_risk": risk_data
            },
            "analysis_type": "quantitative",
            "ticker": ticker
        }
    
    return llm_quantitative_analyst_node