# /Users/fr./Downloads/TradingAgents-main/tests/conftest.py
"""
测试配置文件
"""
import pytest
import tempfile
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def default_config():
    """提供默认配置"""
    from tradingagents.adaptive_system.config import AdaptiveConfig
    return AdaptiveConfig()


@pytest.fixture
def custom_config():
    """提供自定义配置"""
    from tradingagents.adaptive_system.config import AdaptiveConfig
    return AdaptiveConfig(
        initial_weight=1.5,
        min_weight=0.2,
        max_weight=4.0,
        learning_rate=0.2,
        error_window_size=10
    )


@pytest.fixture
def adaptive_system():
    """提供自适应系统实例"""
    from tradingagents.adaptive_system import AdaptiveSystem
    return AdaptiveSystem()


@pytest.fixture
def sample_agents():
    """提供样本智能体数据"""
    return {
        "tech_analyst": {"layer": "analyst", "predictions": [1.2, 1.3], "actuals": [1.1, 1.25]},
        "news_analyst": {"layer": "analyst", "predictions": [1.1, 1.4], "actuals": [1.0, 1.35]},
        "risk_debator": {"layer": "debator", "predictions": [0.8, 0.9], "actuals": [0.9, 0.95]},
    }


@pytest.fixture
def temp_config_file():
    """提供临时配置文件"""
    from tradingagents.adaptive_system.config import AdaptiveConfig
    
    config = AdaptiveConfig(initial_weight=2.0, learning_rate=0.5)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config.save(f.name)
        yield f.name
    
    # 清理临时文件
    import os
    if os.path.exists(f.name):
        os.unlink(f.name)


@pytest.fixture
def weight_manager():
    """提供权重管理器实例"""
    from tradingagents.adaptive_system.weight_manager import AdaptiveWeightManager
    from tradingagents.adaptive_system.config import AdaptiveConfig
    
    config = AdaptiveConfig()
    return AdaptiveWeightManager(config)


@pytest.fixture
def layer_manager():
    """提供层级管理器实例"""
    from tradingagents.adaptive_system.layer_manager import LayerManager
    return LayerManager()