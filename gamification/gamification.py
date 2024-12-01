from db.db_utils import SessionLocal
from db.db_models import StudySession, User
from sqlalchemy import func
import streamlit as st

def assign_badges(user_id):
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        session.close()
        return

    completed_sessions = session.query(func.count(StudySession.id)).filter(
        StudySession.course.has(user_id=user_id),
        StudySession.completed == True
    ).scalar()

    total_hours = session.query(func.sum(StudySession.duration)).filter(
        StudySession.course.has(user_id=user_id),
        StudySession.completed == True
    ).scalar() or 0

    badges = user.badges.split(",") if user.badges else []

    # Define badge criteria
    if completed_sessions >= 50 and "Master Studier" not in badges:
        badges.append("Master Studier")
    if total_hours >= 100 and "Hour Champion" not in badges:
        badges.append("Hour Champion")
    if completed_sessions >= 100 and "Century Scholar" not in badges:
        badges.append("Century Scholar")
    # Add more badges as needed

    user.badges = ",".join(badges)
    session.commit()
    session.close()

def display_badges(user):
    badges = user.badges.split(",") if user.badges else []
    if badges:
        st.sidebar.subheader("🏅 Badges Earned")
        for badge in badges:
            st.sidebar.write(f"• {badge}")
    else:
        st.sidebar.info("Earn badges by completing study sessions!")
