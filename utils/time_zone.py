from datetime import datetime, timedelta, timezone

def get_now_time():
    utc_now = datetime.now(timezone.utc)
    moscow_offset = timezone(timedelta(hours=3))
    moscow_time = utc_now.astimezone(moscow_offset)
    return moscow_time

def check_time(end_time):
    if end_time is None:
        return False  # Если end_time отсутствует, возвращаем False
    
    if isinstance(end_time, str):
        try:
            # Преобразование строки в datetime
            end_time = datetime.fromisoformat(end_time)
        except ValueError:
            return False  # Если формат неправильный, возвращаем False
    
    now = get_now_time()
    current_time = end_time - now
    
    # Проверка: время истекло
    if current_time.total_seconds() <= 0:
        return False
    else:
        return current_time