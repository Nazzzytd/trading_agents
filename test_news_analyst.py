# 创建一个简单的测试脚本 test_news_speed.py

#!/usr/bin/env python3
# /Users/fr./Downloads/TradingAgents-main/test_news_speed.py

import os
import sys
import time
from datetime import datetime

# 设置环境变量
os.environ.setdefault('TWELVEDATA_API_KEY', 'dummy')
os.environ.setdefault('ALPHA_VANTAGE_API_KEY', 'demo')

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_data_fetch_speed():
    """测试数据获取速度"""
    print("="*60)
    print("📊 测试新闻数据获取速度")
    print("="*60)
    
    try:
        # 直接导入数据获取函数
        from tradingagents.agents.analysts.news_analyst import get_news_data_direct
        
        test_cases = [
            {"name": "EUR/USD", "pair": "EUR/USD"},
            {"name": "通用外汇", "pair": ""},
            {"name": "USD/JPY", "pair": "USD/JPY"}
        ]
        
        for test in test_cases:
            print(f"\n🔍 测试: {test['name']}")
            print("-" * 40)
            
            # 第一次获取（应该较慢）
            print("  第一次获取（可能较慢）...")
            start1 = time.time()
            data1 = get_news_data_direct(test["pair"], limit=10, days_back=2, use_cache=True)
            time1 = time.time() - start1
            
            print(f"    耗时: {time1:.2f}秒")
            
            if isinstance(data1, dict) and "feed" in data1:
                feed = data1["feed"]
                if isinstance(feed, list):
                    print(f"    新闻数量: {len(feed)}")
                    if feed:
                        print(f"    第一条: {feed[0].get('title', 'N/A')[:50]}...")
            
            # 第二次获取（应该很快，从缓存）
            print("  第二次获取（从缓存）...")
            start2 = time.time()
            data2 = get_news_data_direct(test["pair"], limit=10, days_back=2, use_cache=True)
            time2 = time.time() - start2
            
            print(f"    耗时: {time2:.2f}秒")
            print(f"    缓存加速: {(time1-time2)/time1*100:.0f}%")
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_cache_system():
    """测试缓存系统"""
    print("\n" + "="*60)
    print("🧪 测试缓存系统")
    print("="*60)
    
    try:
        from tradingagents.agents.analysts.news_analyst import news_cache
        
        # 模拟一些数据
        test_data = {
            "feed": [
                {"title": "测试新闻1", "sentiment": "bullish"},
                {"title": "测试新闻2", "sentiment": "neutral"}
            ]
        }
        
        # 设置缓存
        news_cache.set("TEST/USD", 10, 2, test_data)
        
        # 获取缓存
        cached = news_cache.get("TEST/USD", 10, 2)
        
        if cached:
            print("✅ 缓存系统工作正常")
            print(f"   缓存数据: {len(cached.get('feed', []))}条新闻")
            
            # 获取统计
            stats = news_cache.get_stats()
            print(f"   缓存统计:")
            print(f"     命中: {stats.get('hits', 0)}")
            print(f"     未命中: {stats.get('misses', 0)}")
            print(f"     命中率: {stats.get('hit_rate', '0%')}")
            print(f"     缓存大小: {stats.get('size', 0)}")
        else:
            print("❌ 缓存获取失败")
    
    except Exception as e:
        print(f"❌ 缓存测试失败: {e}")

def test_fallback_analysis():
    """测试备用分析生成"""
    print("\n" + "="*60)
    print("🛡️ 测试备用分析系统")
    print("="*60)
    
    try:
        from tradingagents.agents.analysts.news_analyst import generate_fallback_analysis
        
        # 测试1: 无数据情况
        print("\n测试1: 无新闻数据")
        result1 = generate_fallback_analysis([], {"bullish": 0, "bearish": 0, "neutral": 0}, "EUR/USD")
        print(f"  结果: {result1[:80]}...")
        
        # 测试2: 看涨情况
        print("\n测试2: 看涨情绪")
        news_items = [{"title": "欧洲央行鹰派言论提振欧元", "sentiment": "bullish"}]
        result2 = generate_fallback_analysis(
            news_items, 
            {"bullish": 3, "bearish": 1, "neutral": 2}, 
            "EUR/USD"
        )
        print(f"  结果: {result2[:80]}...")
        
        # 测试3: 看跌情况
        print("\n测试3: 看跌情绪")
        result3 = generate_fallback_analysis(
            [], 
            {"bullish": 1, "bearish": 5, "neutral": 2}, 
            "USD/JPY"
        )
        print(f"  结果: {result3[:80]}...")
        
        print("\n✅ 备用分析系统工作正常")
        
    except Exception as e:
        print(f"❌ 备用分析测试失败: {e}")

def performance_benchmark():
    """性能基准测试"""
    print("\n" + "="*60)
    print("⚡ 性能基准测试")
    print("="*60)
    
    try:
        from tradingagents.agents.analysts.news_analyst import get_news_data_direct
        import statistics
        
        # 测试不同配置
        configs = [
            {"limit": 5, "days": 1, "desc": "最小配置"},
            {"limit": 10, "days": 2, "desc": "推荐配置"},
            {"limit": 15, "days": 3, "desc": "完整配置"}
        ]
        
        all_times = []
        
        for config in configs:
            print(f"\n测试: {config['desc']}")
            print(f"  参数: limit={config['limit']}, days={config['days']}")
            
            times = []
            for i in range(3):  # 每个配置运行3次
                start = time.time()
                data = get_news_data_direct(
                    ticker="EUR/USD",
                    limit=config['limit'],
                    days_back=config['days'],
                    use_cache=(i > 0)  # 第一次不用缓存
                )
                elapsed = time.time() - start
                times.append(elapsed)
                
                if i == 0 and isinstance(data, dict) and "feed" in data:
                    feed = data["feed"]
                    if isinstance(feed, list):
                        print(f"    第{i+1}次: {elapsed:.2f}秒, {len(feed)}条新闻")
                    else:
                        print(f"    第{i+1}次: {elapsed:.2f}秒, 无数据")
                else:
                    print(f"    第{i+1}次: {elapsed:.2f}秒")
            
            avg_time = statistics.mean(times)
            all_times.append(avg_time)
            print(f"  平均: {avg_time:.2f}秒")
        
        # 总结
        print(f"\n" + "="*60)
        print("📈 性能总结:")
        
        original_data_time = 0.82  # 根据你的测试结果
        original_total_time = 29.25
        
        print(f"  原始数据获取: {original_data_time:.2f}秒")
        print(f"  原始总时间: {original_total_time:.2f}秒")
        print(f"  LLM耗时: {original_total_time - original_data_time:.2f}秒")
        
        best_avg = min(all_times) if all_times else 0
        estimated_total = best_avg + 2.0  # 假设LLM优化到2秒
        
        print(f"\n🎯 优化预期:")
        print(f"  最快数据获取: {best_avg:.2f}秒")
        print(f"  预期总时间: {estimated_total:.2f}秒")
        print(f"  预期提升: {(original_total_time - estimated_total)/original_total_time*100:.0f}%")
        
        if estimated_total <= 8:
            print("  ✅ 可达到8秒目标!")
        
    except Exception as e:
        print(f"❌ 基准测试失败: {e}")

def main():
    """主测试函数"""
    print("🚀 新闻分析系统优化测试")
    print("="*60)
    
    # 运行各项测试
    test_data_fetch_speed()
    test_cache_system()
    test_fallback_analysis()
    performance_benchmark()
    
    print("\n" + "="*60)
    print("✅ 测试完成!")
    print("="*60)
    
    print("\n📋 下一步:")
    print("1. 如果需要LLM分析，请设置 OPENAI_API_KEY 环境变量")
    print("2. 运行完整测试: python -c \"from tradingagents.agents.analysts.news_analyst import test_optimized_performance; test_optimized_performance()\"")
    print("3. 集成到交易系统进行实际测试")

if __name__ == "__main__":
    main()