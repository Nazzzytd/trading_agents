# /Users/fr./Downloads/TradingAgents-main/tradingagents/agents/utils/quant_data_tools.py
"""
简化版量化数据工具 - 只暴露核心量化分析功能
"""
from langchain_core.tools import tool
from typing import Annotated, Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from tradingagents.dataflows.interface import route_to_vendor

logger = logging.getLogger(__name__)

# 直接导入您的 TwelveData 类
try:
    from tradingagents.dataflows.vendors.twelvedata_data import twelvedata_forex
    TWELVEDATA_AVAILABLE = True
except ImportError:
    TWELVEDATA_AVAILABLE = False
    logger.warning("TwelveData 模块不可用")

# ==================== 内部辅助函数（不暴露为工具）====================

def _get_forex_data_internal(symbol: str, periods: int = 100, timeframe: str = "1day") -> Dict[str, Any]:
    """
    内部函数：获取外汇OHLC数据
    不暴露为工具，仅供内部使用
    """
    if not TWELVEDATA_AVAILABLE:
        return {"success": False, "error": "TwelveData 模块不可用"}
    
    try:
        # 直接调用 TwelveData
        result = twelvedata_forex.get_forex_ohlc(
            symbol=symbol,
            interval=timeframe,
            output_size=periods
        )
        
        if not result.get("success", False):
            return {"success": False, "error": result.get("error", "未知错误")}
        
        # 提取 DataFrame
        df = result.get("dataframe")
        if df is None:
            records = result.get("data", [])
            df = pd.DataFrame(records)
        
        if df.empty:
            return {"success": False, "error": "没有获取到数据"}
        
        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "periods": periods,
            "dataframe": df,
            "records": df.to_dict('records'),
            "data_points": len(df)
        }
        
    except Exception as e:
        logger.error(f"获取外汇数据失败: {e}")
        return {"success": False, "error": str(e)}

def _get_returns_data_internal(symbol: str, periods: int = 100, timeframe: str = "1day") -> Dict[str, Any]:
    """
    内部函数：获取收益率数据
    不暴露为工具，仅供内部使用
    """
    # 先获取OHLC数据
    data_result = _get_forex_data_internal(symbol, periods, timeframe)
    
    if not data_result.get("success", False):
        return data_result
    
    df = data_result.get("dataframe")
    if df is None:
        return {"success": False, "error": "数据提取失败"}
    
    # 确保有收盘价列
    if 'close' not in df.columns:
        return {"success": False, "error": "数据缺少收盘价列"}
    
    # 计算收益率
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df = df.dropna(subset=['close'])
    
    if len(df) < 20:
        return {"success": False, "error": "数据量不足"}
    
    returns = df['close'].pct_change().dropna()
    
    return {
        "success": True,
        "symbol": symbol,
        "timeframe": timeframe,
        "periods": periods,
        "returns": returns.tolist(),
        "returns_count": len(returns),
        "summary": {
            "mean": float(returns.mean()) if len(returns) > 0 else 0,
            "std": float(returns.std()) if len(returns) > 0 else 0,
            "min": float(returns.min()) if len(returns) > 0 else 0,
            "max": float(returns.max()) if len(returns) > 0 else 0
        }
    }

# ==================== 对外暴露的工具函数 ====================

@tool 
def get_risk_metrics_data(
    symbol: Annotated[str, "Forex pair symbol"],
    periods: Annotated[int, "Number of periods"] = 252,
    timeframe: Annotated[str, "Timeframe"] = "1day"
) -> str:
    """
    获取风险指标数据（基于 TwelveData）
    
    返回JSON格式包含：
    - 年化波动率
    - 最大回撤
    - 夏普比率
    - VaR值等
    """
    if not TWELVEDATA_AVAILABLE:
        return json.dumps({"success": False, "error": "TwelveData 模块不可用"})
    
    try:
        # 使用内部函数获取收益率数据
        returns_result = _get_returns_data_internal(symbol, periods, timeframe)
        
        if not returns_result.get("success", False):
            return json.dumps(returns_result)
        
        # 计算风险指标
        returns = pd.Series(returns_result.get("returns", []))
        risk_metrics = _calculate_risk_metrics_pure(returns)
        
        return json.dumps({
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "periods": periods,
            "data_points": len(returns),
            "risk_metrics": risk_metrics
        }, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"计算风险指标失败: {e}")
        return json.dumps({"success": False, "error": str(e)})

@tool
def get_volatility_data(
    symbol: Annotated[str, "Forex pair symbol"],
    periods: Annotated[int, "Number of periods"] = 60,
    timeframe: Annotated[str, "Timeframe"] = "1day"
) -> str:
    """
    获取波动率数据（基于 TwelveData）
    
    返回JSON格式包含：
    - 日波动率
    - 年化波动率
    - ATR
    - 滚动波动率等
    """
    if not TWELVEDATA_AVAILABLE:
        return json.dumps({"success": False, "error": "TwelveData 模块不可用"})
    
    try:
        # 使用内部函数获取OHLC数据
        data_result = _get_forex_data_internal(symbol, periods, timeframe)
        
        if not data_result.get("success", False):
            return json.dumps(data_result)
        
        df = data_result.get("dataframe")
        if df is None:
            return json.dumps({"success": False, "error": "数据提取失败"})
        
        # 确保有需要的列
        required_cols = ['open', 'high', 'low', 'close']
        for col in required_cols:
            if col not in df.columns:
                return json.dumps({"success": False, "error": f"缺少{col}列"})
        
        # 转换为数值
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna()
        
        if len(df) < 20:
            return json.dumps({"success": False, "error": "数据量不足"})
        
        # 计算波动率指标
        volatility_metrics = _calculate_volatility_pure(df)
        
        return json.dumps({
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "periods": periods,
            "data_points": len(df),
            "volatility_metrics": volatility_metrics
        }, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"计算波动率数据失败: {e}")
        return json.dumps({"success": False, "error": str(e)})

# ==================== 简化版本 ====================

@tool
def simple_forex_data(
    symbol: Annotated[str, "Forex pair symbol"],
    what: Annotated[str, "What data to get: 'returns', 'ohlc', 'risk', 'volatility'"],
    periods: Annotated[int, "Number of periods"] = 100
) -> str:
    """
    简化的外汇数据获取工具（多功能合一）
    
    参数:
        symbol: 货币对符号
        what: 需要的数据类型
            - 'returns': 收益率数据
            - 'ohlc': OHLC价格数据
            - 'risk': 风险指标数据
            - 'volatility': 波动率数据
        periods: 数据周期数
    
    返回:
        JSON格式的数据
    """
    try:
        if what == "returns":
            # 使用内部函数
            result = _get_returns_data_internal(symbol, periods, "1day")
            return json.dumps(result, ensure_ascii=False)
            
        elif what == "ohlc":
            # 使用内部函数
            result = _get_forex_data_internal(symbol, periods, "1day")
            if result.get("success", False):
                # 只返回必要的数据
                return json.dumps({
                    "success": True,
                    "symbol": symbol,
                    "type": "ohlc",
                    "data_points": result.get("data_points", 0),
                    "data": result.get("records", [])
                }, ensure_ascii=False)
            return json.dumps(result, ensure_ascii=False)
            
        elif what == "risk":
            # 调用已有的风险指标函数
            return get_risk_metrics_data(symbol, periods, "1day")
            
        elif what == "volatility":
            # 调用已有的波动率函数
            return get_volatility_data(symbol, periods, "1day")
            
        else:
            return json.dumps({
                "success": False, 
                "error": f"不支持的数据类型: {what}",
                "supported_types": ["returns", "ohlc", "risk", "volatility"]
            })
            
    except Exception as e:
        logger.error(f"获取数据失败: {e}")
        return json.dumps({"success": False, "error": str(e)})

# ==================== 纯数据计算函数 ====================

def _calculate_risk_metrics_pure(returns: pd.Series) -> Dict:
    """计算风险指标（纯数据）"""
    if len(returns) == 0:
        return {}
    
    metrics = {}
    
    # 基本统计
    metrics['mean_return'] = float(returns.mean())
    metrics['std_return'] = float(returns.std())
    metrics['skewness'] = float(returns.skew())
    metrics['kurtosis'] = float(returns.kurtosis())
    
    # 年化指标
    metrics['annual_return'] = float(metrics['mean_return'] * 252)
    metrics['annual_volatility'] = float(metrics['std_return'] * np.sqrt(252))
    
    # 风险指标
    metrics['var_95'] = float(np.percentile(returns, 5))
    
    # 最大回撤
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    metrics['max_drawdown'] = float(drawdown.min())
    
    # 夏普比率（假设无风险利率2%）
    risk_free_daily = 0.02 / 252
    excess_returns = returns - risk_free_daily
    sharpe = np.sqrt(252) * excess_returns.mean() / returns.std() if returns.std() > 0 else 0
    metrics['sharpe_ratio'] = float(sharpe)
    
    return metrics

def _calculate_volatility_pure(df: pd.DataFrame) -> Dict:
    """计算波动率指标（纯数据）"""
    metrics = {}
    
    # 收益率
    returns = df['close'].pct_change().dropna()
    
    if len(returns) < 20:
        return metrics
    
    # 基本波动率
    metrics['daily_volatility'] = float(returns.std())
    metrics['annual_volatility'] = float(returns.std() * np.sqrt(252))
    
    # 滚动波动率
    rolling_vol_20 = returns.rolling(20).std()
    metrics['current_vol_20d'] = float(rolling_vol_20.iloc[-1] if len(rolling_vol_20) > 0 else 0)
    
    # ATR
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = np.maximum(np.maximum(high_low, high_close), low_close)
    atr_14 = true_range.rolling(14).mean()
    metrics['atr_14'] = float(atr_14.iloc[-1] if len(atr_14) > 0 else 0)
    
    return metrics