
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

def working_example():
    """可工作的示例"""
    
    print("🚀 可工作的集成示例")
    print("=" * 60)
    
    try:
        # 1. 技术数据
        from tradingagents.agents.utils.technical_indicators_tools import get_technical_data
        
        print("📈 获取技术数据...")
        tech_data = get_technical_data(
            symbol="EUR/USD",
            curr_date="2024-12-02",
            look_back_days=30
        )
        
        if tech_data and isinstance(tech_data, dict) and tech_data.get("success"):
            print(f"   ✅ 技术数据获取成功")
            data = tech_data.get("data", {})
            if isinstance(data, list):
                print(f"   📊 数据条数: {len(data)}")
            elif isinstance(data, dict):
                print(f"   📊 数据字段: {list(data.keys())}")
        else:
            print(f"   ❌ 技术数据获取失败")
    
    except Exception as e:
        print(f"   ⚠️  技术数据错误: {e}")
    
    try:
        # 2. 新闻数据
        from tradingagents.dataflows.interface import route_to_vendor
        
        print("📰 获取新闻数据...")
        news_data = route_to_vendor(
            "get_news",
            ticker="EUR/USD",
            limit=5,
            start_date="2024-11-01",
            end_date="2024-11-30"
        )
        
        if news_data:
            print(f"   ✅ 新闻数据获取成功")
            if isinstance(news_data, dict):
                feed = news_data.get("feed", [])
                print(f"   📊 新闻条数: {len(feed)}")
        else:
            print(f"   ❌ 新闻数据获取失败")
    
    except Exception as e:
        print(f"   ⚠️  新闻数据错误: {e}")
    
    try:
        # 3. 权重管理器
        from tradingagents.adaptive_system.weight_manager import AdaptiveWeightManager
        from tradingagents.adaptive_system.config import AdaptiveConfig
        
        print("⚖️  设置权重管理器...")
        config = AdaptiveConfig()
        weight_manager = AdaptiveWeightManager(config)
        
        # 注册分析师
        analysts = [
            ("macro_analyst", "strategic"),
            ("news_analyst", "operational"),
            ("technical_analyst", "tactical")
        ]
        
        for name, layer in analysts:
            weight_manager.register_agent(name, layer)
            weight_manager.update_weight(name, 1.0)  # 初始权重
        
        print(f"   ✅ 注册了 {len(analysts)} 个分析师")
        
        # 获取权重
        weights = weight_manager.get_normalized_weights()
        print(f"   📊 初始权重分配:")
        for analyst, weight in weights.items():
            print(f"     {analyst}: {weight:.1%}")
    
    except Exception as e:
        print(f"   ⚠️  权重管理器错误: {e}")
    
    print("
" + "=" * 60)
    print("✅ 示例运行完成!")
    print("=" * 60)

if __name__ == "__main__":
    working_example()
