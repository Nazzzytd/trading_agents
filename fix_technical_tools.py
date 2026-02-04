import re

# 读取文件
with open('tradingagents/agents/utils/technical_indicators_tools.py', 'r') as f:
    content = f.read()

print("正在修复 technical_indicators_tools.py...")

# 查找第140-150行的问题区域
lines = content.split('\n')
print(f"文件总行数: {len(lines)}")

# 显示有问题的区域
print("\n=== 问题区域 (第135-150行) ===")
for i, line in enumerate(lines[134:150], 135):
    print(f"第{i}行: {line}")

# 修复第140-145行的问题
# 问题出现在 try 块中有一个孤立的 pass 语句
problem_start = None
for i, line in enumerate(lines):
    if 'try:' in line and i > 130 and i < 150:
        problem_start = i
        break

if problem_start:
    print(f"\n找到问题开始于第{problem_start+1}行")
    
    # 检查接下来的几行
    for j in range(problem_start, min(problem_start + 10, len(lines))):
        print(f"第{j+1}行: {lines[j]}")
    
    # 修复：删除孤立的 pass 语句，确保 try 块正确闭合
    # 查找 try: 后的 pass 语句
    try_line = problem_start
    pass_line = None
    
    for j in range(try_line + 1, min(try_line + 5, len(lines))):
        if 'pass' in lines[j] and lines[j].strip() == 'pass':
            pass_line = j
            break
    
    if pass_line:
        print(f"找到孤立的 pass 语句在第{pass_line+1}行，删除它")
        del lines[pass_line]
    
    # 重新组合内容
    content = '\n'.join(lines)
    
    # 确保 try 块有正确的结构
    # 查找 try: 后的 def route_to_vendor
    try_pattern = r'try:\s*\n\s*def route_to_vendor'
    if re.search(try_pattern, content):
        print("发现 try 块内直接定义函数的问题")
        # 修复：在 try 块中添加适当的异常处理
        fixed_try_block = '''try:
    # 占位符函数，避免循环导入
    def route_to_vendor(*args, **kwargs):
        """占位符函数，避免循环导入"""
        return "技术指标工具 - 避免循环导入，请直接调用具体函数"
    route_func = route_to_vendor
    setattr(current_module, 'route_to_vendor', route_func)
except ImportError as e:
    logger.error(f"无法导入 route_to_vendor: {e}")
    return {"success": False, "error": f"数据路由函数不可用: {e}"}'''
        
        # 替换有问题的 try 块
        old_try_block = '''try:
                # 占位符函数，避免循环导入
    pass
def route_to_vendor(*args, **kwargs):
    """占位符函数，避免循环导入"""
    return "技术指标工具 - 避免循环导入，请直接调用具体函数"
                route_func = route_to_vendor
                setattr(current_module, 'route_to_vendor', route_func)
            except ImportError as e:
                logger.error(f"无法导入 route_to_vendor: {e}")
                return {"success": False, "error": f"数据路由函数不可用: {e}"}'''
        
        if old_try_block in content:
            content = content.replace(old_try_block, fixed_try_block)
            print("✅ 已修复 try 块结构")
        else:
            print("⚠️ 未找到旧的 try 块格式，尝试其他修复")
    else:
        print("✅ try 块结构看起来正常")

# 保存修复后的文件
with open('tradingagents/agents/utils/technical_indicators_tools.py', 'w') as f:
    f.write(content)

print("\n✅ 修复完成")
