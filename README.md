AI-Powered Classroom Attendance and Participation Monitoring System
This system uses MediaPipe and Django to automatically track student attendance and participation in a classroom setting.

Features
Face Detection for Attendance: Automatically marks students present when their face is detected
Hand Raise Detection for Participation: Tracks student participation by detecting hand raises
Session Management: Teachers can create, manage, and end classroom sessions
Student Login: Students join via a unique session link with their name and ID
Real-time Dashboard: View attendance and participation data in real-time
Export Functionality: Export session data to CSV for record-keeping
Technologies Used
Backend: Django (Python)
Detection: MediaPipe (Face & Hand Detection), OpenCV
Frontend: Django Templates, Bootstrap, JavaScript
Database: SQLite (development) / PostgreSQL (production)
Installation
Clone the repository
Install dependencies:
pip install django opencv-python mediapipe
Run migrations:
python manage.py makemigrations
python manage.py migrate
Create a superuser:
python manage.py createsuperuser
Run the development server:
python manage.py runserver
Usage
Log in as a teacher
Create a new session
Share the generated link with students
Students join the session with their name and ID
The system automatically tracks attendance and participation
End the session and export data when finished
License
This project is licensed under the MIT License - see the LICENSE file for details.
