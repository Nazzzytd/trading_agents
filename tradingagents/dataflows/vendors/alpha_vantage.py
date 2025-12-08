# Import functions from specialized modules
from .alpha_vantage_forex import get_forex
from .alpha_vantage_news import get_news
from .alpha_vantage_economic import get_economic_calendar_formatted

__all__ = [
    'get_forex',
    'get_news',
    'get_economic_calendar_formatted'  # 新增
]
