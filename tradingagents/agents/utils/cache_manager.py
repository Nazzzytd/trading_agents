"""
缓存管理工具，用于管理宏观经济数据的缓存
"""
import os
import glob
import pickle
import time
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_cache_info():
    """
    获取缓存统计信息
    """
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cache", "macro")
    
    if not os.path.exists(cache_dir):
        return {"total_files": 0, "total_size_mb": 0, "oldest_cache": None, "newest_cache": None}
    
    cache_files = glob.glob(os.path.join(cache_dir, "*.pkl"))
    
    total_size = 0
    creation_times = []
    
    for file_path in cache_files:
        total_size += os.path.getsize(file_path)
        creation_times.append(os.path.getmtime(file_path))
    
    info = {
        "total_files": len(cache_files),
        "total_size_mb": total_size / (1024 * 1024),
        "oldest_cache": datetime.fromtimestamp(min(creation_times)).strftime('%Y-%m-%d %H:%M') if creation_times else None,
        "newest_cache": datetime.fromtimestamp(max(creation_times)).strftime('%Y-%m-%d %H:%M') if creation_times else None,
        "cache_dir": cache_dir
    }
    
    return info

def clear_old_cache(days_old=7):
    """
    清理过期缓存文件
    """
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cache", "macro")
    
    if not os.path.exists(cache_dir):
        return {"cleaned": 0, "error": "Cache directory does not exist"}
    
    cache_files = glob.glob(os.path.join(cache_dir, "*.pkl"))
    cutoff_time = time.time() - (days_old * 24 * 3600)
    
    cleaned_count = 0
    for file_path in cache_files:
        if os.path.getmtime(file_path) < cutoff_time:
            try:
                os.remove(file_path)
                cleaned_count += 1
            except Exception as e:
                logger.error(f"Error removing cache file {file_path}: {e}")
    
    return {"cleaned": cleaned_count, "remaining": len(glob.glob(os.path.join(cache_dir, "*.pkl")))}

def preview_cache_contents(limit=10):
    """
    预览缓存内容
    """
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cache", "macro")
    
    if not os.path.exists(cache_dir):
        return []
    
    cache_files = glob.glob(os.path.join(cache_dir, "*.pkl"))
    preview_data = []
    
    for i, file_path in enumerate(cache_files[:limit]):
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            
            # 尝试获取数据信息
            if isinstance(data, str):
                # 如果是字符串输出，提取前几行
                preview = data[:200] + "..." if len(data) > 200 else data
            else:
                preview = str(type(data))
            
            preview_data.append({
                "file": os.path.basename(file_path),
                "size_kb": os.path.getsize(file_path) / 1024,
                "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M'),
                "preview": preview
            })
        except Exception as e:
            preview_data.append({
                "file": os.path.basename(file_path),
                "error": str(e)
            })
    
    return preview_data