"""
模拟数据回测演示
当yfinance被限制时使用
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mock_stock_data(ticker='AAPL', days=100, start_price=150):
    """
    生成模拟股票数据
    
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
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 生成随机价格走势（几何布朗运动）
    np.random.seed(42)  # 固定随机种子以便复现
    returns = np.random.normal(0.0005, 0.02, days)  # 日收益率
    
    # 计算价格
    prices = start_price * np.exp(np.cumsum(returns))
    
    # 生成OHLCV数据
    data = pd.DataFrame(index=dates)
    data['Close'] = prices
    
    # 生成Open, High, Low（基于Close）
    data['Open'] = data['Close'].shift(1) * (1 + np.random.normal(0, 0.01, days))
    data['High'] = data[['Open', 'Close']].max(axis=1) * (1 + np.abs(np.random.normal(0, 0.005, days)))
    data['Low'] = data[['Open', 'Close']].min(axis=1) * (1 - np.abs(np.random.normal(0, 0.005, days)))
    data['Volume'] = np.random.randint(1000000, 10000000, days)
    
    # 填充NaN值
    data['Open'].iloc[0] = start_price
    data['High'].iloc[0] = start_price * 1.01
    data['Low'].iloc[0] = start_price * 0.99
    
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
    df['SMA_short'] = df['Close'].rolling(window=window_short).mean()
    df['SMA_long'] = df['Close'].rolling(window=window_long).mean()
    
    # 生成交易信号
    # 当短期均线上穿长期均线时买入（金叉）
    # 当短期均线下穿长期均线时卖出（死叉）
    df['Signal'] = 0
    df['Signal'][window_long:] = np.where(
        df['SMA_short'][window_long:] > df['SMA_long'][window_long:], 1, 0
    )
    
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
    df['Cumulative_Market'] = (1 + df['Returns']).cumprod() - 1
    df['Cumulative_Strategy'] = (1 + df['Strategy_Returns']).cumprod() - 1
    
    # 计算夏普比率（简化版）
    excess_returns = df['Strategy_Returns'].dropna() - 0.02/252  # 假设无风险利率2%
    sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    
    return df, sharpe_ratio

def run_backtest_demo():
    """运行回测演示"""
    print("="*70)
    print("模拟数据回测演示")
    print("="*70)
    
    # 1. 生成模拟数据
    print("\n1. 生成模拟股票数据...")
    ticker = 'AAPL'
    mock_data = generate_mock_stock_data(ticker=ticker, days=200, start_price=150)
    
    print(f"生成 {len(mock_data)} 天数据")
    print(f"日期范围: {mock_data.index[0].date()} 到 {mock_data.index[-1].date()}")
    print(f"\n数据概览:")
    print(mock_data[['Open', 'High', 'Low', 'Close', 'Volume']].head())
    
    # 2. 应用交易策略
    print("\n2. 应用移动平均线策略...")
    strategy_data = simple_moving_average_strategy(mock_data)
    
    # 显示策略信号
    print("\n策略信号示例 (最后10天):")
    display_cols = ['Close', 'SMA_short', 'SMA_long', 'Signal', 'Position']
    print(strategy_data[display_cols].tail(10))
    
    # 3. 计算收益率
    print("\n3. 计算策略表现...")
    result_data, sharpe_ratio = calculate_returns(strategy_data)
    
    # 4. 显示结果
    print("\n4. 回测结果:")
    print(f"初始价格: ${mock_data['Close'].iloc[0]:.2f}")
    print(f"最终价格: ${mock_data['Close'].iloc[-1]:.2f}")
    print(f"价格变化: {((mock_data['Close'].iloc[-1]/mock_data['Close'].iloc[0])-1)*100:.2f}%")
    
    print(f"\n策略表现:")
    print(f"累计市场收益: {result_data['Cumulative_Market'].iloc[-1]*100:.2f}%")
    print(f"累计策略收益: {result_data['Cumulative_Strategy'].iloc[-1]*100:.2f}%")
    print(f"夏普比率: {sharpe_ratio:.3f}")
    
    # 5. 交易统计
    trades = result_data[result_data['Position'] != 0]
    print(f"\n交易统计:")
    print(f"总交易次数: {len(trades)}")
    if len(trades) > 0:
        print(f"买入信号: {len(trades[trades['Position'] > 0])}")
        print(f"卖出信号: {len(trades[trades['Position'] < 0])}")
    
    # 6. 保存结果
    result_data.to_csv(f'{ticker.lower()}_backtest_result.csv')
    print(f"\n结果已保存到: {ticker.lower()}_backtest_result.csv")
    
    print("\n" + "="*70)
    print("回测演示完成")
    print("="*70)
    
    return result_data

if __name__ == "__main__":
    run_backtest_demo()
