# cli/backtest_cli_enhanced.py
"""
增强版回测CLI - 为自适应系统做准备
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
from rich.progress import Progress
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

console = Console()

# ==================== 数据层 ====================
class PerformanceDatabase:
    """性能数据库 - 存储所有回测结果"""
    
    def __init__(self, db_path="./performance_db"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(exist_ok=True)
        
        # 子目录
        self.results_dir = self.db_path / "results"
        self.metrics_dir = self.db_path / "metrics"
        self.models_dir = self.db_path / "models"
        
        for dir in [self.results_dir, self.metrics_dir, self.models_dir]:
            dir.mkdir(exist_ok=True)
    
    def save_result(self, result, source="cli", metadata=None):
        """保存回测结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_id = f"{result.get('symbol', 'UNKNOWN')}_{timestamp}"
        
        # 保存完整结果
        result_file = self.results_dir / f"{result_id}.json"
        
        result_data = {
            "result_id": result_id,
            "timestamp": timestamp,
            "source": source,
            "metadata": metadata or {},
            "result": result
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        # 提取关键指标
        self._extract_metrics(result_id, result)
        
        return result_id
    
    def _extract_metrics(self, result_id, result):
        """提取并存储关键绩效指标"""
        metrics = {
            "result_id": result_id,
            "symbol": result.get("symbol"),
            "action": result.get("action"),
            "decision_date": result.get("decision_date"),
            "pnl_percent": result.get("pnl_percent", 0),
            "sharpe_ratio": result.get("sharpe_ratio", 0),
            "max_drawdown": result.get("max_drawdown", 0),
            "win_rate": result.get("win_rate", 0),
            "hold_days": result.get("hold_days", 0),
            "timestamp": datetime.now().isoformat()
        }
        
        metrics_file = self.metrics_dir / f"{result_id}_metrics.json"
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    def get_performance_stats(self, symbol=None, action=None, days_back=30):
        """获取性能统计"""
        metrics_files = list(self.metrics_dir.glob("*_metrics.json"))
        
        if not metrics_files:
            return {}
        
        metrics_list = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for file in metrics_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 过滤条件
                if symbol and data.get("symbol") != symbol:
                    continue
                if action and data.get("action") != action:
                    continue
                
                # 时间过滤
                metric_date = datetime.fromisoformat(data.get("timestamp", "2000-01-01"))
                if metric_date < cutoff_date:
                    continue
                
                metrics_list.append(data)
            except:
                continue
        
        if not metrics_list:
            return {}
        
        # 计算统计
        pnls = [m.get("pnl_percent", 0) for m in metrics_list]
        sharpes = [m.get("sharpe_ratio", 0) for m in metrics_list]
        
        return {
            "total_trades": len(metrics_list),
            "avg_pnl": np.mean(pnls),
            "std_pnl": np.std(pnls),
            "avg_sharpe": np.mean(sharpes),
            "win_rate": sum(1 for p in pnls if p > 0) / len(pnls) * 100,
            "best_trade": max(pnls) if pnls else 0,
            "worst_trade": min(pnls) if pnls else 0,
            "recent_trades": metrics_list[-10:]  # 最近10笔
        }

# ==================== 自适应层 ====================
class AdaptiveSystem:
    """自适应系统 - 基于回测结果优化策略"""
    
    def __init__(self, db: PerformanceDatabase):
        self.db = db
        self.learning_history = []
    
    def analyze_performance(self, symbol, lookback_days=30):
        """分析历史表现"""
        stats = self.db.get_performance_stats(symbol=symbol, days_back=lookback_days)
        
        if not stats or stats["total_trades"] < 5:
            return {"status": "insufficient_data", "recommendation": "需要更多数据"}
        
        # 分析模式
        analysis = {
            "status": "analyzed",
            "total_trades": stats["total_trades"],
            "performance_summary": {
                "profitability": "profitable" if stats["avg_pnl"] > 0 else "unprofitable",
                "consistency": "consistent" if stats["std_pnl"] < 5 else "volatile",
                "risk_adjusted": "good" if stats["avg_sharpe"] > 1.0 else "poor"
            },
            "patterns": self._detect_patterns(stats),
            "recommendations": self._generate_recommendations(stats)
        }
        
        return analysis
    
    def _detect_patterns(self, stats):
        """检测交易模式"""
        patterns = []
        
        # 检查是否有趋势
        recent_trades = stats.get("recent_trades", [])
        if len(recent_trades) >= 3:
            recent_pnls = [t["pnl_percent"] for t in recent_trades]
            
            # 趋势检测
            if all(p > 0 for p in recent_pnls):
                patterns.append("winning_streak")
            elif all(p < 0 for p in recent_pnls):
                patterns.append("losing_streak")
            
            # 波动性变化
            if np.std(recent_pnls) > stats["std_pnl"] * 1.5:
                patterns.append("increasing_volatility")
        
        return patterns
    
    def _generate_recommendations(self, stats):
        """生成优化建议"""
        recommendations = []
        
        # 基于表现的建议
        if stats["avg_pnl"] < 0:
            recommendations.append({
                "type": "risk_management",
                "priority": "high",
                "action": "减少仓位规模或增加止损",
                "reason": "平均收益为负"
            })
        
        if stats["win_rate"] < 40:
            recommendations.append({
                "type": "strategy",
                "priority": "high", 
                "action": "重新评估入场信号",
                "reason": "胜率偏低"
            })
        
        if stats["avg_sharpe"] < 0.5:
            recommendations.append({
                "type": "risk_adjustment",
                "priority": "medium",
                "action": "优化止盈止损比例",
                "reason": "风险调整后收益低"
            })
        
        # 如果有赢钱/输钱趋势
        if "losing_streak" in self._detect_patterns(stats):
            recommendations.append({
                "type": "psychology",
                "priority": "high",
                "action": "暂停交易，重新评估策略",
                "reason": "连续亏损可能表示市场条件变化"
            })
        
        return recommendations
    
    def optimize_parameters(self, symbol, current_params):
        """优化策略参数"""
        stats = self.db.get_performance_stats(symbol=symbol, days_back=90)
        
        if not stats or stats["total_trades"] < 10:
            return current_params  # 数据不足，返回原参数
        
        optimized = current_params.copy()
        
        # 基于历史表现调整参数
        if stats["avg_pnl"] < 0:
            # 亏损时减少仓位，增加止损
            if "position_size" in optimized:
                optimized["position_size"] *= 0.8
            if "stop_loss_pct" in optimized:
                optimized["stop_loss_pct"] *= 0.9  # 更紧的止损
        
        if stats["win_rate"] > 60 and stats["avg_pnl"] > 2:
            # 表现好时适度增加风险
            if "position_size" in optimized:
                optimized["position_size"] *= 1.2
        
        # 基于波动性调整持有时间
        if stats["std_pnl"] > 8:
            if "hold_days" in optimized:
                optimized["hold_days"] = max(3, optimized["hold_days"] - 2)
        
        return optimized

# ==================== 集成桥接 ====================
class MainCLIBridge:
    """主CLI桥接器"""
    
    def __init__(self, backtest_engine, db, adaptive_system):
        self.backtest_engine = backtest_engine
        self.db = db
        self.adaptive_system = adaptive_system
        
    def on_main_cli_decision(self, decision_data):
        """
        当主CLI产生决策时调用
        decision_data 应包含:
          - symbol: 交易品种
          - action: 交易动作 (BUY/SELL/HOLD)
          - date: 决策日期
          - confidence: 置信度
          - reasoning: 决策理由
          - agents_involved: 参与的智能体
        """
        console.print("[dim]🔗 主CLI决策接收: 启动自动回测...[/dim]")
        
        # 提取信息
        symbol = decision_data.get("symbol")
        action = decision_data.get("action")
        date = decision_data.get("date")
        
        if not all([symbol, action, date]):
            console.print("[red]❌ 决策数据不完整[/red]")
            return None
        
        # 运行回测
        result = self.backtest_engine.run_backtest(
            symbol=symbol,
            decision_date=date,
            action=action,
            hold_days=10  # 默认持有10天
        )
        
        if "error" in result:
            console.print(f"[red]❌ 回测失败: {result['error']}[/red]")
            return None
        
        # 保存结果
        result_id = self.db.save_result(result, source="main_cli", metadata=decision_data)
        
        # 分析表现
        analysis = self.adaptive_system.analyze_performance(symbol)
        
        # 生成反馈报告
        feedback = self._generate_feedback_report(result, analysis, decision_data)
        
        # 优化参数（如果适用）
        optimized_params = self._optimize_for_next_decision(symbol, decision_data)
        
        return {
            "result_id": result_id,
            "backtest_result": result,
            "performance_analysis": analysis,
            "feedback": feedback,
            "optimized_parameters": optimized_params
        }
    
    def _generate_feedback_report(self, result, analysis, decision_data):
        """生成反馈报告"""
        feedback = {
            "timestamp": datetime.now().isoformat(),
            "original_decision": {
                "symbol": decision_data.get("symbol"),
                "action": decision_data.get("action"),
                "confidence": decision_data.get("confidence", 0),
                "agents": decision_data.get("agents_involved", [])
            },
            "backtest_outcome": {
                "pnl_percent": result.get("pnl_percent", 0),
                "sharpe_ratio": result.get("sharpe_ratio", 0),
                "success": result.get("pnl_percent", 0) > 0
            },
            "learning_points": [],
            "suggestions": []
        }
        
        # 学习点
        if result.get("pnl_percent", 0) > 5:
            feedback["learning_points"].append("决策产生了显著正收益")
        elif result.get("pnl_percent", 0) < -5:
            feedback["learning_points"].append("决策产生了显著负收益，需要反思")
        
        # 建议
        if "recommendations" in analysis:
            for rec in analysis["recommendations"]:
                if rec.get("priority") == "high":
                    feedback["suggestions"].append(rec["action"])
        
        return feedback
    
    def _optimize_for_next_decision(self, symbol, decision_data):
        """为下一次决策优化参数"""
        current_params = {
            "position_size": 0.01,  # 1%仓位
            "stop_loss_pct": 2.0,
            "take_profit_pct": 4.0,
            "hold_days": 10,
            "confidence_threshold": decision_data.get("confidence", 0.7)
        }
        
        optimized = self.adaptive_system.optimize_parameters(symbol, current_params)
        
        console.print(f"[dim]🔄 参数优化: {current_params} → {optimized}[/dim]")
        
        return optimized

# ==================== 主CLI模拟器 ====================
class MockMainCLI:
    """模拟主CLI用于测试"""
    
    def __init__(self, bridge):
        self.bridge = bridge
    
    def simulate_decision(self, symbol="EURUSD", action="BUY", confidence=0.75):
        """模拟主CLI产生决策"""
        decision_data = {
            "symbol": symbol,
            "action": action,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "confidence": confidence,
            "reasoning": f"模拟决策: {action} {symbol} 基于技术分析",
            "agents_involved": ["market_analyst", "news_analyst"],
            "timestamp": datetime.now().isoformat()
        }
        
        console.print(f"[bold]🤖 模拟主CLI决策:[/bold]")
        console.print(f"  品种: {symbol}")
        console.print(f"  动作: {action}")
        console.print(f"  置信度: {confidence:.2f}")
        
        # 触发桥接
        return self.bridge.on_main_cli_decision(decision_data)

# ==================== CLI命令 ====================
app = typer.Typer()

@app.command()
def auto_test(
    symbol: str = typer.Option("EURUSD", "--symbol", "-s", help="测试品种"),
    iterations: int = typer.Option(5, "--iterations", "-i", help="测试次数"),
):
    """
    自动测试集成系统
    """
    console.print(Panel.fit(
        f"🤖 自适应系统集成测试",
        border_style="cyan",
        subtitle=f"{symbol} | {iterations}次迭代"
    ))
    
    # 初始化系统
    from cli.backtest_cli import SimpleBacktestEngine
    
    db = PerformanceDatabase()
    adaptive = AdaptiveSystem(db)
    engine = SimpleBacktestEngine()
    bridge = MainCLIBridge(engine, db, adaptive)
    mock_cli = MockMainCLI(bridge)
    
    results = []
    
    for i in range(iterations):
        console.print(f"\n[bold]🔄 迭代 {i+1}/{iterations}[/bold]")
        
        # 模拟决策（交替买入卖出）
        action = "BUY" if i % 2 == 0 else "SELL"
        confidence = 0.7 + (i * 0.05)  # 逐步增加置信度
        
        feedback = mock_cli.simulate_decision(symbol, action, confidence)
        
        if feedback:
            results.append(feedback)
            
            # 显示简要结果
            result = feedback.get("backtest_result", {})
            console.print(f"  结果: {result.get('pnl_percent', 0):.2f}% | "
                         f"夏普: {result.get('sharpe_ratio', 0):.3f}")
    
    # 显示测试总结
    if results:
        console.print("\n" + "="*60)
        console.print("[bold green]📊 测试总结[/bold green]")
        console.print("="*60)
        
        pnls = [r.get("backtest_result", {}).get("pnl_percent", 0) for r in results]
        positive = sum(1 for p in pnls if p > 0)
        
        console.print(f"总测试次数: {len(results)}")
        console.print(f"平均收益率: {np.mean(pnls):.2f}%")
        console.print(f"胜率: {positive/len(results)*100:.1f}%")
        
        # 显示学习建议
        analysis = adaptive.analyze_performance(symbol)
        if "recommendations" in analysis:
            console.print("\n[bold]🎯 系统建议:[/bold]")
            for rec in analysis["recommendations"][:3]:  # 显示前3个
                console.print(f"  • {rec.get('action')} ({rec.get('reason')})")

@app.command()
def analyze_history(
    symbol: str = typer.Argument(..., help="分析品种"),
    days: int = typer.Option(30, "--days", "-d", help="分析天数"),
):
    """
    分析历史表现
    """
    db = PerformanceDatabase()
    adaptive = AdaptiveSystem(db)
    
    analysis = adaptive.analyze_performance(symbol, days)
    
    console.print(Panel.fit(
        f"📈 {symbol} 历史表现分析",
        border_style="green",
        subtitle=f"过去{days}天"
    ))
    
    if analysis["status"] == "insufficient_data":
        console.print("[yellow]⚠️  数据不足，需要更多交易记录[/yellow]")
        return
    
    # 显示分析结果
    table = Table(box=box.ROUNDED)
    table.add_column("指标", style="cyan")
    table.add_column("数值", style="green")
    
    table.add_row("总交易次数", str(analysis.get("total_trades", 0)))
    
    perf = analysis.get("performance_summary", {})
    table.add_row("盈利能力", perf.get("profitability", "N/A"))
    table.add_row("一致性", perf.get("consistency", "N/A"))
    table.add_row("风险调整", perf.get("risk_adjusted", "N/A"))
    
    console.print(table)
    
    # 显示模式
    patterns = analysis.get("patterns", [])
    if patterns:
        console.print(f"\n[bold]🔄 检测到模式:[/bold]")
        for pattern in patterns:
            pattern_names = {
                "winning_streak": "📈 赢钱趋势",
                "losing_streak": "📉 输钱趋势", 
                "increasing_volatility": "⚡ 波动增加"
            }
            console.print(f"  • {pattern_names.get(pattern, pattern)}")
    
    # 显示建议
    recommendations = analysis.get("recommendations", [])
    if recommendations:
        console.print(f"\n[bold]🎯 优化建议:[/bold]")
        for rec in recommendations[:5]:  # 显示前5个
            priority_icon = "🔴" if rec.get("priority") == "high" else "🟡"
            console.print(f"  {priority_icon} {rec.get('action')}")

def main():
    """主函数"""
    console.print(Panel.fit(
        "[bold green]TradingAgents 自适应回测系统[/bold green]\n"
        "[dim]为智能体系统提供自动回测和反馈循环[/dim]",
        border_style="green"
    ))
    
    app()

if __name__ == "__main__":
    main()