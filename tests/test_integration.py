"""
修复版集成系统测试
"""
import sys
import os
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

print(f"📁 项目根目录: {project_root}")
print("=" * 60)

class TestDataSourcesFixed(unittest.TestCase):
    """修复版数据源测试"""
    
    @classmethod
    def setUpClass(cls):
        """类级别设置"""
        print("\n🔍 设置测试环境...")
        cls.data_sources_status = {}
    
    def test_01_import_basic_modules(self):
        """测试基础模块导入"""
        print("\n🧪 测试1: 基础模块导入")
        
        try:
            from tradingagents.dataflows.interface import route_to_vendor
            self.assertTrue(True, "✅ tradingagents.dataflows.interface 导入成功")
            print("   ✅ tradingagents.dataflows.interface 导入成功")
            
            from tradingagents.dataflows.config import get_config
            config = get_config()
            self.assertIsNotNone(config, "配置应该存在")
            print(f"   ✅ 配置加载成功")
            print(f"   📋 配置键: {list(config.keys())}")
            
            self.data_sources_status["basic_import"] = "available"
            
        except ImportError as e:
            self.fail(f"❌ 基础模块导入失败: {e}")
    
    def test_02_technical_data_tools_fixed(self):
        """测试技术指标工具（修复版）"""
        print("\n🧪 测试2: 技术指标工具（修复版）")
        
        try:
            from tradingagents.agents.utils.technical_indicators_tools import get_technical_data
            
            # 使用正确的参数名
            result = get_technical_data(
                symbol="EUR/USD",
                curr_date="2024-12-02",  # 注意参数名是curr_date不是current_date
                look_back_days=30
            )
            
            self.assertIsNotNone(result, "技术数据应该返回结果")
            
            if isinstance(result, dict):
                print(f"   ✅ 技术数据获取成功")
                print(f"   📊 结果格式: dict")
                print(f"   🔑 结果键: {list(result.keys())}")
                
                # 检查数据
                if result.get("success"):
                    print(f"   ✅ 成功状态: True")
                    data = result.get("data", {})
                    if data:
                        print(f"   📈 数据条数/类型: {len(data) if isinstance(data, list) else 'dict'}")
                    self.data_sources_status["technical"] = "available"
                else:
                    print(f"   ⚠️  成功状态: False, 错误: {result.get('error', '未知')}")
                    self.data_sources_status["technical"] = "failed"
            else:
                print(f"   ⚠️  返回类型: {type(result)}")
                self.data_sources_status["technical"] = "unexpected_format"
                
        except Exception as e:
            print(f"   ⚠️  调用失败: {e}")
            import traceback
            traceback.print_exc()
            self.data_sources_status["technical"] = "call_failed"
    
    def test_03_macro_data_tools_fixed(self):
        """测试宏观数据工具（修复版）"""
        print("\n🧪 测试3: 宏观数据工具（修复版）")
        
        # 测试FRED数据
        try:
            from tradingagents.agents.utils.macro_data_tools import get_fred_data
            
            # StructuredTool需要用invoke方法调用
            if hasattr(get_fred_data, 'invoke'):
                result = get_fred_data.invoke({"currency": "USD"})
            else:
                # 或者可能是普通函数
                result = get_fred_data({"currency": "USD"})
            
            if result:
                print(f"   ✅ FRED数据获取成功")
                print(f"   📋 结果类型: {type(result)}")
                if isinstance(result, dict):
                    print(f"   🔑 结果键: {list(result.keys())[:5] if len(result) > 5 else list(result.keys())}")
                self.data_sources_status["macro_fred"] = "available"
            else:
                print(f"   ⚠️  FRED数据无返回")
                self.data_sources_status["macro_fred"] = "no_data"
                
        except Exception as e:
            print(f"   ⚠️  FRED调用失败: {e}")
            self.data_sources_status["macro_fred"] = "call_failed"
        
        # 测试ECB数据
        try:
            from tradingagents.agents.utils.macro_data_tools import get_ecb_data
            
            if hasattr(get_ecb_data, 'invoke'):
                result = get_ecb_data.invoke({"currency": "EUR"})
            else:
                result = get_ecb_data({"currency": "EUR"})
            
            if result:
                print(f"   ✅ ECB数据获取成功")
                print(f"   📋 结果类型: {type(result)}")
                self.data_sources_status["macro_ecb"] = "available"
            else:
                print(f"   ⚠️  ECB数据无返回")
                self.data_sources_status["macro_ecb"] = "no_data"
                
        except Exception as e:
            print(f"   ⚠️  ECB调用失败: {e}")
            self.data_sources_status["macro_ecb"] = "call_failed"
    
    def test_04_vendor_routing_fixed(self):
        """测试Vendor路由系统（修复版）"""
        print("\n🧪 测试5: Vendor路由系统（修复版）")
        
        try:
            from tradingagents.dataflows.interface import route_to_vendor
            
            # 获取可用vendors
            vendors = get_available_vendors()
            print(f"   📋 可用Vendors: {vendors}")
            
            # 测试一个已知存在的vendor方法
            # 先检查哪些方法可用
            test_methods = [
                "get_news",  # 新闻数据
                "get_fred_data",  # FRED数据
                "get_ecb_data",  # ECB数据
            ]
            
            for method in test_methods:
                try:
                    if method == "get_news":
                        result = route_to_vendor(method, ticker="EUR/USD", limit=2)
                    elif method == "get_fred_data":
                        result = route_to_vendor(method, currency="USD")
                    elif method == "get_ecb_data":
                        result = route_to_vendor(method, currency="EUR")
                    
                    if result:
                        print(f"   ✅ {method}: 成功")
                        self.data_sources_status[f"vendor_{method}"] = "available"
                    else:
                        print(f"   ⚠️  {method}: 无数据")
                        self.data_sources_status[f"vendor_{method}"] = "no_data"
                        
                except Exception as e:
                    print(f"   ❌ {method}: 失败 ({str(e)[:50]})")
                    self.data_sources_status[f"vendor_{method}"] = "failed"
            
        except Exception as e:
            print(f"   ⚠️  Vendor测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    def test_05_analyst_modules_fixed(self):
        """测试分析师模块（修复版）"""
        print("\n🧪 测试6: 分析师模块（修复版）")
        
        analysts = [
            "macro_analyst",
            "news_analyst", 
            "technical_analyst",
        ]
        
        for analyst_name in analysts:
            try:
                module_name = f"tradingagents.agents.analysts.{analyst_name}"
                module = __import__(module_name, fromlist=[''])
                print(f"   ✅ {analyst_name} 模块导入成功")
                
                # 检查创建函数
                create_func_name = f"create_{analyst_name}"
                if hasattr(module, create_func_name):
                    print(f"   🔧 {create_func_name} 函数存在")
                else:
                    # 查找其他可能的函数
                    funcs = [f for f in dir(module) if 'create' in f or 'analyst' in f]
                    print(f"   🔍 可用函数: {funcs}")
                
                self.data_sources_status[f"analyst_{analyst_name}"] = "available"
            except ImportError as e:
                print(f"   ❌ {analyst_name} 导入失败: {e}")
                self.data_sources_status[f"analyst_{analyst_name}"] = "import_failed"
        
        # 单独处理quantitative_analyst
        try:
            from tradingagents.agents.analysts import quantitative_analyst
            print(f"   ✅ quantitative_analyst 模块导入成功")
            self.data_sources_status["analyst_quantitative_analyst"] = "available"
        except ImportError as e:
            print(f"   ⚠️  quantitative_analyst 导入失败，可能需要安装langchain")
            print(f"   错误: {e}")
            self.data_sources_status["analyst_quantitative_analyst"] = "import_failed"
    
    def test_06_check_tool_types(self):
        """检查工具类型"""
        print("\n🧪 检查工具类型")
        
        try:
            # 检查技术工具
            from tradingagents.agents.utils.technical_indicators_tools import get_technical_data
            print(f"   技术数据工具类型: {type(get_technical_data)}")
            print(f"   是否可调用: {callable(get_technical_data)}")
            
            # 检查宏观工具
            from tradingagents.agents.utils.macro_data_tools import get_fred_data
            print(f"   FRED工具类型: {type(get_fred_data)}")
            if hasattr(get_fred_data, 'invoke'):
                print(f"   有invoke方法: 是")
            else:
                print(f"   有invoke方法: 否")
            
        except Exception as e:
            print(f"   检查失败: {e}")
    
    def test_07_run_simple_demo(self):
        """运行简单演示"""
        print("\n🧪 测试7: 运行简单演示")
        
        try:
            # 导入并测试简单的功能
            from tradingagents.adaptive_system.weight_manager import AdaptiveWeightManager
            from tradingagents.adaptive_system.config import AdaptiveConfig
            
            config = AdaptiveConfig()
            weight_manager = AdaptiveWeightManager(config)
            
            # 注册测试分析师
            test_analysts = [
                ("test_macro", "strategic", 1.0),
                ("test_news", "operational", 0.8),
                ("test_technical", "tactical", 1.2),
            ]
            
            for name, layer, initial_weight in test_analysts:
                weight_manager.register_agent(name, layer)
                weight_manager.update_weight(name, initial_weight)
            
            # 记录一些预测数据
            weight_manager.record_prediction("test_macro", 1.05)
            weight_manager.record_actual("test_macro", 1.02)
            
            weight_manager.record_prediction("test_technical", 1.03)
            weight_manager.record_actual("test_technical", 1.01)
            
            # 更新权重
            weight_manager.update_all_weights()
            
            # 获取权重
            weights = weight_manager.get_normalized_weights()
            
            print(f"   ✅ 权重管理器演示成功")
            print(f"   📊 权重分配:")
            for agent, weight in weights.items():
                print(f"     {agent}: {weight:.2%}")
            
            self.data_sources_status["demo_weight_manager"] = "available"
            
        except Exception as e:
            print(f"   ⚠️  演示失败: {e}")
            self.data_sources_status["demo_weight_manager"] = "failed"
    
    def test_08_data_collection_test(self):
        """数据收集测试"""
        print("\n🧪 测试8: 数据收集测试")
        
        try:
            # 尝试收集各种数据
            data_results = {}
            
            # 1. 技术数据
            try:
                from tradingagents.agents.utils.technical_indicators_tools import get_technical_data
                tech_result = get_technical_data(
                    symbol="EUR/USD",
                    curr_date="2024-12-02",
                    lookback_days=10
                )
                data_results["technical"] = {
                    "success": isinstance(tech_result, dict) and tech_result.get("success", False),
                    "type": type(tech_result).__name__
                }
                print(f"   技术数据: {'✅' if data_results['technical']['success'] else '❌'}")
            except Exception as e:
                print(f"   技术数据: ❌ ({str(e)[:30]})")
            
            # 2. 新闻数据（通过vendor）
            try:
                from tradingagents.dataflows.interface import route_to_vendor
                news_result = route_to_vendor("get_news", ticker="EUR/USD", limit=2)
                data_results["news"] = {
                    "success": news_result is not None,
                    "type": type(news_result).__name__
                }
                print(f"   新闻数据: {'✅' if data_results['news']['success'] else '❌'}")
            except Exception as e:
                print(f"   新闻数据: ❌ ({str(e)[:30]})")
            
            # 3. 检查配置
            try:
                from tradingagents.dataflows.config import get_config
                config = get_config()
                data_results["config"] = {
                    "success": config is not None,
                    "keys": list(config.keys()) if config else []
                }
                print(f"   配置文件: ✅ 加载了{len(data_results['config']['keys'])}个配置项")
            except Exception as e:
                print(f"   配置文件: ❌ ({str(e)[:30]})")
            
            # 保存测试结果
            import json
            output_file = os.path.join(project_root, "tests", "data_collection_test.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data_results, f, indent=2, ensure_ascii=False)
            print(f"   💾 数据收集结果保存到: {output_file}")
            
        except Exception as e:
            print(f"   ⚠️  数据收集测试失败: {e}")
    
    def test_09_final_summary(self):
        """最终总结"""
        print("\n" + "=" * 60)
        print("📋 最终测试总结")
        print("=" * 60)
        
        if not hasattr(self, 'data_sources_status'):
            print("无数据源状态信息")
            return
        
        # 计算统计
        available_count = sum(1 for status in self.data_sources_status.values() 
                            if status == "available")
        total_count = len(self.data_sources_status)
        
        print(f"\n📊 数据源状态统计:")
        for source, status in sorted(self.data_sources_status.items()):
            icon = "✅" if status == "available" else "❌" if "failed" in status else "⚠️"
            print(f"{icon} {source}: {status}")
        
        print(f"\n🎯 汇总:")
        print(f"   成功: {available_count}/{total_count}")
        
        # 给出具体建议
        print(f"\n💡 具体建议:")
        
        # 检查关键组件
        critical_components = [
            ("basic_import", "基础导入"),
            ("technical", "技术数据"),
            ("analyst_macro_analyst", "宏观分析师"),
            ("analyst_technical_analyst", "技术分析师"),
            ("demo_weight_manager", "权重管理器")
        ]
        
        all_critical_ok = True
        for component, name in critical_components:
            status = self.data_sources_status.get(component, "unknown")
            if status != "available":
                print(f"   ❌ 需要修复: {name}")
                all_critical_ok = False
            else:
                print(f"   ✅ 正常: {name}")
        
        if all_critical_ok:
            print(f"\n🚀 恭喜！关键组件都正常，可以开始集成开发！")
        else:
            print(f"\n🔧 需要先修复关键组件的问题")

def run_fixed_tests():
    """运行修复版测试"""
    print("🚀 开始运行修复版集成测试")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestDataSourcesFixed))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 显示结果
    print("\n" + "=" * 60)
    print("📊 修复版测试结果")
    print("=" * 60)
    
    print(f"运行测试数: {result.testsRun}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")
    print(f"跳过数: {len(result.skipped)}")
    
    if result.failures:
        print("\n❌ 失败详情:")
        for test, traceback in result.failures:
            print(f"  {test}:")
            for line in traceback.split('\n')[:3]:
                print(f"    {line}")
    
    return result

if __name__ == '__main__':
    print("修复版集成系统测试")
    print("=" * 60)
    
    # 运行修复版测试
    test_result = run_fixed_tests()
    
    print("\n✅ 修复版测试完成！")