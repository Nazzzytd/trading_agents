#!/usr/bin/env python3
"""
修复日期问题的 TwelveData 测试
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

def test_fixed_dates():
    """使用修复的日期进行测试"""
    print("🔧 使用修复的日期进行测试")
    print("=" * 40)
    
    from tradingagents.agents.utils.core_forex_tools import get_forex_data
    
    # 使用确定有数据的日期范围
    test_cases = [
        {
            "symbol": "EUR/USD",
            "start_date": "2024-01-01",
            "end_date": "2024-01-10"
        },
        {
            "symbol": "XAU/USD", 
            "start_date": "2024-02-01",
            "end_date": "2024-02-15"
        },
        {
            "symbol": "GBP/JPY",
            "start_date": "2024-03-01", 
            "end_date": "2024-03-10"
        }
    ]
    
    for case in test_cases:
        print(f"\n🔍 测试 {case['symbol']} ({case['start_date']} 到 {case['end_date']})")
        try:
            result = get_forex_data.invoke(case)
            
            if isinstance(result, dict) and result.get("success"):
                data_points = len(result.get("data", []))
                print(f"   ✅ 成功获取 {data_points} 个数据点")
                if data_points > 0:
                    first_point = result["data"][0]
                    last_point = result["data"][-1]
                    print(f"   时间范围: {first_point.get('datetime')} 到 {last_point.get('datetime')}")
            else:
                print(f"   ❌ 失败: {result}")
                
        except Exception as e:
            print(f"   💥 异常: {e}")

if __name__ == "__main__":
    test_fixed_dates()