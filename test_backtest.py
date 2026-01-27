import sys
import os

# 添加项目根目录到Python路径
current_dir = os.getcwd()
sys.path.insert(0, current_dir)

print(f"当前目录: {current_dir}")
print(f"Python路径: {sys.path[:3]}")

# 尝试导入
try:
    print("\n尝试从 tradingagents.backtest 导入...")
    from tradingagents.backtest import yfinance_data
    print("成功导入 yfinance_data 模块")
    
    # 检查是否有demonstrate_yfinance_usage函数
    if hasattr(yfinance_data, 'demonstrate_yfinance_usage'):
        print("找到 demonstrate_yfinance_usage 函数")
        yfinance_data.demonstrate_yfinance_usage()
    else:
        print("在 yfinance_data 模块中没有找到 demonstrate_yfinance_usage 函数")
        print("可用的函数/类:")
        for item in dir(yfinance_data):
            if not item.startswith('_'):
                print(f"  - {item}")
                
except ImportError as e:
    print(f"导入错误: {e}")
    print("\n尝试查看 backtest 目录内容...")
    backtest_dir = os.path.join(current_dir, 'tradingagents', 'backtest')
    if os.path.exists(backtest_dir):
        print(f"backtest目录 ({backtest_dir}) 内容:")
        for item in os.listdir(backtest_dir):
            item_path = os.path.join(backtest_dir, item)
            if os.path.isdir(item_path):
                print(f"  [目录] {item}")
            else:
                print(f"  [文件] {item}")
    else:
        print(f"backtest目录不存在: {backtest_dir}")
