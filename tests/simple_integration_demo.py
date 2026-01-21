
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ========== 1. 设置环境 ==========
# 设置项目路径
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# 加载环境变量
env_path = os.path.join(project_root, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
    print(f"✅ 环境变量从 {env_path} 加载")
else:
    print("⚠️  未找到.env文件")
    load_dotenv()

print("=" * 60)
print("🚀 简单集成演示")
print("=" * 60)

# ========== 2. 导入模块 ==========
try:
    from tradingagents.adaptive_system.weight_manager import AdaptiveWeightManager
    from tradingagents.adaptive_system.config import AdaptiveConfig
    from tradingagents.adaptive_system.layer_manager import LayerManager
    
    print("✅ 模块导入成功")
    
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)

# ========== 3. 创建系统 ==========
# 创建配置
config = AdaptiveConfig()

# 创建权重管理器
weight_manager = AdaptiveWeightManager(config)

# 创建层管理器
layer_manager = LayerManager()

print("✅ 系统组件创建成功")

# ========== 4. 注册分析师 ==========
analysts = [
    ("macro_analyst", "strategic", "宏观分析师"),
    ("news_analyst", "operational", "新闻分析师"),
    ("technical_analyst", "tactical", "技术分析师")
]

for agent_id, layer, description in analysts:
    weight_manager.register_agent(agent_id, layer)
    print(f"📝 注册: {description} ({layer}层)")

print(f"✅ 注册了 {len(analysts)} 个分析师")

# ========== 5. 模拟数据 ==========
print("\n📊 模拟预测数据...")

# 模拟宏观分析师预测
weight_manager.record_prediction("macro_analyst", 1.05)  # 预测上涨5%
weight_manager.record_actual("macro_analyst", 1.02)      # 实际上涨2%

# 模拟技术分析师预测
weight_manager.record_prediction("technical_analyst", 1.03)  # 预测上涨3%
weight_manager.record_actual("technical_analyst", 1.01)      # 实际上涨1%

# 模拟新闻分析师预测
weight_manager.record_prediction("news_analyst", 0.98)  # 预测下跌2%
weight_manager.record_actual("news_analyst", 1.00)      # 实际持平

print("✅ 模拟数据记录完成")

# ========== 6. 计算权重 ==========
print("\n⚖️  计算自适应权重...")

# 更新所有权重
weight_manager.update_all_weights()

# 获取归一化权重
weights = weight_manager.get_normalized_weights()

print("📈 权重分配:")
for agent, weight in weights.items():
    # 获取描述
    description = next((desc for aid, _, desc in analysts if aid == agent), agent)
    print(f"  {description}: {weight:.1%}")

# ========== 7. 层级调整 ==========
print("\n🏗️  层级权重调整...")

# 模拟层级调整
for agent_id, layer, description in analysts:
    error = weight_manager.get_agent_error(agent_id, default=0.5)
    
    # 使用层管理器调整权重
    adjusted_weight = layer_manager.adjust_weight(
        agent_id,
        current_error=error,
        layer_name=layer,
        market_volatility=1.0
    )
    
    print(f"  {description}: 误差={error:.3f}, 调整后权重={adjusted_weight:.3f}")

# ========== 8. 最终决策 ==========
print("\n🎯 最终决策模拟...")

# 模拟各分析师的预测
predictions = {
    "macro_analyst": 0.65,  # 看涨
    "technical_analyst": 0.70,  # 看涨
    "news_analyst": 0.45  # 看跌
}

# 计算加权决策
weighted_decision = 0.0
for agent, prediction in predictions.items():
    weight = weights.get(agent, 0.0)
    weighted_decision += prediction * weight
    print(f"  {agent}: 预测={prediction:.2f}, 权重={weight:.1%}, 贡献={prediction * weight:.3f}")

print(f"\n💡 加权决策值: {weighted_decision:.3f}")

# 决策建议
if weighted_decision > 0.60:
    recommendation = "买入"
elif weighted_decision < 0.40:
    recommendation = "卖出"
else:
    recommendation = "观望"

print(f"🎯 最终建议: {recommendation}")

print("\n" + "=" * 60)
print("✅ 简单集成演示完成!")
print("=" * 60)
