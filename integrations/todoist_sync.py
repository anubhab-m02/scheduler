# integrations/todoist_sync.py
import todoist
from db.db_utils import SessionLocal
from db.db_models import StudySession, Course
from config import TIMEZONE

def sync_to_todoist(user_id):
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if not user or not user.todoist_api_token:
        session.close()
        return False, "User not found or Todoist API token missing."

    api = todoist.TodoistAPI(user.todoist_api_token)
    api.sync()

    sessions = session.query(StudySession).join(Course).filter(
        Course.user_id == user_id,
        StudySession.start_time >= datetime.utcnow()
    ).all()
    session.close()

    for s in sessions:
        task_content = f"Study {s.course.name}"
        due_date = s.start_time.strftime('%Y-%m-%dT%H:%M:%S')
        task = api.items.add(task_content, due={'date': due_date, 'timezone': TIMEZONE})
    api.commit()
    return True, "Study sessions synced with Todoist successfully!"
