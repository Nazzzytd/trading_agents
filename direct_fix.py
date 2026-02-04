with open('tradingagents/agents/utils/technical_indicators_tools.py', 'r') as f:
    lines = f.readlines()

print("修复第142行的缩进问题...")

# 第142行（索引141）应该是: def route_to_vendor(*args, **kwargs):
# 但它应该在 try 块内，所以需要缩进

# 找到第140行（索引139）的 try:
try_line = 139  # 第140行
print(f"第{try_line+1}行: {lines[try_line].rstrip()}")

# 第142行（索引141）需要缩进
if len(lines) > 141:
    print(f"修复前的第{142}行: {repr(lines[141])}")
    
    # 确保有正确的缩进（8个空格，因为它在 try 块内的 if 块内）
    if not lines[141].startswith('        '):  # 8个空格
        lines[141] = '        ' + lines[141].lstrip()
        print(f"修复后的第{142}行: {repr(lines[141])}")
    
    # 第143行（索引142）也需要缩进
    if len(lines) > 142 and lines[142].strip():
        if not lines[142].startswith('        '):
            lines[142] = '        ' + lines[142].lstrip()
            print(f"修复第{143}行的缩进")
    
    # 第144行（索引143）也需要缩进
    if len(lines) > 143 and lines[143].strip():
        if not lines[143].startswith('        '):
            lines[143] = '        ' + lines[143].lstrip()
            print(f"修复第{144}行的缩进")

# 保存修复
with open('tradingagents/agents/utils/technical_indicators_tools.py', 'w') as f:
    f.writelines(lines)

print("✅ 修复完成")
