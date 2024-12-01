# 📚 Personalized Study Scheduler with Pomodoro Integration

This project is a personalized study scheduler application that integrates with Google Calendar and Todoist. It helps users manage their study sessions, track performance, and receive feedback and suggestions to improve their study habits.

## Features

- **User Authentication**: Register and log in to access personalized features.
- **Course Management**: Add, delete, and view courses with deadlines and priorities.
- **Study Schedule Generation**: Create study schedules using the Pomodoro technique.
- **Feedback Collection**: Submit feedback or journal entries and analyze sentiment and emotions.
- **Performance Metrics**: Track study sessions and visualize performance over time.
- **Gamification**: Earn badges based on study achievements.
- **Integration with Google Calendar and Todoist**: Sync study sessions with external calendars.
- **Notifications**: Receive email notifications for upcoming study sessions.
- **Resource Management**: Add and view study resources.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/anubhab-m02/scheduler.git
    cd scheduler
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up environment variables:
    - Create a `.env` file in the root directory.
    - Add the following variables:
        ```env
        EMAIL_ADDRESS=your_email@example.com
        EMAIL_PASSWORD=your_email_password
        TIMEZONE=UTC
        ```

5. Initialize the database:
    ```sh
    python -c "from db.db_utils import Base, engine; Base.metadata.create_all(engine)"
    ```

## Usage

1. Run the application:
    ```sh
    streamlit run app.py
    ```

2. Open your web browser and navigate to `http://localhost:8501`.

3. Register a new user or log in with existing credentials.

4. Use the sidebar to add courses, customize settings, and manage study groups.

5. Generate a study schedule and sync it with Google Calendar or Todoist.

6. Submit feedback and view performance metrics and suggestions.

## Project Structure

- `app.py`: Main application file.
- `db/`: Database models and utility functions.
- `integrations/`: Integration with external services (Google Calendar, Todoist, notifications).
- `analytics/`: Sentiment analysis and suggestions.
- `scheduler/`: Study schedule generation.
- `utils/`: Helper functions.
- `config.py`: Configuration settings.
- `requirements.txt`: List of required packages.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.
