import smtplib
from email.mime.text import MIMEText
from db.db_utils import SessionLocal
from db.db_models import StudySession, Course, User
from datetime import datetime, timedelta
from config import EMAIL_ADDRESS, EMAIL_PASSWORD, TIMEZONE
import pytz

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email

    # Connect to the SMTP server
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

def send_upcoming_session_notifications(user_id):
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        session.close()
        return

    now = datetime.utcnow()
    upcoming_time = now + timedelta(hours=1)
    sessions = session.query(StudySession).join(Course).filter(
        Course.user_id == user_id,
        StudySession.start_time >= now,
        StudySession.start_time <= upcoming_time,
        StudySession.completed == False,
        StudySession.skipped == False,
        StudySession.rescheduled == False
    ).all()
    session.close()

    for s in sessions:
        local_start_time = s.start_time.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(user.timezone))
        subject = f"Upcoming Study Session: {s.course.name}"
        body = f"""Hi {user.username},

You have a study session for {s.course.name} scheduled at {local_start_time.strftime('%Y-%m-%d %H:%M')} ({user.timezone}).

Happy Studying!

Best regards,
Study Scheduler App
"""
        send_email(user.email, subject, body)
