# check_project_structure.py
import os
import sys

def print_structure(path, indent=0, max_depth=3):
    """打印项目结构"""
    if indent > max_depth:
        return
        
    base_name = os.path.basename(path)
    print("  " * indent + f"📁 {base_name}/")
    
    try:
        items = os.listdir(path)
        for item in sorted(items):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                print_structure(item_path, indent + 1, max_depth)
            else:
                print("  " * (indent + 1) + f"📄 {item}")
    except Exception as e:
        print("  " * (indent + 1) + f"❌ 无法访问: {e}")

# 检查项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))
print(f"项目根目录: {project_root}")
print_structure(project_root, max_depth=4)

# 特别检查 tradingagents/agents 目录
agents_dir = os.path.join(project_root, 'tradingagents', 'agents')
print(f"\n详细检查 {agents_dir}:")
if os.path.exists(agents_dir):
    for root, dirs, files in os.walk(agents_dir):
        level = root.replace(agents_dir, '').count(os.sep)
        indent = '  ' * level
        print(f'{indent}📁 {os.path.basename(root)}/')
        subindent = '  ' * (level + 1)
        for file in sorted(files):
            if file.endswith('.py'):
                print(f'{subindent}📄 {file}')
else:
    print(f"❌ {agents_dir} 不存在")