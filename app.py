import streamlit as st
from datetime import datetime, timedelta
from typing import List
import pandas as pd

class Course:
    def __init__(self, name: str, deadline: datetime, hours_per_week: float):
        self.name = name
        self.deadline = deadline
        self.hours_per_week = hours_per_week

class StudySession:
    def __init__(self, course: str, start_time: datetime, duration: timedelta):
        self.course = course
        self.start_time = start_time
        self.duration = duration

def create_study_schedule(courses: List[Course], start_date: datetime, end_date: datetime, pomodoro_interval: int = 25, pomodoro_break: int = 5):
    schedule = []
    total_days = (end_date - start_date).days + 1
    daily_hours = {}

    for course in courses:
        weeks = total_days / 7
        total_hours = course.hours_per_week * weeks
        daily_hours[course.name] = total_hours / total_days if total_days > 0 else 0

    for day in range(total_days):
        day_date = start_date + timedelta(days=day)
        current_time = day_date.replace(hour=9, minute=0, second=0, microsecond=0)
        for course in courses:
            hours = daily_hours.get(course.name, 0)
            pomodoros = int((hours * 60) / pomodoro_interval)
            for _ in range(pomodoros):
                if current_time.hour >= 21:
                    break
                session = StudySession(
                    course=course.name,
                    start_time=current_time,
                    duration=timedelta(minutes=pomodoro_interval)
                )
                schedule.append(session)
                current_time += timedelta(minutes=pomodoro_interval + pomodoro_break)
    return schedule

def main():
    st.title("📚 Personalized Study Scheduler with Pomodoro Integration")

    if 'courses' not in st.session_state:
        st.session_state.courses = []

    st.sidebar.header("Add a Course")
    with st.sidebar.form("add_course_form"):
        course_name = st.text_input("Course Name")
        deadline = st.date_input("Deadline", min_value=datetime.today())
        hours_per_week = st.number_input("Hours per Week", min_value=0.0, step=0.5)
        submitted = st.form_submit_button("Add Course")
        if submitted:
            if course_name.strip() == "":
                st.sidebar.error("Course name cannot be empty.")
            else:
                course = Course(
                    name=course_name,
                    deadline=datetime.combine(deadline, datetime.min.time()),
                    hours_per_week=hours_per_week
                )
                st.session_state.courses.append(course)
                st.sidebar.success(f"Added course: {course_name}")

    if st.session_state.courses:
        st.header("📋 Courses Added")
        courses_data = {
            "Course Name": [course.name for course in st.session_state.courses],
            "Deadline": [course.deadline.strftime("%Y-%m-%d") for course in st.session_state.courses],
            "Hours/Week": [course.hours_per_week for course in st.session_state.courses]
        }
        st.table(pd.DataFrame(courses_data))
    else:
        st.info("No courses added yet. Use the sidebar to add your courses.")

    st.header("🗓️ Define Study Period")
    with st.form("study_period_form"):
        start_date = st.date_input("Start Date", datetime.today())
        end_date = st.date_input("End Date", datetime.today() + timedelta(weeks=4))
        if start_date > end_date:
            st.error("Start date must be before end date.")
        submitted = st.form_submit_button("Generate Schedule")
        if submitted:
            if not st.session_state.courses:
                st.error("Please add at least one course before generating the schedule.")
            elif start_date > end_date:
                st.error("Start date must be before end date.")
            else:
                start_dt = datetime.combine(start_date, datetime.min.time())
                end_dt = datetime.combine(end_date, datetime.min.time())
                schedule = create_study_schedule(st.session_state.courses, start_dt, end_dt)
                if schedule:
                    st.session_state.schedule = schedule
                else:
                    st.warning("No study sessions generated. Please check your inputs.")

    if 'schedule' in st.session_state:
        st.header("📅 Study Schedule")
        schedule = st.session_state.schedule
        if schedule:
            schedule_data = {
                "Start Time": [session.start_time.strftime("%Y-%m-%d %H:%M") for session in schedule],
                "Course": [session.course for session in schedule],
                "Duration (mins)": [int(session.duration.total_seconds() / 60) for session in schedule]
            }
            df_schedule = pd.DataFrame(schedule_data)
            st.dataframe(df_schedule)

            csv = df_schedule.to_csv(index=False)
            st.download_button(
                label="📥 Download Schedule as CSV",
                data=csv,
                file_name='study_schedule.csv',
                mime='text/csv',
            )
        else:
            st.warning("No study sessions to display.")

if __name__ == "__main__":
    main()
