"""
Narzędzia do konwersji i obsługi dat
"""
from datetime import datetime, date
import time


def unix_to_datetime(unix_timestamp):
    """Konwertuje znacznik czasu Unix na obiekt datetime"""
    return datetime.utcfromtimestamp(unix_timestamp)


def unix_to_date_string(unix_timestamp, format_str='%Y-%m-%d %H:%M:%S'):
    """Konwertuje znacznik czasu Unix na czytelną datę jako string"""
    return unix_to_datetime(unix_timestamp).strftime(format_str)


def date_string_to_unix(date_str, format_str='%Y-%m-%d'):
    """Konwertuje datę w formacie string na znacznik czasu Unix"""
    dt = datetime.strptime(date_str, format_str)
    return int(dt.timestamp())


def today_unix_range():
    """Zwraca zakres unix timestamp dla dzisiejszego dnia (początek i koniec)"""
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())
    
    return int(start_of_day.timestamp()), int(end_of_day.timestamp())


def date_range_to_unix(start_date_str, end_date_str):
    """
    Konwertuje zakres dat string na unix timestamps
    
    Args:
        start_date_str: Data początkowa w formacie 'YYYY-MM-DD'
        end_date_str: Data końcowa w formacie 'YYYY-MM-DD'
    
    Returns:
        tuple: (start_unix, end_unix) gdzie end_unix zawiera cały dzień końcowy
    """
    start_unix = date_string_to_unix(start_date_str)
    end_unix = date_string_to_unix(end_date_str) + 86400  # +1 dzień (86400 sekund)
    
    return start_unix, end_unix


def get_day_start_unix(unix_timestamp):
    """
    Zwraca unix timestamp początku dnia dla podanego timestampu
    
    Args:
        unix_timestamp: Unix timestamp
        
    Returns:
        int: Unix timestamp początku tego samego dnia (00:00:00)
    """
    dt = unix_to_datetime(unix_timestamp)
    start_of_day = datetime.combine(dt.date(), datetime.min.time())
    return int(start_of_day.timestamp())


def get_day_end_unix(unix_timestamp):
    """
    Zwraca unix timestamp końca dnia dla podanego timestampu
    
    Args:
        unix_timestamp: Unix timestamp
        
    Returns:
        int: Unix timestamp końca tego samego dnia (23:59:59)
    """
    dt = unix_to_datetime(unix_timestamp)
    end_of_day = datetime.combine(dt.date(), datetime.max.time())
    return int(end_of_day.timestamp())


def get_current_unix():
    """Zwraca aktualny unix timestamp"""
    return int(time.time())


def format_time_for_display(unix_timestamp):
    """Formatuje unix timestamp do wyświetlenia w GUI"""
    return unix_to_date_string(unix_timestamp, '%Y-%m-%d %H:%M:%S')


def is_same_day(unix_timestamp1, unix_timestamp2):
    """Sprawdza czy dwa unix timestampy są z tego samego dnia"""
    dt1 = unix_to_datetime(unix_timestamp1)
    dt2 = unix_to_datetime(unix_timestamp2)
    return dt1.date() == dt2.date()
