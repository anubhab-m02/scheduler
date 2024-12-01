from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from .db_models import Base, User, Course, StudySession, StudyGroup, Resource, Feedback
import bcrypt

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
def add_feedback(user_id, content, sentiment):
    session = SessionLocal()
    feedback = Feedback(
        user_id=user_id,
        content=content,
        sentiment=sentiment
    )
    session.add(feedback)
    session.commit()
    session.close()
    return feedback

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