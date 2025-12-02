from openai import OpenAI
from tradingagents.dataflows.config import get_config
from typing import Optional 


# 在 /Users/fr./Downloads/TradingAgents-main/tradingagents/dataflows/vendors/openai.py 中添加

# 在 /Users/fr./Downloads/TradingAgents-main/tradingagents/dataflows/vendors/openai.py 中添加/修改

def get_forex_news_openai(
    ticker: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    topics: Optional[str] = None,
    limit: Optional[int] = None,
    **kwargs  # 接受额外的关键字参数
) -> str:
    """使用OpenAI作为备用新闻来源分析外汇新闻
    
    Args:
        ticker: 货币对，如 "EUR/USD", "USD/JPY"
        start_date: 开始日期 yyyy-mm-dd
        end_date: 结束日期 yyyy-mm-dd
        topics: 新闻主题
        limit: 数量限制
    
    Returns:
        str: OpenAI生成的外汇新闻分析报告
    """
    config = get_config()
    client = OpenAI(base_url=config["backend_url"])
    
    # 构建查询字符串
    query_parts = []
    
    # 添加货币对信息
    if ticker and ticker.strip():
        query_parts.append(f"forex news for {ticker}")
    else:
        query_parts.append("general forex market news")
    
    # 添加时间范围
    if start_date and end_date:
        query_parts.append(f"from {start_date} to {end_date}")
    elif start_date:
        query_parts.append(f"from {start_date}")
    elif end_date:
        query_parts.append(f"until {end_date}")
    
    # 添加主题信息
    if topics:
        # 解析topics
        topic_list = [t.strip() for t in topics.split(",")]
        if len(topic_list) > 0:
            query_parts.append(f"focusing on {', '.join(topic_list)}")
    
    query_text = "Search for " + " ".join(query_parts)
    
    if limit:
        query_text += f", limit to {limit} most relevant articles"
    
    system_prompt = """You are a forex market analyst. Search for the most recent and relevant forex news.
    Focus on:
    1. Central bank announcements and policy changes
    2. Major economic indicators (GDP, CPI, employment data)
    3. Geopolitical events affecting currency markets
    4. Market sentiment and technical analysis insights
    
    Provide a concise but comprehensive report with:
    - Key news events and their significance
    - Potential impact on major currency pairs
    - Trading implications and timeframes
    - Risk assessment"""
    
    response = client.responses.create(
        model=config["quick_think_llm"],
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"{system_prompt}\n\nQuery: {query_text}",
                    }
                ],
            }
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {"type": "approximate"},
                "search_context_size": "high",
            }
        ],
        temperature=0.7,
        max_output_tokens=2048,
        top_p=0.9,
        store=True,
    )

    return response.output_text


def get_fundamentals_openai(ticker, curr_date):
    config = get_config()
    client = OpenAI(base_url=config["backend_url"])

    response = client.responses.create(
        model=config["quick_think_llm"],
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"Can you search Fundamental for discussions on {ticker} during of the month before {curr_date} to the month of {curr_date}. Make sure you only get the data posted during that period. List as a table, with PE/PS/Cash flow/ etc",
                    }
                ],
            }
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {"type": "approximate"},
                "search_context_size": "low",
            }
        ],
        temperature=1,
        max_output_tokens=4096,
        top_p=1,
        store=True,
    )

    return response.output[1].content[0].text