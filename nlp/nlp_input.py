# nlp/nlp_input.py
import re
from datetime import datetime
import pytz

def parse_course_input(text):
    """
    Example input: "I need to study Mathematics by May 15th for 5 hours a week"
    """
    pattern = r"I need to study ([\w\s]+) by (\w+ \d{1,2}(?:st|nd|rd|th)?) for (\d+) hours a week"
    match = re.match(pattern, text, re.IGNORECASE)
    if match:
        course_name = match.group(1).strip()
        deadline_str = match.group(2).strip()
        hours_per_week = float(match.group(3))

        # Parse deadline date
        try:
            deadline = datetime.strptime(deadline_str, '%B %dth')
        except ValueError:
            try:
                deadline = datetime.strptime(deadline_str, '%B %d')
            except ValueError:
                return None, None, None

        # Adjust year if necessary
        now = datetime.now()
        deadline = deadline.replace(year=now.year)
        if deadline < now:
            deadline = deadline.replace(year=now.year + 1)

        return course_name, deadline, hours_per_week
    return None, None, None
