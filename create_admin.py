from werkzeug.security import generate_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client['attendance_db']

# Create admin user
admin_user = {
    "username": "admin",
    "password": generate_password_hash("admin123"),
    "role": "admin"
}

# Create faculty user
faculty_user = {
    "username": "faculty1",
    "password": generate_password_hash("faculty123"),
    "role": "faculty"
}

# Create student user
student_user = {
    "username": "student1",
    "password": generate_password_hash("student123"),
    "role": "student"
}

# Add test subject
test_subject = {
    "name": "Computer Science",
    "code": "CS101",
    "faculty_id": str(ObjectId())  # We'll update this after creating faculty
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
    db.subjects.insert_one(test_subject)
    print("Test subject created")

if not db.users.find_one({"username": "student1"}):
    db.users.insert_one(student_user)
    print("Student user created")

print("\nVerifying data in MongoDB:")
print("\nUsers:")
for user in db.users.find():
    print(f"Username: {user['username']}, Role: {user['role']}")

print("\nSubjects:")
for subject in db.subjects.find():
    print(f"Subject: {subject['name']}, Code: {subject['code']}")
