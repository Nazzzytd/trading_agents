"""
技术指标分析工具
集成多个技术指标计算，为交易决策提供数据支持
"""

from langchain_core.tools import tool
from typing import Annotated, List, Dict, Any, Optional
import pandas as pd
import numpy as np
import logging
import json
from datetime import datetime, timedelta
import sys
import os

# ==================== 配置和初始化 ====================
logger = logging.getLogger(__name__)

# 模拟数据模式（当真实数据源不可用时启用）
SIMULATION_MODE = os.environ.get('TECHNICAL_SIMULATION_MODE', 'false').lower() == 'true'

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

# ==================== 数据获取和路由功能 ====================

def get_router_function():
    """
    安全获取路由函数
    支持多种导入方式和模拟模式
    """
    if SIMULATION_MODE:
        logger.info("使用模拟模式，返回模拟路由函数")
        
        def simulated_router(func_name, *args, **kwargs):
            """模拟路由函数，返回模拟数据"""
            symbol = args[0] if len(args) > 0 else kwargs.get('symbol', 'EUR/USD')
            start_date = args[1] if len(args) > 1 else kwargs.get('start_date', '2024-01-01')
            end_date = args[2] if len(args) > 2 else kwargs.get('end_date', '2024-01-15')
            
            logger.info(f"模拟数据: {symbol} from {start_date} to {end_date}")
            return generate_simulated_data(symbol, start_date, end_date)
        
        return simulated_router
    
    # 尝试多种导入方式
    route_func = None
    
    # 方式1: 检查全局变量（如果已经注入）
    if 'route_to_vendor' in globals():
        route_func = globals()['route_to_vendor']
        if callable(route_func) and route_func.__name__ != "route_to_vendor_placeholder":
            logger.info("使用全局路由函数")
            return route_func
    
    # 方式2: 尝试从常见路径导入
    possible_modules = [
        'tradingagents.agents.utils.router',
        'utils.router',
        'router',
        '.router'
    ]
    
    for module_path in possible_modules:
        try:
            module = __import__(module_path, fromlist=['route_to_vendor'])
            route_func = getattr(module, 'route_to_vendor', None)
            if route_func and callable(route_func):
                logger.info(f"成功从 {module_path} 导入路由函数")
                return route_func
        except (ImportError, AttributeError, ModuleNotFoundError):
            continue
    
    # 方式3: 最后尝试从sys.modules查找
    for module_name in list(sys.modules.keys()):
        if 'router' in module_name.lower():
            try:
                module = sys.modules[module_name]
                route_func = getattr(module, 'route_to_vendor', None)
                if route_func and callable(route_func):
                    logger.info(f"从 {module_name} 找到路由函数")
                    return route_func
            except:
                continue
    
    # 如果都失败，返回一个警告函数
    logger.warning("无法找到路由函数，使用降级模式")
    
    def fallback_router(*args, **kwargs):
        return {
            "success": False,
            "error": "路由功能不可用，请检查配置或启用模拟模式",
            "data": []
        }
    
    return fallback_router

def generate_simulated_data(symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """生成模拟价格数据"""
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # 根据货币对设置基准价格
        symbol_lower = symbol.lower()
        if 'jpy' in symbol_lower:
            base_price = 150.0
            volatility = 0.5
        elif 'gold' in symbol_lower or 'xau' in symbol_lower:
            base_price = 2000.0
            volatility = 10.0
        else:
            base_price = 1.1000
            volatility = 0.005
        
        # 生成日期序列
        date_range = pd.date_range(start=start_dt, end=end_dt, freq='D')
        
        data = []
        current_price = base_price
        
        for i, date in enumerate(date_range):
            # 随机价格变动
            change = np.random.normal(0, volatility)
            current_price = current_price * (1 + change)
            
            # 生成OHLC数据
            open_price = current_price * (1 + np.random.normal(0, volatility * 0.5))
            high_price = max(open_price, current_price) + abs(np.random.normal(0, volatility * 0.3))
            low_price = min(open_price, current_price) - abs(np.random.normal(0, volatility * 0.3))
            close_price = current_price
            
            data.append({
                "datetime": date.strftime("%Y-%m-%d"),
                "date": date.strftime("%Y-%m-%d"),
                "open": round(open_price, 6),
                "high": round(high_price, 6),
                "low": round(low_price, 6),
                "close": round(close_price, 6),
                "volume": np.random.randint(1000, 10000)
            })
        
        return {
            "success": True,
            "data": data,
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "simulated": True
        }
    
    except Exception as e:
        logger.error(f"生成模拟数据失败: {e}")
        return {
            "success": False,
            "error": f"模拟数据生成失败: {str(e)}",
            "data": []
        }

def parse_price_data(price_data: Any) -> Dict[str, Any]:
    """统一解析价格数据，支持多种格式"""
    if price_data is None:
        return {"success": False, "error": "数据为空", "data": []}
    
    # 如果是字符串，尝试解析为JSON
    if isinstance(price_data, str):
        try:
            # 检查是否是JSON格式
            if price_data.strip().startswith('{') or price_data.strip().startswith('['):
                price_data = json.loads(price_data)
            else:
                # 尝试解析其他格式
                logger.warning(f"非JSON字符串格式: {price_data[:100]}...")
                return {"success": False, "error": "无法解析的数据格式", "raw_data": price_data[:200]}
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return {"success": False, "error": f"JSON解析失败: {str(e)}", "raw_data": price_data[:200]}
    
    # 处理解析后的数据
    if isinstance(price_data, dict):
        # 检查是否有错误
        if not price_data.get("success", True):
            error_msg = price_data.get("error", "未知错误")
            logger.error(f"数据获取失败: {error_msg}")
            return {"success": False, "error": error_msg, "data": []}
        
        # 提取数据
        if "data" in price_data:
            data_points = price_data["data"]
        else:
            # 尝试查找其他可能的数据键
            possible_keys = ['values', 'prices', 'series', 'items', 'results', 'ohlc']
            data_points = []
            for key in possible_keys:
                if key in price_data and isinstance(price_data[key], list):
                    data_points = price_data[key]
                    logger.info(f"使用替代数据键: {key}")
                    break
            
            if not data_points and all(k in price_data for k in ['open', 'high', 'low', 'close']):
                # 如果字典本身包含OHLC数据
                data_points = [price_data]
    
    elif isinstance(price_data, list):
        data_points = price_data
    
    else:
        return {"success": False, "error": f"不支持的数据类型: {type(price_data)}", "data": []}
    
    if not data_points:
        return {"success": False, "error": "无数据点", "data": []}
    
    return {"success": True, "data": data_points}

def get_technical_data(symbol: str, curr_date: str, look_back_days: int = 60) -> dict:
    """
    获取技术指标数据 - 修复版
    返回原始技术指标数据供分析使用
    """
    try:
        logger.info(f"获取技术数据: {symbol}, 日期: {curr_date}, 回溯: {look_back_days}天")
        
        # 获取路由函数
        route_func = get_router_function()
        
        # 计算日期范围
        current_date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
        start_date = (current_date_obj - timedelta(days=look_back_days)).strftime("%Y-%m-%d")
        end_date = curr_date
        
        # 获取价格数据
        logger.info(f"调用路由函数获取 {symbol} 价格数据: {start_date} 到 {end_date}")
        price_result = route_func("get_forex_data", symbol, start_date, end_date)
        
        # 解析价格数据
        parsed_data = parse_price_data(price_result)
        if not parsed_data["success"]:
            return {"success": False, "error": parsed_data.get("error", "数据解析失败")}
        
        data_points = parsed_data["data"]
        
        if not data_points:
            return {"success": False, "error": "无有效数据点", "debug": {"data_points_length": 0}}
        
        logger.info(f"成功获取 {len(data_points)} 个数据点")
        
        # 转换为DataFrame
        try:
            df = pd.DataFrame(data_points)
            logger.info(f"DataFrame创建成功，形状: {df.shape}")
        except Exception as e:
            logger.error(f"创建DataFrame失败: {e}")
            return {"success": False, "error": f"数据格式错误: {e}"}
        
        # 识别和处理日期列
        date_columns = ['datetime', 'date', 'time', 'timestamp', 'Date', 'DateTime']
        date_col = None
        
        for col in date_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                    df = df.sort_values(col).reset_index(drop=True)
                    date_col = col
                    logger.info(f"使用日期列: {col}")
                    break
                except Exception as e:
                    logger.warning(f"列 {col} 无法转换为日期: {e}")
                    continue
        
        if date_col is None:
            logger.warning("未找到日期列，使用索引作为时间序列")
        
        # 标准化OHLC列名
        column_mapping = {}
        ohlc_columns = ['open', 'high', 'low', 'close']
        
        for target_col in ohlc_columns:
            # 检查标准小写
            if target_col in df.columns:
                column_mapping[target_col] = target_col
            else:
                # 检查可能的变体
                possible_names = [
                    target_col.capitalize(),
                    target_col.upper(),
                    target_col.title(),
                    f"{target_col.capitalize()}Price",
                    f"{target_col.upper()}_PRICE"
                ]
                
                for possible in possible_names:
                    if possible in df.columns:
                        column_mapping[target_col] = possible
                        logger.info(f"映射 {target_col} -> {possible}")
                        break
        
        # 检查是否有缺失的必要列
        missing_cols = [col for col in ohlc_columns if col not in column_mapping]
        if missing_cols:
            logger.error(f"缺少必要的列: {missing_cols}")
            logger.error(f"可用列: {list(df.columns)}")
            
            # 尝试使用第一行数据作为参考
            if len(df) > 0:
                logger.error(f"第一行数据样本: {dict(df.iloc[0])}")
            
            return {"success": False, "error": f"缺少必要的价格列: {missing_cols}"}
        
        # 应用列映射
        for target_col, source_col in column_mapping.items():
            if target_col != source_col:
                df[target_col] = df[source_col]
        
        # 确保数值类型
        for col in ohlc_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 检查并处理NaN值
        nan_count = df[ohlc_columns].isna().sum().sum()
        if nan_count > 0:
            logger.warning(f"发现 {nan_count} 个NaN值，进行填充")
            df[ohlc_columns] = df[ohlc_columns].ffill().bfill()
            
            # 如果还有NaN，删除这些行
            if df[ohlc_columns].isna().any().any():
                initial_len = len(df)
                df = df.dropna(subset=ohlc_columns)
                logger.warning(f"删除 {initial_len - len(df)} 行包含NaN的数据")
        
        if len(df) < 20:  # 需要足够的数据计算指标
            return {"success": False, "error": f"数据不足 ({len(df)} 行)，需要至少20行数据"}
        
        # 计算技术指标
        logger.info("开始计算技术指标...")
        df_with_indicators = calculate_all_indicators(df)
        
        # 计算斐波那契水平
        fib_levels = calculate_fibonacci_levels(df_with_indicators, min(60, len(df_with_indicators)))
        
        # 获取最新指标值
        latest_indicators = {}
        indicator_columns = [col for col in df_with_indicators.columns 
                           if col not in (ohlc_columns + [date_col] + ['volume', 'Volume']) 
                           and pd.api.types.is_numeric_dtype(df_with_indicators[col])]
        
        for col in indicator_columns:
            try:
                value = df_with_indicators[col].iloc[-1]
                if not pd.isna(value):
                    latest_indicators[col] = float(value)
            except Exception as e:
                logger.warning(f"获取指标 {col} 失败: {e}")
        
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
            "metadata": {
                "date_range": f"{df_with_indicators[date_col].iloc[0] if date_col else 'N/A'} 到 {df_with_indicators[date_col].iloc[-1] if date_col else 'N/A'}",
                "indicators_count": len(latest_indicators),
                "simulated": price_result.get("simulated", False) if isinstance(price_result, dict) else False
            }
        }
        
        logger.info(f"技术数据获取成功: {symbol}, 价格: {result['current_price']:.6f}")
        return result
        
    except Exception as e:
        logger.error(f"获取技术数据失败 {symbol}: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

# ==================== LangChain 工具函数 ====================

@tool
def get_technical_indicators_data(
    symbol: Annotated[str, "外汇货币对符号, 例如: EUR/USD, GBP/JPY, XAU/USD"],
    curr_date: Annotated[str, "当前交易日期, 格式 YYYY-mm-dd"],
    look_back_days: Annotated[int, "回溯天数, 默认60天"] = 60
) -> str:
    """
    获取技术指标原始数据。
    返回格式化的技术指标数值，不包含分析解读。
    
    示例:
    get_technical_indicators_data("EUR/USD", "2024-01-15", 30)
    """
    try:
        # 获取技术数据
        tech_data = get_technical_data(symbol, curr_date, look_back_days)
        
        if not tech_data["success"]:
            error_msg = tech_data.get("error", "未知错误")
            return f"❌ 获取技术数据失败: {error_msg}"
        
        # 准备输出
        current_price = tech_data["current_price"]
        latest_indicators = tech_data["latest_indicators"]
        
        output_lines = [
            f"# 📊 技术指标数据 - {symbol}",
            f"**分析日期**: {curr_date} | **回溯周期**: {look_back_days}天",
            f"**数据点数**: {tech_data['data_points']}",
            f"**数据来源**: {'模拟数据' if tech_data.get('metadata', {}).get('simulated') else '真实数据'}",
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
            "移动平均线": sorted([col for col in latest_indicators.keys() 
                               if col.startswith(('SMA_', 'EMA_'))]),
            "波动指标": ["BB_Upper", "BB_Middle", "BB_Lower", "BB_Width", "BB_Position", "ATR"]
        }
        
        for category, indicators in indicator_categories.items():
            category_lines = []
            for indicator in indicators:
                if indicator in latest_indicators:
                    value = latest_indicators[indicator]
                    category_lines.append(f"- **{indicator}**: {value:.6f}")
            
            if category_lines:
                output_lines.append(f"### {category}")
                output_lines.extend(category_lines)
                output_lines.append("")
        
        # 如果指标较少，显示所有可用指标
        if len(latest_indicators) < 5:
            output_lines.append("### 所有可用指标")
            for indicator, value in latest_indicators.items():
                output_lines.append(f"- **{indicator}**: {value:.6f}")
            output_lines.append("")
        
        output_lines.extend([
            "## 💡 使用说明",
            "- 以上为技术指标原始数值",
            "- 请结合价格行为进行综合分析",
            f"- 数据期间: {tech_data.get('metadata', {}).get('date_range', '未知')}",
            ""
        ])
        
        return "\n".join(output_lines)
        
    except Exception as e:
        return f"❌ 获取技术指标数据失败: {str(e)}"

@tool
def get_fibonacci_levels(
    symbol: Annotated[str, "外汇货币对符号"],
    curr_date: Annotated[str, "当前交易日期, 格式 YYYY-mm-dd"],
    look_back_days: Annotated[int, "回溯天数, 默认60天"] = 60
) -> str:
    """
    获取斐波那契回撤水平数据。
    
    示例:
    get_fibonacci_levels("EUR/USD", "2024-01-15", 30)
    """
    try:
        tech_data = get_technical_data(symbol, curr_date, look_back_days)
        
        if not tech_data["success"]:
            error_msg = tech_data.get("error", "未知错误")
            return f"❌ 获取数据失败: {error_msg}"
        
        fib_levels = tech_data.get("fibonacci_levels", {})
        if not fib_levels or 'levels' not in fib_levels:
            return "❌ 无法计算斐波那契水平"
        
        current_price = tech_data["current_price"]
        
        output_lines = [
            f"# 📐 斐波那契回撤水平 - {symbol}",
            f"**分析日期**: {curr_date}",
            f"**当前价格**: {current_price:.6f}",
            f"**计算区间**: {look_back_days}天",
            f"**数据来源**: {'模拟数据' if tech_data.get('metadata', {}).get('simulated') else '真实数据'}",
            "",
            "## 关键水平位:"
        ]
        
        # 找出当前价格最近的斐波那契水平
        closest_level = None
        min_distance = float('inf')
        
        levels = fib_levels['levels']
        sorted_levels = sorted(levels.items(), key=lambda x: float(x[0]))
        
        for level, value in sorted_levels:
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
            
            # 标记当前价格相对于水平的位置
            position = "上方" if current_price > value else "下方" if current_price < value else "正好在"
            output_lines.append(f"- **{level} ({level_desc})**: {value:.6f} [{position}]")
        
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
                "## 📍 当前位置分析",
                f"**最接近水平**: {level} ({level_desc})",
                f"**水平价位**: {value:.6f}",
                f"**距离**: {min_distance:.6f}",
                f"**相对位置**: {'上方' if current_price > value else '下方'}",
                "",
                "## 🎯 交易意义",
                f"- **{level}水平**: {level_desc}",
                "- **作用**: 潜在的支撑/阻力位",
                "- **建议**: 观察价格在该水平的反应"
            ])
        
        return "\n".join(output_lines)
        
    except Exception as e:
        return f"❌ 获取斐波那契水平失败: {str(e)}"

@tool
def get_indicators(
    symbol: Annotated[str, "外汇货币对符号, 例如: EUR/USD, GBP/JPY, XAU/USD"],
    indicators: Annotated[List[str], "要计算的技术指标列表, 例如: ['rsi', 'macd', 'sma_20']"],
    end_date: Annotated[str, "结束日期, 格式 YYYY-mm-dd"],
    look_back_days: Annotated[int, "回溯天数, 默认60天"] = 60
) -> str:
    """
    计算指定技术指标。
    
    支持的指标:
    - rsi: 相对强弱指数 (14周期)
    - macd: 指数平滑异同移动平均线
    - sma_N: 简单移动平均线 (N为周期)
    - ema_N: 指数移动平均线 (N为周期)
    - bollinger: 布林带
    - stoch: 随机指标
    - atr: 平均真实波幅
    
    示例:
    get_indicators("EUR/USD", ["rsi", "macd"], "2024-01-15", 30)
    """
    try:
        # 获取技术数据
        tech_data = get_technical_data(symbol, end_date, look_back_days)
        
        if not tech_data["success"]:
            error_msg = tech_data.get("error", "未知错误")
            return f"❌ 无法获取 {symbol} 数据: {error_msg}"
        
        current_price = tech_data["current_price"]
        latest_indicators = tech_data["latest_indicators"]
        
        # 构建响应
        output_lines = [
            f"# 📊 技术指标计算 - {symbol}",
            f"**结束日期**: {end_date} | **回溯天数**: {look_back_days}",
            f"**当前价格**: {current_price:.6f}",
            f"**数据来源**: {'模拟数据' if tech_data.get('metadata', {}).get('simulated') else '真实数据'}",
            f"**请求指标**: {', '.join(indicators)}",
            ""
        ]
        
        # 为每个请求的指标提供详细分析
        indicators_found = 0
        for indicator in indicators:
            indicator_lower = indicator.lower().strip()
            output_lines.append(f"## 🔧 {indicator.upper()} 指标")
            
            found = False
            
            # RSI
            if indicator_lower == 'rsi' and 'RSI' in latest_indicators:
                rsi_value = latest_indicators['RSI']
                output_lines.append(f"- **当前值**: {rsi_value:.2f}")
                if rsi_value < 30:
                    output_lines.append("- **信号**: 🔴 超卖区域 (可能反弹)")
                    output_lines.append("- **建议**: 考虑买入机会")
                elif rsi_value > 70:
                    output_lines.append("- **信号**: 🟢 超买区域 (可能回调)")
                    output_lines.append("- **建议**: 考虑卖出机会")
                else:
                    output_lines.append("- **信号**: ⚪ 正常范围")
                    output_lines.append("- **建议**: 观望或结合其他指标")
                output_lines.append("- **说明**: 14周期相对强弱指数，衡量价格动量")
                found = True
            
            # MACD
            elif indicator_lower == 'macd':
                macd_val = latest_indicators.get('MACD')
                macd_signal = latest_indicators.get('MACD_Signal')
                if macd_val is not None and macd_signal is not None:
                    output_lines.append(f"- **MACD线**: {macd_val:.6f}")
                    output_lines.append(f"- **信号线**: {macd_signal:.6f}")
                    output_lines.append(f"- **差值**: {(macd_val - macd_signal):.6f}")
                    
                    if macd_val > macd_signal:
                        output_lines.append("- **信号**: 🟢 金叉信号 (看涨)")
                        output_lines.append("- **建议**: 考虑做多")
                    else:
                        output_lines.append("- **信号**: 🔴 死叉信号 (看跌)")
                        output_lines.append("- **建议**: 考虑做空")
                    
                    hist = latest_indicators.get('MACD_Histogram')
                    if hist is not None:
                        output_lines.append(f"- **柱状图**: {hist:.6f}")
                        output_lines.append(f"- **动量**: {'增强' if hist > 0 else '减弱'}")
                    
                    output_lines.append("- **说明**: 趋势动量指标")
                    found = True
            
            # SMA
            elif indicator_lower.startswith('sma_'):
                try:
                    period = indicator_lower.replace('sma_', '')
                    sma_key = f'SMA_{period}'
                    if sma_key in latest_indicators:
                        sma_value = latest_indicators[sma_key]
                        output_lines.append(f"- **{period}周期SMA**: {sma_value:.6f}")
                        
                        relation = "上方" if current_price > sma_value else "下方"
                        distance_pct = abs(current_price - sma_value) / sma_value * 100
                        output_lines.append(f"- **与当前价关系**: 当前价在SMA{relation} ({distance_pct:.2f}%)")
                        
                        if current_price > sma_value:
                            output_lines.append("- **信号**: 🟢 看涨趋势")
                        else:
                            output_lines.append("- **信号**: 🔴 看跌趋势")
                        
                        output_lines.append("- **说明**: 简单移动平均线，趋势方向指标")
                        found = True
                except:
                    pass
            
            # EMA
            elif indicator_lower.startswith('ema_'):
                try:
                    period = indicator_lower.replace('ema_', '')
                    ema_key = f'EMA_{period}'
                    if ema_key in latest_indicators:
                        ema_value = latest_indicators[ema_key]
                        output_lines.append(f"- **{period}周期EMA**: {ema_value:.6f}")
                        
                        relation = "上方" if current_price > ema_value else "下方"
                        output_lines.append(f"- **与当前价关系**: 当前价在EMA{relation}")
                        
                        output_lines.append("- **说明**: 指数移动平均线，对近期价格更敏感")
                        found = True
                except:
                    pass
            
            # 布林带
            elif indicator_lower == 'bollinger' or indicator_lower == 'bb':
                bb_upper = latest_indicators.get('BB_Upper')
                bb_middle = latest_indicators.get('BB_Middle')
                bb_lower = latest_indicators.get('BB_Lower')
                bb_position = latest_indicators.get('BB_Position')
                
                if all(v is not None for v in [bb_upper, bb_middle, bb_lower]):
                    output_lines.append(f"- **上轨**: {bb_upper:.6f}")
                    output_lines.append(f"- **中轨**: {bb_middle:.6f}")
                    output_lines.append(f"- **下轨**: {bb_lower:.6f}")
                    
                    if bb_position is not None:
                        output_lines.append(f"- **位置**: {bb_position:.2%}")
                        if bb_position < 0.2:
                            output_lines.append("- **信号**: 🟢 接近下轨 (可能反弹)")
                            output_lines.append("- **建议**: 潜在买入机会")
                        elif bb_position > 0.8:
                            output_lines.append("- **信号**: 🔴 接近上轨 (可能回调)")
                            output_lines.append("- **建议**: 潜在卖出机会")
                        else:
                            output_lines.append("- **信号**: ⚪ 中轨附近")
                            output_lines.append("- **建议**: 观望")
                    
                    bb_width = latest_indicators.get('BB_Width')
                    if bb_width is not None:
                        output_lines.append(f"- **带宽**: {bb_width:.4f}")
                        output_lines.append(f"- **波动率**: {'高' if bb_width > 0.05 else '中等' if bb_width > 0.02 else '低'}")
                    
                    output_lines.append("- **说明**: 波动率和价格位置指标")
                    found = True
            
            # 随机指标
            elif indicator_lower == 'stoch' or indicator_lower == 'stochastic':
                stoch_k = latest_indicators.get('Stoch_K')
                stoch_d = latest_indicators.get('Stoch_D')
                
                if stoch_k is not None and stoch_d is not None:
                    output_lines.append(f"- **%K线**: {stoch_k:.2f}")
                    output_lines.append(f"- **%D线**: {stoch_d:.2f}")
                    
                    if stoch_k < 20 and stoch_d < 20:
                        output_lines.append("- **信号**: 🟢 超卖区域 (可能反弹)")
                        output_lines.append("- **建议**: 考虑买入")
                    elif stoch_k > 80 and stoch_d > 80:
                        output_lines.append("- **信号**: 🔴 超买区域 (可能回调)")
                        output_lines.append("- **建议**: 考虑卖出")
                    else:
                        output_lines.append("- **信号**: ⚪ 正常范围")
                        output_lines.append("- **建议**: 观望")
                    
                    output_lines.append("- **说明**: 动量振荡器，超买超卖指标")
                    found = True
            
            # ATR
            elif indicator_lower == 'atr':
                atr_value = latest_indicators.get('ATR')
                if atr_value is not None:
                    output_lines.append(f"- **ATR值**: {atr_value:.6f}")
                    
                    atr_pct = atr_value / current_price * 100
                    volatility = '高' if atr_pct > 1.0 else '中等' if atr_pct > 0.5 else '低'
                    output_lines.append(f"- **波动率**: {volatility} ({atr_pct:.2f}%)")
                    
                    output_lines.append("- **说明**: 平均真实波幅，衡量价格波动性")
                    found = True
            
            else:
                output_lines.append(f"- **状态**: ⚠️ 指标 '{indicator}' 未找到或不可用")
                output_lines.append(f"- **可用指标**: {', '.join(sorted(latest_indicators.keys()))}")
            
            if found:
                indicators_found += 1
            
            output_lines.append("")  # 空行分隔
        
        # 如果没有找到任何指标
        if indicators_found == 0:
            output_lines.append("## ⚠️ 未找到请求的指标")
            output_lines.append("可用的指标包括:")
            for indicator in sorted(latest_indicators.keys()):
                output_lines.append(f"- {indicator}: {latest_indicators[indicator]:.6f}")
            output_lines.append("")
        
        output_lines.extend([
            "## 💡 综合分析建议",
            f"- **找到指标**: {indicators_found}/{len(indicators)}",
            "- **建议**: 结合多个指标确认交易信号",
            "- **注意**: 考虑不同时间框架的指标一致性",
            "- **风险**: 使用ATR设置止损水平",
            "",
            "## 📊 数据质量",
            f"- **数据点**: {tech_data['data_points']}",
            f"- **数据期间**: {tech_data.get('metadata', {}).get('date_range', '未知')}",
            f"- **数据来源**: {'模拟数据 - 仅用于测试' if tech_data.get('metadata', {}).get('simulated') else '真实数据'}"
        ])
        
        return "\n".join(output_lines)
        
    except Exception as e:
        return f"❌ 技术指标计算失败: {str(e)}"

# ==================== 辅助函数和测试代码 ====================

def list_available_indicators() -> List[str]:
    """列出所有可用的技术指标"""
    return [
        "RSI - 相对强弱指数",
        "MACD - 指数平滑异同移动平均线",
        "SMA_N - 简单移动平均线 (N=5,10,20,50,200)",
        "EMA_N - 指数移动平均线 (N=5,10,20,50,200)",
        "BB_Upper - 布林带上轨",
        "BB_Middle - 布林中轨",
        "BB_Lower - 布林带下轨",
        "BB_Width - 布林带宽度",
        "BB_Position - 布林带位置",
        "Stoch_K - 随机指标K线",
        "Stoch_D - 随机指标D线",
        "ATR - 平均真实波幅"
    ]

def test_technical_tools():
    """测试技术指标工具"""
    print("🧪 测试技术指标工具...")
    
    # 测试数据获取
    test_symbol = "EUR/USD"
    test_date = "2024-01-15"
    
    print(f"\n1. 测试 {test_symbol} 技术指标数据...")
    result = get_technical_data(test_symbol, test_date, 30)
    
    if result["success"]:
        print(f"✅ 数据获取成功")
        print(f"   价格: {result['current_price']:.6f}")
        print(f"   指标数: {len(result['latest_indicators'])}")
        print(f"   数据点: {result['data_points']}")
        
        # 测试工具函数
        print(f"\n2. 测试工具函数输出...")
        print("-" * 50)
        print(get_technical_indicators_data(test_symbol, test_date, 30))
        print("-" * 50)
    else:
        print(f"❌ 数据获取失败: {result.get('error')}")

# 如果直接运行此文件，执行测试
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("技术指标工具 - 修复版")
    print("=" * 60)
    
    # 显示配置
    print(f"模拟模式: {SIMULATION_MODE}")
    print(f"可用指标: {len(list_available_indicators())} 种")
    
    # 运行测试
    test_technical_tools()