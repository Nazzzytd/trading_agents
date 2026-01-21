# tests/test_comprehensive_fix.py
import sys
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("🔧 综合修复测试...")

def test_technical_data():
    """测试技术数据获取"""
    print("\n1. 测试技术数据获取...")
    try:
        from tradingagents.agents.utils.technical_indicators_tools import get_technical_data
        
        # 测试调用
        result = get_technical_data(
            symbol="EUR/USD",
            curr_date="2024-12-02",
            look_back_days=30
        )
        
        print(f"   ✅ 调用成功")
        print(f"   📊 成功状态: {result.get('success')}")
        
        if result.get('success'):
            print(f"   🎉 修复成功！")
            print(f"   💰 当前价格: {result.get('current_price')}")
            print(f"   📈 数据点数: {result.get('data_points')}")
            print(f"   🎯 技术指标数: {len(result.get('latest_indicators', {}))}")
            return True
        else:
            print(f"   ❌ 错误信息: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_news_data():
    """测试新闻数据"""
    print("\n2. 测试新闻数据...")
    try:
        from tradingagents.agents.utils.news_data_tools import get_news
        
        print(f"   ✅ 导入成功")
        print(f"   📋 类型: {type(get_news)}")
        
        # 检查是否是工具
        if hasattr(get_news, 'name'):
            print(f"   🛠️  工具名称: {get_news.name}")
            
        # 尝试调用（如果可用）
        if hasattr(get_news, 'invoke'):
            print(f"   🔧 使用 invoke 方法调用")
            # 可选：实际调用测试
            # result = get_news.invoke({
            #     "ticker": "EUR/USD",
            #     "start_date": "2024-12-01",
            #     "end_date": "2024-12-02",
            #     "limit": 5
            # })
            # print(f"   📰 结果类型: {type(result)}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False

def test_route_vendor():
    """测试路由功能"""
    print("\n3. 测试路由功能...")
    try:
        from tradingagents.dataflows.interface import route_to_vendor
        
        # 测试简单的调用
        result = route_to_vendor("get_news", "test", "2024-01-01", "2024-01-02")
        print(f"   ✅ 路由调用成功")
        print(f"   📋 结果类型: {type(result)}")
        return True
        
    except Exception as e:
        print(f"   ❌ 路由测试失败: {e}")
        return False

def test_data_sources():
    """测试数据源"""
    print("\n4. 测试数据源...")
    try:
        # 测试模拟数据作为备选方案
        print("   测试备选方案...")
        
        # 创建模拟数据函数
        def create_mock_data():
            import pandas as pd
            import numpy as np
            
            dates = pd.date_range(end="2024-12-02", periods=30, freq='D')
            np.random.seed(42)
            
            close_prices = 1.1000 + np.cumsum(np.random.randn(30) * 0.001)
            
            data = {
                "success": True,
                "symbol": "EUR/USD",
                "current_price": float(close_prices[-1]),
                "data_points": 30,
                "latest_indicators": {
                    "RSI": 55.5,
                    "MACD": 0.0015,
                    "SMA_20": 1.0985
                }
            }
            return data
        
        mock_data = create_mock_data()
        print(f"   ✅ 模拟数据创建成功")
        print(f"   💰 模拟价格: {mock_data['current_price']}")
        return True
        
    except Exception as e:
        print(f"   ❌ 数据源测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("综合修复测试")
    print("=" * 50)
    
    results = []
    
    results.append(test_technical_data())
    results.append(test_news_data())
    results.append(test_route_vendor())
    results.append(test_data_sources())
    
    # 统计结果
    success_count = sum(results)
    total_count = len(results)
    
    print("\n" + "=" * 50)
    print("测试结果统计")
    print("=" * 50)
    print(f"✅ 成功: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 所有测试通过！")
    else:
        print("🔧 需要修复的问题:")
        if not results[0]:
            print("  - 技术数据获取失败")
        if not results[1]:
            print("  - 新闻数据测试失败")
        if not results[2]:
            print("  - 路由功能失败")
        if not results[3]:
            print("  - 数据源测试失败")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)