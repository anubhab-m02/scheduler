from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
from db.db_utils import SessionLocal
from db.db_models import StudySession, Course
from config import TIMEZONE

SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google(user):
    creds = None
    token_path = f'credentials/token_{user.id}.pickle'
    creds_path = 'credentials/google_credentials.json'
    
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    return creds

def sync_to_google_calendar(user_id):
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        session.close()
        return False, "User not found."

    creds = authenticate_google(user)
    service = build('calendar', 'v3', credentials=creds)

    sessions = session.query(StudySession).join(Course).filter(
        Course.user_id == user_id,
        StudySession.start_time >= datetime.utcnow()
    ).all()
    session.close()

    for s in sessions:
        event = {
            'summary': f"Study: {s.course.name}",
            'start': {
                'dateTime': s.start_time.isoformat(),
                'timeZone': TIMEZONE,
            },
            'end': {
                'dateTime': (s.start_time + timedelta(hours=s.duration)).isoformat(),
                'timeZone': TIMEZONE,
            },
        }
        service.events().insert(calendarId='primary', body=event).execute()
    return True, "Study schedule synced with Google Calendar successfully!"
