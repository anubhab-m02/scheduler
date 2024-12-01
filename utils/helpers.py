import pytz
from datetime import datetime

def get_user_timezone(user_timezone):
    try:
        return pytz.timezone(user_timezone)
    except pytz.UnknownTimeZoneError:
        return pytz.UTC

def format_datetime(dt, user_timezone):
    tz = get_user_timezone(user_timezone)
    return dt.astimezone(tz).strftime('%Y-%m-%d %H:%M')
