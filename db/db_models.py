# db/db_models.py
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Association Table for Study Groups
user_groups = Table(
    'user_groups', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('group_id', Integer, ForeignKey('study_groups.id'))
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # Hashed password
    timezone = Column(String, default='UTC')
    goals = Column(String)  # Comma-separated goals
    todoist_api_token = Column(String)  # For Todoist integration
    badges = Column(String)  # Comma-separated badges

    courses = relationship("Course", back_populates="user")
    study_groups = relationship(
        "StudyGroup",
        secondary=user_groups,
        back_populates="members"
    )
    resources = relationship("Resource", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")

class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    deadline = Column(DateTime, nullable=False)
    hours_per_week = Column(Float, nullable=False)
    priority = Column(Integer, default=1)  # 1: High, 2: Medium, 3: Low
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship("User", back_populates="courses")
    study_sessions = relationship("StudySession", back_populates="course")

class StudySession(Base):
    __tablename__ = "study_sessions"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    start_time = Column(DateTime)
    duration = Column(Float)  # Duration in hours
    completed = Column(Boolean, default=False)
    skipped = Column(Boolean, default=False)
    rescheduled = Column(Boolean, default=False)
    course = relationship("Course", back_populates="study_sessions")

class StudyGroup(Base):
    __tablename__ = 'study_groups'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    members = relationship(
        "User",
        secondary=user_groups,
        back_populates="study_groups"
    )

class Resource(Base):
    __tablename__ = 'resources'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship("User", back_populates="resources")

class Feedback(Base):
    __tablename__ = 'feedback'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    content = Column(String, nullable=False)
    sentiment = Column(Float, nullable=False)  # Polarity score
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="feedbacks")
