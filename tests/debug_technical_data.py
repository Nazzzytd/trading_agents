# tests/debug_technical_data.py
import sys
import os
import logging

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("🔍 调试技术数据获取...")

def test_route_vendor_directly():
    """直接测试 route_to_vendor"""
    print("\n1. 直接测试 route_to_vendor...")
    try:
        from tradingagents.dataflows.interface import route_to_vendor
        
        result = route_to_vendor("get_forex_data", "EUR/USD", "2024-11-02", "2024-12-02")
        print(f"   ✅ 调用成功")
        print(f"   📋 结果类型: {type(result)}")
        
        if isinstance(result, str):
            print(f"   📄 字符串长度: {len(result)}")
            print(f"   📝 前500字符:")
            print("-" * 50)
            print(result[:500])
            print("-" * 50)
            
            # 尝试解析
            try:
                import json
                parsed = json.loads(result)
                print(f"   ✅ 可以解析为JSON")
                print(f"   📊 解析后类型: {type(parsed)}")
                if isinstance(parsed, dict):
                    print(f"   🔑 字典键: {list(parsed.keys())}")
            except:
                print(f"   ❌ 无法解析为JSON")
                
        elif isinstance(result, dict):
            print(f"   📊 字典键: {list(result.keys())}")
            if 'data' in result:
                data = result['data']
                if data and len(data) > 0:
                    print(f"   📈 数据点: {len(data)}")
                    print(f"   📋 第一个数据点: {data[0]}")
        
        return result
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_simplified_version():
    """测试简化版本"""
    print("\n2. 测试简化版本...")
    try:
        # 使用之前提到的简化版本
        from datetime import datetime, timedelta
        import pandas as pd
        import numpy as np
        
        symbol = "EUR/USD"
        curr_date = "2024-12-02"
        look_back_days = 30
        
        # 生成模拟数据
        dates = pd.date_range(end=curr_date, periods=look_back_days, freq='D')
        
        np.random.seed(42)
        close_prices = 1.1000 + np.cumsum(np.random.randn(look_back_days) * 0.001)
        
        data = {
            "success": True,
            "symbol": symbol,
            "current_price": float(close_prices[-1]),
            "data_points": look_back_days,
            "latest_indicators": {
                "RSI": 55.5,
                "MACD": 0.0015,
                "SMA_20": float(np.mean(close_prices[-20:]) if len(close_prices) >= 20 else np.mean(close_prices))
            }
        }
        
        print(f"   ✅ 模拟数据创建成功")
        print(f"   💰 价格: {data['current_price']}")
        return data
        
    except Exception as e:
        print(f"   ❌ 简化版本失败: {e}")
        return None

def test_get_technical_data():
    """测试原始函数"""
    print("\n3. 测试原始 get_technical_data 函数...")
    try:
        from tradingagents.agents.utils.technical_indicators_tools import get_technical_data
        
        result = get_technical_data(
            symbol="EUR/USD",
            curr_date="2024-12-02",
            look_back_days=30
        )
        
        print(f"   📊 成功状态: {result.get('success')}")
        
        if result.get('success'):
            print(f"   🎉 成功!")
            print(f"   💰 当前价格: {result.get('current_price')}")
            print(f"   📈 数据点数: {result.get('data_points')}")
        else:
            print(f"   ❌ 错误: {result.get('error')}")
            
            # 如果有调试信息
            if 'debug_info' in result:
                print(f"   🔍 调试信息: {result['debug_info']}")
        
        return result
        
    except Exception as e:
        print(f"   ❌ 函数调用失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主调试函数"""
    print("=" * 60)
    print("调试技术数据获取问题")
    print("=" * 60)
    
    # 测试1: 直接调用 route_to_vendor
    raw_result = test_route_vendor_directly()
    
    # 测试2: 简化版本
    simple_result = test_simplified_version()
    
    # 测试3: 原始函数
    original_result = test_get_technical_data()
    
    print("\n" + "=" * 60)
    print("调试总结")
    print("=" * 60)
    
    if original_result and original_result.get('success'):
        print("✅ 原始函数工作正常!")
    elif simple_result:
        print("⚠️  原始函数失败，但简化版本可用")
        print("💡 建议: 使用简化版本或修复数据解析")
    else:
        print("❌ 所有测试都失败")
        
    print("\n💡 建议下一步:")
    print("1. 检查 route_to_vendor 返回的数据格式")
    print("2. 确保数据包含正确的列名 (open, high, low, close)")
    print("3. 如果数据格式不匹配，可能需要更新数据解析逻辑")

if __name__ == "__main__":
    main()