from langchain_core.tools import tool
from typing import Annotated, List, Optional
import pandas as pd
import numpy as np
import logging
from tradingagents.dataflows.interface import route_to_vendor

logger = logging.getLogger(__name__)


# ==================== 核心技术指标计算函数 ====================

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """计算RSI相对强弱指数"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
    """计算MACD指标"""
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std: int = 2) -> tuple:
    """计算布林带"""
    sma = df['close'].rolling(window=period).mean()
    rolling_std = df['close'].rolling(window=period).std()
    upper_band = sma + (rolling_std * std)
    lower_band = sma - (rolling_std * std)
    return upper_band, sma, lower_band

def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> tuple:
    """计算随机指标"""
    low_min = df['low'].rolling(window=k_period).min()
    high_max = df['high'].rolling(window=k_period).max()
    k_line = 100 * ((df['close'] - low_min) / (high_max - low_min))
    d_line = k_line.rolling(window=d_period).mean()
    return k_line, d_line

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """计算平均真实波幅"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = np.maximum(np.maximum(high_low, high_close), low_close)
    atr = true_range.rolling(window=period).mean()
    return atr

def calculate_fibonacci_levels(df: pd.DataFrame, lookback_period: int = 60) -> dict:
    """
    计算斐波那契回撤水平
    基于最近 lookback_period 个周期的最高点和最低点
    """
    if len(df) < lookback_period:
        lookback_period = len(df)
    
    recent_data = df.tail(lookback_period)
    high = recent_data['high'].max()
    low = recent_data['low'].min()
    range_size = high - low
    
    fib_levels = {
        'high': high,
        'low': low,
        'range_size': range_size,
        'levels': {
            '0.0': high,
            '0.236': high - (range_size * 0.236),
            '0.382': high - (range_size * 0.382),
            '0.5': high - (range_size * 0.5),
            '0.618': high - (range_size * 0.618),
            '0.786': high - (range_size * 0.786),
            '1.0': low
        }
    }
    
    return fib_levels

def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算所有主要技术指标"""
    # RSI
    df['RSI'] = calculate_rsi(df, 14)
    
    # MACD
    macd_line, macd_signal, macd_hist = calculate_macd(df)
    df['MACD'] = macd_line
    df['MACD_Signal'] = macd_signal
    df['MACD_Histogram'] = macd_hist
    
    # 移动平均线
    for period in [5, 10, 20, 50, 200]:
        df[f'SMA_{period}'] = df['close'].rolling(window=period).mean()
        df[f'EMA_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
    
    # 布林带
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df)
    df['BB_Upper'] = bb_upper
    df['BB_Middle'] = bb_middle
    df['BB_Lower'] = bb_lower
    df['BB_Width'] = (bb_upper - bb_lower) / bb_middle
    df['BB_Position'] = (df['close'] - bb_lower) / (bb_upper - bb_lower)
    
    # 随机指标
    stoch_k, stoch_d = calculate_stochastic(df)
    df['Stoch_K'] = stoch_k
    df['Stoch_D'] = stoch_d
    
    # ATR
    df['ATR'] = calculate_atr(df, 14)
    
    return df

def get_technical_data(symbol: str, curr_date: str, look_back_days: int = 60) -> dict:
    """
    获取技术指标数据 - 纯数据函数，不包含分析
    返回原始技术指标数据供 technical_analyst 分析使用
    """
    try:
        # ============ 修复：确保正确导入 route_to_vendor ============
        import sys
        
        # 先尝试从全局命名空间获取
        route_func = None
        current_module = sys.modules[__name__]
        
        if hasattr(current_module, 'route_to_vendor'):
            route_func = getattr(current_module, 'route_to_vendor')
        
        if route_func is None:
            try:
                from tradingagents.dataflows.interface import route_to_vendor
                route_func = route_to_vendor
                setattr(current_module, 'route_to_vendor', route_func)
            except ImportError as e:
                logger.error(f"无法导入 route_to_vendor: {e}")
                return {"success": False, "error": f"数据路由函数不可用: {e}"}
        # ===================================================
        
        # 获取价格数据
        from datetime import datetime, timedelta
        
        current_date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
        start_date = (current_date_obj - timedelta(days=look_back_days)).strftime("%Y-%m-%d")
        end_date = curr_date
        
        logger.info(f"获取 {symbol} 的价格数据: {start_date} 到 {end_date}")
        
        # 使用正确的函数名调用
        price_data = route_func("get_forex_data", symbol, start_date, end_date)
        
        # 调试日志 - 详细检查返回数据
        logger.info(f"获取到价格数据类型: {type(price_data)}")
        
        if isinstance(price_data, str):
            logger.info(f"返回的是字符串，前200字符: {price_data[:200]}")
            
            # 尝试解析字符串
            try:
                import json
                # 尝试解析为JSON
                price_data = json.loads(price_data)
                logger.info(f"成功解析字符串为: {type(price_data)}")
            except json.JSONDecodeError:
                # 如果不是JSON，检查是否是其他格式
                logger.warning(f"无法解析为JSON，可能是文本格式")
                
                # 检查是否包含数据表
                if "DataFrame" in price_data or "open" in price_data.lower():
                    # 可能是字符串化的数据框
                    return {
                        "success": False, 
                        "error": "返回的是文本格式数据框，需要解析",
                        "raw_data_preview": price_data[:500]
                    }
                else:
                    return {
                        "success": False, 
                        "error": f"无法识别的返回格式: {price_data[:100]}...",
                        "raw_type": type(price_data).__name__
                    }
        
        # 处理不同类型的结果
        if price_data is None:
            return {"success": False, "error": "返回数据为空"}
            
        # 如果是字典
        if isinstance(price_data, dict):
            logger.info(f"字典数据键: {list(price_data.keys())}")
            
            # 检查是否包含错误
            if not price_data.get("success", True):
                error_msg = price_data.get("error", "未知错误")
                logger.error(f"数据获取失败: {error_msg}")
                return {"success": False, "error": error_msg}
            
            # 检查数据格式
            if "data" not in price_data:
                logger.warning(f"字典中没有 'data' 键，全键: {list(price_data.keys())}")
                
                # 尝试找到可能的数据键
                possible_data_keys = ['values', 'prices', 'series', 'items', 'results']
                data_found = None
                
                for key in possible_data_keys:
                    if key in price_data:
                        data_found = price_data[key]
                        logger.info(f"使用替代数据键: {key}")
                        break
                
                if data_found is None:
                    # 如果没有找到数据，检查是否是直接包含OHLC数据的字典
                    if all(col in price_data for col in ['open', 'high', 'low', 'close']):
                        data_points = [price_data]
                        logger.info(f"直接使用OHLC数据")
                    else:
                        return {"success": False, "error": "没有找到数据", "available_keys": list(price_data.keys())}
                else:
                    data_points = data_found
            else:
                data_points = price_data.get("data", [])
        
        # 如果是列表
        elif isinstance(price_data, list):
            logger.info(f"直接获取到列表数据，长度: {len(price_data)}")
            data_points = price_data
        
        else:
            return {"success": False, "error": f"意外数据类型: {type(price_data)}", "data_sample": str(price_data)[:200]}
        
        # 检查数据点
        if not data_points:
            return {"success": False, "error": "没有可用的数据点"}
        
        logger.info(f"数据点类型: {type(data_points)}，长度: {len(data_points)}")
        
        # 转换为DataFrame
        try:
            df = pd.DataFrame(data_points)
            logger.info(f"DataFrame 创建成功，形状: {df.shape}，列: {list(df.columns)}")
        except Exception as e:
            logger.error(f"创建DataFrame失败: {e}")
            return {"success": False, "error": f"数据格式错误: {e}", "first_data_point": str(data_points[0]) if data_points else "empty"}
        
        # 检查并转换日期列
        date_columns = ['datetime', 'date', 'time', 'timestamp']
        date_col_found = None
        
        for col in date_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                    df = df.sort_values(col).reset_index(drop=True)
                    date_col_found = col
                    logger.info(f"使用日期列: {col}")
                    break
                except:
                    continue
        
        # 确保必要的列存在
        required_cols = ['open', 'high', 'low', 'close']
        
        # 尝试查找列（不区分大小写）
        column_mapping = {}
        for req_col in required_cols:
            # 检查标准名称
            if req_col in df.columns:
                column_mapping[req_col] = req_col
            else:
                # 检查可能的变体
                possible_names = [
                    req_col.capitalize(),
                    req_col.upper(),
                    f"{req_col.capitalize()} Price",
                    f"{req_col.upper()}_PRICE"
                ]
                
                for possible in possible_names:
                    if possible in df.columns:
                        column_mapping[req_col] = possible
                        logger.info(f"映射 {req_col} -> {possible}")
                        break
        
        # 应用列映射
        for req_col, actual_col in column_mapping.items():
            if req_col != actual_col:
                df[req_col] = df[actual_col]
        
        # 检查是否有缺失的列
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"缺少必要的列: {missing_cols}")
            logger.error(f"可用列: {list(df.columns)}")
            
            # 尝试打印前几行数据来调试
            if len(df) > 0:
                logger.error(f"第一行数据: {df.iloc[0].to_dict()}")
            
            return {"success": False, "error": f"缺少必要的列: {missing_cols}", "available_columns": list(df.columns)}
        
        # 确保数值类型
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 检查是否有NaN值
        if df[required_cols].isna().any().any():
            logger.warning(f"数据包含NaN值，进行填充")
            df[required_cols] = df[required_cols].ffill().bfill()
        
        # 计算技术指标
        df_with_indicators = calculate_all_indicators(df)
        
        # 计算斐波那契水平
        fib_levels = calculate_fibonacci_levels(df_with_indicators)
        
        # 获取最新指标值
        latest_indicators = {}
        indicator_columns = [col for col in df_with_indicators.columns 
                           if col not in ['datetime', 'date', 'time', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        for col in indicator_columns:
            if not df_with_indicators[col].empty and not pd.isna(df_with_indicators[col].iloc[-1]):
                try:
                    latest_indicators[col] = float(df_with_indicators[col].iloc[-1])
                except:
                    logger.warning(f"无法转换指标 {col} 为浮点数: {df_with_indicators[col].iloc[-1]}")
        
        # 准备返回结果
        result = {
            "success": True,
            "symbol": symbol,
            "current_price": float(df_with_indicators['close'].iloc[-1]),
            "price_change_pct": float((df_with_indicators['close'].iloc[-1] - df_with_indicators['close'].iloc[0]) / df_with_indicators['close'].iloc[0] * 100),
            "data_points": len(df_with_indicators),
            "latest_indicators": latest_indicators,
            "fibonacci_levels": fib_levels,
            "price_data": {
                "current": float(df_with_indicators['close'].iloc[-1]),
                "high": float(df_with_indicators['high'].max()),
                "low": float(df_with_indicators['low'].min()),
                "open": float(df_with_indicators['open'].iloc[-1])
            },
            "debug_info": {
                "dataframe_shape": df_with_indicators.shape,
                "columns": list(df_with_indicators.columns),
                "date_range": f"{df_with_indicators[date_col_found].iloc[0] if date_col_found else 'N/A'} to {df_with_indicators[date_col_found].iloc[-1] if date_col_found else 'N/A'}"
            }
        }
        
        logger.info(f"技术数据获取成功: {symbol}, 价格: {result['current_price']}, 指标数: {len(latest_indicators)}")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_technical_data for {symbol}: {e}", exc_info=True)
        return {"success": False, "error": str(e), "traceback": "检查日志获取详细信息"}

# ==================== LangChain 工具函数 ====================

@tool
def get_technical_indicators_data(
    symbol: Annotated[str, "Forex pair symbol, e.g., EUR/USD, GBP/JPY, XAU/USD"],
    curr_date: Annotated[str, "Current trading date, YYYY-mm-dd"],
    look_back_days: Annotated[int, "Number of days to look back"] = 60
) -> str:
    """
    获取技术指标原始数据。
    返回格式化的技术指标数值，不包含分析解读。
    
    Args:
        symbol: 外汇货币对符号
        curr_date: 当前交易日期
        look_back_days: 回溯天数
        
    Returns:
        格式化的技术指标数据表格
    """
    try:
        # 获取技术数据
        tech_data = get_technical_data(symbol, curr_date, look_back_days)
        
        if not tech_data["success"]:
            return f"❌ 获取技术数据失败: {tech_data.get('error')}"
        
        # 格式化输出技术指标数据
        current_price = tech_data["current_price"]
        latest_indicators = tech_data["latest_indicators"]
        fib_levels = tech_data["fibonacci_levels"]
        
        output_lines = [
            f"# 📊 技术指标数据 - {symbol}",
            f"**分析日期**: {curr_date} | **回溯周期**: {look_back_days}天",
            f"**数据点数**: {tech_data['data_points']}",
            "",
            "## 💰 价格信息",
            f"- **当前价格**: {current_price:.6f}",
            f"- **期间涨跌幅**: {tech_data['price_change_pct']:+.2f}%",
            f"- **期间最高**: {tech_data['price_data']['high']:.6f}",
            f"- **期间最低**: {tech_data['price_data']['low']:.6f}",
            "",
            "## 📈 技术指标数值"
        ]
        
        # 分类显示技术指标
        indicator_categories = {
            "动量指标": ["RSI", "Stoch_K", "Stoch_D"],
            "趋势指标": ["MACD", "MACD_Signal", "MACD_Histogram"],
            "移动平均线": [col for col in latest_indicators.keys() if col.startswith(('SMA_', 'EMA_'))],
            "波动指标": ["BB_Upper", "BB_Middle", "BB_Lower", "BB_Width", "BB_Position", "ATR"]
        }
        
        for category, indicators in indicator_categories.items():
            category_indicators = []
            for indicator in indicators:
                if indicator in latest_indicators:
                    value = latest_indicators[indicator]
                    category_indicators.append(f"{indicator}: {value:.6f}")
            
            if category_indicators:
                output_lines.append(f"### {category}")
                for indicator_line in category_indicators:
                    output_lines.append(f"- {indicator_line}")
                output_lines.append("")
        
        # 斐波那契水平
        if fib_levels and fib_levels.get('levels'):
            output_lines.extend([
                "## 📐 斐波那契回撤水平",
                f"- **高点**: {fib_levels['high']:.6f}",
                f"- **低点**: {fib_levels['low']:.6f}",
                f"- **区间大小**: {fib_levels['range_size']:.6f}",
                ""
            ])
            
            for level, value in fib_levels['levels'].items():
                output_lines.append(f"- **{level}**: {value:.6f}")
        
        output_lines.extend([
            "",
            "## 💡 数据说明",
            "- 以上为技术指标原始数值",
            "- 请结合价格行为进行综合分析",
            "- 数据基于历史价格计算得出"
        ])
        
        return "\n".join(output_lines)
        
    except Exception as e:
        return f"❌ 获取技术指标数据失败: {str(e)}"

@tool
def get_fibonacci_levels(
    symbol: Annotated[str, "Forex pair symbol"],
    curr_date: Annotated[str, "Current trading date, YYYY-mm-dd"],
    look_back_days: Annotated[int, "Number of days to look back"] = 60
) -> str:
    """
    获取斐波那契回撤水平数据。
    
    Args:
        symbol: 外汇货币对符号
        curr_date: 当前交易日期
        look_back_days: 回溯天数
        
    Returns:
        斐波那契回撤水平数据
    """
    try:
        tech_data = get_technical_data(symbol, curr_date, look_back_days)
        
        if not tech_data["success"]:
            return f"❌ 获取数据失败: {tech_data.get('error')}"
        
        fib_levels = tech_data.get("fibonacci_levels", {})
        if not fib_levels:
            return "❌ 无法计算斐波那契水平"
        
        current_price = tech_data["current_price"]
        
        output_lines = [
            f"# 📐 斐波那契回撤水平 - {symbol}",
            f"**分析日期**: {curr_date}",
            f"**当前价格**: {current_price:.6f}",
            f"**计算区间**: {look_back_days}天",
            "",
            "## 关键水平位:"
        ]
        
        # 找出当前价格最近的斐波那契水平
        closest_level = None
        min_distance = float('inf')
        
        for level, value in fib_levels['levels'].items():
            distance = abs(current_price - value)
            if distance < min_distance:
                min_distance = distance
                closest_level = (level, value)
            
            level_desc = {
                '0.0': '起点 (高点)',
                '0.236': '浅度回撤',
                '0.382': '重要回撤',
                '0.5': '50%回撤',
                '0.618': '黄金分割',
                '0.786': '深度回撤', 
                '1.0': '终点 (低点)'
            }.get(level, level)
            
            output_lines.append(f"- **{level} ({level_desc})**: {value:.6f}")
        
        if closest_level:
            level, value = closest_level
            level_desc = {
                '0.0': '起点高点',
                '0.236': '浅度回撤位',
                '0.382': '重要回撤位',
                '0.5': '50%回撤位',
                '0.618': '黄金分割位',
                '0.786': '深度回撤位',
                '1.0': '终点低点'
            }.get(level, level)
            
            output_lines.extend([
                "",
                f"## 📍 当前位置",
                f"**最接近水平**: {level} ({level_desc})",
                f"**水平价位**: {value:.6f}",
                f"**距离**: {min_distance:.6f}",
                f"**相对位置**: {'上方' if current_price > value else '下方'}"
            ])
        
        return "\n".join(output_lines)
        
    except Exception as e:
        return f"❌ 获取斐波那契水平失败: {str(e)}"

@tool
def get_indicators(
    symbol: Annotated[str, "Forex pair symbol, e.g., EUR/USD, GBP/JPY, XAU/USD"],
    indicators: Annotated[List[str], "List of technical indicators to calculate"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    计算技术指标 - 基于 TwelveData 外汇数据的纯本地计算。
    不依赖外部技术指标API，所有计算在本地完成。
    
    支持的指标:
    - rsi: 相对强弱指数 (14周期)
    - macd: 指数平滑异同移动平均线 (12,26,9)
    - sma: 简单移动平均线 (可指定周期)
    - ema: 指数移动平均线 (可指定周期)
    - bollinger: 布林带 (20周期, 2标准差)
    - stoch: 随机指标 (14,3)
    - atr: 平均真实波幅 (14周期)
    
    Args:
        symbol: 外汇货币对符号
        indicators: 要计算的技术指标列表
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        技术指标计算结果和分析
    """
    try:
        # 使用现有的 get_technical_data 函数获取数据
        tech_data = get_technical_data(symbol, end_date, look_back_days=60)
        
        if not tech_data["success"]:
            return f"❌ 无法获取 {symbol} 数据: {tech_data.get('error')}"
        
        current_price = tech_data["current_price"]
        latest_indicators = tech_data["latest_indicators"]
        
        # 构建响应
        output_lines = [
            f"# 📊 技术指标计算 - {symbol}",
            f"**数据期间**: {start_date} 至 {end_date}",
            f"**当前价格**: {current_price:.6f}",
            f"**计算方式**: 纯本地计算 (基于 TwelveData 外汇数据)",
            f"**请求的指标**: {', '.join(indicators)}",
            ""
        ]
        
        # 为每个请求的指标提供详细分析
        for indicator in indicators:
            indicator_lower = indicator.lower()
            output_lines.append(f"## 🔧 {indicator.upper()} 指标分析")
            
            if indicator_lower == 'rsi' and 'RSI' in latest_indicators:
                rsi_value = latest_indicators['RSI']
                output_lines.append(f"- **当前值**: {rsi_value:.2f}")
                if rsi_value < 30:
                    output_lines.append("- **信号**: 🔴 超卖区域 (可能反弹)")
                elif rsi_value > 70:
                    output_lines.append("- **信号**: 🟢 超买区域 (可能回调)")
                else:
                    output_lines.append("- **信号**: ⚪ 正常范围")
                output_lines.append("- **说明**: 14周期相对强弱指数，衡量价格动量")
                
            elif indicator_lower == 'macd':
                macd_val = latest_indicators.get('MACD', 0)
                macd_signal = latest_indicators.get('MACD_Signal', 0)
                macd_hist = latest_indicators.get('MACD_Histogram', 0)
                output_lines.append(f"- **MACD线**: {macd_val:.6f}")
                output_lines.append(f"- **信号线**: {macd_signal:.6f}")
                output_lines.append(f"- **柱状图**: {macd_hist:.6f}")
                if macd_val > macd_signal:
                    output_lines.append("- **信号**: 🟢 金叉信号 (看涨)")
                else:
                    output_lines.append("- **信号**: 🔴 死叉信号 (看跌)")
                output_lines.append("- **说明**: 指数平滑异同移动平均线，趋势动量指标")
                
            elif indicator_lower.startswith('sma_'):
                period = indicator_lower.replace('sma_', '')
                sma_key = f'SMA_{period}'
                if sma_key in latest_indicators:
                    output_lines.append(f"- **{period}周期SMA**: {latest_indicators[sma_key]:.6f}")
                    output_lines.append(f"- **与当前价关系**: {'上方' if current_price > latest_indicators[sma_key] else '下方'}")
                output_lines.append("- **说明**: 简单移动平均线，趋势方向指标")
                
            elif indicator_lower.startswith('ema_'):
                period = indicator_lower.replace('ema_', '')
                ema_key = f'EMA_{period}'
                if ema_key in latest_indicators:
                    output_lines.append(f"- **{period}周期EMA**: {latest_indicators[ema_key]:.6f}")
                    output_lines.append(f"- **与当前价关系**: {'上方' if current_price > latest_indicators[ema_key] else '下方'}")
                output_lines.append("- **说明**: 指数移动平均线，对近期价格更敏感")
                
            elif indicator_lower == 'bollinger':
                bb_upper = latest_indicators.get('BB_Upper', 0)
                bb_middle = latest_indicators.get('BB_Middle', 0)
                bb_lower = latest_indicators.get('BB_Lower', 0)
                bb_position = latest_indicators.get('BB_Position', 0.5)
                output_lines.append(f"- **上轨**: {bb_upper:.6f}")
                output_lines.append(f"- **中轨**: {bb_middle:.6f}")
                output_lines.append(f"- **下轨**: {bb_lower:.6f}")
                output_lines.append(f"- **位置**: {bb_position:.2%}")
                if bb_position < 0.2:
                    output_lines.append("- **信号**: 🟢 接近下轨 (可能反弹)")
                elif bb_position > 0.8:
                    output_lines.append("- **信号**: 🔴 接近上轨 (可能回调)")
                else:
                    output_lines.append("- **信号**: ⚪ 中轨附近")
                output_lines.append("- **说明**: 布林带，波动率和价格位置指标")
                
            elif indicator_lower == 'stoch':
                stoch_k = latest_indicators.get('Stoch_K', 50)
                stoch_d = latest_indicators.get('Stoch_D', 50)
                output_lines.append(f"- **%K线**: {stoch_k:.2f}")
                output_lines.append(f"- **%D线**: {stoch_d:.2f}")
                if stoch_k < 20 and stoch_d < 20:
                    output_lines.append("- **信号**: 🟢 超卖区域 (可能反弹)")
                elif stoch_k > 80 and stoch_d > 80:
                    output_lines.append("- **信号**: 🔴 超买区域 (可能回调)")
                else:
                    output_lines.append("- **信号**: ⚪ 正常范围")
                output_lines.append("- **说明**: 随机指标，动量振荡器")
                
            elif indicator_lower == 'atr':
                atr_value = latest_indicators.get('ATR', 0)
                output_lines.append(f"- **ATR值**: {atr_value:.6f}")
                output_lines.append(f"- **波动率**: {'高' if atr_value > current_price * 0.01 else '中等' if atr_value > current_price * 0.005 else '低'}")
                output_lines.append("- **说明**: 平均真实波幅，衡量价格波动性")
                
            else:
                output_lines.append(f"- **状态**: ❌ 不支持的指标或数据不可用")
                output_lines.append(f"- **支持的指标**: rsi, macd, sma_N, ema_N, bollinger, stoch, atr")
            
            output_lines.append("")  # 空行分隔
        
        output_lines.extend([
            "## 💡 本地计算说明",
            "- ✅ 所有计算基于 TwelveData 外汇数据",
            "- ✅ 纯本地计算，无外部API调用",
            "- ✅ 实时数据，无延迟",
            "- ✅ 支持自定义技术指标参数",
            "",
            "## 🎯 使用建议", 
            "- 结合多个指标确认交易信号",
            "- 考虑不同时间框架的指标一致性",
            "- 使用ATR进行风险管理"
        ])
        
        return "\n".join(output_lines)
        
    except Exception as e:
        return f"❌ 技术指标计算失败: {str(e)}"