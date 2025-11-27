#!/usr/bin/env python3
"""
测试 TwelveData 外汇数据配置
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

def test_get_forex_data():
    """测试 get_forex_data 功能"""
    print("🚀 开始 get_forex_data 功能测试")
    print("=" * 50)
    
    # 检查 API Key
    api_key = os.getenv("TWELVEDATA_API_KEY")
    if api_key:
        print(f"🔑 TwelveData API Key: {api_key[:10]}...")
    else:
        print("❌ TWELVEDATA_API_KEY 环境变量未设置")
        return False
    
    print("🧪 测试 get_forex_data 功能")
    print("=" * 50)
    
    # 1. 导入工具
    print("1. 📥 导入工具...")
    try:
        from tradingagents.agents.utils.core_forex_tools import get_forex_data
        print(f"   ✅ 工具导入成功: {get_forex_data.name}")
        print(f"   描述: {get_forex_data.description}")
        print(f"   参数: {get_forex_data.args}")
    except ImportError as e:
        print(f"   ❌ 工具导入失败: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 导入过程中出错: {e}")
        return False
    
    # 2. 测试工具调用
    print("\n2. 📞 测试工具调用...")
    test_symbols = ["EUR/USD", "XAU/USD", "GBP/JPY"]
    
    # 设置测试日期（使用最近日期确保有数据）
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    
    for symbol in test_symbols:
        print(f"\n🔍 测试 {symbol}...")
        try:
            # 使用正确的调用方式
            result = get_forex_data.invoke({
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date
            })
            
            if result and "❌" not in str(result):
                print(f"   ✅ 工具调用成功")
                print(f"   返回数据长度: {len(str(result))} 字符")
                # 显示部分结果预览
                result_preview = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                print(f"   结果预览: {result_preview}")
            else:
                print(f"   ⚠️  工具返回异常: {result}")
                
        except Exception as e:
            print(f"   ❌ 工具调用失败: {e}")
            # 继续测试其他符号
            continue
    
    # 3. 测试详细数据流
    print("\n3. 🔄 测试详细数据流")
    print("=" * 50)
    print("🔍 详细测试 EUR/USD...")
    try:
        # 测试更长的数据周期
        detailed_result = get_forex_data.invoke({
            "symbol": "EUR/USD",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        })
        
        if detailed_result and "❌" not in str(detailed_result):
            print("   ✅ 详细数据流测试成功")
            # 分析返回的数据结构
            if "datetime" in str(detailed_result):
                print("   📊 包含时间序列数据")
            if "open" in str(detailed_result) and "close" in str(detailed_result):
                print("   💰 包含OHLC价格数据")
        else:
            print(f"   ❌ 详细数据流测试失败: {detailed_result}")
            
    except Exception as e:
        print(f"   ❌ 详细测试失败: {e}")
    
    # 4. 测试配置
    print("\n4. ⚙️ 测试配置")
    print("=" * 50)
    try:
        from tradingagents.dataflows.config import get_config
        config = get_config()
        
        data_vendors = config.get("data_vendors", {})
        forex_vendor = data_vendors.get("core_forex_apis", "未知")
        
        print(f"✅ 配置加载成功")
        print(f"   外汇数据供应商: {forex_vendor}")
        
        # 显示可用供应商
        from tradingagents.dataflows.interface import VENDOR_METHODS
        if "get_forex_data" in VENDOR_METHODS:
            available_vendors = list(VENDOR_METHODS["get_forex_data"].keys())
            print(f"   get_forex_data 可用供应商: {available_vendors}")
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("✅ 测试完成！")
    print("\n📋 下一步:")
    print("1. 如果测试成功，可以开始使用外汇分析系统")
    print("2. 如果仍有问题，请检查 TwelveData API 配置和数据权限")
    
    return True

if __name__ == "__main__":
    success = test_get_forex_data()
    sys.exit(0 if success else 1)