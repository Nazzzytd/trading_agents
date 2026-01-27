"""
回测结果可视化
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

def load_and_visualize():
    """加载并可视化回测结果"""
    print("加载回测结果数据...")
    
    try:
        # 加载数据
        result_data = pd.read_csv('aapl_backtest_result.csv', index_col='Date', parse_dates=True)
        mock_data = pd.read_csv('aapl_mock_data.csv', index_col='Date', parse_dates=True)
        
        print(f"加载成功:")
        print(f"  回测结果数据形状: {result_data.shape}")
        print(f"  模拟数据形状: {mock_data.shape}")
        
    except FileNotFoundError:
        print("找不到数据文件，运行模拟回测演示...")
        # 如果文件不存在，重新运行模拟
        exec(open('mock_backtest_demo_fixed.py').read())
        return
    
    # 创建图表
    create_visualizations(result_data)

def create_visualizations(data):
    """创建可视化图表"""
    print("\n创建可视化图表...")
    
    # 设置中文字体（如果需要）
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 创建多个子图
    fig = plt.figure(figsize=(16, 12))
    
    # 1. 价格和移动平均线
    ax1 = plt.subplot(3, 2, 1)
    ax1.plot(data.index, data['Close'], label='收盘价', alpha=0.8, linewidth=1.5)
    ax1.plot(data.index, data['SMA_short'], label='短期均线(10日)', alpha=0.7, linestyle='--')
    ax1.plot(data.index, data['SMA_long'], label='长期均线(30日)', alpha=0.7, linestyle='--')
    
    # 标记买入卖出点
    buy_signals = data[data['Position'] > 0]
    sell_signals = data[data['Position'] < 0]
    
    if not buy_signals.empty:
        ax1.scatter(buy_signals.index, buy_signals['Close'], 
                   color='green', marker='^', s=100, label='买入信号', zorder=5)
    if not sell_signals.empty:
        ax1.scatter(sell_signals.index, sell_signals['Close'], 
                   color='red', marker='v', s=100, label='卖出信号', zorder=5)
    
    ax1.set_title('AAPL - 价格和移动平均线策略', fontsize=12, fontweight='bold')
    ax1.set_ylabel('价格 ($)', fontsize=10)
    ax1.legend(loc='best', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # 2. 累计收益率对比
    ax2 = plt.subplot(3, 2, 2)
    ax2.plot(data.index, data['Cumulative_Market'], 
             label='市场累计收益', alpha=0.8, linewidth=2)
    ax2.plot(data.index, data['Cumulative_Strategy'], 
             label='策略累计收益', alpha=0.8, linewidth=2)
    ax2.axhline(y=1, color='gray', linestyle='--', alpha=0.5)
    ax2.set_title('累计收益率对比', fontsize=12, fontweight='bold')
    ax2.set_ylabel('累计收益率 (倍数)', fontsize=10)
    ax2.legend(loc='best', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='x', rotation=45)
    
    # 3. 每日收益率
    ax3 = plt.subplot(3, 2, 3)
    ax3.bar(data.index, data['Returns'].fillna(0) * 100, 
            alpha=0.6, width=0.8, color='blue', label='市场日收益率')
    ax3.bar(data.index, data['Strategy_Returns'].fillna(0) * 100,
            alpha=0.6, width=0.4, color='orange', label='策略日收益率')
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax3.set_title('每日收益率', fontsize=12, fontweight='bold')
    ax3.set_ylabel('收益率 (%)', fontsize=10)
    ax3.legend(loc='best', fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='x', rotation=45)
    
    # 4. 信号分布
    ax4 = plt.subplot(3, 2, 4)
    signal_counts = data['Signal'].value_counts().sort_index()
    colors = ['red', 'green']
    labels = ['不持有 (0)', '持有 (1)']
    ax4.bar(labels, signal_counts.values, color=colors, alpha=0.7)
    ax4.set_title('持仓信号分布', fontsize=12, fontweight='bold')
    ax4.set_ylabel('天数', fontsize=10)
    for i, v in enumerate(signal_counts.values):
        ax4.text(i, v + 0.5, str(v), ha='center', va='bottom', fontsize=10)
    ax4.grid(True, alpha=0.3, axis='y')
    
    # 5. 滚动波动率
    ax5 = plt.subplot(3, 2, 5)
    returns_volatility = data['Returns'].rolling(window=20).std() * np.sqrt(252) * 100
    strategy_volatility = data['Strategy_Returns'].rolling(window=20).std() * np.sqrt(252) * 100
    
    ax5.plot(data.index, returns_volatility, label='市场波动率', alpha=0.8)
    ax5.plot(data.index, strategy_volatility, label='策略波动率', alpha=0.8)
    ax5.set_title('滚动年化波动率 (20日窗口)', fontsize=12, fontweight='bold')
    ax5.set_ylabel('波动率 (%)', fontsize=10)
    ax5.set_xlabel('日期', fontsize=10)
    ax5.legend(loc='best', fontsize=9)
    ax5.grid(True, alpha=0.3)
    ax5.tick_params(axis='x', rotation=45)
    
    # 6. 交易收益分布
    ax6 = plt.subplot(3, 2, 6)
    if 'Position' in data.columns:
        trades = data[data['Position'] != 0]
        if not trades.empty:
            # 计算每笔交易的收益（简化）
            trade_returns = []
            in_trade = False
            entry_price = 0
            
            for idx, row in data.iterrows():
                if row['Position'] > 0 and not in_trade:
                    in_trade = True
                    entry_price = row['Close']
                elif row['Position'] < 0 and in_trade:
                    in_trade = False
                    exit_price = row['Close']
                    trade_return = (exit_price / entry_price - 1) * 100
                    trade_returns.append(trade_return)
            
            if trade_returns:
                ax6.hist(trade_returns, bins=10, alpha=0.7, color='purple', edgecolor='black')
                ax6.axvline(x=np.mean(trade_returns), color='red', linestyle='--', 
                           label=f'平均: {np.mean(trade_returns):.2f}%')
                ax6.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
                ax6.set_title('交易收益分布', fontsize=12, fontweight='bold')
                ax6.set_xlabel('收益 (%)', fontsize=10)
                ax6.set_ylabel('频次', fontsize=10)
                ax6.legend(loc='best', fontsize=9)
                ax6.grid(True, alpha=0.3)
            else:
                ax6.text(0.5, 0.5, '无完整交易记录', 
                        ha='center', va='center', transform=ax6.transAxes, fontsize=12)
                ax6.set_title('交易收益分布', fontsize=12, fontweight='bold')
        else:
            ax6.text(0.5, 0.5, '无交易信号', 
                    ha='center', va='center', transform=ax6.transAxes, fontsize=12)
            ax6.set_title('交易收益分布', fontsize=12, fontweight='bold')
    
    # 添加整体标题
    plt.suptitle('AAPL 股票回测分析报告', fontsize=16, fontweight='bold', y=0.98)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'backtest_visualization_{timestamp}.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\n图表已保存为: {filename}")
    
    # 显示图表
    plt.show()
    
    # 打印统计摘要
    print_statistics(data)

def print_statistics(data):
    """打印统计摘要"""
    print("\n" + "="*60)
    print("回测统计摘要")
    print("="*60)
    
    # 基本统计
    market_return = (data['Cumulative_Market'].iloc[-1] - 1) * 100
    strategy_return = (data['Cumulative_Strategy'].iloc[-1] - 1) * 100
    
    print(f"\n收益率统计:")
    print(f"  市场累计收益: {market_return:.2f}%")
    print(f"  策略累计收益: {strategy_return:.2f}%")
    print(f"  超额收益: {strategy_return - market_return:.2f}%")
    
    # 波动率
    market_vol = data['Returns'].std() * np.sqrt(252) * 100
    strategy_vol = data['Strategy_Returns'].std() * np.sqrt(252) * 100
    
    print(f"\n风险统计:")
    print(f"  市场年化波动率: {market_vol:.2f}%")
    print(f"  策略年化波动率: {strategy_vol:.2f}%")
    
    # 夏普比率
    risk_free_rate = 0.02  # 2% 无风险利率
    market_sharpe = (data['Returns'].mean() * 252 - risk_free_rate) / (data['Returns'].std() * np.sqrt(252)) \
                    if data['Returns'].std() > 0 else 0
    strategy_sharpe = (data['Strategy_Returns'].mean() * 252 - risk_free_rate) / (data['Strategy_Returns'].std() * np.sqrt(252)) \
                      if data['Strategy_Returns'].std() > 0 else 0
    
    print(f"\n风险调整收益:")
    print(f"  市场夏普比率: {market_sharpe:.3f}")
    print(f"  策略夏普比率: {strategy_sharpe:.3f}")
    
    # 最大回撤
    market_cumulative = data['Cumulative_Market']
    strategy_cumulative = data['Cumulative_Strategy']
    
    market_drawdown = (market_cumulative / market_cumulative.cummax() - 1).min() * 100
    strategy_drawdown = (strategy_cumulative / strategy_cumulative.cummax() - 1).min() * 100
    
    print(f"\n最大回撤:")
    print(f"  市场最大回撤: {market_drawdown:.2f}%")
    print(f"  策略最大回撤: {strategy_drawdown:.2f}%")
    
    # 交易统计
    total_trades = (data['Position'].abs() > 0).sum()
    buy_signals = (data['Position'] > 0).sum()
    sell_signals = (data['Position'] < 0).sum()
    
    print(f"\n交易统计:")
    print(f"  总交易次数: {total_trades}")
    print(f"  买入信号: {buy_signals}")
    print(f"  卖出信号: {sell_signals}")
    print(f"  持仓天数占比: {data['Signal'].mean()*100:.1f}%")

if __name__ == "__main__":
    load_and_visualize()
