from apscheduler.schedulers.background import BackgroundScheduler
from integrations.notifications import send_upcoming_session_notifications
from apscheduler.triggers.interval import IntervalTrigger
from db.db_utils import SessionLocal, User
from datetime import datetime, timedelta, time
import streamlit as st
import pytz

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=pytz.UTC)
    trigger = IntervalTrigger(minutes=30)
    scheduler.add_job(
        check_and_send_notifications,
        trigger=trigger,
        id='check_and_send_notifications',
        name='Check and Send Notifications',
        replace_existing=True
    )
    scheduler.start()


def check_and_send_notifications():
    session = SessionLocal()
    users = session.query(User).all()
    session.close()
    for user in users:
        send_upcoming_session_notifications(user.id)

def create_study_schedule(courses, start_date, end_date, pomodoro_interval, pomodoro_break, daily_start_time, daily_study_limit):
    """
    Generate a study schedule based on user courses and preferences.
    
    Args:
        courses (list): List of Course objects.
        start_date (datetime): Start date of the study period.
        end_date (datetime): End date of the study period.
        pomodoro_interval (int): Duration of each Pomodoro session in minutes.
        pomodoro_break (int): Break duration between Pomodoro sessions in minutes.
        daily_start_time (time): Time to start studying each day.
        daily_study_limit (float): Maximum study hours per day.
    
    Returns:
        list: A list of study session dictionaries.
    """
    schedule = []
    total_days = (end_date - start_date).days + 1  # Include end_date
    daily_hours = {}

    # Sort courses by priority (1: High, 2: Medium, 3: Low)
    sorted_courses = sorted(courses, key=lambda x: x.priority)

    # Calculate total study hours per course
    for course in sorted_courses:
        weeks = total_days / 7
        total_hours = course.hours_per_week * weeks
        daily_hours[course.name] = total_hours / total_days if total_days > 0 else 0

    # Generate study sessions using Pomodoro
    for day in range(total_days):
        day_date = start_date + timedelta(days=day)
        current_time = datetime.combine(day_date, daily_start_time)
        study_hours_today = 0

        for course in sorted_courses:
            # Check if the study period extends beyond the course deadline
            if day_date > course.deadline:
                st.warning(f"Study period for {course.name} exceeds its deadline.")
                continue

            hours = daily_hours.get(course.name, 0)
            pomodoros = int((hours * 60) / pomodoro_interval)
            for _ in range(pomodoros):
                if current_time.hour >= 21 or study_hours_today >= daily_study_limit:
                    break
                session_entry = {
                    'course_id': course.id,
                    'start_time': current_time,
                    'duration': pomodoro_interval / 60  # Convert minutes to hours
                }
                schedule.append(session_entry)
                current_time += timedelta(minutes=pomodoro_interval + pomodoro_break)
                study_hours_today += pomodoro_interval / 60  # Convert minutes to hours
    return schedule
