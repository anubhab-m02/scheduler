from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from .db_models import Base, User, Course, StudySession, StudyGroup, Resource, Feedback
import bcrypt
from datetime import datetime, timezone

# Initialize the database engine and session
engine = create_engine('sqlite:///study_scheduler.db')  # Update if using PostgreSQL
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

# User-related functions
def create_user(username, email, password):
    session = SessionLocal()
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(username=username, email=email, password=hashed_password)
    session.add(user)
    session.commit()
    session.close()
    return user

def get_user(username):
    session = SessionLocal()
    user = session.query(User).filter(User.username == username).first()
    session.close()
    return user

def verify_password(user, password):
    return bcrypt.checkpw(password.encode(), user.password.encode())

# Course-related functions
def add_course(user_id, name, deadline, hours_per_week, priority=1):
    session = SessionLocal()
    course = Course(
        name=name,
        deadline=deadline,
        hours_per_week=hours_per_week,
        priority=priority,
        user_id=user_id
    )
    session.add(course)
    session.commit()
    session.close()
    return course

def get_user_courses(user_id):
    session = SessionLocal()
    courses = session.query(Course).filter(Course.user_id == user_id).all()
    session.close()
    return courses

# StudySession-related functions
def add_study_session(course_id, start_time, duration):
    session = SessionLocal()
    study_session = StudySession(
        course_id=course_id,
        start_time=start_time,
        duration=duration
    )
    session.add(study_session)
    session.commit()
    session.close()
    return study_session

# StudyGroup-related functions
def create_study_group(user_id, group_name):
    session = SessionLocal()
    existing_group = session.query(StudyGroup).filter(StudyGroup.name == group_name).first()
    if existing_group:
        session.close()
        return None  # Group already exists
    group = StudyGroup(name=group_name)
    user = session.query(User).filter(User.id == user_id).first()
    group.members.append(user)
    session.add(group)
    session.commit()
    session.close()
    return group

def join_study_group(user_id, group_name):
    session = SessionLocal()
    group = session.query(StudyGroup).filter(StudyGroup.name == group_name).first()
    user = session.query(User).filter(User.id == user_id).first()
    if group and user not in group.members:
        group.members.append(user)
        session.commit()
    session.close()

# Resource-related functions
def add_resource(user_id, title, url):
    session = SessionLocal()
    resource = Resource(title=title, url=url, user_id=user_id)
    session.add(resource)
    session.commit()
    session.close()
    return resource

# Feedback-related functions
Feedback.metadata.create_all(bind=engine)

def add_feedback(user_id: int, content: str, sentiment: float, sentiment_label: str, emotions: dict, timestamp: datetime):
    """
    Add a feedback entry to the database.

    Args:
        user_id (int): The ID of the user submitting feedback.
        content (str): The feedback content.
        sentiment (float): The compound sentiment score.
        sentiment_label (str): The sentiment category ('Positive', 'Negative', 'Neutral').
        emotions (dict): The emotion scores.
        timestamp (datetime): The time of feedback submission.
    """
    session = SessionLocal()
    try:
        feedback_entry = Feedback(
            user_id=user_id,
            content=content,
            sentiment=sentiment,
            sentiment_label=sentiment_label,
            emotions=json.dumps(emotions),
            timestamp=timestamp
        )
        session.add(feedback_entry)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        st.error(f"Error saving feedback: {e}")
    finally:
        session.close()

def get_user_feedbacks(user_id: int):
    """
    Retrieve all feedback entries for a specific user.

    Args:
        user_id (int): The ID of the user.

    Returns:
        list: A list of Feedback objects.
    """
    session = SessionLocal()
    try:
        feedbacks = session.query(Feedback).filter(Feedback.user_id == user_id).order_by(Feedback.timestamp.desc()).all()
        return feedbacks
    except SQLAlchemyError as e:
        st.error(f"Error retrieving feedbacks: {e}")
        return []
    finally:
        session.close()

def update_feedback(user_id: int, feedback_id: int, new_content: str, sentiment_results: dict, emotions: dict):
    """
    Update a feedback entry in the database.

    Args:
        user_id (int): The ID of the user.
        feedback_id (int): The ID of the feedback to update.
        new_content (str): The updated feedback content.
        sentiment_results (dict): The updated sentiment analysis results.
        emotions (dict): The updated emotion analysis results.
    """
    session = SessionLocal()
    try:
        feedback_entry = session.query(Feedback).filter(Feedback.id == feedback_id, Feedback.user_id == user_id).first()
        if feedback_entry:
            feedback_entry.content = new_content
            feedback_entry.sentiment = sentiment_results['compound']
            feedback_entry.sentiment_label = sentiment_results['sentiment']
            feedback_entry.emotions = json.dumps(emotions)
            feedback_entry.timestamp = datetime.utcnow()
            session.commit()
        else:
            st.error("Feedback entry not found or unauthorized.")
    except SQLAlchemyError as e:
        session.rollback()
        st.error(f"Error updating feedback: {e}")
    finally:
        session.close()

def remove_feedback(user_id: int, feedback_id: int) -> bool:
    """
    Remove a feedback entry from the database.

    Args:
        user_id (int): The ID of the user.
        feedback_id (int): The ID of the feedback to remove.

    Returns:
        bool: True if deletion was successful, False otherwise.
    """
    session = SessionLocal()
    try:
        feedback_entry = session.query(Feedback).filter(Feedback.id == feedback_id, Feedback.user_id == user_id).first()
        if feedback_entry:
            session.delete(feedback_entry)
            session.commit()
            return True
        else:
            return False
    except SQLAlchemyError as e:
        session.rollback()
        st.error(f"Error deleting feedback: {e}")
        return False
    finally:
        session.close()

# Delete course-related functions
def delete_course(user_id: int, course_id: int) -> bool:
    """
    Delete a course from the database.

    Args:
        user_id (int): The ID of the user requesting the deletion.
        course_id (int): The ID of the course to be deleted.

    Returns:
        bool: True if deletion was successful, False otherwise.
    """
    session = SessionLocal()
    try:
        # Retrieve the course ensuring it belongs to the user
        course = session.query(Course).filter(Course.id == course_id, Course.user_id == user_id).first()
        if course:
            session.delete(course)
            session.commit()
            return True
        else:
            return False  # Course not found or does not belong to the user
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error deleting course: {e}")
        return False
    finally:
        session.close()