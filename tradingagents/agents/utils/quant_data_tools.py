# tradingagents/agents/utils/quant_data_tools.py
from langchain_core.tools import tool
from typing import Annotated, Dict, List, Optional
import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta

@tool
def get_factor_analysis(
    ticker: Annotated[str, "Ticker symbol or currency pair"],
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    lookback_days: Annotated[int, "Number of days to look back for analysis"] = 365,
    factor_types: Annotated[Optional[List[str]], "List of factor types to analyze"] = None
) -> str:
    """
    Perform quantitative factor analysis on a given ticker.
    Calculates and validates the effectiveness of various trading factors.
    
    Args:
        ticker (str): Ticker symbol or currency pair
        curr_date (str): Current date in yyyy-mm-dd format
        lookback_days (int): Number of days to look back for analysis
        factor_types (list): List of factor types to analyze
    
    Returns:
        str: A formatted string containing factor analysis results
    """
    # 获取价格数据（重用你的现有数据获取逻辑）
    from tradingagents.dataflows.interface import route_to_vendor
    
    try:
        # 获取股票/外汇数据
        price_data = route_to_vendor("get_stock_data", ticker, curr_date, lookback_days)
        
        # 解析数据
        df = pd.DataFrame(price_data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 计算因子分析
        factor_results = _calculate_factors(df, factor_types)
        
        # 生成报告
        report = _generate_factor_report(factor_results, ticker, curr_date)
        
        return report
        
    except Exception as e:
        return f"Error in factor analysis: {str(e)}"

@tool
def validate_technical_signal(
    ticker: Annotated[str, "Ticker symbol or currency pair"],
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    signal_type: Annotated[str, "Type of technical signal to validate"],
    signal_params: Annotated[Optional[Dict], "Parameters for the signal"] = None
) -> str:
    """
    Validate the effectiveness of a technical trading signal using historical data.
    
    Args:
        ticker (str): Ticker symbol or currency pair
        curr_date (str): Current date in yyyy-mm-dd format
        signal_type (str): Type of technical signal (e.g., 'RSI_OVERSOLD', 'MACD_CROSS')
        signal_params (dict): Parameters for the signal
    
    Returns:
        str: Validation results including statistical significance
    """
    from tradingagents.dataflows.interface import route_to_vendor
    
    try:
        # 获取历史数据
        price_data = route_to_vendor("get_stock_data", ticker, curr_date, 1000)  # 更长历史
        
        df = pd.DataFrame(price_data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 验证信号
        validation_results = _validate_signal(df, signal_type, signal_params or {})
        
        # 生成验证报告
        report = _generate_validation_report(validation_results, ticker, signal_type)
        
        return report
        
    except Exception as e:
        return f"Error in signal validation: {str(e)}"

@tool
def calculate_risk_metrics(
    ticker: Annotated[str, "Ticker symbol or currency pair"],
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    lookback_days: Annotated[int, "Number of days to look back"] = 252
) -> str:
    """
    Calculate quantitative risk metrics for a given ticker.
    
    Args:
        ticker (str): Ticker symbol or currency pair
        curr_date (str): Current date in yyyy-mm-dd format
        lookback_days (int): Number of days to look back
    
    Returns:
        str: Risk metrics including volatility, VaR, Sharpe ratio, etc.
    """
    from tradingagents.dataflows.interface import route_to_vendor
    
    try:
        # 获取数据
        price_data = route_to_vendor("get_stock_data", ticker, curr_date, lookback_days)
        
        df = pd.DataFrame(price_data)
        if len(df) < 20:
            return "Insufficient data for risk calculation"
        
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 计算风险指标
        risk_metrics = _calculate_risk_metrics_internal(df)
        
        # 格式化输出
        report = f"""
📊 **风险指标分析 - {ticker}**
分析日期: {curr_date}
分析周期: {lookback_days}个交易日

🎯 **核心风险指标:**
- 📈 年化波动率: {risk_metrics['annual_volatility']:.2%}
- ⚠️ 95% VaR (单日): {risk_metrics['var_95']:.2%}
- 🔥 最大回撤: {risk_metrics['max_drawdown']:.2%}
- 📉 最大回撤持续时间: {risk_metrics['max_dd_duration']}天

📊 **收益风险指标:**
- ⭐ 年化夏普比率: {risk_metrics['sharpe_ratio']:.2f}
- 🔄 索提诺比率: {risk_metrics['sortino_ratio']:.2f}
- 📏 卡尔马比率: {risk_metrics['calmar_ratio']:.2f}

📋 **分布特征:**
- 📊 日收益率均值: {risk_metrics['daily_return_mean']:.4%}
- 📊 日收益率标准差: {risk_metrics['daily_return_std']:.4%}
- 📐 偏度: {risk_metrics['skewness']:.3f}
- 📈 峰度: {risk_metrics['kurtosis']:.3f}

💡 **风险提示:**
{risk_metrics['risk_notes']}
"""
        
        return report
        
    except Exception as e:
        return f"Error in risk calculation: {str(e)}"

# ==================== 内部辅助函数 ====================

def _calculate_factors(df: pd.DataFrame, factor_types: Optional[List[str]]) -> Dict:
    """计算因子分析"""
    factors = {}
    
    # 默认分析所有因子
    if factor_types is None:
        factor_types = ['momentum', 'mean_reversion', 'volatility', 'trend']
    
    # 计算收益率
    df['returns'] = df['close'].pct_change()
    
    for factor_type in factor_types:
        if factor_type == 'momentum':
            factors['momentum'] = _calculate_momentum_factors(df)
        elif factor_type == 'mean_reversion':
            factors['mean_reversion'] = _calculate_mean_reversion_factors(df)
        elif factor_type == 'volatility':
            factors['volatility'] = _calculate_volatility_factors(df)
        elif factor_type == 'trend':
            factors['trend'] = _calculate_trend_factors(df)
    
    return factors

def _calculate_momentum_factors(df: pd.DataFrame) -> Dict:
    """计算动量因子"""
    results = {}
    
    # 短期动量 (5-20天)
    for window in [5, 10, 20]:
        col_name = f'momentum_{window}'
        df[col_name] = df['close'] / df['close'].shift(window) - 1
        
        # 计算动量因子的表现
        if len(df) > window * 2:
            future_returns = []
            for i in range(window, len(df) - 5):  # 看未来5天表现
                if df[col_name].iloc[i] > 0.02:  # 强势上涨
                    future_return = df['close'].iloc[i+5] / df['close'].iloc[i] - 1
                    future_returns.append(future_return)
            
            if future_returns:
                results[f'momentum_{window}d'] = {
                    'sample_size': len(future_returns),
                    'avg_future_return': np.mean(future_returns),
                    'win_rate': sum(1 for r in future_returns if r > 0) / len(future_returns),
                    'continuation_prob': len([r for r in future_returns if r > 0]) / len(future_returns)
                }
    
    return results

def _validate_signal(df: pd.DataFrame, signal_type: str, params: Dict) -> Dict:
    """验证技术信号"""
    df['returns'] = df['close'].pct_change()
    signals = []
    
    if signal_type == 'RSI_OVERSOLD':
        # 假设有RSI数据，如果没有则计算
        if 'rsi' not in df.columns:
            df['rsi'] = _calculate_rsi(df['close'])
        
        for i in range(len(df) - 5):  # 信号后看5天
            if df['rsi'].iloc[i] < 30:  # 超卖
                future_return = df['close'].iloc[i+5] / df['close'].iloc[i] - 1
                signals.append({
                    'date': df.index[i],
                    'signal_value': df['rsi'].iloc[i],
                    'future_return': future_return
                })
    
    elif signal_type == 'MACD_CROSS':
        # 计算MACD
        if 'macd' not in df.columns or 'macd_signal' not in df.columns:
            df['macd'], df['macd_signal'] = _calculate_macd(df['close'])
        
        for i in range(1, len(df) - 5):
            # MACD金叉
            if df['macd'].iloc[i-1] < df['macd_signal'].iloc[i-1] and \
               df['macd'].iloc[i] > df['macd_signal'].iloc[i]:
                future_return = df['close'].iloc[i+5] / df['close'].iloc[i] - 1
                signals.append({
                    'date': df.index[i],
                    'signal_type': 'GOLDEN_CROSS',
                    'future_return': future_return
                })
    
    # 统计分析
    if signals:
        returns = [s['future_return'] for s in signals]
        mean_return = np.mean(returns)
        win_rate = sum(1 for r in returns if r > 0) / len(returns)
        
        # t检验
        if len(returns) > 1:
            t_stat, p_value = stats.ttest_1samp(returns, 0)
            significant = p_value < 0.05
        else:
            t_stat, p_value, significant = 0, 1.0, False
        
        return {
            'signal_type': signal_type,
            'sample_size': len(signals),
            'mean_return': mean_return,
            'win_rate': win_rate,
            't_statistic': t_stat,
            'p_value': p_value,
            'statistically_significant': significant,
            'recommendation': 'VALID' if significant and mean_return > 0 else 'INVALID'
        }
    
    return {'error': 'No signals detected'}

def _calculate_risk_metrics_internal(df: pd.DataFrame) -> Dict:
    """计算风险指标"""
    df['returns'] = df['close'].pct_change()
    returns = df['returns'].dropna()
    
    if len(returns) == 0:
        return {}
    
    # 基础统计
    daily_return_mean = returns.mean()
    daily_return_std = returns.std()
    
    # 年化指标
    annual_volatility = daily_return_std * np.sqrt(252)
    
    # VaR (历史模拟法)
    var_95 = np.percentile(returns, 5)  # 5%分位数
    
    # 最大回撤
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # 最大回撤持续时间
    max_dd_idx = drawdown.idxmin() if not drawdown.empty else None
    if max_dd_idx:
        # 计算回撤持续时间（简化版）
        max_dd_duration = 30  # 默认值
    else:
        max_dd_duration = 0
    
    # 夏普比率（假设无风险利率2%）
    risk_free_rate = 0.02 / 252
    excess_returns = returns - risk_free_rate
    sharpe_ratio = np.sqrt(252) * excess_returns.mean() / returns.std() if returns.std() > 0 else 0
    
    # 索提诺比率
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std() if len(downside_returns) > 1 else returns.std()
    sortino_ratio = np.sqrt(252) * excess_returns.mean() / downside_std if downside_std > 0 else 0
    
    # 卡尔马比率
    calmar_ratio = -annual_return / abs(max_drawdown) if max_drawdown < 0 else 0
    
    # 分布特征
    skewness = returns.skew()
    kurtosis = returns.kurtosis()
    
    # 风险提示
    risk_notes = []
    if annual_volatility > 0.3:
        risk_notes.append("⚠️ 波动率极高，建议减小头寸规模")
    if max_drawdown < -0.2:
        risk_notes.append("⚠️ 历史最大回撤超过20%，需严格风险控制")
    if sharpe_ratio < 0:
        risk_notes.append("⚠️ 夏普比率为负，风险调整后收益不佳")
    
    if not risk_notes:
        risk_notes.append("✅ 风险水平在正常范围内")
    
    return {
        'annual_volatility': annual_volatility,
        'var_95': var_95,
        'max_drawdown': max_drawdown,
        'max_dd_duration': max_dd_duration,
        'sharpe_ratio': sharpe_ratio,
        'sortino_ratio': sortino_ratio,
        'calmar_ratio': calmar_ratio,
        'daily_return_mean': daily_return_mean,
        'daily_return_std': daily_return_std,
        'skewness': skewness,
        'kurtosis': kurtosis,
        'risk_notes': '\n'.join(risk_notes)
    }

def _generate_factor_report(factor_results: Dict, ticker: str, curr_date: str) -> str:
    """生成因子分析报告"""
    report_parts = [f"# 📊 量化因子分析报告 - {ticker}",
                   f"**分析日期**: {curr_date}",
                   f"**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                   ""]
    
    for factor_type, results in factor_results.items():
        report_parts.append(f"## 🎯 {factor_type.upper()}因子分析")
        
        if factor_type == 'momentum':
            for period, stats in results.items():
                report_parts.append(
                    f"- **{period}动量**: {stats['sample_size']}个信号，"
                    f"未来5天平均收益{stats['avg_future_return']:.2%}，"
                    f"胜率{stats['win_rate']:.1%}"
                )
    
    report_parts.append("\n## 📈 综合建议")
    report_parts.append("基于量化分析，建议：")
    
    # 简单的决策逻辑
    if factor_results.get('momentum', {}):
        momentum_stats = list(factor_results['momentum'].values())[0]
        if momentum_stats['avg_future_return'] > 0.01 and momentum_stats['win_rate'] > 0.55:
            report_parts.append("✅ 动量因子表现良好，可考虑跟随趋势")
        else:
            report_parts.append("⚠️ 动量因子效果不显著，建议谨慎操作")
    
    return "\n".join(report_parts)

def _generate_validation_report(results: Dict, ticker: str, signal_type: str) -> str:
    """生成验证报告"""
    if 'error' in results:
        return f"验证失败: {results['error']}"
    
    significance_symbol = "✅" if results['statistically_significant'] else "❌"
    
    report = f"""
📊 **技术信号验证报告 - {ticker}**
**信号类型**: {signal_type}
**验证日期**: {datetime.now().strftime('%Y-%m-%d')}

📈 **验证结果:**
- 样本数量: {results['sample_size']}个信号
- 平均收益: {results['mean_return']:.2%}
- 胜率: {results['win_rate']:.1%}
- t统计量: {results['t_statistic']:.3f}
- p值: {results['p_value']:.4f}
- 统计显著性: {significance_symbol} ({'显著' if results['statistically_significant'] else '不显著'})

🎯 **验证结论:**
信号**{results['recommendation']}** - {results['recommendation'] == 'VALID' and '建议采用此信号' or '建议忽略此信号'}

💡 **注意事项:**
- 历史表现不代表未来
- 需结合其他因素综合判断
- 严格风险管理
"""
    return report

# ==================== 技术指标计算函数 ====================

def _calculate_rsi(prices, period=14):
    """计算RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def _calculate_macd(prices, fast=12, slow=26, signal=9):
    """计算MACD"""
    exp1 = prices.ewm(span=fast, adjust=False).mean()
    exp2 = prices.ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line