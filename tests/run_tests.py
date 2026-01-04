# /Users/fr./Downloads/TradingAgents-main/tests/run_tests.py
#!/usr/bin/env python3
"""
运行所有测试
"""
import unittest
import sys
import os

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("运行自适应系统测试套件")
    print("=" * 60)
    
    # 添加项目根目录到Python路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.insert(0, project_root)
    
    # 发现并运行所有测试
    test_loader = unittest.TestLoader()
    
    # 运行每个测试文件
    test_files = [
        'test_weight_manager.py',
        'test_layer_manager.py', 
        'test_adaptive_system.py'
    ]
    
    all_success = True
    
    for test_file in test_files:
        print(f"\n{'='*40}")
        print(f"运行测试: {test_file}")
        print('='*40)
        
        try:
            # 加载测试
            test_suite = test_loader.loadTestsFromName(f'tests.{test_file[:-3]}')
            
            # 运行测试
            test_runner = unittest.TextTestRunner(verbosity=2)
            result = test_runner.run(test_suite)
            
            if not result.wasSuccessful():
                all_success = False
                
        except Exception as e:
            print(f"运行测试 {test_file} 时出错: {str(e)}")
            all_success = False
    
    print("\n" + "=" * 60)
    if all_success:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)
    
    return all_success

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)