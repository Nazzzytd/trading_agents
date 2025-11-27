# /scan_stock_references.py
import os
import re
import sys

def scan_directory_for_stock_references(root_dir):
    """
    扫描整个项目目录，查找所有引用 get_stock_data 的地方
    """
    stock_references = []
    
    # 要扫描的文件扩展名
    extensions = {'.py', '.yaml', '.yml', '.json', '.md', '.txt'}
    
    # 要排除的目录
    excluded_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', 'env'}
    
    print(f"🔍 开始扫描目录: {root_dir}")
    print("=" * 60)
    
    for root, dirs, files in os.walk(root_dir):
        # 排除不需要的目录
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 查找 get_stock_data 引用
                    if 'get_stock_data' in content:
                        lines = content.split('\n')
                        for line_num, line in enumerate(lines, 1):
                            if 'get_stock_data' in line:
                                # 计算相对路径
                                rel_path = os.path.relpath(file_path, root_dir)
                                stock_references.append({
                                    'file': rel_path,
                                    'line': line_num,
                                    'content': line.strip(),
                                    'full_path': file_path
                                })
                                
                except Exception as e:
                    print(f"⚠️  无法读取文件 {file_path}: {e}")
    
    return stock_references

def analyze_references(references):
    """
    分析引用并分类
    """
    categories = {
        'imports': [],
        'function_calls': [],
        'tool_definitions': [],
        'comments': [],
        'other': []
    }
    
    for ref in references:
        content = ref['content'].lower()
        
        if 'import' in content and 'get_stock_data' in content:
            categories['imports'].append(ref)
        elif 'def get_stock_data' in content or '@tool' in content:
            categories['tool_definitions'].append(ref)
        elif 'get_stock_data(' in content:
            categories['function_calls'].append(ref)
        elif '#' in content and content.index('#') < content.index('get_stock_data'):
            categories['comments'].append(ref)
        else:
            categories['other'].append(ref)
    
    return categories

def print_report(categories):
    """
    打印扫描报告
    """
    total_refs = sum(len(refs) for refs in categories.values())
    
    print(f"\n📊 扫描结果: 共找到 {total_refs} 个 get_stock_data 引用")
    print("=" * 60)
    
    for category, refs in categories.items():
        if refs:
            print(f"\n🔸 {category.upper()} ({len(refs)} 个):")
            for ref in refs[:10]:  # 只显示前10个
                print(f"   📄 {ref['file']}:{ref['line']}")
                print(f"      {ref['content']}")
            if len(refs) > 10:
                print(f"   ... 还有 {len(refs) - 10} 个")

def suggest_fixes(categories):
    """
    根据扫描结果提供修复建议
    """
    print(f"\n🔧 修复建议")
    print("=" * 60)
    
    if categories['imports']:
        print("\n📥 需要更新的导入:")
        for ref in categories['imports']:
            print(f"   - {ref['file']}: 将 get_stock_data 改为 get_forex_data")
    
    if categories['function_calls']:
        print("\n📞 需要更新的函数调用:")
        for ref in categories['function_calls']:
            print(f"   - {ref['file']}: 将 get_stock_data(...) 改为 get_forex_data(...)")
    
    if categories['tool_definitions']:
        print("\n🛠️ 需要更新的工具定义:")
        for ref in categories['tool_definitions']:
            print(f"   - {ref['file']}: 需要重写工具定义")

def main():
    project_root = '/Users/fr./Downloads/TradingAgents-main'
    
    if not os.path.exists(project_root):
        print(f"❌ 项目目录不存在: {project_root}")
        return
    
    # 扫描项目
    references = scan_directory_for_stock_references(project_root)
    
    if not references:
        print("🎉 恭喜！没有找到任何 get_stock_data 引用")
        return
    
    # 分析引用
    categories = analyze_references(references)
    
    # 打印报告
    print_report(categories)
    
    # 提供修复建议
    suggest_fixes(categories)
    
    # 保存详细报告到文件
    report_file = os.path.join(project_root, 'stock_references_report.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("get_stock_data 引用扫描报告\n")
        f.write("=" * 50 + "\n\n")
        
        for category, refs in categories.items():
            if refs:
                f.write(f"{category.upper()}:\n")
                for ref in refs:
                    f.write(f"  {ref['file']}:{ref['line']}\n")
                    f.write(f"    {ref['content']}\n\n")
    
    print(f"\n📝 详细报告已保存到: {report_file}")

if __name__ == "__main__":
    main()