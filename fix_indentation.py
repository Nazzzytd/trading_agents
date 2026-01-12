import re

with open('tradingagents/adaptive_system/graph_integration.py', 'r') as f:
    lines = f.readlines()

# 找到 create_weight_calculator 函数
in_calculator = False
fixed_lines = []
for i, line in enumerate(lines):
    # 检查是否在 create_weight_calculator 函数中
    if 'def create_weight_calculator(' in line:
        in_calculator = True
        fixed_lines.append(line)
        continue
    
    if in_calculator and line.strip().startswith('def calculate_weights'):
        # 找到内嵌函数，确保缩进正确
        fixed_lines.append(line)
        
        # 检查下一行
        if i+1 < len(lines) and lines[i+1].strip().startswith('"""'):
            # 文档字符串，确保缩进比函数多一层
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith('"'):
                # 确保有正确的缩进
                if len(lines[j]) - len(lines[j].lstrip()) < 8:  # 少于8个空格
                    lines[j] = ' ' * 8 + lines[j].lstrip()
                fixed_lines.append(lines[j])
                j += 1
            continue
    
    if in_calculator and line.strip() == 'return calculate_weights':
        in_calculator = False
    
    fixed_lines.append(line)

# 保存修复后的文件
with open('tradingagents/adaptive_system/graph_integration.py', 'w') as f:
    f.writelines(fixed_lines)

print("缩进修复完成")
