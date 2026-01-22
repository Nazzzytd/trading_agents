"""
工具函数模块
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
import logging
from datetime import datetime, timedelta
from .config import MarketState

logger = logging.getLogger(__name__)


def validate_dataframe(df: pd.DataFrame, required_columns: List[str] = None) -> Tuple[bool, str]:
    """
    验证DataFrame格式
    
    Args:
        df: 要验证的DataFrame
        required_columns: 必须存在的列
        
    Returns:
        (是否有效, 错误信息)
    """
    if df.empty:
        return False, "DataFrame为空"
    
    if required_columns is None:
        required_columns = ['open', 'high', 'low', 'close', 'volume']
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"缺少必要列: {missing_columns}"
    
    # 检查NaN值
    nan_counts = df[required_columns].isna().sum()
    if nan_counts.any():
        nan_cols = nan_counts[nan_counts > 0].index.tolist()
        return False, f"数据包含NaN值: {nan_cols}"
    
    return True, "数据有效"


def calculate_price_change(prices: pd.Series, periods: int = 1) -> float:
    """
    计算价格变化百分比
    
    Args:
        prices: 价格序列
        periods: 周期数
        
    Returns:
        价格变化百分比
    """
    if len(prices) < periods + 1:
        return 0.0
    
    current_price = prices.iloc[-1]
    prev_price = prices.iloc[-periods-1]
    
    if prev_price == 0:
        return 0.0
    
    return (current_price - prev_price) / prev_price


def normalize_scores(scores: Dict[str, float]) -> Dict[str, float]:
    """
    归一化分数到0-1范围
    
    Args:
        scores: 原始分数字典
        
    Returns:
        归一化后的分数
    """
    if not scores:
        return {}
    
    values = list(scores.values())
    min_val = min(values)
    max_val = max(values)
    
    if max_val == min_val:
        return {k: 0.5 for k in scores.keys()}
    
    normalized = {}
    for key, value in scores.items():
        normalized[key] = (value - min_val) / (max_val - min_val)
    
    return normalized


def smooth_states(state_sequence: List[str], window: int = 3) -> List[str]:
    """
    平滑状态序列
    
    Args:
        state_sequence: 原始状态序列
        window: 平滑窗口大小
        
    Returns:
        平滑后的状态序列
    """
    if len(state_sequence) < window:
        return state_sequence
    
    smoothed = []
    for i in range(len(state_sequence)):
        start = max(0, i - window + 1)
        end = i + 1
        window_states = state_sequence[start:end]
        
        # 统计窗口内各状态出现次数
        state_counts = {}
        for state in window_states:
            state_counts[state] = state_counts.get(state, 0) + 1
        
        # 选择最频繁的状态
        most_common = max(state_counts.items(), key=lambda x: x[1])[0]
        smoothed.append(most_common)
    
    return smoothed


def detect_state_patterns(states: List[str], min_pattern_length: int = 3) -> List[Dict]:
    """
    检测状态模式
    
    Args:
        states: 状态序列
        min_pattern_length: 最小模式长度
        
    Returns:
        检测到的模式列表
    """
    if len(states) < min_pattern_length * 2:
        return []
    
    patterns = []
    n = len(states)
    
    for pattern_length in range(min_pattern_length, n // 2 + 1):
        for start in range(n - pattern_length * 2 + 1):
            pattern = states[start:start + pattern_length]
            
            # 检查是否重复
            next_segment = states[start + pattern_length:start + pattern_length * 2]
            if pattern == next_segment:
                pattern_info = {
                    "pattern": pattern,
                    "length": pattern_length,
                    "start_index": start,
                    "repetitions": 2
                }
                
                # 检查是否有更多重复
                for i in range(2, (n - start) // pattern_length):
                    next_segment = states[start + pattern_length * i:start + pattern_length * (i + 1)]
                    if pattern == next_segment:
                        pattern_info["repetitions"] = i + 1
                    else:
                        break
                
                patterns.append(pattern_info)
    
    return patterns


def calculate_confidence_interval(values: List[float], confidence: float = 0.95) -> Tuple[float, float]:
    """
    计算置信区间
    
    Args:
        values: 数值列表
        confidence: 置信水平
        
    Returns:
        (下界, 上界)
    """
    if not values:
        return 0.0, 0.0
    
    mean = np.mean(values)
    std = np.std(values)
    n = len(values)
    
    if n < 2:
        return mean, mean
    
    # Z分数（大样本近似）
    from scipy import stats
    try:
        z_score = stats.norm.ppf((1 + confidence) / 2)
        margin = z_score * std / np.sqrt(n)
        return mean - margin, mean + margin
    except:
        # 如果scipy不可用，使用简单估计
        margin = 2 * std / np.sqrt(n)
        return mean - margin, mean + margin


def merge_analyses(analyses: List[Dict], method: str = 'weighted') -> Dict:
    """
    合并多个分析结果
    
    Args:
        analyses: 分析结果列表
        method: 合并方法 ('weighted', 'majority', 'average')
        
    Returns:
        合并后的分析结果
    """
    if not analyses:
        return {}
    
    if len(analyses) == 1:
        return analyses[0].copy()
    
    # 只考虑成功的分析
    successful_analyses = [a for a in analyses if a.get('success', False)]
    if not successful_analyses:
        return analyses[0].copy()
    
    if method == 'majority':
        return _merge_by_majority(successful_analyses)
    elif method == 'average':
        return _merge_by_average(successful_analyses)
    else:  # weighted
        return _merge_by_weighted(successful_analyses)


def _merge_by_majority(analyses: List[Dict]) -> Dict:
    """按多数原则合并"""
    # 统计各状态出现次数
    state_counts = {}
    for analysis in analyses:
        state = analysis.get('market_state', 'unknown')
        state_counts[state] = state_counts.get(state, 0) + 1
    
    # 选择最频繁的状态
    merged_state = max(state_counts.items(), key=lambda x: x[1])[0]
    
    # 创建合并结果
    merged = analyses[0].copy()
    merged['market_state'] = merged_state
    merged['confidence'] = state_counts[merged_state] / len(analyses)
    merged['merged_from'] = len(analyses)
    
    return merged


def _merge_by_weighted(analyses: List[Dict]) -> Dict:
    """按加权原则合并"""
    total_confidence = sum(a.get('confidence', 0.0) for a in analyses)
    
    if total_confidence == 0:
        return _merge_by_majority(analyses)
    
    # 加权平均状态（简化处理）
    state_scores = {}
    for analysis in analyses:
        state = analysis.get('market_state', 'unknown')
        confidence = analysis.get('confidence', 0.0)
        state_scores[state] = state_scores.get(state, 0.0) + confidence
    
    merged_state = max(state_scores.items(), key=lambda x: x[1])[0]
    avg_confidence = total_confidence / len(analyses)
    
    merged = analyses[0].copy()
    merged['market_state'] = merged_state
    merged['confidence'] = avg_confidence
    merged['merged_from'] = len(analyses)
    
    return merged


def _merge_by_average(analyses: List[Dict]) -> Dict:
    """按平均原则合并"""
    # 简化实现，使用加权平均
    return _merge_by_weighted(analyses)


def generate_analysis_summary(result: Dict, include_details: bool = False) -> str:
    """
    生成分析摘要
    
    Args:
        result: 分析结果
        include_details: 是否包含详细信息
        
    Returns:
        摘要字符串
    """
    if not result.get('success', False):
        return f"分析失败: {result.get('error', '未知错误')}"
    
    lines = []
    symbol = result.get('symbol', 'Unknown')
    state = result.get('state_chinese', '未知状态')
    confidence = result.get('confidence', 0.0)
    
    lines.append(f"{symbol}: {state} (置信度: {confidence:.0%})")
    
    if include_details:
        signals = result.get('trading_signals', [])
        if signals:
            primary_signal = signals[0]
            action = primary_signal.get('action', 'N/A')
            reason = primary_signal.get('reason', '')
            lines.append(f"建议: {action} - {reason}")
    
    return "\n".join(lines)


def save_analysis_to_file(result: Dict, filepath: str, format: str = 'json'):
    """
    保存分析结果到文件
    
    Args:
        result: 分析结果
        filepath: 文件路径
        format: 格式 ('json', 'csv', 'txt')
    """
    try:
        if format == 'json':
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        
        elif format == 'csv':
            # 创建简化的CSV格式
            import csv
            flat_result = _flatten_dict(result)
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(flat_result.keys())
                writer.writerow(flat_result.values())
        
        elif format == 'txt':
            summary = generate_analysis_summary(result, include_details=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(summary)
        
        logger.info(f"分析结果已保存到: {filepath}")
        
    except Exception as e:
        logger.error(f"保存分析结果失败: {e}")


def _flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """扁平化字典"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # 简化处理列表
            items.append((new_key, str(v)))
        else:
            items.append((new_key, v))
    return dict(items)


def load_config_from_dict(config_dict: Dict) -> MarketAnalysisConfig:
    """
    从字典创建配置对象
    
    Args:
        config_dict: 配置字典
        
    Returns:
        配置对象
    """
    from .config import MarketAnalysisConfig
    
    # 过滤掉无效键
    valid_keys = {f.name for f in MarketAnalysisConfig.__dataclass_fields__.values()}
    filtered_dict = {k: v for k, v in config_dict.items() if k in valid_keys}
    
    return MarketAnalysisConfig(**filtered_dict)