"""
自适应回测工作流 - 修复增强版
文件位置: /Users/fr./Downloads/TradingAgents-main/cli/adaptive_workflow.py
"""

import sys
import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import numpy as np

# 确保可以导入其他cli模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("🚀 加载自适应回测系统...")

class AdaptiveBacktestWorkflow:
    """
    自适应回测工作流
    连接主CLI决策和回测验证，提供反馈循环
    """
    
    def __init__(self, data_dir="./adaptive_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # 尝试导入现有的回测系统
        try:
            from cli.backtest_cli import SimpleBacktestEngine
            self.backtest_engine = SimpleBacktestEngine()
            self.has_backtest = True
            print("✅ 回测引擎加载成功")
        except (ImportError, ModuleNotFoundError) as e:
            print(f"⚠️  无法导入回测引擎: {e}")
            print("⚠️  使用模拟回测模式")
            self.backtest_engine = None
            self.has_backtest = False
    
    def process_main_cli_decision(self, decision_data):
        """
        处理主CLI的决策
        Args:
            decision_data: 包含symbol, action, date, confidence, reasoning等
        Returns:
            包含回测结果、分析和建议的字典
        """
        print(f"\n🔗 自适应系统收到决策:")
        print(f"   品种: {decision_data.get('symbol')}")
        print(f"   动作: {decision_data.get('action')}")
        print(f"   日期: {decision_data.get('date')}")
        print(f"   置信度: {decision_data.get('confidence', 0):.2f}")
        
        # 1. 运行回测
        backtest_result = self._run_backtest(decision_data)
        
        # 2. 保存记录
        record = self._save_record(decision_data, backtest_result)
        
        # 3. 分析历史表现
        analysis = self._analyze_performance(decision_data['symbol'])
        
        # 4. 生成反馈
        feedback = self._generate_feedback(decision_data, backtest_result, analysis)
        
        # 5. 优化参数
        optimized_params = self._optimize_parameters(decision_data['symbol'])
        
        return {
            'record_id': record['id'],
            'decision': decision_data,
            'backtest_result': backtest_result,
            'performance_analysis': analysis,
            'feedback': feedback,
            'optimized_parameters': optimized_params,
            'timestamp': datetime.now().isoformat()
        }
    
    def _run_backtest(self, decision_data):
        """运行回测逻辑"""
        symbol = decision_data['symbol']
        date = decision_data['date']
        action = decision_data['action']
        
        if self.has_backtest and self.backtest_engine:
            try:
                print(f"   运行真实回测...")
                return self.backtest_engine.run_backtest(symbol, date, action)
            except Exception as e:
                print(f"⚠️  回测失败: {e}")
        
        return self._simulate_backtest(symbol, date, action, decision_data.get('confidence', 0.5))
    
    def _simulate_backtest(self, symbol, date, action, confidence):
        """模拟回测（当真实引擎不可用时）"""
        print(f"   运行模拟回测...")
        
        seed_str = f"{symbol}{date}{action}{confidence}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16) % 10000
        np.random.seed(seed)
        
        # 模拟收益逻辑
        base_pnl = np.random.normal(2.0, 4.0)
        confidence_effect = (confidence - 0.5) * 3
        final_pnl = np.clip(base_pnl + confidence_effect, -20, 20)
        
        return {
            'symbol': symbol,
            'decision_date': date,
            'action': action,
            'pnl_percent': round(float(final_pnl), 2),
            'sharpe_ratio': round(float(np.random.uniform(0.1, 1.8)), 3),
            'max_drawdown': round(float(np.random.uniform(-3, -15)), 2),
            'hold_days': int(np.random.randint(3, 21)),
            'entry_price': 1.10000,
            'exit_price': round(1.10000 * (1 + final_pnl/100), 5),
            'simulated': True
        }

    def _save_record(self, decision_data, backtest_result):
        """保存记录到文件"""
        record_id = f"{decision_data['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        record = {
            'id': record_id,
            'timestamp': datetime.now().isoformat(),
            'decision': decision_data,
            'backtest_result': backtest_result
        }
        
        file_path = self.data_dir / f"{record_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
        
        print(f"📁 记录已保存: {file_path}")
        return record

    def _analyze_performance(self, symbol, lookback_days=30):
        """分析历史表现"""
        print(f"   分析 {symbol} 的历史表现...")
        records = []
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        
        for file in self.data_dir.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data.get('decision', {}).get('symbol') == symbol:
                    record_time = datetime.fromisoformat(data.get('timestamp', '2000-01-01'))
                    if record_time >= cutoff_date:
                        records.append(data)
            except Exception:
                continue
        
        if len(records) < 3:
            return {'status': 'insufficient_data', 'message': f'只有 {len(records)} 条记录，需要更多数据'}
        
        pnls = [r.get('backtest_result', {}).get('pnl_percent', 0) for r in records]
        
        analysis = {
            'status': 'analyzed',
            'total_trades': len(records),
            'avg_pnl': round(float(np.mean(pnls)), 2),
            'std_pnl': round(float(np.std(pnls)), 2),
            'win_rate': round(sum(1 for p in pnls if p > 0) / len(pnls) * 100, 1),
            'best_trade': round(float(max(pnls)), 2),
            'worst_trade': round(float(min(pnls)), 2),
            'patterns': self._detect_patterns(records)
        }
        analysis['recommendations'] = self._generate_recommendations(analysis)
        return analysis

    def _detect_patterns(self, records):
        """检测交易模式"""
        patterns = []
        if len(records) >= 3:
            recent_pnls = [r.get('backtest_result', {}).get('pnl_percent', 0) for r in records[-3:]]
            if all(p > 0 for p in recent_pnls): patterns.append('winning_streak')
            elif all(p < 0 for p in recent_pnls): patterns.append('losing_streak')
        return patterns

    def _generate_feedback(self, decision, result, analysis):
        """生成实时反馈文本"""
        pnl = result.get('pnl_percent', 0)
        suggestions = []
        if pnl > 0:
            suggestions.append("当前决策逻辑与回测表现一致，建议维持。")
        else:
            suggestions.append("回测显示潜在亏损，建议重新检查入场因子。")
        
        return {
            'summary': f"回测预期收益 {pnl}%",
            'suggestions': suggestions
        }

    def _generate_recommendations(self, analysis):
        """生成优化建议"""
        recs = []
        if analysis['avg_pnl'] < 0:
            recs.append({'priority': 'high', 'action': '降低仓位', 'reason': '平均收益为负'})
        if analysis['win_rate'] < 40:
            recs.append({'priority': 'high', 'action': '优化信号', 'reason': '胜率较低'})
        return recs

    def _optimize_parameters(self, symbol):
        """优化策略参数"""
        return {
            'position_size': 0.01,
            'stop_loss_pct': 2.0,
            'take_profit_pct': 4.0,
            'min_confidence': 0.6
        }

# ==================== 演示与指南 ====================

def demo_simple():
    print("="*60)
    print("🤖 自适应回测系统演示")
    print("="*60)
    
    workflow = AdaptiveBacktestWorkflow(data_dir="./adaptive_demo_data")
    
    decisions = [
        {'symbol': 'EURUSD', 'action': 'BUY', 'date': '2024-12-01', 'confidence': 0.82}
    ]
    
    for dec in decisions:
        try:
            result = workflow.process_main_cli_decision(dec)
            pnl = result['backtest_result']['pnl_percent']
            print(f"   回测结果: {pnl}%")
        except Exception as e:
            print(f"   ❌ 错误: {e}")

def show_integration_guide():
    print("\n" + "="*60)
    print("🔧 如何集成到主CLI (main.py)")
    print("="*60)
    guide = """
    1. 导入: from cli.adaptive_workflow import AdaptiveBacktestWorkflow
    2. 实例化: workflow = AdaptiveBacktestWorkflow()
    3. 调用: 
       adaptive_result = workflow.process_main_cli_decision({
           'symbol': ticker,
           'action': action,
           'date': analysis_date,
           'confidence': confidence
       })
    """
    print(guide)

if __name__ == "__main__":
    demo_simple()
    show_integration_guide()