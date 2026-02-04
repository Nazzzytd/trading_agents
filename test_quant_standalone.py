"""
独立测试量化工具 - 不依赖其他模块
"""
import sys
import os

# 手动添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 先导入必要的模块
from langchain_core.tools import tool
import json

# 定义独立的测试工具
@tool
def test_get_risk_metrics_data(symbol: str, periods: int = 252, timeframe: str = "1day") -> str:
    """
    测试风险指标工具
    
    参数:
        symbol: 货币对符号
        periods: 数据周期数
        timeframe: 时间周期
    
    返回:
        JSON格式的数据
    """
    return json.dumps({
        "success": True,
        "test": "standalone",
        "symbol": symbol,
        "periods": periods,
        "timeframe": timeframe
    }, ensure_ascii=False)

@tool
def test_simple_forex_data(symbol: str, what: str, periods: int = 100) -> str:
    """
    测试简化数据工具
    
    参数:
        symbol: 货币对符号
        what: 数据类型
        periods: 数据周期数
    
    返回:
        JSON格式的数据
    """
    return json.dumps({
        "success": True,
        "test": "standalone",
        "symbol": symbol,
        "what": what,
        "periods": periods
    }, ensure_ascii=False)

print("=== 独立测试 ===")
print(f"工具1类型: {type(test_get_risk_metrics_data).__name__}")
print(f"工具2类型: {type(test_simple_forex_data).__name__}")

# 测试调用
try:
    result = test_get_risk_metrics_data.invoke({
        "symbol": "EUR/USD",
        "periods": 252,
        "timeframe": "1day"
    })
    print(f"\n✅ 调用成功: {result}")
except Exception as e:
    print(f"\n❌ 调用失败: {e}")

print("\n✅ 独立测试完成")
