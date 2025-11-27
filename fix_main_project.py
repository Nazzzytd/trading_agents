# /fix_main_project_fixed.py
import os
import re
import sys

def replace_in_file(file_path, old_text, new_text):
    """在文件中替换文本"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 统计替换次数
        original_count = content.count(old_text)
        if original_count == 0:
            return 0
            
        # 执行替换
        new_content = content.replace(old_text, new_text)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return original_count
        
    except Exception as e:
        print(f"❌ 无法处理文件 {file_path}: {e}")
        return 0

def fix_main_project():
    """只修复主 tradingagents 文件夹"""
    project_root = '/Users/fr./Downloads/TradingAgents-main'
    main_project_dir = os.path.join(project_root, 'tradingagents')
    
    if not os.path.exists(main_project_dir):
        print(f"❌ 主项目目录不存在: {main_project_dir}")
        return
    
    print(f"🔧 开始修复主项目: {main_project_dir}")
    print("=" * 60)
    
    # 定义修复规则
    fix_rules = [
        # 导入语句修复
        ('from tradingagents.agents.utils.agent_utils import get_stock_data, get_indicators',
         'from tradingagents.agents.utils.agent_utils import get_forex_data, get_indicators'),
        
        ('from tradingagents.agents.utils.agent_utils import get_stock_data',
         'from tradingagents.agents.utils.agent_utils import get_forex_data'),
        
        # 函数调用修复
        ('get_stock_data(', 'get_forex_data('),
        ('route_to_vendor("get_stock_data"', 'route_to_vendor("get_forex_data"'),
        
        # 工具定义修复（在 vendors 目录中）
        ('def get_stock_data(', 'def get_forex_data('),
        
        # 配置和注释修复
        ('"get_stock_data":', '"get_forex_data":'),
        ('get_stock_data', 'get_forex_data'),  # 通用替换
    ]
    
    total_fixes = 0
    fixed_files = []
    
    # 扫描主项目目录
    for root, dirs, files in os.walk(main_project_dir):
        # 排除 copy 目录
        if 'tradingagents copy' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_root)
                
                file_fixes = 0
                for old_text, new_text in fix_rules:
                    fixes = replace_in_file(file_path, old_text, new_text)
                    file_fixes += fixes
                
                if file_fixes > 0:
                    fixed_files.append((rel_path, file_fixes))
                    total_fixes += file_fixes
    
    # 打印修复结果
    print(f"\n✅ 修复完成！共在 {len(fixed_files)} 个文件中进行了 {total_fixes} 处修改")
    print("=" * 60)
    
    if fixed_files:
        print("\n📝 修复的文件列表:")
        for file_path, fixes in sorted(fixed_files):
            print(f"   📄 {file_path} ({fixes} 处修改)")
    
    # 特别检查几个关键文件
    key_files = [
        'tradingagents/agents/analysts/market_analyst.py',
        'tradingagents/agents/utils/agent_utils.py',
        'tradingagents/dataflows/vendors/yfin_utils.py',
        'tradingagents/graph/trading_graph.py'
    ]
    
    print(f"\n🔍 关键文件检查:")
    for key_file in key_files:
        full_path = os.path.join(project_root, key_file)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                stock_refs = content.count('get_stock_data')
                forex_refs = content.count('get_forex_data')
                status = "✅ 已修复" if stock_refs == 0 else "❌ 仍需修复"
                print(f"   {key_file}: {status} (stock: {stock_refs}, forex: {forex_refs})")
    
    return project_root

def create_verification_script(project_root):
    """创建验证脚本"""
    script_content = '''#!/usr/bin/env python3
"""
验证 get_stock_data 是否已完全替换为 get_forex_data
"""

import os
import sys

project_root = '/Users/fr./Downloads/TradingAgents-main'

def verify_fixes():
    """验证修复结果"""
    print("🔍 验证修复结果")
    print("=" * 50)
    
    # 检查关键文件
    key_files = [
        'tradingagents/agents/analysts/market_analyst.py',
        'tradingagents/agents/utils/agent_utils.py', 
        'tradingagents/dataflows/interface.py',
        'tradingagents/graph/trading_graph.py'
    ]
    
    all_clean = True
    
    for rel_path in key_files:
        full_path = os.path.join(project_root, rel_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                stock_count = content.count('get_stock_data')
                if stock_count > 0:
                    print(f"❌ {rel_path}: 仍有 {stock_count} 个 get_stock_data 引用")
                    all_clean = False
                else:
                    print(f"✅ {rel_path}: 已完全修复")
    
    print("\\n" + "=" * 50)
    if all_clean:
        print("🎉 所有关键文件都已修复完成！")
    else:
        print("⚠️  仍有文件需要手动修复")
    
    # 测试外汇数据功能
    print("\\n🧪 测试外汇数据功能...")
    try:
        sys.path.insert(0, project_root)
        from tradingagents.agents.utils.core_forex_tools import get_forex_data
        print("✅ get_forex_data 工具导入成功")
        
        # 测试工具基本信息
        print(f"   工具名称: {get_forex_data.name}")
        print(f"   工具描述: {get_forex_data.description[:80]}...")
        
    except Exception as e:
        print(f"❌ 外汇数据工具测试失败: {e}")

if __name__ == "__main__":
    verify_fixes()
'''

    script_path = os.path.join(project_root, 'verify_fixes.py')
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"\n📋 验证脚本已创建: {script_path}")
    print("运行命令: python verify_fixes.py")

if __name__ == "__main__":
    project_root = fix_main_project()
    create_verification_script(project_root)
    
    print(f"\n🎯 下一步:")
    print("1. 运行验证脚本: python verify_fixes.py")
    print("2. 如果仍有问题，手动检查报告中的文件")
    print("3. 测试外汇数据功能是否正常工作")