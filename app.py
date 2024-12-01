# app.py

import streamlit as st
from db.db_utils import (
    create_user, get_user, verify_password,
    add_course, get_user_courses,
    add_study_session, create_study_group,
    join_study_group, add_resource,
    add_feedback, SessionLocal, delete_course,
    add_feedback, get_user_feedbacks, 
    update_feedback, remove_feedback
)
from db.db_models import User, Course, StudySession, Feedback, Resource, StudyGroup
from sqlalchemy.orm import joinedload
from integrations.calendar_sync import sync_to_google_calendar
from integrations.todoist_sync import sync_to_todoist
from integrations.notifications import send_upcoming_session_notifications
from gamification.gamification import assign_badges, display_badges
from analytics.suggestions import generate_suggestions
from analytics.sentiment_analysis import analyze_sentiment, analyze_emotions
from nlp.nlp_input import parse_course_input
from scheduler.scheduler import start_scheduler, check_and_send_notifications, create_study_schedule
from utils.helpers import format_datetime
import pandas as pd
import plotly.express as px
import json
from datetime import datetime, timedelta, time
import pytz
import os

# Initialize the scheduler
if 'scheduler_started' not in st.session_state:
    start_scheduler()
    st.session_state.scheduler_started = True

# Page configuration
st.set_page_config(page_title="📚 Personalized Study Scheduler", layout="wide")
st.title("📚 Personalized Study Scheduler with Pomodoro Integration")

# Initialize session state for user authentication
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None

# User Authentication
if not st.session_state.logged_in:
    st.sidebar.header("🔑 Login")
    login_form = st.sidebar.form("login_form")
    username = login_form.text_input("Username")
    password = login_form.text_input("Password", type="password")
    login_submitted = login_form.form_submit_button("Login")
    if login_submitted:
        user = get_user(username)
        if user and verify_password(user, password):
            st.session_state.logged_in = True
            st.session_state.user = user
            st.sidebar.success(f"Logged in as {username}")
        else:
            st.sidebar.error("Invalid username or password.")

    st.sidebar.markdown("---")
    st.sidebar.header("📄 Register")
    register_form = st.sidebar.form("register_form")
    new_username = register_form.text_input("New Username")
    new_email = register_form.text_input("Email")
    new_password = register_form.text_input("New Password", type="password")
    register_submitted = register_form.form_submit_button("Register")
    if register_submitted:
        if get_user(new_username):
            st.sidebar.error("Username already exists.")
        elif not new_username or not new_email or not new_password:
            st.sidebar.error("All fields are required.")
        else:
            user = create_user(new_username, new_email, new_password)
            st.sidebar.success(f"User {new_username} registered successfully! Please log in.")
else:
    st.sidebar.header(f"👋 Welcome, {st.session_state.user.username}!")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.sidebar.success("Logged out successfully.")

    # Sidebar for Adding Courses and Customization Options
    with st.sidebar:
        st.header("🔧 Settings")

        # Update Profile
        st.subheader("👤 Update Profile")
        with st.form("profile_form"):
            email = st.text_input("Email", value=st.session_state.user.email)
            timezone = st.text_input("Timezone", value=st.session_state.user.timezone)
            goals = st.text_area("Goals (comma-separated)", value=st.session_state.user.goals if st.session_state.user.goals else "")
            todoist_token = st.text_input("Todoist API Token", value=st.session_state.user.todoist_api_token if st.session_state.user.todoist_api_token else "")
            submitted_profile = st.form_submit_button("Update Profile")
            if submitted_profile:
                # Update user details
                session = SessionLocal()
                db_user = session.query(User).filter(User.id == st.session_state.user.id).first()
                db_user.email = email
                db_user.timezone = timezone
                db_user.goals = goals
                db_user.todoist_api_token = todoist_token
                session.commit()
                session.close()
                st.sidebar.success("Profile updated successfully!")
                # Update session state
                st.session_state.user.email = email
                st.session_state.user.timezone = timezone
                st.session_state.user.goals = goals
                st.session_state.user.todoist_api_token = todoist_token

        st.markdown("---")

        # Add a Course via Form
        st.subheader("📝 Add a Course")
        with st.form("add_course_form"):
            course_name = st.text_input("Course Name")
            deadline = st.date_input("Deadline", min_value=datetime.today())
            hours_per_week = st.number_input("Hours per Week", min_value=0.0, step=0.5)
            priority = st.selectbox(
                "Priority",
                options=[1, 2, 3],
                format_func=lambda x: {1: "High", 2: "Medium", 3: "Low"}[x]
            )
            submitted_course = st.form_submit_button("Add Course")
            if submitted_course:
                if course_name.strip() == "":
                    st.error("Course name cannot be empty.")
                else:
                    course = add_course(
                        user_id=st.session_state.user.id,
                        name=course_name,
                        deadline=datetime.combine(deadline, datetime.min.time()),
                        hours_per_week=hours_per_week,
                        priority=priority
                    )
                    st.success(f"Added course: {course_name}")

        st.markdown("---")

        # Customization Options
        st.subheader("⚙️ Customization Options")
        with st.form("customization_form_unique"):
            pomodoro_interval = st.number_input(
                "Pomodoro Interval (minutes)",
                min_value=10,
                max_value=60,
                value=25,
                step=1
            )
            pomodoro_break = st.number_input(
                "Pomodoro Break (minutes)",
                min_value=1,
                max_value=30,
                value=5,
                step=1
            )
            daily_start_time = st.time_input("Daily Start Time", value=time(9, 0))
            daily_study_limit = st.number_input(
                "Daily Study Limit (hours)",
                min_value=1.0,
                max_value=24.0,
                value=8.0,
                step=0.5
            )
            submitted_custom = st.form_submit_button("Update Settings")
            if submitted_custom:
                # Save customization settings to session_state
                st.session_state.pomodoro_interval = pomodoro_interval
                st.session_state.pomodoro_break = pomodoro_break
                st.session_state.daily_start_time = daily_start_time
                st.session_state.daily_study_limit = daily_study_limit
                st.sidebar.success("Customization settings updated.")

        st.markdown("---")

        # Manage Study Groups
        st.subheader("👥 Manage Study Groups")
        with st.form("study_group_form"):
            group_action = st.selectbox("Action", ["Create Group", "Join Group"])
            group_name = st.text_input("Group Name")
            submitted_group = st.form_submit_button("Submit")
            if submitted_group:
                if group_name.strip() == "":
                    st.error("Group name cannot be empty.")
                else:
                    if group_action == "Create Group":
                        group = create_study_group(st.session_state.user.id, group_name)
                        if group:
                            st.success(f"Study group '{group_name}' created and joined successfully!")
                        else:
                            st.error("Group already exists.")
                    elif group_action == "Join Group":
                        join_study_group(st.session_state.user.id, group_name)
                        st.success(f"Joined study group '{group_name}' successfully!")

        # Add Resource
        st.subheader("📚 Add a Resource")
        with st.form("resource_form"):
            resource_title = st.text_input("Resource Title")
            resource_url = st.text_input("Resource URL")
            submitted_resource = st.form_submit_button("Add Resource")
            if submitted_resource:
                if resource_title.strip() == "" or resource_url.strip() == "":
                    st.error("Both title and URL are required.")
                else:
                    add_resource(st.session_state.user.id, resource_title, resource_url)
                    st.success("Resource added successfully!")

        # Sync with Google Calendar
        st.markdown("---")
        st.subheader("🔄 Sync Integrations")
        if st.button("📅 Sync with Google Calendar"):
            success, message = sync_to_google_calendar(st.session_state.user.id)
            if success:
                st.success(message)
            else:
                st.error(message)

        if st.button("📝 Sync with Todoist"):
            success, message = sync_to_todoist(st.session_state.user.id)
            if success:
                st.success(message)
            else:
                st.error(message)

        else:
            st.info("Please log in to access the study scheduler.")

    if st.session_state.logged_in:
        # Fetch user courses from the database
        # def get_user_courses_display(user_id):
        #     session = SessionLocal()
        #     courses = session.query(Course).filter(Course.user_id == user_id).all()
        #     session.close()
        #     return courses

        user_courses = get_user_courses(st.session_state.user.id)

        # Display added courses
        if user_courses:
            st.header("📋 Courses Added")
            courses_data = {
                "Course ID": [course.id for course in user_courses],
                "Course Name": [course.name for course in user_courses],
                "Deadline": [course.deadline.strftime("%Y-%m-%d") for course in user_courses],
                "Hours/Week": [course.hours_per_week for course in user_courses],
                "Priority": [ {1: "High", 2: "Medium", 3: "Low"}[course.priority] for course in user_courses]
            }
            df_courses = pd.DataFrame(courses_data)
            st.table(df_courses)

            # Section to Delete Courses
            st.subheader("🗑️ Delete Courses")
            # Create options in the format "Course Name (ID: course.id)"
            delete_options = [f"{course.name} (ID: {course.id})" for course in user_courses]
            selected_courses = st.multiselect("Select courses to delete:", options=delete_options)

            if st.button("Delete Selected Courses"):
                if selected_courses:
                    for course_option in selected_courses:
                        # Extract course ID from the option string
                        try:
                            course_id_str = course_option.split("ID: ")[1].rstrip(")")
                            course_id = int(course_id_str)
                        except (IndexError, ValueError):
                            st.error(f"Invalid course selection: {course_option}")
                            continue
                        success = delete_course(user_id=st.session_state.user.id, course_id=course_id)
                        if success:
                            st.success(f"Deleted course: {course_option.split(' (ID:')[0]}")
                        else:
                            st.error(f"Failed to delete course: {course_option.split(' (ID:')[0]}")
                    # Refresh the courses list after deletion
                    user_courses = get_user_courses(st.session_state.user.id)
                    st.rerun()
                else:
                    st.warning("No courses selected for deletion.")
        else:
            st.info("No courses added yet. Use the sidebar to add your courses.")

        st.header("🗓️ Define Study Period")
        with st.form("study_period_form"):
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", datetime.today())
            with col2:
                end_date = st.date_input("End Date", datetime.today() + timedelta(weeks=4))
            if start_date > end_date:
                st.error("Start date must be before end date.")
            submitted_schedule = st.form_submit_button("Generate Schedule")
            if submitted_schedule:
                if not user_courses:
                    st.error("Please add at least one course before generating the schedule.")
                elif start_date > end_date:
                    st.error("Start date must be before end date.")
                else:
                    # Retrieve customization settings from session_state or use defaults
                    pomodoro_interval = st.session_state.get('pomodoro_interval', 25)
                    pomodoro_break = st.session_state.get('pomodoro_break', 5)
                    daily_start_time = st.session_state.get('daily_start_time', time(9, 0))
                    daily_study_limit = st.session_state.get('daily_study_limit', 8.0)

                    # Generate schedule
                    schedule = create_study_schedule(
                        courses=user_courses,
                        start_date=datetime.combine(start_date, daily_start_time),
                        end_date=datetime.combine(end_date, time(23, 59)),
                        pomodoro_interval=pomodoro_interval,
                        pomodoro_break=pomodoro_break,
                        daily_start_time=daily_start_time,
                        daily_study_limit=daily_study_limit
                    )
                    if schedule:
                        # Add study sessions to the database
                        for s in schedule:
                            add_study_session(
                                course_id=s['course_id'],
                                start_time=s['start_time'],
                                duration=s['duration']
                            )
                        st.success("Study schedule generated successfully!")
                    else:
                        st.warning("No study sessions generated. Please check your inputs.")

        # Function to create study schedule
        def create_study_schedule(courses, start_date, end_date, pomodoro_interval, pomodoro_break, daily_start_time, daily_study_limit):
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

        # Display Study Schedule with Interactive Calendar View
        
        def display_study_schedule(user_id):
            session = SessionLocal()
            try:
                # Eagerly load the 'course' relationship using joinedload
                sessions = session.query(StudySession).options(joinedload(StudySession.course)).filter(
                    Course.user_id == user_id
                ).all()

                if sessions:
                    schedule_data = {
                        "Course": [s.course.name for s in sessions],
                        "Start Time": [s.start_time for s in sessions],
                        "End Time": [s.start_time + timedelta(hours=s.duration) for s in sessions],
                        "Completed": [s.completed for s in sessions]
                    }
                    df_schedule = pd.DataFrame(schedule_data)
                else:
                    df_schedule = pd.DataFrame()

            except Exception as e:
                st.error(f"Error fetching study sessions: {e}")
                df_schedule = pd.DataFrame()
            finally:
                session.close()

            if not df_schedule.empty:
                # Create Gantt Chart using Plotly
                fig = px.timeline(
                    df_schedule,
                    x_start="Start Time",
                    x_end="End Time",
                    y="Course",
                    color="Course",
                    title="Study Schedule Timeline",
                    labels={"Start Time": "Start Time", "End Time": "End Time", "Course": "Course"}
                )
                fig.update_yaxes(categoryorder="total ascending")
                fig.update_layout(
                    xaxis_title="Date and Time",
                    yaxis_title="Course",
                    legend_title="Courses",
                    hovermode="closest",
                    height=600
                )
                st.plotly_chart(fig, use_container_width=True)

                # Optionally, download the schedule as CSV
                with st.expander("📥 Download Schedule"):
                    csv = df_schedule.to_csv(index=False)
                    st.download_button(
                        label="Download Schedule as CSV",
                        data=csv,
                        file_name='study_schedule.csv',
                        mime='text/csv',
                    )
            else:
                st.warning("No study sessions to display.")

        display_study_schedule(st.session_state.user.id)

        # Study Session Log
        def mark_session(session_id, status):
            session_db = SessionLocal()
            study_session = session_db.query(StudySession).filter(StudySession.id == session_id).first()
            if study_session:
                if status == "Completed":
                    study_session.completed = True
                elif status == "Skipped":
                    study_session.skipped = True
                elif status == "Rescheduled":
                    study_session.rescheduled = True
                session_db.commit()
            session_db.close()

        def display_study_sessions(user_id):
            try:
                with SessionLocal() as session:
                    # Eagerly load the 'course' relationship using joinedload
                    sessions = session.query(StudySession).options(joinedload(StudySession.course)).join(Course).filter(
                        Course.user_id == user_id
                    ).all()

                    if sessions:
                        schedule_data = {
                            "Session ID": [s.id for s in sessions],
                            "Course": [s.course.name for s in sessions],
                            "Start Time": [s.start_time for s in sessions],
                            "Duration (hrs)": [s.duration for s in sessions],
                            "Completed": [s.completed for s in sessions],
                            "Skipped": [s.skipped for s in sessions],
                            "Rescheduled": [s.rescheduled for s in sessions]
                        }
                        df_sessions = pd.DataFrame(schedule_data)
                    else:
                        df_sessions = pd.DataFrame()

                if not df_sessions.empty:
                    st.subheader("📝 Study Session Log")
                    st.dataframe(df_sessions)

                    # Interactive controls to update session status
                    for s in sessions:
                        if not (s.completed or s.skipped or s.rescheduled):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button(f"✅ Mark Completed {s.id}"):
                                    mark_session(s.id, "Completed")
                                    assign_badges(user_id)
                                    st.experimental_rerun()
                            with col2:
                                if st.button(f"❌ Mark Skipped {s.id}"):
                                    mark_session(s.id, "Skipped")
                                    st.experimental_rerun()
                            with col3:
                                if st.button(f"🔄 Mark Rescheduled {s.id}"):
                                    mark_session(s.id, "Rescheduled")
                                    st.experimental_rerun()
                else:
                    st.info("No study sessions logged yet.")
            except Exception as e:
                st.error(f"Error displaying study sessions: {e}")

        # Performance Metrics
        def display_performance_metrics(user_id):
            session_db = SessionLocal()
            sessions = session_db.query(StudySession).join(Course).filter(
                Course.user_id == user_id,
                StudySession.completed == True
            ).all()
            session_db.close()

            if sessions:
                total_sessions = len(sessions)
                completed_sessions = sum(1 for s in sessions if s.completed)
                skipped_sessions = sum(1 for s in sessions if s.skipped)
                rescheduled_sessions = sum(1 for s in sessions if s.rescheduled)
                total_study_hours = sum(s.duration for s in sessions)

                st.subheader("📈 Performance Metrics")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Sessions", total_sessions)
                col2.metric("Completed Sessions", completed_sessions)
                col3.metric("Skipped Sessions", skipped_sessions)
                col4.metric("Total Study Hours", f"{total_study_hours:.2f} hrs")

                # Visualization: Study Hours Over Time
                df = pd.DataFrame({
                    "Date": [s.start_time.date() for s in sessions],
                    "Hours": [s.duration for s in sessions]
                })
                if not df.empty:
                    df_grouped = df.groupby("Date").sum().reset_index()
                    fig = px.line(df_grouped, x="Date", y="Hours", title="Study Hours Over Time")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No completed study sessions to display.")
            else:
                st.info("No study sessions to display.")

        display_performance_metrics(st.session_state.user.id)

        # Display Badges
        display_badges(st.session_state.user)

        # Study Suggestions
        st.subheader("💡 Study Tips & Suggestions")
        suggestions = generate_suggestions(st.session_state.user.id)
        if suggestions:
            for tip in suggestions:
                st.write(f"- {tip}")
        else:
            st.info("Keep up the great work! Your study habits are on track.")

        # Collect and Display Feedback
        def collect_feedback(user_id):
            st.subheader("📝 Submit Feedback or Journal Entry")
            with st.form("feedback_form"):
                feedback = st.text_area("Your Feedback/Journal Entry", height=150)
                submitted_feedback = st.form_submit_button("Submit")
                if submitted_feedback:
                    if feedback.strip() == "":
                        st.error("Feedback cannot be empty.")
                    else:
                        # Perform sentiment and emotion analysis
                        sentiment_results = analyze_sentiment(feedback)
                        emotions = analyze_emotions(feedback)
                        
                        # Store feedback with sentiment and emotions
                        add_feedback(
                            user_id=user_id,
                            content=feedback,
                            sentiment=sentiment_results['compound'],
                            sentiment_label=sentiment_results['sentiment'],
                            emotions=emotions,
                            timestamp=datetime.utcnow()
                        )
                        st.success("Feedback submitted successfully!")
                        
                        # Provide suggestions based on sentiment
                        if sentiment_results['compound'] < -0.5:
                            st.warning("It seems you're feeling stressed. Consider taking a short break or practicing relaxation techniques.")
                        elif sentiment_results['compound'] > 0.5:
                            st.success("Great to hear you're feeling good! Keep up the positive energy!")
                        else:
                            st.info("Thank you for your feedback!")
        collect_feedback(st.session_state.user.id)

        def display_feedback(user_id):
            feedbacks = get_user_feedbacks(user_id)
            
            st.subheader("📊 Your Feedback History")
            if feedbacks:
                # Prepare data for visualization
                data = []
                for fb in feedbacks:
                    emotions = json.loads(fb.emotions) if fb.emotions else {}
                    data.append({
                        "ID": fb.id,
                        "Content": fb.content,
                        "Sentiment Score": fb.sentiment,
                        "Sentiment": fb.sentiment_label,
                        "Emotions": emotions,
                        "Timestamp": fb.timestamp
                    })
                
                df_feedback = pd.DataFrame(data)
                
                # Display Feedback Entries with Options to Edit/Delete
                st.dataframe(df_feedback[['ID', 'Content', 'Sentiment', 'Emotions', 'Timestamp']].sort_values(by='Timestamp', ascending=False))
                
                # Interactive Controls to Edit/Delete Feedback
                for index, row in df_feedback.iterrows():
                    st.markdown(f"**Feedback ID:** {row['ID']}")
                    st.write(f"**Content:** {row['Content']}")
                    st.write(f"**Sentiment:** {row['Sentiment']} (Score: {row['Sentiment Score']})")
                    st.write(f"**Emotions:** {row['Emotions']}")
                    st.write(f"**Submitted At:** {row['Timestamp']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Edit Feedback {row['ID']}"):
                            edit_feedback(user_id, row['ID'], row['Content'])
                    with col2:
                        if st.button(f"Delete Feedback {row['ID']}"):
                            delete_feedback(user_id, row['ID'])
                            st.experimental_rerun()
                    
                    st.markdown("---")
                
                # Visualize Sentiment Distribution
                st.markdown("### Sentiment Distribution")
                sentiment_counts = df_feedback['Sentiment'].value_counts().reset_index()
                sentiment_counts.columns = ['Sentiment', 'Count']
                fig_sentiment = px.pie(sentiment_counts, names='Sentiment', values='Count', title='Sentiment Distribution')
                st.plotly_chart(fig_sentiment, use_container_width=True)
                
                # Visualize Sentiment Over Time
                st.markdown("### Sentiment Over Time")
                df_feedback['Date'] = df_feedback['Timestamp'].dt.date
                sentiment_over_time = df_feedback.groupby('Date')['Sentiment Score'].mean().reset_index()
                fig_trend = px.line(sentiment_over_time, x='Date', y='Sentiment Score', title='Average Sentiment Over Time', markers=True)
                fig_trend.add_hline(y=0, line_dash="dash", line_color="red")
                st.plotly_chart(fig_trend, use_container_width=True)
                
                # Visualize Emotion Distribution
                st.markdown("### Emotion Distribution")
                all_emotions = {}
                for emotions in df_feedback['Emotions']:
                    for emotion, score in emotions.items():
                        all_emotions[emotion] = all_emotions.get(emotion, 0) + score
                if all_emotions:
                    df_emotions = pd.DataFrame(list(all_emotions.items()), columns=['Emotion', 'Total Score'])
                    fig_emotions = px.bar(df_emotions, x='Emotion', y='Total Score', title='Total Emotion Scores', color='Emotion')
                    st.plotly_chart(fig_emotions, use_container_width=True)
                
                # Provide actionable insights based on feedback
                st.markdown("### Insights")
                positive_feedback = df_feedback[df_feedback['Sentiment'] == 'Positive']
                negative_feedback = df_feedback[df_feedback['Sentiment'] == 'Negative']
                
                st.write(f"**Total Positive Feedback:** {len(positive_feedback)}")
                st.write(f"**Total Negative Feedback:** {len(negative_feedback)}")
                
                if len(negative_feedback) > len(positive_feedback):
                    st.warning("It seems you've had more negative experiences recently. Consider reviewing your study habits or taking breaks to improve your well-being.")
                elif len(positive_feedback) > len(negative_feedback):
                    st.success("Great job! You've had more positive experiences. Keep up the good work!")
                else:
                    st.info("Your feedback is balanced. Keep tracking your study sessions to maintain or improve your study habits.")
            else:
                st.info("No feedback submitted yet.")
                
        display_feedback(st.session_state.user.id)

        def edit_feedback(user_id, feedback_id, current_content):
            st.subheader(f"✏️ Edit Feedback ID: {feedback_id}")
            new_content = st.text_area("Update Your Feedback/Journal Entry", value=current_content, height=150)
            if st.button("Save Changes"):
                if new_content.strip() == "":
                    st.error("Feedback cannot be empty.")
                else:
                    # Re-analyze sentiment and emotions
                    sentiment_results = analyze_sentiment(new_content)
                    emotions = analyze_emotions(new_content)
                    
                    # Update feedback in the database
                    update_feedback(user_id, feedback_id, new_content, sentiment_results, emotions)
                    st.success("Feedback updated successfully!")
                    st.experimental_rerun()

        def delete_feedback(user_id, feedback_id):
            result = remove_feedback(user_id, feedback_id)
            if result:
                st.success("Feedback deleted successfully!")
            else:
                st.error("Failed to delete feedback.")

        # Display Resources
        def display_resources(user_id):
            session_db = SessionLocal()
            resources = session_db.query(Resource).filter(Resource.user_id == user_id).all()
            session_db.close()

            st.subheader("📖 Your Resources")
            if resources:
                for res in resources:
                    st.markdown(f"- [{res.title}]({res.url})")
            else:
                st.info("No resources added yet.")

        display_resources(st.session_state.user.id)

        # Display Group Resources
        def display_group_resources(user_id):
            session_db = SessionLocal()
            groups = session_db.query(StudyGroup).join(StudyGroup.members).filter(User.id == user_id).all()
            if not groups:
                session_db.close()
                return
            st.subheader("🔗 Group Resources")
            for group in groups:
                st.markdown(f"**Group: {group.name}**")
                for member in group.members:
                    for res in member.resources:
                        st.markdown(f"- [{res.title}]({res.url}) (by {member.username})")
            session_db.close()

        display_group_resources(st.session_state.user.id)

        # Recommendations
        def display_recommendations(user_id):
            suggestions = generate_suggestions(user_id)
            if suggestions:
                st.subheader("🤖 Recommended Study Times")
                for idx, time_hour in enumerate(suggestions, 1):
                    if isinstance(time_hour, (int, float)):
                        try:
                            hour = int(time_hour)
                            minute = int((time_hour - hour) * 60)
                            period = "AM" if hour < 12 else "PM"
                            display_hour = hour if 1 <= hour <= 12 else hour - 12 if hour > 12 else 12
                            st.write(f"{idx}. {display_hour}:{minute:02d} {period}")
                        except ValueError:
                            st.warning(f"{idx}. Invalid time format: {time_hour}")
                    elif isinstance(time_hour, str):
                        st.info(f"{idx}. {time_hour}")
                    else:
                        st.warning(f"{idx}. Unknown suggestion type.")
            else:
                st.info("Provide more completed study sessions to receive study time recommendations.")

        display_recommendations(st.session_state.user.id)
