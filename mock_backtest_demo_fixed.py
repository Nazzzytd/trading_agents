"""
模拟数据回测演示 - 修复版
当yfinance被限制时使用
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mock_stock_data(ticker='AAPL', days=100, start_price=150):
    """
    生成模拟股票数据 - 修复版
    
    Parameters:
    -----------
    ticker : str
        股票代码
    days : int
        生成的天数
    start_price : float
        起始价格
    
    Returns:
    --------
    pandas.DataFrame
        模拟股票数据
    """
    # 生成日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days-1)  # 减1确保天数正确
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    print(f"生成 {len(dates)} 个日期: {dates[0].date()} 到 {dates[-1].date()}")
    
    # 生成随机价格走势（几何布朗运动）
    np.random.seed(42)  # 固定随机种子以便复现
    returns = np.random.normal(0.0005, 0.02, days)  # 日收益率
    
    # 计算价格
    prices = start_price * np.exp(np.cumsum(returns))
    
    # 创建空的DataFrame
    data = pd.DataFrame(index=dates)
    
    # 确保长度匹配
    if len(prices) != len(data):
        print(f"警告: 价格长度({len(prices)}) != 索引长度({len(data)})")
        # 调整价格长度
        prices = prices[:len(data)]
    
    # 生成OHLCV数据
    data['Close'] = prices
    
    # 生成Open, High, Low（基于Close）
    data['Open'] = data['Close'].shift(1) * (1 + np.random.normal(0, 0.01, len(data)))
    data['Open'].iloc[0] = start_price  # 第一天的开盘价
    
    # 生成最高价和最低价
    for i in range(len(data)):
        if i == 0:
            data.loc[data.index[i], 'High'] = start_price * 1.01
            data.loc[data.index[i], 'Low'] = start_price * 0.99
        else:
            day_open = data.loc[data.index[i], 'Open']
            day_close = data.loc[data.index[i], 'Close']
            high_low_range = np.random.uniform(0.005, 0.03)  # 日内波动范围
            data.loc[data.index[i], 'High'] = max(day_open, day_close) * (1 + high_low_range/2)
            data.loc[data.index[i], 'Low'] = min(day_open, day_close) * (1 - high_low_range/2)
    
    # 生成成交量
    data['Volume'] = np.random.randint(1000000, 10000000, len(data))
    
    data.index.name = 'Date'
    return data

def simple_moving_average_strategy(data, window_short=10, window_long=30):
    """
    简单移动平均线策略
    
    Parameters:
    -----------
    data : pandas.DataFrame
        股票数据
    window_short : int
        短期移动平均窗口
    window_long : int
        长期移动平均窗口
    
    Returns:
    --------
    pandas.DataFrame
        添加了信号的数据
    """
    df = data.copy()
    
    # 计算移动平均
    df['SMA_short'] = df['Close'].rolling(window=window_short, min_periods=1).mean()
    df['SMA_long'] = df['Close'].rolling(window=window_long, min_periods=1).mean()
    
    # 生成交易信号
    # 当短期均线上穿长期均线时买入（金叉）
    # 当短期均线下穿长期均线时卖出（死叉）
    df['Signal'] = 0
    df.loc[df['SMA_short'] > df['SMA_long'], 'Signal'] = 1
    
    # 计算持仓变化
    df['Position'] = df['Signal'].diff()
    
    return df

def calculate_returns(df, initial_capital=10000):
    """
    计算策略收益率
    
    Parameters:
    -----------
    df : pandas.DataFrame
        包含信号的数据
    initial_capital : float
        初始资本
    
    Returns:
    --------
    tuple
        (累计收益率, 策略数据)
    """
    df = df.copy()
    
    # 计算日收益率
    df['Returns'] = df['Close'].pct_change()
    
    # 计算策略收益率（当持有时获得市场收益，否则为0）
    df['Strategy_Returns'] = df['Signal'].shift(1) * df['Returns']
    
    # 计算累计收益率
    df['Cumulative_Market'] = (1 + df['Returns']).cumprod()
    df['Cumulative_Strategy'] = (1 + df['Strategy_Returns']).cumprod()
    
    # 计算最终收益
    market_return = (df['Cumulative_Market'].iloc[-1] - 1) * 100
    strategy_return = (df['Cumulative_Strategy'].iloc[-1] - 1) * 100
    
    # 计算夏普比率（简化版）
    excess_returns = df['Strategy_Returns'].dropna() - 0.02/252  # 假设无风险利率2%
    if len(excess_returns) > 0 and excess_returns.std() > 0:
        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    else:
        sharpe_ratio = 0
    
    return df, market_return, strategy_return, sharpe_ratio

def analyze_trades(df):
    """分析交易记录"""
    trades = df[df['Position'] != 0].copy()
    
    if len(trades) == 0:
        return [], 0, 0
    
    # 初始化交易记录
    trade_records = []
    in_position = False
    entry_price = 0
    entry_date = None
    
    for date, row in df.iterrows():
        if row['Position'] > 0 and not in_position:  # 买入信号
            in_position = True
            entry_price = row['Close']
            entry_date = date
            print(f"{date.date()}: 买入 @ ${entry_price:.2f}")
            
        elif row['Position'] < 0 and in_position:  # 卖出信号
            in_position = False
            exit_price = row['Close']
            exit_date = date
            returns_pct = (exit_price / entry_price - 1) * 100
            
            trade_records.append({
                'Entry': entry_date.date(),
                'Exit': exit_date.date(),
                'Entry_Price': entry_price,
                'Exit_Price': exit_price,
                'Returns_%': returns_pct,
                'Holding_Days': (exit_date - entry_date).days
            })
            print(f"{date.date()}: 卖出 @ ${exit_price:.2f} (收益: {returns_pct:.2f}%)")
    
    # 计算胜率
    if trade_records:
        winning_trades = [t for t in trade_records if t['Returns_%'] > 0]
        win_rate = len(winning_trades) / len(trade_records) * 100
        avg_return = np.mean([t['Returns_%'] for t in trade_records])
    else:
        win_rate = 0
        avg_return = 0
    
    return trade_records, win_rate, avg_return

def run_backtest_demo():
    """运行回测演示"""
    print("="*70)
    print("模拟数据回测演示 (修复版)")
    print("="*70)
    
    # 1. 生成模拟数据
    print("\n1. 生成模拟股票数据...")
    ticker = 'AAPL'
    mock_data = generate_mock_stock_data(ticker=ticker, days=100, start_price=150)
    
    print(f"\n数据概览:")
    print(f"数据形状: {mock_data.shape}")
    print(f"列名: {list(mock_data.columns)}")
    print(f"\n前5行数据:")
    print(mock_data[['Open', 'High', 'Low', 'Close', 'Volume']].head())
    print(f"\n最后5行数据:")
    print(mock_data[['Open', 'High', 'Low', 'Close', 'Volume']].tail())
    
    # 2. 应用交易策略
    print("\n2. 应用移动平均线策略...")
    strategy_data = simple_moving_average_strategy(mock_data)
    
    # 显示策略信号
    print("\n策略信号示例:")
    display_cols = ['Close', 'SMA_short', 'SMA_long', 'Signal']
    print(strategy_data[display_cols].head(15))
    
    # 3. 计算收益率
    print("\n3. 计算策略表现...")
    result_data, market_return, strategy_return, sharpe_ratio = calculate_returns(strategy_data)
    
    # 4. 分析交易
    print("\n4. 交易分析...")
    trades, win_rate, avg_return = analyze_trades(result_data)
    
    # 5. 显示结果
    print("\n5. 回测结果总结:")
    print("-" * 40)
    print(f"股票代码: {ticker}")
    print(f"数据期间: {result_data.index[0].date()} 到 {result_data.index[-1].date()}")
    print(f"数据天数: {len(result_data)}")
    print(f"初始价格: ${mock_data['Close'].iloc[0]:.2f}")
    print(f"最终价格: ${mock_data['Close'].iloc[-1]:.2f}")
    print(f"价格变化: {((mock_data['Close'].iloc[-1]/mock_data['Close'].iloc[0])-1)*100:.2f}%")
    
    print(f"\n策略表现:")
    print(f"市场累计收益: {market_return:.2f}%")
    print(f"策略累计收益: {strategy_return:.2f}%")
    print(f"超额收益: {strategy_return - market_return:.2f}%")
    print(f"夏普比率: {sharpe_ratio:.3f}")
    
    print(f"\n交易统计:")
    print(f"总交易次数: {len(trades)}")
    print(f"胜率: {win_rate:.1f}%")
    print(f"平均每笔交易收益: {avg_return:.2f}%")
    
    if trades:
        print(f"\n交易明细:")
        for i, trade in enumerate(trades, 1):
            print(f"交易{i}: {trade['Entry']} → {trade['Exit']} "
                  f"({trade['Holding_Days']}天) "
                  f"{trade['Returns_%']:.2f}%")
    
    # 6. 保存结果
    result_data.to_csv(f'{ticker.lower()}_backtest_result.csv')
    mock_data.to_csv(f'{ticker.lower()}_mock_data.csv')
    print(f"\n数据已保存:")
    print(f"  - 模拟数据: {ticker.lower()}_mock_data.csv")
    print(f"  - 回测结果: {ticker.lower()}_backtest_result.csv")
    
    # 7. 可视化建议
    print(f"\n7. 可视化建议:")
    print("""
    建议使用以下代码可视化结果:
    
    import matplotlib.pyplot as plt
    
    # 1. 价格和移动平均线
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    ax1.plot(result_data.index, result_data['Close'], label='收盘价', alpha=0.7)
    ax1.plot(result_data.index, result_data['SMA_short'], label='短期均线', alpha=0.7)
    ax1.plot(result_data.index, result_data['SMA_long'], label='长期均线', alpha=0.7)
    
    # 标记买入卖出点
    buy_signals = result_data[result_data['Position'] > 0]
    sell_signals = result_data[result_data['Position'] < 0]
    
    ax1.scatter(buy_signals.index, buy_signals['Close'], 
                color='green', marker='^', s=100, label='买入信号')
    ax1.scatter(sell_signals.index, sell_signals['Close'], 
                color='red', marker='v', s=100, label='卖出信号')
    
    ax1.set_title(f'{ticker} 价格和交易信号')
    ax1.set_ylabel('价格 ($)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 累计收益率对比
    ax2.plot(result_data.index, result_data['Cumulative_Market'], 
             label='市场累计收益', alpha=0.7)
    ax2.plot(result_data.index, result_data['Cumulative_Strategy'], 
             label='策略累计收益', alpha=0.7)
    ax2.set_title('累计收益率对比')
    ax2.set_ylabel('累计收益率')
    ax2.set_xlabel('日期')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{ticker.lower()}_backtest_chart.png', dpi=150)
    plt.show()
    """)
    
    print("\n" + "="*70)
    print("回测演示完成!")
    print("="*70)
    
    return result_data

if __name__ == "__main__":
    run_backtest_demo()
