with open('tradingagents/agents/utils/technical_indicators_tools.py', 'r') as f:
    lines = f.readlines()

print(f"文件总行数: {len(lines)}")

# 找到有问题的第140-150行
print("\n=== 修复前的第135-155行 ===")
for i in range(135, 155):
    if i < len(lines):
        print(f"第{i+1:3d}行: {lines[i].rstrip()}")

# 具体问题在第140-150行：
# 第140行: try:
# 第141行: def route_to_vendor(*args, **kwargs):  <-- 这行应该在try块内，需要缩进
# 但第141行没有缩进

# 修复：重新组织第140-150行的代码
# 找到 try: 开始的行
try_line = -1
for i, line in enumerate(lines):
    if i >= 135 and i <= 150 and 'try:' in line:
        try_line = i
        break

if try_line != -1:
    print(f"\n找到 try: 在第{try_line+1}行")
    
    # 检查 try: 后面的行
    print("检查 try 块内容:")
    for i in range(try_line, try_line + 10):
        if i < len(lines):
            print(f"第{i+1}行: {lines[i].rstrip()}")
    
    # 修复：确保 try 块内的代码正确缩进
    # 从第141行开始，到对应的 except 之前，都应该缩进
    
    # 找到 try 块的结束（对应的 except 行）
    except_line = -1
    for i in range(try_line + 1, min(try_line + 20, len(lines))):
        if 'except' in lines[i] and lines[i].strip().startswith('except'):
            except_line = i
            break
    
    if except_line != -1:
        print(f"找到对应的 except 在第{except_line+1}行")
        
        # 修复 try 块内的缩进
        for i in range(try_line + 1, except_line):
            if lines[i].strip():  # 非空行
                # 确保有正确的缩进（至少4个空格）
                if not lines[i].startswith('    '):
                    lines[i] = '    ' + lines[i]
                    print(f"修复第{i+1}行的缩进")
    else:
        print("⚠️ 没有找到对应的 except 语句")
        
        # 如果找不到 except，可能需要手动修复这个区域
        # 重新构建正确的代码
        
        # 找到从 try_line 开始的有问题的代码块
        problem_start = try_line
        problem_end = -1
        
        # 查找下一个非缩进的 def 或函数定义
        for i in range(try_line + 1, min(try_line + 10, len(lines))):
            if lines[i].strip().startswith('def ') and not lines[i].startswith('    '):
                problem_end = i
                break
        
        if problem_end != -1:
            print(f"找到问题代码块: 第{problem_start+1}行到第{problem_end+1}行")
            
            # 重建正确的代码
            correct_code = '''        if route_func is None:
            try:
                # 占位符函数，避免循环导入
                def route_to_vendor(*args, **kwargs):
                    """占位符函数，避免循环导入"""
                    return "技术指标工具 - 避免循环导入，请直接调用具体函数"
                route_func = route_to_vendor
                setattr(current_module, 'route_to_vendor', route_func)
            except ImportError as e:
                logger.error(f"无法导入 route_to_vendor: {e}")
                return {"success": False, "error": f"数据路由函数不可用: {e}"}'''
            
            # 替换有问题的代码
            lines[problem_start:problem_end+1] = [line + '\n' for line in correct_code.split('\n')]
            print("✅ 已替换有问题的代码块")
        else:
            print("⚠️ 无法确定问题代码块的范围")

# 保存修复
with open('tradingagents/agents/utils/technical_indicators_tools.py', 'w') as f:
    f.writelines(lines)

print("\n✅ 修复完成")
