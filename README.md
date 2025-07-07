# Attendance Management System

  A web-based attendance management system built with Flask and MongoDB.

## Features

- User roles: Admin, Faculty, and Student
- Real-time attendance tracking
- Subject management
- Attendance reports
- Secure authentication

## Tech Stack

- Python/Flask
- MongoDB
- Bootstrap
- JavaScript

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure MongoDB:
- Install MongoDB
- Start MongoDB service
- Update connection string in config.py

3. Initialize the database:
```bash
python create_admin.py
```

4. Run the application:
```bash
python run.py
```
## Default Credentials

- Admin: username=admin, password=admin123
- Faculty: username=faculty1, password=faculty123
- Student: username=student1, password=student123
