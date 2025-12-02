import requests
import pandas as pd
import os
import time
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TwelveDataForex:
    """TwelveData 外汇数据获取 - 修复参数处理"""
    
    def __init__(self):
        try:
            api_key = os.getenv("TWELVEDATA_API_KEY")
            if not api_key:
                print("WARNING: TWELVEDATA_API_KEY 环境变量未设置，twelvedata功能将不可用")
                self.api_key = None
            else:
                self.api_key = api_key
        except Exception as e:
            print(f"WARNING: 初始化twelvedata失败: {e}")
            self.api_key = None
            
        self.base_url = "https://api.twelvedata.com"
        self.last_request_time = 0
        self.min_request_interval = 7.5
        
        # 支持的外汇对（包含XAU/USD）
        self.supported_pairs = [
            "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", 
            "AUD/USD", "USD/CAD", "NZD/USD", "EUR/GBP",
            "EUR/JPY", "GBP/JPY", "XAU/USD"
        ]

    def get_forex_ohlc(self, symbol: str, start_date: str = None, end_date: str = None, 
                      interval: str = "1day", output_size: int = 100) -> Dict[str, Any]:
        """
        获取外汇OHLC数据 - 修复参数处理
        
        Args:
            symbol: 货币对符号
            start_date: 开始日期 (YYYY-MM-DD) - 可选
            end_date: 结束日期 (YYYY-MM-DD) - 可选  
            interval: 时间间隔 - 默认1day
            output_size: 输出数据点数 - 默认100
        """
        if symbol not in self.supported_pairs:
            return {
                "success": False,
                "error": f"不支持的货币对: {symbol}",
                "supported_pairs": self.supported_pairs
            }
        
        try:
            # 速率限制
            current_time = time.time()
            if current_time - self.last_request_time < self.min_request_interval:
                time.sleep(self.min_request_interval)
            
            # 构建API参数
            params = {
                'symbol': symbol,
                'interval': interval,
                'apikey': self.api_key,
            }
            
            # 根据传入的参数决定使用哪种模式
            if start_date and end_date:
                # 使用日期范围模式
                params['start_date'] = start_date
                params['end_date'] = end_date
                logger.info(f"使用日期范围模式: {start_date} 到 {end_date}")
            else:
                # 使用数据点数模式
                params['outputsize'] = output_size
                logger.info(f"使用数据点数模式: {output_size} 个数据点")
            
            response = requests.get(f"{self.base_url}/time_series", 
                                  params=params, timeout=15)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                
                if 'values' not in data:
                    error_msg = data.get('message', 'Unknown error')
                    if 'invalid syntax' in error_msg.lower():
                        # 处理日期格式问题 - 回退到数据点数模式
                        logger.warning(f"日期模式失败，回退到数据点数模式: {error_msg}")
                        return self._fallback_to_outputsize(symbol, interval, output_size)
                    return {
                        "success": False,
                        "error": f"API错误: {error_msg}",
                        "symbol": symbol
                    }
                
                # 转换为DataFrame
                df = self._parse_to_dataframe(data['values'], symbol)
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "data": df.to_dict('records'),
                    "dataframe": df,  # 同时返回DataFrame用于计算
                    "metadata": {
                        "data_points": len(df),
                        "interval": interval,
                        "source": "twelvedata",
                        "mode": "date_range" if start_date and end_date else "outputsize"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP错误 {response.status_code}",
                    "symbol": symbol
                }
                
        except Exception as e:
            logger.error(f"获取 {symbol} 数据失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol
            }

    def _fallback_to_outputsize(self, symbol: str, interval: str, output_size: int) -> Dict[str, Any]:
        """回退到数据点数模式"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'outputsize': output_size,
                'apikey': self.api_key,
            }
            
            response = requests.get(f"{self.base_url}/time_series", 
                                  params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'values' not in data:
                    error_msg = data.get('message', 'Unknown error')
                    return {
                        "success": False,
                        "error": f"回退模式也失败: {error_msg}",
                        "symbol": symbol
                    }
                
                df = self._parse_to_dataframe(data['values'], symbol)
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "data": df.to_dict('records'),
                    "dataframe": df,
                    "metadata": {
                        "data_points": len(df),
                        "interval": interval,
                        "source": "twelvedata",
                        "mode": "outputsize_fallback"
                    }
                }
            else:
                return {
                    "success": False, 
                    "error": f"回退模式HTTP错误 {response.status_code}",
                    "symbol": symbol
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"回退模式异常: {str(e)}",
                "symbol": symbol
            }

    def _parse_to_dataframe(self, values: List[Dict], symbol: str) -> pd.DataFrame:
        """解析为DataFrame"""
        records = []
        for item in values:
            try:
                record = {
                    'datetime': item.get('datetime'),
                    'open': float(item.get('open', 0)),
                    'high': float(item.get('high', 0)),
                    'low': float(item.get('low', 0)),
                    'close': float(item.get('close', 0)),
                    'volume': int(item.get('volume', 0))
                }
                records.append(record)
            except (ValueError, TypeError) as e:
                logger.warning(f"解析数据记录失败: {item}, 错误: {e}")
                continue
        
        if not records:
            return pd.DataFrame()
            
        df = pd.DataFrame(records)
        if not df.empty:
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.sort_values('datetime').reset_index(drop=True)
        df['symbol'] = symbol
        
        return df

# 全局实例
twelvedata_forex = TwelveDataForex()