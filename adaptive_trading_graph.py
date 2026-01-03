# adaptive_trading_graph.py
"""
自适应增强版 TradingAgentsGraph
通过子类继承方式集成自适应权重系统
"""
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from typing import Dict, Any, List, Optional
from datetime import datetime

# 尝试导入原Graph
try:
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    GRAPH_IMPORT_SUCCESS = True
except ImportError as e:
    print(f"⚠️  无法导入原TradingAgentsGraph: {e}")
    print("将创建独立的自适应处理器")
    GRAPH_IMPORT_SUCCESS = False


class AdaptiveGraphEnhancer:
    """自适应Graph增强器核心类"""
    
    def __init__(self):
        from tradingagents.adaptive_system import AdaptiveSystem
        self.adaptive = AdaptiveSystem()
        self._register_default_agents()
    
    def _register_default_agents(self):
        """注册所有智能体类型"""
        agents = [
            # 基础分析师（来自init_agent_state）
            ("market_analyst", "analyst"),
            ("sentiment_analyst", "analyst"),
            ("news_analyst", "analyst"),
            ("technical_analyst", "analyst"),
            ("quantitative_analyst", "analyst"),
            
            # 研究团队
            ("bull_researcher", "researcher"),
            ("bear_researcher", "researcher"),
            
            # 风险管理（来自risk_debate_state）
            ("risky_analyst", "debator"),
            ("safe_analyst", "debator"),
            ("neutral_analyst", "debator"),
            
            # 交易和管理
            ("trader", "trader"),
            ("research_manager", "manager"),
            ("portfolio_manager", "manager"),
        ]
        
        for name, agent_type in agents:
            self.adaptive.register_agent(name, agent_type)
    
    def enhance_final_state(self, final_state: Dict[str, Any], 
                           company_name: str, trade_date: str) -> Dict[str, Any]:
        """
        增强最终状态
        
        从您的 propagate 方法看，final_state 包含：
        - 各种 report 字段
        - final_trade_decision
        - investment_debate_state
        - risk_debate_state
        """
        # 输入验证
        if not isinstance(final_state, dict):
            print(f"⚠️ final_state 必须是字典类型，但收到 {type(final_state)}")
            return final_state
        
        if not company_name or not trade_date:
            print("⚠️ company_name 和 trade_date 不能为空")
            return final_state
        
        # 1. 提取预测信号
        predictions = self._extract_from_final_state(final_state)
        
        if not predictions:
            print(f"⚠️  {company_name} @ {trade_date}: 未提取到有效预测")
            return final_state
        
        print(f"\n🔧 自适应增强 - {company_name} @ {trade_date}")
        print(f"   提取到 {len(predictions)} 个智能体预测")
        
        # 2. 处理预测
        for agent_name, signal in predictions.items():
            self.adaptive.record_prediction(agent_name, signal)
        
        adaptive_result = self.adaptive.get_weighted_decision(predictions)
        
        # 3. 构建增强数据
        enhanced_data = {
            "adaptive_timestamp": datetime.now().isoformat(),
            "adaptive_predictions": predictions,
            "adaptive_weights": adaptive_result["weights"],
            "adaptive_decision": adaptive_result["weighted_decision"],
            "adaptive_raw_decision": adaptive_result["weighted_decision"],  # 原始数值信号
        }
        
        # 4. 解析原始决策
        if "final_trade_decision" in final_state:
            original_decision = final_state["final_trade_decision"]
            enhanced_data["original_decision"] = original_decision
            enhanced_data["original_decision_numeric"] = self._parse_decision(original_decision)
            
            # 显示对比
            print(f"   📊 原始决策: {self._truncate_text(original_decision, 60)}")
            print(f"   ⚖️  自适应决策: {adaptive_result['weighted_decision']:.3f}")
            print(f"   🔢 原始数值: {enhanced_data['original_decision_numeric']:.3f}")
        
        # 5. 添加到final_state（不破坏原结构）
        # 检查是否已存在增强数据
        if "_adaptive_enhancement" in final_state:
            print("⚠️  已存在增强数据，将替换")
        
        final_state["_adaptive_enhancement"] = enhanced_data
        
        # 6. 保存到文件
        self._save_enhancement(final_state, company_name, trade_date)
        
        return final_state
    
    def _extract_from_final_state(self, state: Dict[str, Any]) -> Dict[str, float]:
        """从final_state中提取预测信号"""
        predictions = {}
        
        # 1. 从各种报告中提取（基于您的 propagate 方法）
        report_fields = [
            "market_report",
            "sentiment_report", 
            "news_report",
            "technical_report",
            "quantitative_report",
            "research_manager_report",  # 添加遗漏的字段
            "portfolio_manager_report",  # 添加遗漏的字段
        ]
        
        for field in report_fields:
            if field in state and state[field]:
                agent_name = field.replace("_report", "")
                if agent_name == "market":
                    agent_name = "market_analyst"
                elif agent_name == "sentiment":
                    agent_name = "sentiment_analyst"
                elif agent_name == "news":
                    agent_name = "news_analyst"
                elif agent_name == "technical":
                    agent_name = "technical_analyst"
                elif agent_name == "quantitative":
                    agent_name = "quantitative_analyst"
                
                signal = self._parse_report_signal(state[field])
                predictions[agent_name] = signal
        
        # 2. 从debate states中提取
        if "investment_debate_state" in state:
            debate_state = state["investment_debate_state"]
            if hasattr(debate_state, 'current_response'):
                predictions["bull_researcher"] = self._parse_debate_signal(
                    debate_state.current_response, "bull"
                )
        
        if "risk_debate_state" in state:
            risk_state = state["risk_debate_state"]
            # 可能包含多个风险分析师的观点
        
        # 3. 检查是否有直接可用的数值信号
        if "signals" in state and isinstance(state["signals"], dict):
            for name, value in state["signals"].items():
                if isinstance(value, (int, float)):
                    predictions[name] = float(value)
        
        return predictions
    
    def _parse_report_signal(self, content: str) -> float:
        """改进的信号解析"""
        if not content or not isinstance(content, str):
            return 0.0
        
        content_lower = content.lower()
        
        # 使用正则表达式提取数值信号
        import re
        
        # 尝试提取明确的数值信号 (如 "signal: 0.75")
        num_patterns = [
            r'signal[:=]\s*(-?\d+\.?\d*)',
            r'confidence[:=]\s*(\d+\.?\d*)',
            r'score[:=]\s*(-?\d+\.?\d*)',
        ]
        
        for pattern in num_patterns:
            matches = re.findall(pattern, content_lower)
            if matches:
                try:
                    value = float(matches[0])
                    return max(-1.0, min(1.0, value))  # 限制在[-1, 1]
                except ValueError:
                    pass
        
        # 使用更精确的关键词匹配
        signal_map = [
            (['strong buy', 'definitely buy'], 0.9),
            (['buy', 'long', 'bullish'], 0.6),
            (['hold', 'neutral'], 0.0),
            (['sell', 'short', 'bearish'], -0.6),
            (['strong sell', 'definitely sell'], -0.9),
        ]
        
        for keywords, signal in signal_map:
            if any(keyword in content_lower for keyword in keywords):
                # 检查是否有否定词（如 "not bullish"）
                if any(f"not {k}" in content_lower for k in keywords):
                    return -signal * 0.5
                return signal
        
        return 0.0
    
    def _parse_debate_signal(self, content: str, analyst_type: str) -> float:
        """解析辩论信号"""
        if not content:
            return 0.0
        
        if analyst_type == "bull":
            return 0.6 if "bull" in content.lower() else 0.3
        elif analyst_type == "bear":
            return -0.6 if "bear" in content.lower() else -0.3
        
        return 0.0
    
    def _parse_decision(self, decision_text: str) -> float:
        """解析最终决策文本"""
        if not decision_text:
            return 0.0
        
        text_lower = decision_text.lower()
        
        # 检查明确的交易指令
        if "buy" in text_lower and "sell" not in text_lower:
            # 尝试提取百分比
            import re
            percentages = re.findall(r'(\d+(?:\.\d+)?)%', decision_text)
            if percentages:
                size = float(percentages[0]) / 100.0
                return min(1.0, 0.5 + size)  # 仓位越大信号越强
            return 0.8
        elif "sell" in text_lower and "buy" not in text_lower:
            return -0.8
        elif "hold" in text_lower:
            return 0.0
        
        return 0.0
    
    def _truncate_text(self, text: str, max_len: int = 50) -> str:
        """截断文本"""
        if not text or not isinstance(text, str):
            return ""
        if len(text) <= max_len:
            return text
        return text[:max_len] + "..."
    
    def _save_enhancement(self, state: Dict[str, Any], company: str, date: str):
        """保存增强结果"""
        output_dir = "adaptive_enhancements"
        os.makedirs(output_dir, exist_ok=True)
        
        safe_company = company.replace("/", "_").replace(" ", "_")
        safe_date = date.replace(" ", "_").replace(":", "_")
        
        filename = f"{output_dir}/{safe_company}_{safe_date}.json"
        
        # 只保存增强部分，避免文件过大
        enhancement_data = {
            "company": company,
            "date": date,
            "timestamp": datetime.now().isoformat(),
            "enhancement": state.get("_adaptive_enhancement", {}),
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(enhancement_data, f, indent=2)
            print(f"   💾 增强结果保存到: {filename}")
        except Exception as e:
            print(f"   ⚠️ 保存失败: {e}")
    
    def update_with_market_result(self, actual_change: float):
        """更新权重"""
        agents = list(self.adaptive.weight_manager.agents.keys())
        
        print(f"\n📈 权重更新 - 市场变动: {actual_change:.2%}")
        
        for agent in agents:
            self.adaptive.update_with_result(agent, actual_change)
        
        print(f"   ✅ 已更新 {len(agents)} 个智能体")


# ==================== 主集成类 ====================

if GRAPH_IMPORT_SUCCESS:
    class AdaptiveTradingAgentsGraph(TradingAgentsGraph):
        """
        自适应增强版 TradingAgentsGraph
        继承原类，重写 propagate 方法添加自适应功能
        """
        
        def __init__(self, selected_analysts=None, debug=False, *args, **kwargs):
            """
            初始化，添加自适应增强器
            
            Args:
                selected_analysts: 选择的分析师列表（原Graph参数）
                debug: 调试模式（原Graph参数）
                *args, **kwargs: 其他传递给父类的参数
            """
            # 提取父类可能需要的参数，其余传给父类
            super().__init__(selected_analysts=selected_analysts, debug=debug, *args, **kwargs)
            self.adaptive_enhancer = AdaptiveGraphEnhancer()
            print("✅ 自适应TradingAgentsGraph 已初始化")
            print(f"   模式: {'调试' if debug else '正常'}")
            print(f"   分析师: {selected_analysts}")
        
        def propagate(self, company_name, trade_date):
            """
            增强的 propagate 方法
            
            在原有流程基础上：
            1. 运行原始Graph获取决策
            2. 提取各智能体信号
            3. 应用自适应权重
            4. 返回增强结果
            """
            # 调用父类的原始方法
            final_state, processed_signal = super().propagate(company_name, trade_date)
            
            # 添加自适应增强
            enhanced_state = self.adaptive_enhancer.enhance_final_state(
                final_state, company_name, trade_date
            )
            
            # 如果增强后有权重决策，可以替代或补充原信号
            if "_adaptive_enhancement" in enhanced_state:
                adaptive_data = enhanced_state["_adaptive_enhancement"]
                
                # 可以选择使用自适应决策
                # processed_signal = adaptive_data["adaptive_decision"]
                
                # 或者融合决策
                original_signal = self._extract_signal_from_decision(
                    enhanced_state.get("final_trade_decision", "")
                )
                adaptive_signal = adaptive_data["adaptive_decision"]
                
                # 简单加权平均
                fused_signal = 0.3 * original_signal + 0.7 * adaptive_signal
                
                # 更新processed_signal（可选）
                # processed_signal = fused_signal
            
            return enhanced_state, processed_signal
        
        def _extract_signal_from_decision(self, decision_text: str) -> float:
            """从决策文本中提取信号"""
            enhancer = AdaptiveGraphEnhancer()
            return enhancer._parse_decision(decision_text)
        
        def update_adaptive_weights(self, actual_change: float):
            """更新自适应权重（交易后调用）"""
            self.adaptive_enhancer.update_with_market_result(actual_change)
else:
    # 备用方案：独立处理器
    class AdaptiveTradingAgentsGraph:
        """独立的自适应处理器（当无法导入原Graph时）"""
        
        def __init__(self, selected_analysts=None, debug=False, **kwargs):
            """
            独立处理器的构造函数
            
            Args:
                selected_analysts: 模拟的选择分析师列表
                debug: 调试模式
                **kwargs: 其他参数（用于保持接口兼容）
            """
            self.selected_analysts = selected_analysts or []
            self.debug = debug
            self.adaptive_enhancer = AdaptiveGraphEnhancer()
            self.original_params = kwargs  # 保存其他参数
            
            print("⚠️  使用独立自适应处理器（原Graph导入失败）")
            if debug:
                print(f"   模拟分析师: {self.selected_analysts}")
        
        def propagate(self, company_name, trade_date, mock_state=None):
            """模拟 propagate 方法"""
            if mock_state is None:
                # 创建模拟状态
                mock_state = self._create_mock_state(company_name, trade_date)
            
            enhanced_state = self.adaptive_enhancer.enhance_final_state(
                mock_state, company_name, trade_date
            )
            
            # 模拟处理信号
            processed_signal = enhanced_state.get("_adaptive_enhancement", {}).get(
                "adaptive_decision", 0.0
            )
            
            return enhanced_state, processed_signal
        
        def _create_mock_state(self, company_name: str, trade_date: str) -> Dict[str, Any]:
            """创建模拟状态"""
            return {
                "company_of_interest": company_name,
                "trade_date": trade_date,
                "market_report": f"Market analysis for {company_name} on {trade_date}. Bullish momentum observed.",
                "news_report": f"News analysis suggests positive sentiment for {company_name}.",
                "technical_report": "Buy signal confirmed. RSI 45, MACD bullish.",
                "final_trade_decision": f"Buy {company_name} with 2% position. Target: 1.1000, Stop: 1.0850.",
            }
        
        def update_adaptive_weights(self, actual_change: float):
            """更新自适应权重"""
            self.adaptive_enhancer.update_with_market_result(actual_change)


# ==================== 使用示例 ====================

def demonstrate_usage():
    """演示如何使用自适应Graph"""
    
    print("🚀 自适应TradingAgentsGraph 使用演示")
    print("=" * 50)
    
    try:
        # 尝试使用增强版Graph（正确传递参数）
        graph = AdaptiveTradingAgentsGraph(
            selected_analysts=["market", "social", "news", "technical"],
            debug=True,
            # 如果有其他原Graph参数，可以继续添加
            # model_name="gpt-4",
            # max_tokens=1000,
        )
        
        print("\n🧪 模拟运行Graph...")
        
        # 模拟 propagate 调用
        final_state, signal = graph.propagate(
            company_name="EURUSD",
            trade_date="2024-01-15"
        )
        
        print(f"\n✅ Graph运行完成:")
        print(f"   最终信号: {signal:.3f}")
        
        if "_adaptive_enhancement" in final_state:
            adaptive_data = final_state["_adaptive_enhancement"]
            print(f"   自适应决策: {adaptive_data['adaptive_decision']:.3f}")
            print(f"   原始决策: {adaptive_data.get('original_decision_numeric', 0):.3f}")
        
        # 模拟市场更新
        print("\n📈 模拟市场更新...")
        graph.update_adaptive_weights(0.015)  # 1.5%上涨
        
    except Exception as e:
        print(f"⚠️  Graph运行失败: {e}")
        print("\n使用独立模式演示...")
        
        # 使用独立处理器（参数与增强版保持一致）
        processor = AdaptiveTradingAgentsGraph(
            selected_analysts=["market", "technical"],
            debug=True
        )
        
        # 模拟 propagate 调用
        final_state, signal = processor.propagate(
            company_name="EURUSD",
            trade_date="2024-01-15"
        )
        
        print(f"\n✅ 独立处理器运行完成:")
        print(f"   最终信号: {signal:.3f}")
        
        if "_adaptive_enhancement" in final_state:
            adaptive_data = final_state["_adaptive_enhancement"]
            print(f"   自适应决策: {adaptive_data['adaptive_decision']:.3f}")
        
        # 模拟市场更新
        processor.update_adaptive_weights(0.012)


def get_integration_instructions(import_success=True): # 建议通过参数传递状态
    """获取集成说明"""
    
    print("\n" + "="*60)
    print("🎯 集成到您的系统")
    print("="*60)
    
    # 使用传入的参数判断
    if import_success:
        print("""
✅ 检测到原TradingAgentsGraph可导入

集成步骤：
1. 将本文件保存为 adaptive_trading_graph.py
2. 在您现有的代码中替换：

   原代码：
   from tradingagents.graph.trading_graph import TradingAgentsGraph
   graph = TradingAgentsGraph(selected_analysts=..., debug=...)
   
   修改为：
   from adaptive_trading_graph import AdaptiveTradingAgentsGraph
   graph = AdaptiveTradingAgentsGraph(selected_analysts=..., debug=...)

使用方法与原Graph完全相同：
   # 运行Graph
   final_state, signal = graph.propagate("EURUSD", "2024-01-15")

   # 交易后更新权重
   actual_change = get_actual_price_change()  # 您的逻辑
   graph.update_adaptive_weights(actual_change)

增强的数据在 final_state["_adaptive_enhancement"] 中
""")
    else:
        print("""
⚠️ 原TradingAgentsGraph不可用，将使用独立自适应处理器。

使用方法：
1. 将本文件保存为 adaptive_trading_graph.py
2. 在您的代码中使用：
   from adaptive_trading_graph import AdaptiveTradingAgentsGraph

   graph = AdaptiveTradingAgentsGraph(selected_analysts=["market", "technical"])
   final_state, signal = graph.propagate("EURUSD", "2024-01-15")
   graph.update_adaptive_weights(0.015)
""")

    print("📝 注意事项:")
    print(" • 增强数据保存在 final_state['_adaptive_enhancement']")
    print(" • 自适应权重自动学习和更新")
    print(" • 结果保存在 adaptive_enhancements/ 目录")

# 正确的入口检查
if __name__ == "__main__":
    # 假设 GRAPH_IMPORT_SUCCESS 在文件顶部定义
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        GRAPH_IMPORT_SUCCESS = True
    except ImportError:
        GRAPH_IMPORT_SUCCESS = False

    # demonstrate_usage() # 确保此函数已定义
    get_integration_instructions(GRAPH_IMPORT_SUCCESS)