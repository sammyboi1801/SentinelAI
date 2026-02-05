import time
import threading
from plyer import notification
from datetime import datetime, timedelta

def get_time():
    return datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")

def _notify(msg, wait_sec):
    time.sleep(wait_sec)
    notification.notify(title='Sentinel', message=msg, app_name='Sentinel', timeout=10)

def set_timer(minutes, message="Timer Done"):
    threading.Thread(target=_notify, args=(message, minutes*60), daemon=True).start()
    return f"Timer set for {minutes} mins."

def set_alarm(time_str, message="Alarm"):
    try:
        now = datetime.now()
        tgt = datetime.strptime(time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
        if tgt < now: tgt += timedelta(days=1)
        wait = (tgt - now).total_seconds()
        threading.Thread(target=_notify, args=(message, wait), daemon=True).start()
        return f"Alarm set for {tgt.strftime('%H:%M')}."
    except: return "Invalid format. Use HH:MM."