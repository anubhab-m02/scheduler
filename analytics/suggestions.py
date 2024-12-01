from db.db_utils import SessionLocal
from db.db_models import StudySession, User, Course

def generate_suggestions(user_id):
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        session.close()
        return []

    sessions = session.query(StudySession).join(Course).filter(
        Course.user_id == user_id,
        StudySession.completed == True
    ).all()
    session.close()

    total_completed = len(sessions)
    total_hours = sum(s.duration for s in sessions)

    suggestions = []

    if total_hours < 20:
        suggestions.append("Consider increasing your daily study limit to achieve your goals faster.")
    if total_completed % 10 == 0 and total_completed != 0:
        suggestions.append("Great job on completing 10 study sessions! Keep up the good work!")
    if total_hours > 100:
        suggestions.append("You've surpassed 100 study hours! Time to set new challenges.")
    if total_completed < 10:
        suggestions.append("Start building a consistent study habit by scheduling regular sessions.")
    # Add more suggestions based on different criteria

    return suggestions
