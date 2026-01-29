# /Users/fr./Downloads/TradingAgents-main/cli/backtest_cli.py
"""
TradingAgents 独立回测CLI
与主系统解耦，专门用于回测验证
"""

import sys
import os
from datetime import datetime, timedelta
import json
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn
import pandas as pd
import numpy as np

# 添加项目路径，确保可以导入其他模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

console = Console()

# 创建Typer应用
backtest_app = typer.Typer(
    name="backtest",
    help="TradingAgents 回测系统",
    add_completion=True,
)

# 尝试导入现有的回测系统（可选）
try:
    from tradingagents.backtest.backtest_engine import ForexBacktestEngine, TradeDecision, TradeAction
    HAS_ADVANCED_BACKTEST = True
    console.print("[dim]✅ 高级回测系统可用[/dim]")
except ImportError:
    HAS_ADVANCED_BACKTEST = False
    console.print("[dim]⚠️  使用简单回测引擎[/dim]")

# 独立的数据获取函数
class ForexDataFetcher:
    """外汇数据获取器"""
    
    def __init__(self, cache_dir="./data_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_data(self, symbol, start_date, end_date, interval="1d"):
        """获取外汇数据"""
        try:
            import yfinance as yf
            
            # 转换符号格式
            yf_symbol = self._convert_symbol(symbol)
            
            console.print(f"[dim]📥 获取数据: {yf_symbol} ({start_date} 到 {end_date})[/dim]")
            
            data = yf.download(
                yf_symbol, 
                start=start_date, 
                end=end_date,
                progress=False
            )
            
            if data.empty:
                console.print(f"[yellow]⚠️  无数据，使用模拟数据[/yellow]")
                return self._create_mock_data(symbol, start_date, end_date)
            
            return data
            
        except Exception as e:
            console.print(f"[yellow]⚠️  数据获取失败: {e}[/yellow]")
            return self._create_mock_data(symbol, start_date, end_date)
    
    def _convert_symbol(self, symbol):
        """转换外汇符号格式"""
        symbol_map = {
            "EURUSD": "EURUSD=X",
            "GBPUSD": "GBPUSD=X", 
            "USDJPY": "JPY=X",
            "USDCHF": "CHF=X",
            "AUDUSD": "AUDUSD=X",
            "USDCAD": "CAD=X",
            "NZDUSD": "NZDUSD=X",
            "XAUUSD": "GC=F",  # 黄金
            "XAGUSD": "SI=F",  # 白银
        }
        
        return symbol_map.get(symbol, f"{symbol}=X")
    
    def _create_mock_data(self, symbol, start_date, end_date):
        """创建模拟数据"""
        console.print(f"[dim]🎭 创建 {symbol} 的模拟数据[/dim]")
        
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        n_days = len(dates)
        
        np.random.seed(42)
        
        # 基础价格
        base_prices = {
            "EURUSD": 1.10,
            "GBPUSD": 1.25, 
            "USDJPY": 145.0,
            "USDCHF": 0.88,
            "AUDUSD": 0.65,
            "USDCAD": 1.35,
            "NZDUSD": 0.60,
            "XAUUSD": 1950.0,
            "XAGUSD": 23.50
        }
        
        base_price = base_prices.get(symbol, 1.0)
        
        # 生成价格序列
        returns = np.random.normal(0.0002, 0.008, n_days)
        prices = base_price * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'Open': prices * 0.998,
            'High': prices * 1.003,
            'Low': prices * 0.997,
            'Close': prices,
            'Volume': np.random.randint(10000, 100000, n_days)
        }, index=dates)
        
        return df

# 简单的回测引擎
class SimpleBacktestEngine:
    """简单回测引擎"""
    
    def __init__(self, initial_capital=10000, spread_pips=2.0):
        self.initial_capital = initial_capital
        self.spread_pips = spread_pips
        self.data_fetcher = ForexDataFetcher()
        
    def run_backtest(self, symbol, decision_date, action, hold_days=10):
        """运行回测"""
        console.print(f"[dim]🔍 回测 {symbol} {action} @ {decision_date}[/dim]")
        
        # 获取数据
        decision_dt = datetime.strptime(decision_date, "%Y-%m-%d")
        start_date = (decision_dt - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = (decision_dt + timedelta(days=hold_days + 5)).strftime("%Y-%m-%d")
        
        data = self.data_fetcher.get_data(symbol, start_date, end_date)
        
        if data.empty:
            return {"error": "无数据"}
        
        # 找到决策日
        decision_timestamp = pd.Timestamp(decision_dt)
        if decision_timestamp not in data.index:
            # 找最近的工作日
            if decision_timestamp > data.index[-1]:
                return {"error": "决策日期在数据范围之后"}
            # 使用前向填充
            decision_idx = data.index.get_indexer([decision_timestamp], method='pad')[0]
        else:
            decision_idx = data.index.get_loc(decision_timestamp)
        
        if decision_idx < 0 or decision_idx >= len(data) - 5:
            return {"error": "无法找到有效入场点"}
        
        # 考虑点差
        spread = self.spread_pips / 10000
        
        if action == "BUY":
            entry_price = data['Close'].iloc[decision_idx] + spread  # 买入用卖价
        else:  # SELL
            entry_price = data['Close'].iloc[decision_idx] - spread  # 卖出用买价
        
        # 模拟持有期
        equity_curve = []
        prices_after = []
        
        for i in range(hold_days):
            exit_idx = min(decision_idx + i + 1, len(data) - 1)
            current_price = data['Close'].iloc[exit_idx]
            prices_after.append(current_price)
            
            # 计算当前盈亏
            if action == "BUY":
                pnl_pct = (current_price - spread - entry_price) / entry_price * 100
            else:
                pnl_pct = (entry_price - (current_price + spread)) / entry_price * 100
            
            equity_curve.append(pnl_pct)
            
            # 简单止损止盈逻辑
            if pnl_pct < -20:  # 止损20%
                break
            if pnl_pct > 30:   # 止盈30%
                break
        
        # 最终结果
        if action == "BUY":
            exit_price = prices_after[-1] - spread  # 平多用买价
            final_pnl_pct = (exit_price - entry_price) / entry_price * 100
        else:
            exit_price = prices_after[-1] + spread  # 平空用卖价
            final_pnl_pct = (entry_price - exit_price) / entry_price * 100
        
        # 计算绩效指标
        if equity_curve:
            returns_series = pd.Series(equity_curve) / 100  # 转换为小数
            if len(returns_series) > 1 and returns_series.std() > 0:
                sharpe_ratio = np.sqrt(252) * returns_series.mean() / returns_series.std()
            else:
                sharpe_ratio = 0
            
            # 最大回撤
            cumulative = (1 + returns_series).cumprod()
            running_max = cumulative.cummax()
            drawdown = (cumulative / running_max - 1) * 100
            max_drawdown = drawdown.min()
        else:
            sharpe_ratio = 0
            max_drawdown = 0
        
        return {
            "symbol": symbol,
            "decision_date": decision_date,
            "action": action,
            "entry_price": round(entry_price, 5),
            "exit_price": round(exit_price, 5),
            "hold_days": len(equity_curve),
            "pnl_percent": round(final_pnl_pct, 2),
            "pnl_amount": round(self.initial_capital * 0.01 * final_pnl_pct / 100, 2),
            "sharpe_ratio": round(sharpe_ratio, 3),
            "max_drawdown": round(max_drawdown, 2),
            "equity_curve": equity_curve,
            "max_profit": round(max(equity_curve) if equity_curve else 0, 2),
            "max_loss": round(min(equity_curve) if equity_curve else 0, 2)
        }

@backtest_app.command("single")
def backtest_single(
    symbol: str = typer.Argument(..., help="交易品种，如 EURUSD"),
    date: str = typer.Argument(..., help="决策日期，格式 YYYY-MM-DD"),
    action: str = typer.Option("BUY", "--action", "-a", help="交易动作: BUY 或 SELL"),
    hold_days: int = typer.Option(10, "--hold", "-h", help="持有天数"),
    capital: float = typer.Option(10000, "--capital", "-c", help="初始资金"),
    save: bool = typer.Option(True, "--save/--no-save", help="保存结果"),
    advanced: bool = typer.Option(False, "--advanced", help="使用高级回测引擎"),
):
    """
    运行单次回测分析
    """
    console.print(Panel.fit(
        f"📊 回测分析: {symbol} {action} @ {date}",
        border_style="cyan",
        subtitle=f"持有 {hold_days} 天 | 资金 ${capital:,.0f}"
    ))
    
    # 选择回测引擎
    if advanced and HAS_ADVANCED_BACKTEST:
        console.print("[dim]⚙️  使用高级回测引擎...[/dim]")
        result = run_advanced_backtest(symbol, date, action, hold_days, capital)
    else:
        engine = SimpleBacktestEngine(initial_capital=capital)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("执行回测...", total=None)
            result = engine.run_backtest(symbol, date, action, hold_days)
    
    if "error" in result:
        console.print(f"[red]❌ 回测失败: {result['error']}[/red]")
        return
    
    # 显示结果
    display_results(result)
    
    # 保存结果
    if save:
        save_single_result(result)

@backtest_app.command("batch")
def backtest_batch(
    symbol: str = typer.Argument(..., help="交易品种"),
    start_date: str = typer.Argument(..., help="开始日期"),
    end_date: str = typer.Argument(..., help="结束日期"),
    action: str = typer.Option("BUY", "--action", "-a", help="交易动作"),
    hold_days: int = typer.Option(10, "--hold", "-h", help="持有天数"),
    interval: str = typer.Option("weekly", "--interval", "-i", help="决策频率: daily, weekly, monthly"),
    capital: float = typer.Option(10000, "--capital", "-c", help="初始资金"),
):
    """
    批量回测 - 测试策略在历史期间的表现
    """
    console.print(Panel.fit(
        f"📈 批量回测: {symbol} ({start_date} 到 {end_date})",
        border_style="blue",
        subtitle=f"频率: {interval} | 动作: {action}"
    ))
    
    # 生成日期列表
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    dates = []
    current = start_dt
    
    interval_days = {
        "daily": 1,
        "weekly": 7,
        "monthly": 30
    }
    
    interval_day = interval_days.get(interval, 7)
    
    while current <= end_dt:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=interval_day)
    
    console.print(f"📅 测试 {len(dates)} 个决策点 ({interval})")
    
    # 运行批量回测
    results = []
    engine = SimpleBacktestEngine(initial_capital=capital)
    
    with Progress() as progress:
        task = progress.add_task("批量回测中...", total=len(dates))
        
        for date_str in dates:
            result = engine.run_backtest(symbol, date_str, action, hold_days)
            if "error" not in result:
                results.append(result)
            progress.update(task, advance=1)
    
    if not results:
        console.print("[red]❌ 无有效回测结果[/red]")
        return
    
    # 统计结果
    display_batch_summary(results, symbol, start_date, end_date, interval)
    
    # 保存批量结果
    save_batch_results(results, symbol, start_date, end_date, interval, action)

@backtest_app.command("report")
def backtest_report(
    show_all: bool = typer.Option(False, "--all", "-a", help="显示所有结果"),
    limit: int = typer.Option(10, "--limit", "-l", help="显示数量"),
):
    """
    查看回测报告
    """
    console.print(Panel.fit("📋 回测结果报告", border_style="green"))
    
    import glob
    
    # 查找结果文件
    result_dirs = [
        "./backtest_results",
        "./batch_backtest_results", 
        "./cli_backtest_results"
    ]
    
    all_files = []
    for dir_path in result_dirs:
        if os.path.exists(dir_path):
            json_files = glob.glob(os.path.join(dir_path, "**/*.json"), recursive=True)
            all_files.extend(json_files)
    
    if not all_files:
        console.print("[yellow]暂无回测结果[/yellow]")
        return
    
    # 按修改时间排序
    all_files.sort(key=os.path.getmtime, reverse=True)
    
    console.print(f"📁 找到 {len(all_files)} 个回测结果文件")
    
    # 显示最近的结果
    files_to_show = all_files if show_all else all_files[:limit]
    
    table = Table(title="回测记录", box=box.SIMPLE)
    table.add_column("序号", style="cyan", width=5)
    table.add_column("文件名", style="white", width=35)
    table.add_column("大小", style="blue", width=10)
    table.add_column("修改时间", style="green", width=12)
    table.add_column("类型", style="yellow", width=8)
    
    for i, file_path in enumerate(files_to_show, 1):
        size_kb = os.path.getsize(file_path) / 1024
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        file_name = os.path.basename(file_path)
        
        # 判断类型
        if "batch" in file_name or "historical" in file_name:
            file_type = "批量"
        else:
            file_type = "单次"
        
        table.add_row(
            str(i),
            file_name[:30] + ("..." if len(file_name) > 30 else ""),
            f"{size_kb:.1f}KB",
            mtime.strftime("%m-%d %H:%M"),
            file_type
        )
    
    console.print(table)
    
    if not show_all and len(all_files) > limit:
        console.print(f"[yellow]... 还有 {len(all_files) - limit} 个结果未显示，使用 --all 查看全部[/yellow]")

def display_results(result):
    """显示回测结果"""
    console.print("\n" + "="*60)
    console.print("[bold green]📊 回测结果汇总[/bold green]")
    console.print("="*60)
    
    # 创建结果表格
    table = Table(box=box.ROUNDED)
    table.add_column("指标", style="cyan", width=20)
    table.add_column("数值", style="green", width=15)
    table.add_column("评价", style="yellow", width=15)
    
    # 评价函数
    def eval_pnl(value):
        if value > 10: return "🎯 优秀"
        elif value > 5: return "✅ 良好"
        elif value > 0: return "🟡 一般"
        else: return "🔴 不佳"
    
    def eval_sharpe(value):
        if value > 1.5: return "🎯 优秀"
        elif value > 1.0: return "✅ 良好"
        elif value > 0.5: return "🟡 一般"
        else: return "🔴 不佳"
    
    def eval_drawdown(value):
        if value > -5: return "🎯 优秀"
        elif value > -10: return "✅ 良好"
        elif value > -15: return "🟡 一般"
        else: return "🔴 不佳"
    
    table.add_row("交易品种", result['symbol'], "-")
    table.add_row("交易动作", result['action'], "-")
    table.add_row("决策日期", result['decision_date'], "-")
    table.add_row("持有天数", str(result['hold_days']), "-")
    table.add_row("", "", "")  # 空行
    
    table.add_row("收益率", f"{result['pnl_percent']:.2f}%", 
                 eval_pnl(result['pnl_percent']))
    table.add_row("盈亏金额", f"${result['pnl_amount']:.2f}", "-")
    table.add_row("夏普比率", f"{result['sharpe_ratio']:.3f}", 
                 eval_sharpe(result['sharpe_ratio']))
    table.add_row("最大回撤", f"{result['max_drawdown']:.2f}%", 
                 eval_drawdown(result['max_drawdown']))
    table.add_row("最大盈利", f"{result['max_profit']:.2f}%", "-")
    table.add_row("最大亏损", f"{result['max_loss']:.2f}%", "-")
    table.add_row("", "", "")  # 空行
    
    table.add_row("入场价格", f"{result['entry_price']:.5f}", "-")
    table.add_row("出场价格", f"{result['exit_price']:.5f}", "-")
    table.add_row("价差", f"{abs(result['exit_price'] - result['entry_price']):.5f}", "-")
    
    console.print(table)
    
    # 决策建议
    console.print("\n[bold]🎯 决策建议:[/bold]")
    
    pnl = result['pnl_percent']
    sharpe = result['sharpe_ratio']
    drawdown = result['max_drawdown']
    
    if pnl > 10 and sharpe > 1.5 and drawdown > -10:
        console.print("[green]✅ 强烈建议执行 - 高收益低风险[/green]")
    elif pnl > 5 and sharpe > 1.0 and drawdown > -15:
        console.print("[green]✅ 建议执行 - 收益风险比良好[/green]")
    elif pnl > 0:
        console.print("[yellow]🟡 谨慎考虑 - 收益有限[/yellow]")
    elif pnl > -5:
        console.print("[yellow]⚠️  高风险 - 可能小幅亏损[/yellow]")
    else:
        console.print("[red]🔴 不建议执行 - 预期亏损较大[/red]")

def display_batch_summary(results, symbol, start_date, end_date, interval):
    """显示批量回测汇总"""
    pnls = [r['pnl_percent'] for r in results]
    sharpes = [r['sharpe_ratio'] for r in results]
    drawdowns = [r['max_drawdown'] for r in results]
    
    positive_trades = len([p for p in pnls if p > 0])
    profitable_trades = len([p for p in pnls if p > 2])
    
    console.print(f"\n[bold]📈 批量回测统计 ({len(results)} 次测试):[/bold]")
    
    stats_table = Table(box=box.SIMPLE)
    stats_table.add_column("统计指标", style="cyan")
    stats_table.add_column("数值", style="green")
    
    stats_table.add_row("平均收益率", f"{np.mean(pnls):.2f}%")
    stats_table.add_row("收益率标准差", f"{np.std(pnls):.2f}%")
    stats_table.add_row("中位数收益率", f"{np.median(pnls):.2f}%")
    stats_table.add_row("最佳收益率", f"{max(pnls):.2f}%")
    stats_table.add_row("最差收益率", f"{min(pnls):.2f}%")
    stats_table.add_row("胜率 (盈亏>0)", f"{positive_trades/len(results)*100:.1f}%")
    stats_table.add_row("盈利率 (盈亏>2%)", f"{profitable_trades/len(results)*100:.1f}%")
    stats_table.add_row("平均夏普比率", f"{np.mean(sharpes):.3f}")
    stats_table.add_row("平均最大回撤", f"{np.mean(drawdowns):.2f}%")
    
    # 计算总收益（假设每次交易1%仓位）
    total_return = np.sum(pnls) * 0.01  # 1%仓位
    annualized_return = total_return * (252 / len(results))  # 年化
    
    stats_table.add_row("累计收益 (1%仓位)", f"{total_return:.2f}%")
    stats_table.add_row("年化收益 (1%仓位)", f"{annualized_return:.2f}%")
    
    console.print(stats_table)
    
    # 评估策略
    avg_pnl = np.mean(pnls)
    win_rate = positive_trades/len(results)*100
    avg_sharpe = np.mean(sharpes)
    
    console.print("\n[bold]📊 策略评估:[/bold]")
    
    if avg_pnl > 5 and win_rate > 60 and avg_sharpe > 1.0:
        console.print("[green]✅ 策略表现优秀，稳定性高[/green]")
    elif avg_pnl > 2 and win_rate > 50 and avg_sharpe > 0.5:
        console.print("[green]✅ 策略表现良好，可以考虑使用[/green]")
    elif avg_pnl > 0:
        console.print("[yellow]🟡 策略表现一般，需要优化[/yellow]")
    else:
        console.print("[red]🔴 策略表现不佳，建议放弃[/red]")

def save_single_result(result):
    """保存单次回测结果"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 创建结果目录
    results_dir = f"./backtest_results/{result['symbol']}"
    os.makedirs(results_dir, exist_ok=True)
    
    # 保存JSON结果
    filename = f"backtest_{result['symbol']}_{result['decision_date'].replace('-', '')}_{timestamp}.json"
    filepath = os.path.join(results_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    console.print(f"\n[green]✅ 结果已保存到: {filepath}[/green]")
    return filepath

def save_batch_results(results, symbol, start_date, end_date, interval, action):
    """保存批量回测结果"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 创建目录
    results_dir = "./batch_backtest_results"
    os.makedirs(results_dir, exist_ok=True)
    
    # 文件名
    filename = f"batch_{symbol}_{start_date.replace('-', '')}_{end_date.replace('-', '')}_{interval}_{timestamp}.json"
    filepath = os.path.join(results_dir, filename)
    
    batch_data = {
        "metadata": {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "interval": interval,
            "action": action,
            "total_tests": len(results),
            "timestamp": timestamp
        },
        "summary": {
            "average_return": float(np.mean([r['pnl_percent'] for r in results])),
            "win_rate": float(len([r for r in results if r['pnl_percent'] > 0]) / len(results) * 100),
            "average_sharpe": float(np.mean([r['sharpe_ratio'] for r in results])),
            "average_max_drawdown": float(np.mean([r['max_drawdown'] for r in results]))
        },
        "results": results[:100]  # 只保存前100个结果，避免文件过大
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(batch_data, f, indent=2, ensure_ascii=False)
    
    console.print(f"\n[green]✅ 批量结果已保存: {filepath}[/green]")
    return filepath

def run_advanced_backtest(symbol, date, action, hold_days, capital):
    """运行高级回测（如果可用）"""
    if not HAS_ADVANCED_BACKTEST:
        return {"error": "高级回测引擎不可用"}
    
    try:
        # 创建高级回测引擎
        engine = ForexBacktestEngine(initial_capital=capital)
        
        # 创建交易决策
        decision = TradeDecision(
            symbol=symbol,
            action=TradeAction.BUY if action == "BUY" else TradeAction.SELL,
            confidence=0.75,
            timestamp=datetime.strptime(date, "%Y-%m-%d"),
            reasoning=f"高级回测: {action} {symbol}",
            source_agents=["backtest_cli"],
            position_size=capital * 0.01  # 1%仓位
        )
        
        # 运行回测
        result_obj = engine.run_backtest_on_decision(
            decision=decision,
            lookback_days=30,
            hold_days=hold_days
        )
        
        # 转换为简单格式
        return {
            "symbol": symbol,
            "decision_date": date,
            "action": action,
            "entry_price": 0,  # 需要从result_obj获取
            "exit_price": 0,
            "hold_days": hold_days,
            "pnl_percent": result_obj.total_return,
            "pnl_amount": 0,
            "sharpe_ratio": result_obj.sharpe_ratio,
            "max_drawdown": result_obj.max_drawdown,
            "max_profit": 0,
            "max_loss": 0
        }
        
    except Exception as e:
        console.print(f"[yellow]⚠️  高级回测失败: {e}[/yellow]")
        return {"error": f"高级回测失败: {e}"}

def main():
    """主函数"""
    # 显示欢迎信息
    console.print(Panel.fit(
        "[bold green]TradingAgents 回测系统[/bold green]\n"
        "[dim]独立、快速、无需依赖主系统[/dim]",
        border_style="green",
        padding=(1, 2)
    ))
    
    # 显示系统状态
    console.print(f"[dim]系统状态: {'高级引擎可用' if HAS_ADVANCED_BACKTEST else '简单引擎'}[/dim]")
    console.print(f"[dim]数据源: yfinance + 模拟数据[/dim]")
    
    # 运行Typer应用
    backtest_app()

if __name__ == "__main__":
    main()