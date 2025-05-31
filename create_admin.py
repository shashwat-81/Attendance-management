from werkzeug.security import generate_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['attendance_db']

    # Create collections if they don't exist
    if 'attendance' not in db.list_collection_names():
        db.create_collection('attendance')
        print("Created attendance collection")

    # Create admin user
    admin_user = {
        "username": "admin",
        "password": generate_password_hash("admin123"),
        "role": "admin",
        "created_at": datetime.now()
    }

    # Create faculty user with additional fields
    faculty_user = {
        "username": "faculty1",
        "password": generate_password_hash("faculty123"),
        "role": "faculty",
        "created_at": datetime.now()
    }

    # Create student user with additional fields
    student_user = {
        "username": "student1",
        "password": generate_password_hash("student123"),
        "role": "student",
        "created_at": datetime.now()
    }

    # Add test subject with attendance tracking
    test_subject = {
        "name": "Computer Science",
        "code": "CS101",
        "faculty_id": str(ObjectId()),
        "created_at": datetime.now()
    }

    # Insert or update users
    if not db.users.find_one({"username": "admin"}):
        db.users.insert_one(admin_user)
        print("Admin user created")

    faculty_result = db.users.find_one({"username": "faculty1"})
    if not faculty_result:
        faculty_result = db.users.insert_one(faculty_user)
        print("Faculty user created")
        
        # Update subject with actual faculty ID
        test_subject['faculty_id'] = str(faculty_result.inserted_id)
        subject_result = db.subjects.insert_one(test_subject)
        print("Test subject created")

        # Create sample attendance record
        sample_attendance = {
            "subject_id": str(subject_result.inserted_id),
            "faculty_id": str(faculty_result.inserted_id),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "records": [],
            "created_at": datetime.now()
        }
        db.attendance.insert_one(sample_attendance)
        print("Sample attendance record created")

    # Create student user
    if not db.users.find_one({"username": "student1"}):
        student_result = db.users.insert_one(student_user)
        print("Student user created")

        # Create sample attendance record with more details
        sample_attendance = {
            "subject_id": str(subject_result.inserted_id),
            "subject_name": test_subject["name"],
            "subject_code": test_subject["code"],
            "faculty_id": str(faculty_result.inserted_id),
            "faculty_name": faculty_user["username"],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "records": [
                {
                    "student_id": str(student_result.inserted_id),
                    "student_name": student_user["username"],
                    "status": "present",
                    "marked_at": datetime.now()
                }
            ],
            "created_at": datetime.now()
        }
        
        db.attendance.insert_one(sample_attendance)
        print(f"Sample attendance record created for student {student_user['username']} in subject {test_subject['name']}")

    print("\nVerifying data in MongoDB:")
    print("\nUsers:")
    for user in db.users.find():
        print(f"Username: {user['username']}, Role: {user['role']}")

    print("\nSubjects:")
    for subject in db.subjects.find():
        print(f"Subject: {subject['name']}, Code: {subject['code']}")

    print("\nAttendance Records:")
    for record in db.attendance.find():
        print(f"Date: {record['date']}, Subject: {record['subject_id']}")

    # Create indexes for better query performance
    db.attendance.create_index([("subject_id", 1), ("date", 1)])
    db.attendance.create_index([("faculty_id", 1)])
    
except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
    print("\nMongoDB connection closed")
