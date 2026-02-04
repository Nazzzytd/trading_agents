"""
test_technical_indicators.py
测试技术指标工具
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置模拟模式
os.environ['TECHNICAL_SIMULATION_MODE'] = 'true'

def test_technical_indicators():
    """测试技术指标工具"""
    print("=" * 60)
    print("🧪 测试技术指标工具")
    print("=" * 60)
    
    # 1. 导入技术指标工具
    print("\n1. 导入技术指标工具...")
    try:
        # 假设你的技术指标工具文件名为 technical_indicators.py
        from technical_indicators import (
            get_technical_indicators_data,
            get_fibonacci_levels,
            get_indicators,
            get_technical_data
        )
        print("✅ 技术指标工具导入成功")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保 technical_indicators.py 在正确的位置")
        return
    
    # 2. 测试基础数据获取
    print("\n2. 测试基础数据获取...")
    test_symbol = "EUR/USD"
    test_date = datetime.now().strftime("%Y-%m-%d")  # 使用今天日期
    test_date = "2024-01-15"  # 或者使用固定日期
    
    print(f"测试参数: 符号={test_symbol}, 日期={test_date}, 回溯=30天")
    
    try:
        # 测试 get_technical_data
        result = get_technical_data(test_symbol, test_date, 30)
        if result["success"]:
            print(f"✅ 数据获取成功")
            print(f"   当前价格: {result['current_price']:.6f}")
            print(f"   指标数量: {len(result['latest_indicators'])}")
            print(f"   数据点数: {result['data_points']}")
            print(f"   涨跌幅: {result['price_change_pct']:+.2f}%")
            
            # 显示前几个指标
            print(f"   主要指标:")
            for i, (key, value) in enumerate(list(result['latest_indicators'].items())[:5]):
                print(f"     - {key}: {value:.6f}")
        else:
            print(f"❌ 数据获取失败: {result.get('error')}")
    except Exception as e:
        print(f"❌ 数据获取异常: {e}")
    
    # 3. 测试 LangChain 工具
    print("\n3. 测试 LangChain 工具...")
    
    # 测试 get_technical_indicators_data
    print("\n  3.1 测试 get_technical_indicators_data...")
    try:
        tech_result = get_technical_indicators_data.invoke({
            "symbol": test_symbol,
            "curr_date": test_date,
            "look_back_days": 30
        })
        print(f"   ✅ 工具调用成功")
        print(f"   输出长度: {len(tech_result)} 字符")
        print(f"   前200字符: {tech_result[:200]}...")
    except Exception as e:
        print(f"   ❌ 工具调用失败: {e}")
    
    # 测试 get_fibonacci_levels
    print("\n  3.2 测试 get_fibonacci_levels...")
    try:
        fib_result = get_fibonacci_levels.invoke({
            "symbol": test_symbol,
            "curr_date": test_date,
            "look_back_days": 30
        })
        print(f"   ✅ 工具调用成功")
        print(f"   输出长度: {len(fib_result)} 字符")
        print(f"   前150字符: {fib_result[:150]}...")
    except Exception as e:
        print(f"   ❌ 工具调用失败: {e}")
    
    # 测试 get_indicators
    print("\n  3.3 测试 get_indicators...")
    try:
        indicators_result = get_indicators.invoke({
            "symbol": test_symbol,
            "indicators": ["rsi", "macd", "sma_20"],
            "end_date": test_date,
            "look_back_days": 30
        })
        print(f"   ✅ 工具调用成功")
        print(f"   输出长度: {len(indicators_result)} 字符")
        print(f"   前150字符: {indicators_result[:150]}...")
    except Exception as e:
        print(f"   ❌ 工具调用失败: {e}")
    
    # 4. 测试工具列表和类型
    print("\n4. 检查工具属性...")
    tools = [
        ("技术指标数据", get_technical_indicators_data),
        ("斐波那契水平", get_fibonacci_levels),
        ("指标计算", get_indicators)
    ]
    
    for name, tool in tools:
        print(f"  {name}:")
        print(f"    - 类型: {type(tool).__name__}")
        print(f"    - 名称: {tool.name}")
        print(f"    - 描述: {tool.description[:80]}...")
        print(f"    - 可调用: {callable(tool)}")
    
    # 5. 测试创建分析师代理
    print("\n5. 测试创建分析师代理...")
    try:
        from langchain.agents import create_react_agent, AgentExecutor
        from langchain_openai import ChatOpenAI
        
        # 创建工具列表
        tool_list = [
            get_technical_indicators_data,
            get_fibonacci_levels,
            get_indicators
        ]
        
        print(f"  工具数量: {len(tool_list)}")
        
        # 创建LLM（需要设置OPENAI_API_KEY）
        try:
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
            print(f"  ✅ LLM创建成功")
            
            # 创建代理
            from langchain.agents import AgentExecutor, create_react_agent
            from langchain import hub
            
            prompt = hub.pull("hwchase17/react")
            agent = create_react_agent(llm, tool_list, prompt)
            agent_executor = AgentExecutor(agent=agent, tools=tool_list, verbose=True)
            
            print(f"  ✅ 代理创建成功")
            
        except Exception as e:
            print(f"  ⚠️ 代理创建失败（可能需要API key）: {e}")
            
    except Exception as e:
        print(f"  ❌ 分析师代理测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

def test_with_real_data():
    """测试真实数据模式（需要配置API）"""
    print("\n" + "=" * 60)
    print("🌐 测试真实数据模式")
    print("=" * 60)
    
    # 临时禁用模拟模式
    os.environ['TECHNICAL_SIMULATION_MODE'] = 'false'
    
    # 清理导入的模块
    if 'technical_indicators' in sys.modules:
        del sys.modules['technical_indicators']
    
    try:
        from technical_indicators import get_technical_data
        
        test_symbol = "EUR/USD"
        test_date = "2024-01-15"
        
        print(f"测试真实数据获取: {test_symbol} on {test_date}")
        
        result = get_technical_data(test_symbol, test_date, 30)
        
        if result["success"]:
            print(f"✅ 真实数据获取成功")
            print(f"   价格: {result['current_price']:.6f}")
            print(f"   模拟模式: {result.get('metadata', {}).get('simulated', True)}")
        else:
            print(f"❌ 真实数据获取失败: {result.get('error')}")
            print("   这可能是因为:")
            print("   1. 缺少API配置")
            print("   2. 路由函数不可用")
            print("   3. 数据源无响应")
    
    except Exception as e:
        print(f"❌ 真实数据测试异常: {e}")
    
    finally:
        # 恢复模拟模式
        os.environ['TECHNICAL_SIMULATION_MODE'] = 'true'

def test_tool_integration():
    """测试工具集成到现有系统"""
    print("\n" + "=" * 60)
    print("🔧 测试工具集成")
    print("=" * 60)
    
    try:
        # 导入现有的量化工具
        from test_tool_calls import get_quant_tools
        from technical_indicators import (
            get_technical_indicators_data,
            get_fibonacci_levels,
            get_indicators
        )
        
        print("1. 获取现有的量化工具...")
        existing_tools = get_quant_tools()
        print(f"   现有工具数量: {len(existing_tools)}")
        
        print("\n2. 添加技术指标工具...")
        technical_tools = [
            get_technical_indicators_data,
            get_fibonacci_levels,
            get_indicators
        ]
        
        all_tools = existing_tools + technical_tools
        print(f"   总工具数量: {len(all_tools)}")
        
        print("\n3. 工具分类:")
        print("   量化工具:")
        for i, tool in enumerate(existing_tools, 1):
            print(f"     {i}. {tool.name}")
        
        print("\n   技术指标工具:")
        for i, tool in enumerate(technical_tools, 1):
            print(f"     {i}. {tool.name}")
        
        print("\n✅ 工具集成测试完成")
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")

def main():
    """主测试函数"""
    print("技术指标工具测试套件")
    print("选择测试模式:")
    print("1. 基础功能测试")
    print("2. 真实数据测试")
    print("3. 集成测试")
    print("4. 全部测试")
    
    try:
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            test_technical_indicators()
        elif choice == "2":
            test_with_real_data()
        elif choice == "3":
            test_tool_integration()
        elif choice == "4":
            test_technical_indicators()
            test_with_real_data()
            test_tool_integration()
        else:
            print("无效选择，使用默认测试模式")
            test_technical_indicators()
    except:
        print("使用默认测试模式")
        test_technical_indicators()

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.WARNING,  # 减少日志输出
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    main()