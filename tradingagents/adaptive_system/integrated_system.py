"""
与您现有系统的完整集成
"""
import sys
import os

# 确保可以导入您的模块
sys.path.append('/Users/fr./Downloads/TradingAgents-main')

class FullIntegrationSystem:
    """完整的集成系统"""
    
    def __init__(self):
        # 导入您的分析师
        self.analysts = self._import_analysts()
        
        # 初始化层管理器
        self.layer_manager = DirectDataIntegratedLayerManager()
        
        # 初始化权重管理器
        from tradingagents.adaptive_system.weight_manager import AdaptiveWeightManager
        from tradingagents.adaptive_system.config import AdaptiveConfig
        
        config = AdaptiveConfig()
        self.weight_manager = AdaptiveWeightManager(config)
        
        # 注册您的分析师
        self._register_analysts()
    
    def _import_analysts(self):
        """导入您的分析师模块"""
        analysts = {}
        
        try:
            # 导入宏观分析师
            from tradingagents.agents.analysts.macro_analyst import create_macro_analyst
            analysts["macro_analyst"] = create_macro_analyst
            
            # 导入新闻分析师
            from tradingagents.agents.analysts.news_analyst import create_news_analyst
            analysts["news_analyst"] = create_news_analyst
            
            # 导入技术分析师
            from tradingagents.agents.analysts.technical_analyst import create_technical_analyst
            analysts["technical_analyst"] = create_technical_analyst
            
            # 导入量化分析师
            from tradingagents.agents.analysts.quantitative_analyst import create_quantitative_analyst
            analysts["quantitative_analyst"] = create_quantitative_analyst
            
            print("✅ 成功导入所有分析师")
            
        except ImportError as e:
            print(f"⚠️  导入分析师失败: {e}")
            # 创建模拟分析师作为备用
            analysts = self._create_mock_analysts()
        
        return analysts
    
    def _create_mock_analysts(self):
        """创建模拟分析师（备用）"""
        print("⚠️  使用模拟分析师")
        
        def mock_analyst(state):
            return {
                "messages": [{"role": "assistant", "content": f"模拟分析: {state.get('currency_pair', '未知')}"}],
                f"{state.get('analyst_type', 'mock')}_report": "这是模拟分析报告"
            }
        
        return {
            "macro_analyst": lambda llm: lambda state: mock_analyst({**state, "analyst_type": "macro"}),
            "news_analyst": lambda llm: lambda state: mock_analyst({**state, "analyst_type": "news"}),
            "technical_analyst": lambda llm: lambda state: mock_analyst({**state, "analyst_type": "technical"}),
            "quantitative_analyst": lambda llm: lambda state: mock_analyst({**state, "analyst_type": "quantitative"})
        }
    
    def _register_analysts(self):
        """在权重管理器中注册分析师"""
        analyst_names = [
            "macro_analyst",
            "news_analyst", 
            "technical_analyst",
            "quantitative_analyst"
        ]
        
        for name in analyst_names:
            # 确定层级
            if name == "macro_analyst":
                layer = "strategic"
            elif name == "technical_analyst":
                layer = "tactical"
            elif name == "news_analyst":
                layer = "operational"
            else:  # quantitative_analyst
                layer = "strategic"
            
            self.weight_manager.register_agent(name, layer)
            print(f"📝 注册分析师: {name} ({layer}层)")
    
    def execute_analysis(self, symbol: str, llm=None):
        """执行完整分析流程"""
        print(f"\n🔍 开始分析: {symbol}")
        
        # 1. 直接从数据检测市场状态
        print("📊 检测市场状态...")
        regime_result = self.layer_manager.detect_regime_from_data(symbol)
        
        print(f"  检测结果: {regime_result['dominant_regime']} "
              f"(置信度: {regime_result['confidence']:.1%})")
        
        # 2. 运行各分析师（如果需要）
        analyst_reports = {}
        
        if llm is not None:
            print("🤖 运行分析师...")
            
            # 准备状态
            state = {
                "trade_date": datetime.now().strftime("%Y-%m-%d"),
                "currency_pair": symbol,
                "company_of_interest": symbol,
                "messages": []
            }
            
            # 运行各分析师
            for analyst_name, analyst_creator in self.analysts.items():
                try:
                    print(f"  → {analyst_name}...")
                    analyst_func = analyst_creator(llm)
                    result = analyst_func(state)
                    
                    # 提取报告
                    report_key = f"{analyst_name.split('_')[0]}_report"
                    report_content = result.get(report_key, "无报告内容")
                    
                    analyst_reports[analyst_name] = {
                        "report": report_content,
                        "confidence": 0.6,  # 可替换为实际置信度计算
                        "timestamp": datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    print(f"  ❌ {analyst_name} 运行失败: {e}")
                    analyst_reports[analyst_name] = {
                        "report": f"分析失败: {str(e)}",
                        "confidence": 0.1,
                        "timestamp": datetime.now().isoformat()
                    }
        
        # 3. 计算自适应权重
        print("⚖️ 计算自适应权重...")
        
        # 基于市场状态调整权重
        for analyst_name in self.weight_manager.agents.keys():
            # 获取当前误差
            error = self.weight_manager.get_agent_error(analyst_name)
            
            # 基于市场状态和误差调整权重
            new_weight = self._calculate_adaptive_weight(
                analyst_name, 
                error, 
                regime_result["dominant_regime"],
                regime_result["confidence"]
            )
            
            # 更新权重
            self.weight_manager.update_weight(analyst_name, new_weight)
        
        # 4. 获取最终权重
        final_weights = self.weight_manager.get_normalized_weights()
        
        print("📈 最终权重分配:")
        for analyst, weight in final_weights.items():
            print(f"  {analyst}: {weight:.1%}")
        
        # 5. 综合结果
        return {
            "symbol": symbol,
            "market_regime": regime_result,
            "analyst_reports": analyst_reports if analyst_reports else None,
            "final_weights": final_weights,
            "recommendation": regime_result.get("recommendation", "无建议"),
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_adaptive_weight(self, analyst_name: str, error: float, 
                                 regime: str, regime_confidence: float) -> float:
        """计算自适应权重"""
        # 基本权重计算
        base_weight = 1.0 / (error + 0.01)
        
        # 根据市场状态调整
        regime_adjustment = self._get_regime_adjustment(analyst_name, regime)
        
        # 根据置信度调整
        confidence_factor = 0.5 + regime_confidence
        
        # 最终权重
        final_weight = base_weight * regime_adjustment * confidence_factor
        
        # 边界限制
        return max(0.1, min(final_weight, 3.0))
    
    def _get_regime_adjustment(self, analyst_name: str, regime: str) -> float:
        """获取市场状态调整因子"""
        # 简单调整规则
        adjustment_rules = {
            "macro_analyst": {
                "macro_event": 1.8,
                "trending_bull": 1.3,
                "trending_bear": 1.3,
                "crisis": 1.5,
                "default": 1.0
            },
            "news_analyst": {
                "news_driven": 1.8,
                "high_volatility": 1.4,
                "crisis": 1.6,
                "default": 1.0
            },
            "technical_analyst": {
                "trending_bull": 1.6,
                "trending_bear": 1.6,
                "breakout_up": 1.7,
                "breakout_down": 1.7,
                "ranging": 1.4,
                "default": 1.0
            },
            "quantitative_analyst": {
                "high_volatility": 1.6,
                "quant_shock": 1.8,
                "crisis": 1.5,
                "ranging": 1.3,
                "default": 1.0
            }
        }
        
        analyst_rules = adjustment_rules.get(analyst_name, {"default": 1.0})
        return analyst_rules.get(regime, analyst_rules["default"])
    
    def run_demo(self, symbols: List[str] = None):
        """运行演示"""
        if symbols is None:
            symbols = ["EUR/USD", "USD/JPY", "GBP/USD"]
        
        print("\n" + "="*60)
        print("🚀 完整集成系统演示")
        print("="*60)
        
        results = []
        
        for symbol in symbols:
            print(f"\n📊 分析: {symbol}")
            print("-"*40)
            
            try:
                result = self.execute_analysis(symbol)
                results.append(result)
                
                # 显示结果
                print(f"  市场状态: {result['market_regime']['dominant_regime']}")
                print(f"  置信度: {result['market_regime']['confidence']:.1%}")
                print(f"  建议: {result['recommendation']}")
                print(f"  数据源: {result['market_regime'].get('data_sources', {})}")
                
            except Exception as e:
                print(f"  ❌ 分析失败: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "="*60)
        print("✅ 演示完成!")
        print("="*60)
        
        return results


def main():
    """主函数"""
    try:
        # 创建集成系统
        system = FullIntegrationSystem()
        
        # 运行演示
        results = system.run_demo()
        
        # 显示汇总
        if results:
            print("\n📋 汇总结果:")
            for result in results:
                symbol = result['symbol']
                regime = result['market_regime']['dominant_regime']
                confidence = result['market_regime']['confidence']
                
                print(f"  {symbol}: {regime} ({confidence:.1%})")
        
        return system
        
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("启动完整集成系统...")
    system = main()
    
    if system:
        print("\n🎉 集成系统准备就绪!")
        print("您可以将此系统集成到您的交易流程中。")