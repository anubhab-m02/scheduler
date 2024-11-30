# scheduler/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from integrations.notifications import send_upcoming_session_notifications
from db.db_utils import SessionLocal, User

def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(check_and_send_notifications, 'interval', minutes=30)
    scheduler.start()

def check_and_send_notifications():
    session = SessionLocal()
    users = session.query(User).all()
    session.close()
    for user in users:
        send_upcoming_session_notifications(user.id)
