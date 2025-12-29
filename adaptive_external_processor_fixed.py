# adaptive_external_processor_fixed.py
"""
修复版外部自适应处理器
"""
import sys
import os
import json
from typing import Dict, Any, List
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.adaptive_system import AdaptiveSystem


class ExternalAdaptiveProcessor:
    """外部自适应处理器 - 修复版"""
    
    def __init__(self, config_file="adaptive_config.json"):
        self.adaptive = AdaptiveSystem()
        self.config_file = config_file
        self.prediction_history = []
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                for agent_name, agent_type in config.get("agents", []):
                    self.adaptive.register_agent(agent_name, agent_type)
    
    def process_from_file(self, predictions_file: str) -> Dict[str, Any]:
        """从文件读取预测并处理"""
        if not os.path.exists(predictions_file):
            return {"error": f"File not found: {predictions_file}"}
        
        with open(predictions_file, 'r') as f:
            data = json.load(f)
        
        return self.process_predictions(data.get("predictions", {}), 
                                       data.get("context", "file_input"))
    
    def process_predictions(self, predictions: Dict[str, float], 
                           context: str = "") -> Dict[str, Any]:
        """处理预测数据 - 修复版"""
        print(f"\n🔧 处理预测 - {context}")
        print("-" * 40)
        
        # 修复：正确检查智能体是否已注册
        registered_agents = list(self.adaptive.weight_manager.agents.keys())
        
        for agent_name in predictions.keys():
            if agent_name not in registered_agents:
                agent_type = self._infer_agent_type(agent_name)
                self.adaptive.register_agent(agent_name, agent_type)
                print(f"   ⚙️  自动注册: {agent_name} ({agent_type})")
        
        # 记录预测
        for agent_name, prediction in predictions.items():
            self.adaptive.record_prediction(agent_name, prediction)
        
        # 获取加权决策
        result = self.adaptive.get_weighted_decision(predictions)
        
        # 记录历史
        self.prediction_history.append({
            "timestamp": self._get_timestamp(),
            "context": context,
            "predictions": predictions,
            "result": result,
        })
        
        # 保存到文件
        self._save_result_to_file(result, context)
        
        return result
    
    def _infer_agent_type(self, agent_name: str) -> str:
        """根据名称推断智能体类型"""
        name_lower = agent_name.lower()
        
        if any(word in name_lower for word in ["analyst", "分析"]):
            return "analyst"
        elif any(word in name_lower for word in ["researcher", "research", "研究员"]):
            return "researcher"
        elif any(word in name_lower for word in ["trader", "交易"]):
            return "trader"
        elif any(word in name_lower for word in ["debator", "debate", "辩论"]):
            return "debator"
        elif any(word in name_lower for word in ["manager", "manage", "经理"]):
            return "manager"
        else:
            return "analyst"
    
    def _save_result_to_file(self, result: Dict[str, Any], context: str):
        """保存结果到文件"""
        output = {
            "timestamp": self._get_timestamp(),
            "context": context,
            "weighted_decision": result["weighted_decision"],
            "weights": result["weights"],
            "raw_predictions": result.get("raw_predictions", {}),
        }
        
        output_file = f"adaptive_output_{context.replace(' ', '_')}.json"
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"   💾 结果已保存到: {output_file}")
        return output_file
    
    def _get_timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def update_with_market_result(self, actual_change: float, 
                                 update_file: str = None):
        """用实际市场结果更新权重"""
        if update_file and os.path.exists(update_file):
            with open(update_file, 'r') as f:
                update_data = json.load(f)
                agents_to_update = update_data.get("agents", [])
                actual_change = update_data.get("actual_change", actual_change)
        else:
            agents_to_update = list(self.adaptive.weight_manager.agents.keys())
        
        print(f"\n📈 权重更新 - 市场变动: {actual_change:.2%}")
        
        for agent_name in agents_to_update:
            self.adaptive.update_with_result(agent_name, actual_change)
        
        print(f"   ✅ 已更新 {len(agents_to_update)} 个智能体")
    
    def create_config_for_graph(self):
        """为Graph创建配置文件"""
        config = {
            "adaptive_system": {
                "enabled": True,
                "integration_mode": "external_processor",
                "output_files": {
                    "predictions": "graph_predictions.json",
                    "results": "adaptive_decision.json",
                    "updates": "market_updates.json"
                }
            },
            "agents": [
                ["Market Analyst", "analyst"],
                ["News Analyst", "analyst"],
                ["Technical Analyst", "analyst"],
                ["Bull Researcher", "researcher"],
                ["Bear Researcher", "researcher"],
                ["Trader", "trader"],
            ]
        }
        
        with open("graph_adaptive_config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Graph配置文件已创建: graph_adaptive_config.json")


def demonstrate_external_processing():
    """演示外部处理模式 - 简化版"""
    processor = ExternalAdaptiveProcessor()
    
    print("🚀 外部自适应处理器演示 (修复版)")
    print("=" * 50)
    
    # 1. 创建配置
    processor.create_config_for_graph()
    
    # 2. 模拟Graph预测数据
    graph_predictions = {
        "predictions": {
            "Market Analyst": 0.65,
            "News Analyst": -0.15,
            "Technical Analyst": 0.78,
            "Bull Researcher": 0.92,
            "Bear Researcher": -0.42,
            "Trader": 0.35,
        },
        "context": "graph_decision_cycle_1"
    }
    
    with open("graph_predictions.json", 'w') as f:
        json.dump(graph_predictions, f, indent=2)
    
    print("\n📁 Graph预测已保存到: graph_predictions.json")
    
    # 3. 处理预测
    print("\n🔄 处理Graph预测数据...")
    result = processor.process_from_file("graph_predictions.json")
    
    print(f"\n🎯 自适应决策结果:")
    print(f"   加权信号: {result['weighted_decision']:.4f}")
    
    # 显示权重
    print("   智能体权重:")
    for agent, weight in result['weights'].items():
        print(f"     {agent}: {weight:.3f}")
    
    # 4. 模拟更新
    print("\n📈 模拟市场结果更新...")
    processor.update_with_market_result(0.018)
    
    print("\n✅ 外部处理演示完成!")
    
    # 显示集成说明
    print("\n" + "="*50)
    print("📋 集成到您的系统:")
    print("="*50)
    print("""
步骤1: 在Graph决策点保存预测到JSON文件:
    ```python
    import json
    predictions = {
        "Market Analyst": market_signal,
        "News Analyst": news_signal,
        # ... 其他智能体
    }
    
    with open("current_predictions.json", 'w') as f:
        json.dump({
            "predictions": predictions,
            "context": "实时决策"
        }, f)
    ```

步骤2: 运行自适应处理:
    ```bash
    python adaptive_processor.py --input current_predictions.json
    ```

步骤3: 读取自适应结果:
    ```python
    import json
    with open("adaptive_output_实时决策.json", 'r') as f:
        adaptive_result = json.load(f)
    
    final_decision = adaptive_result["weighted_decision"]
    ```

步骤4: 更新权重（交易后）:
    ```python
    # 保存市场结果
    with open("market_update.json", 'w') as f:
        json.dump({
            "actual_change": actual_price_change,
            "agents": list(predictions.keys())
        }, f)
    
    # 运行更新
    # python adaptive_processor.py --update market_update.json
    ```
    """)


# 简易命令行接口
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="外部自适应处理器")
    parser.add_argument("--input", type=str, help="输入预测文件")
    parser.add_argument("--update", type=str, help="市场更新文件")
    parser.add_argument("--demo", action="store_true", help="运行演示")
    
    args = parser.parse_args()
    
    processor = ExternalAdaptiveProcessor()
    
    if args.demo:
        demonstrate_external_processing()
    elif args.input:
        result = processor.process_from_file(args.input)
        print(json.dumps(result, indent=2))
    elif args.update:
        with open(args.update, 'r') as f:
            data = json.load(f)
            processor.update_with_market_result(
                data.get("actual_change", 0),
                args.update
            )
    else:
        print("请提供参数: --input, --update, 或 --demo")


if __name__ == "__main__":
    main()