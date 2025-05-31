from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from . import mongo, login_manager
from .models import User
from .utils import hash_password, verify_password
from bson.objectid import ObjectId
from datetime import datetime

main = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    return User(user_data) if user_data else None

@main.route('/')
def home():
    return redirect(url_for('main.login'))

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Add debug print statements
        print(f"Login attempt - Username: {username}")
        
        user_data = mongo.db.users.find_one({'username': username})
        
        if not user_data:
            print("User not found in database")
            flash('Invalid username or password', 'error')
            return render_template('login.html')
            
        if not verify_password(password, user_data['password']):
            print("Invalid password")
            flash('Invalid username or password', 'error')
            return render_template('login.html')
        
        print(f"User found: {user_data['username']} with role: {user_data['role']}")    
        user = User(user_data)
        login_user(user)
        
        # Redirect based on role
        if user.role == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        elif user.role == 'faculty':
            return redirect(url_for('main.faculty_dashboard'))
        else:
            return redirect(url_for('main.student_dashboard'))
    
    return render_template('login.html')

@main.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    # Get user counts
    total_users = mongo.db.users.count_documents({})
    faculty_count = mongo.db.users.count_documents({'role': 'faculty'})
    student_count = mongo.db.users.count_documents({'role': 'student'})

    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')
            
            if not all([username, password, role]):
                flash('All fields are required', 'error')
                return redirect(url_for('main.admin_dashboard'))
            
            # Check if username already exists
            if mongo.db.users.find_one({'username': username}):
                flash('Username already exists', 'error')
                return redirect(url_for('main.admin_dashboard'))
            
            # Create new user with timestamp
            new_user = {
                'username': username,
                'password': hash_password(password),
                'role': role,
                'created_at': datetime.now()
            }
            
            mongo.db.users.insert_one(new_user)
            flash('User added successfully', 'success')
            
        except Exception as e:
            print(f"Error adding user: {e}")
            flash('Error adding user', 'error')
    
    # Get all users and sort by creation date
    users = list(mongo.db.users.find().sort('created_at', -1))
    
    return render_template('admin_dashboard.html',
                         users=users,
                         total_users=total_users,
                         faculty_count=faculty_count,
                         student_count=student_count)

@main.route('/faculty')
@login_required
def faculty_dashboard():
    if current_user.role != 'faculty':
        return "Unauthorized", 403
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get all students and subjects
    students = list(mongo.db.users.find({'role': 'student'}))
    subjects = list(mongo.db.subjects.find({'faculty_id': str(current_user.id)}))
    
    # Get attendance status for debugging
    print(f"\nFetching attendance records for {len(students)} students in {len(subjects)} subjects")
    
    # Get attendance records for today
    for student in students:
        student_id = str(student['_id'])
        for subject in subjects:
            subject_id = str(subject['_id'])
            attendance = mongo.db.attendance.find_one({
                'student_id': student_id,
                'subject_id': subject_id,
                'date': today
            })
            print(f"Attendance for student {student['username']} in {subject['name']}: {attendance}")
    
    return render_template('faculty_dashboard.html', 
                         students=students,
                         subjects=subjects,
                         today=today)

@main.route('/student')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return "Unauthorized", 403
    
    try:
        # Get attendance and marks records
        subjects = list(mongo.db.subjects.find())
        subject_dict = {str(subject['_id']): subject for subject in subjects}
        
        # Get all attendance records for the student
        attendance_records = list(mongo.db.attendance.find({
            "records": {
                "$elemMatch": {
                    "student_id": str(current_user.id)
                }
            }
        }))
        
        # Process attendance records
        processed_attendance = []
        for record in attendance_records:
            subject = subject_dict.get(record['subject_id'], {})
            student_record = next(
                (r for r in record['records'] if r['student_id'] == str(current_user.id)), 
                None
            )
            if student_record:
                processed_attendance.append({
                    'date': record['date'],
                    'subject_name': subject.get('name', 'Unknown Subject'),
                    'subject_code': subject.get('code', 'N/A'),
                    'status': student_record['status'],
                    'marked_at': student_record.get('marked_at', record.get('created_at'))
                })
        
        # Sort attendance by date (most recent first)
        processed_attendance.sort(key=lambda x: x['date'], reverse=True)
        
        # Get and process marks
        marks_records = list(mongo.db.marks.find({'student_id': str(current_user.id)}))
        processed_marks = []
        for mark in marks_records:
            subject = subject_dict.get(mark['subject_id'], {})
            processed_marks.append({
                'subject_name': subject.get('name', 'Unknown Subject'),
                'subject_code': subject.get('code', 'N/A'),
                'marks': mark['marks'],
                'grade': mark['grade']
            })
        
        return render_template('student_dashboard.html', 
                             attendance_records=processed_attendance,
                             marks_records=processed_marks,
                             calculate_gpa=calculate_gpa)
                             
    except Exception as e:
        print(f"Error in student dashboard: {e}")
        flash('Error loading dashboard data', 'error')
        return render_template('student_dashboard.html', 
                             attendance_records=[],
                             marks_records=[],
                             calculate_gpa=calculate_gpa)

@main.route('/add_subject', methods=['POST'])
@login_required
def add_subject():
    if current_user.role != 'faculty':
        return "Unauthorized", 403
        
    try:
        subject_name = request.form.get('subject_name')
        subject_code = request.form.get('subject_code')
        
        # Check if subject code already exists
        existing_subject = mongo.db.subjects.find_one({
            'code': subject_code,
            'faculty_id': str(current_user.id)
        })
        
        if existing_subject:
            flash('Subject code already exists', 'error')
            return redirect(url_for('main.faculty_dashboard'))
            
        # Add new subject
        subject = {
            'name': subject_name,
            'code': subject_code,
            'faculty_id': str(current_user.id),
            'created_at': datetime.now()
        }
        
        mongo.db.subjects.insert_one(subject)
        flash('Subject added successfully', 'success')
        
    except Exception as e:
        print(f"Error adding subject: {e}")
        flash('Error adding subject', 'error')
        
    return redirect(url_for('main.faculty_dashboard'))

@main.route('/mark_attendance', methods=['POST'])
@login_required
def mark_attendance():
    if current_user.role != 'faculty':
        return "Unauthorized", 403

    try:
        subject_id = request.form.get('subject_id')
        date = request.form.get('date', datetime.now().strftime("%Y-%m-%d"))
        
        # Log attendance marking attempt
        print(f"\nMarking attendance for subject {subject_id} on {date}")
        
        # Get subject details
        subject = mongo.db.subjects.find_one({'_id': ObjectId(subject_id)})
        if not subject:
            flash('Subject not found', 'error')
            return redirect(url_for('main.faculty_dashboard'))

        # Prepare attendance record
        attendance_record = {
            "subject_id": subject_id,
            "subject_name": subject['name'],
            "subject_code": subject['code'],
            "faculty_id": str(current_user.id),
            "faculty_name": current_user.username,
            "date": date,
            "records": [],
            "updated_at": datetime.now()
        }

        # Process attendance for each student
        for key, value in request.form.items():
            if key.startswith('attendance_'):
                student_id = key.split('_')[1]
                student = mongo.db.users.find_one({'_id': ObjectId(student_id)})
                if student:
                    student_record = {
                        "student_id": str(student['_id']),
                        "student_name": student['username'],
                        "status": value,
                        "marked_at": datetime.now()
                    }
                    attendance_record["records"].append(student_record)
                    print(f"Added attendance for {student['username']}: {value}")

        # Update or insert attendance record
        result = mongo.db.attendance.update_one(
            {
                "subject_id": subject_id,
                "faculty_id": str(current_user.id),
                "date": date
            },
            {"$set": attendance_record},
            upsert=True
        )

        print(f"Attendance marked for {len(attendance_record['records'])} students")
        flash(f'Attendance marked successfully for {len(attendance_record["records"])} students', 'success')

    except Exception as e:
        print(f"Error marking attendance: {e}")
        flash('Error marking attendance', 'error')

    return redirect(url_for('main.faculty_dashboard'))

@main.route('/add_marks', methods=['POST'])
@login_required
def add_marks():
    if current_user.role != 'faculty':
        return "Unauthorized", 403
        
    try:
        subject_id = request.form.get('subject_id')
        if not subject_id:
            flash('Subject is required', 'error')
            return redirect(url_for('main.faculty_dashboard'))

        # Get subject details for verification
        subject = mongo.db.subjects.find_one({'_id': ObjectId(subject_id)})
        if not subject:
            flash('Subject not found', 'error')
            return redirect(url_for('main.faculty_dashboard'))

        marks_added = 0
        
        # Process marks for each student
        for key, value in request.form.items():
            if key.startswith('marks_'):
                student_id = key.split('_')[1]
                marks = int(value)
                
                # Calculate grade
                grade = 'F'
                if marks >= 90: grade = 'A'
                elif marks >= 80: grade = 'B'
                elif marks >= 70: grade = 'C'
                elif marks >= 60: grade = 'D'
                
                # Update or insert marks
                result = mongo.db.marks.update_one(
                    {
                        'student_id': student_id,
                        'subject_id': subject_id,
                        'faculty_id': str(current_user.id)
                    },
                    {
                        '$set': {
                            'marks': marks,
                            'grade': grade,
                            'updated_at': datetime.now()
                        }
                    },
                    upsert=True
                )
                
                if result.modified_count or result.upserted_id:
                    marks_added += 1

        flash(f'Marks updated successfully for {marks_added} students', 'success')
        
    except Exception as e:
        print(f"Error adding marks: {e}")
        flash('Error adding marks', 'error')
        
    return redirect(url_for('main.faculty_dashboard'))

@main.route('/verify_attendance/<subject_id>/<date>')
@login_required
def verify_attendance(subject_id, date):
    if current_user.role != 'faculty':
        return "Unauthorized", 403
        
    try:
        attendance = mongo.db.attendance.find_one({
            "subject_id": subject_id,
            "faculty_id": str(current_user.id),
            "date": date
        })
        
        if attendance:
            print("\nAttendance Record Details:")
            print(f"Subject: {attendance.get('subject_name')} ({attendance.get('subject_code')})")
            print(f"Date: {attendance.get('date')}")
            print(f"Faculty: {attendance.get('faculty_name')}")
            print("\nStudent Records:")
            for record in attendance.get('records', []):
                print(f"- {record['student_name']}: {record['status']}")
            
            return jsonify({
                "status": "success",
                "data": attendance
            })
        else:
            return jsonify({
                "status": "error",
                "message": "No attendance record found"
            })
            
    except Exception as e:
        print(f"Error verifying attendance: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@main.route('/edit_user', methods=['GET', 'POST'])
@login_required
def edit_user():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    user_id = request.args.get('id')
    if not user_id:
        flash('User ID is required', 'error')
        return redirect(url_for('main.admin_dashboard'))

    try:
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('main.admin_dashboard'))

        if request.method == 'POST':
            # Update user details
            updates = {
                'username': request.form['username'],
                'role': request.form['role'],
                'updated_at': datetime.now()
            }
            
            # Only update password if a new one is provided
            if request.form.get('password'):
                updates['password'] = generate_password_hash(request.form['password'])

            mongo.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': updates}
            )
            
            flash('User updated successfully', 'success')
            return redirect(url_for('main.admin_dashboard'))

        return render_template('edit_user.html', user=user)

    except Exception as e:
        flash(f'Error updating user: {str(e)}', 'error')
        return redirect(url_for('main.admin_dashboard'))

@main.route('/delete_user', methods=['POST'])
@login_required
def delete_user():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    try:
        user_id = request.form.get('user_id')
        if not user_id:
            flash('User ID is required', 'error')
            return redirect(url_for('main.admin_dashboard'))

        # Don't allow deleting own account
        if str(current_user.id) == user_id:
            flash('Cannot delete your own account', 'error')
            return redirect(url_for('main.admin_dashboard'))

        result = mongo.db.users.delete_one({'_id': ObjectId(user_id)})
        
        if result.deleted_count:
            flash('User deleted successfully', 'success')
        else:
            flash('User not found', 'error')

    except Exception as e:
        print(f"Error deleting user: {e}")
        flash('Error deleting user', 'error')

    return redirect(url_for('main.admin_dashboard'))

def calculate_gpa(marks_records):
    if not marks_records:
        return 0.0
        
    grade_points = {
        'A': 4.0,
        'B': 3.0,
        'C': 2.0,
        'D': 1.0,
        'F': 0.0
    }
    
    total_points = sum(grade_points[record['grade']] for record in marks_records)
    return round(total_points / len(marks_records), 2)
