
# 修复Python路径问题
import sys
import os
from pathlib import Path

# 添加项目根目录
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)

# 加载环境变量
from dotenv import load_dotenv
env_path = os.path.join(project_root, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
    print(f"✅ 从 {env_path} 加载环境变量")
else:
    print(f"⚠️  未找到.env文件: {env_path}")

# 测试导入
try:
    from tradingagents.dataflows.interface import route_to_vendor
    print("✅ route_to_vendor导入成功")
except ImportError as e:
    print(f"❌ route_to_vendor导入失败: {e}")

print("✅ Python路径修复完成")
