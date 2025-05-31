from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import mongo, login_manager
from .models import User
from .utils import hash_password, verify_password
from bson.objectid import ObjectId

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
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        hashed_password = hash_password(password)
        mongo.db.users.insert_one({'username': username, 'password': hashed_password, 'role': role})
        flash('User added')
    users = list(mongo.db.users.find())
    return render_template('admin_dashboard.html', users=users)

@main.route('/faculty')
@login_required
def faculty_dashboard():
    if current_user.role != 'faculty':
        return "Unauthorized", 403
    students = list(mongo.db.users.find({'role': 'student'}))
    subjects = list(mongo.db.subjects.find())
    return render_template('faculty_dashboard.html', students=students, subjects=subjects)

@main.route('/student')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return "Unauthorized", 403
    
    # Get all attendance records for the student
    attendance_records = list(mongo.db.attendance.find({'student_id': str(current_user.id)}))
    
    # Get subject details for each attendance record
    for record in attendance_records:
        subject = mongo.db.subjects.find_one({'_id': ObjectId(record['subject_id'])})
        if subject:
            record['subject_name'] = subject['name']
        else:
            record['subject_name'] = 'Unknown Subject'
    
    # Get marks for all subjects
    marks_records = list(mongo.db.marks.find({'student_id': str(current_user.id)}))
    
    return render_template('student_dashboard.html', 
                         attendance_records=attendance_records,
                         marks_records=marks_records)

@main.route('/add_subject', methods=['POST'])
@login_required
def add_subject():
    if current_user.role != 'faculty':
        return "Unauthorized", 403
        
    subject_name = request.form['subject_name']
    subject_code = request.form['subject_code']
    
    mongo.db.subjects.insert_one({
        'name': subject_name,
        'code': subject_code,
        'faculty_id': str(current_user.id)
    })
    
    flash('Subject added successfully', 'success')
    return redirect(url_for('main.faculty_dashboard'))

@main.route('/mark_attendance', methods=['POST'])
@login_required
def mark_attendance():
    if current_user.role != 'faculty':
        return "Unauthorized", 403
        
    subject_id = request.form['subject_id']
    date = request.form['date']
    
    for key, value in request.form.items():
        if key.startswith('attendance_'):
            student_id = key.split('_')[1]
            mongo.db.attendance.insert_one({
                'student_id': student_id,
                'subject_id': subject_id,
                'date': date,
                'status': value,
                'faculty_id': str(current_user.id)
            })
    
    flash('Attendance marked successfully', 'success')
    return redirect(url_for('main.faculty_dashboard'))

@main.route('/add_marks', methods=['POST'])
@login_required
def add_marks():
    if current_user.role != 'faculty':
        return "Unauthorized", 403
        
    student_id = request.form['student_id']
    subject_id = request.form['subject_id']
    marks = int(request.form['marks'])
    
    # Calculate grade based on marks
    grade = 'F'
    if marks >= 90: grade = 'A'
    elif marks >= 80: grade = 'B'
    elif marks >= 70: grade = 'C'
    elif marks >= 60: grade = 'D'
    
    mongo.db.marks.insert_one({
        'student_id': student_id,
        'subject_id': subject_id,
        'marks': marks,
        'grade': grade,
        'faculty_id': str(current_user.id)
    })
    
    flash('Marks added successfully', 'success')
    return redirect(url_for('main.faculty_dashboard'))
