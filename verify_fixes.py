#!/usr/bin/env python3
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
    
    print("\n" + "=" * 50)
    if all_clean:
        print("🎉 所有关键文件都已修复完成！")
    else:
        print("⚠️  仍有文件需要手动修复")
    
    # 测试外汇数据功能
    print("\n🧪 测试外汇数据功能...")
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
