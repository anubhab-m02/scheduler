# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
TIMEZONE = os.getenv('TIMEZONE', 'UTC')  # Default to UTC if not set
