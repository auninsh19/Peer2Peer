# app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from collections import defaultdict

from datetime import datetime

import pandas as pd
import plotly.graph_objs as go
import os, math, joblib

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
#from reportlab.pdfgen import canvas



app = Flask(__name__)
app.secret_key = '3f3c8e1b2d4f4e1b8c9a2e1f3b4a5c6d'  # Change this to a random secret key
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'peer_evaluation.db')
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/peer_evaluation.db?check_same_thread=False'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db, User, Course, UserCourseEnrollment, Groups, GroupMembers, Assignments, GroupEvaluations, ParticipationEvaluations, LeadershipEvaluations, CooperationEvaluations, TimeManagementEvaluations, CommunicationEvaluations, ProblemSolvingEvaluations, SelfEvaluations, Comments

db.init_app(app)
migrate = Migrate(app, db)


# Load model once
grade_model = joblib.load('grade_predict_rf_model.pkl')

# Mapping from predicted group to possible grades
group_to_grades = {
    'High': ['A', 'A-', 'B+'],
    'Mid': ['B', 'B-', 'C+', 'C'],
    'Low': ['C-', 'D+', 'D', 'D-', 'F']
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].upper()  # Convert name to uppercase
        email = request.form['email']  # Get email from form
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Check if email or username already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('register'))

        # Store password as plain text (for testing only)
        new_user = User(name=name, email=email, username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if not user:
            print(f"Login failed: No user found with username {username}")  # Debugging
        else:
            print(f"User found: {user.username}, stored password: {user.password}")  # Debugging
            print(f"Entered password: {password}")
            print(f"Check result: {user.password == password}")


        #if user and check_password_hash(user.password, password):
        if user and user.password == password:  # Direct comparison
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            print(f"User {username} logged in with role {user.role}")  # Debugging
            print(f"Session data: {session}")  # Debugging

            # Redirect based on role
            if user.role.lower() == 'admin':
                return redirect(url_for('course_management'))  # Replace with actual admin route
            else:  # for 'student' or 'lecturer'
                return redirect(url_for('course_selection'))

        flash('Invalid username or password', 'danger')
        print("Invalid login attempt")  # Debugging

    return render_template('login.html')


@app.route('/course-management', methods=['GET'])
def course_management():
    if 'user_id' not in session:
        print("User not in session, redirecting to login")  # Debugging
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    page = request.args.get('page', 1, type=int)
    per_page = 10  
    courses = Course.query.paginate(page=page, per_page=per_page)

    #courses = Course.query.all()

    return render_template('course_management.html', 
                            user=user, 
                            courses=courses, 
                            active_page='course_management'
    )


@app.route('/add-course', methods=['POST'])
def add_course():
    course_code = request.form.get('course_code')
    course_name = request.form.get('course_name')
    
    new_course = Course(code=course_code, name=course_name)
    db.session.add(new_course)
    db.session.commit()

    flash('Course added successfully', 'success')
    return redirect(url_for('course_management'))


@app.route('/delete-course/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)

    # Delete related UserCourseEnrollments
    enrollments = UserCourseEnrollment.query.filter_by(course_id=course_id).all()
    for enrollment in enrollments:
        db.session.delete(enrollment)

    db.session.delete(course)
    db.session.commit()
    flash('Course and related enrollments deleted successfully', 'success')
    return redirect(url_for('course_management'))


@app.route('/edit-course/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)

    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if request.method == 'POST':
        course.code = request.form['code']
        course.name = request.form['name']
        db.session.commit()
        flash('Course updated successfully', 'success')
        return redirect(url_for('course_management'))
    
    return render_template('edit_course.html', course=course, user=user, active_page='edit_course')


@app.route('/course_selection')
def course_selection():
    if 'user_id' not in session:
        print("User not in session, redirecting to login")  # Debugging
        return redirect(url_for('login'))

    #print(f"User ID in session: {session['user_id']}")  # Debugging
    user_id = session['user_id']
    user = User.query.get(user_id)

    # Get courses where user is enrolled
    enrolled_courses = Course.query.join(UserCourseEnrollment).filter(UserCourseEnrollment.user_id == user_id).all()

    return render_template('course_selection.html', courses=enrolled_courses, user=user, active_page='course_selection')


@app.route('/enroll', methods=['GET', 'POST'])
def enroll():
    if request.method == 'POST':
        if 'user_id' not in session:
            flash("You need to log in first.", "warning")
            return redirect(url_for('login'))

        user_id = session['user_id']
        role = session['role']  # Get user role (student/lecturer) from session
        course_ids = request.form.getlist('course_ids')  # Get multiple selected course_ids

        if not course_ids:
            flash("Please select at least one course to enroll.", "warning")
            return redirect(url_for('enroll'))

        enrolled_count = 0
        already_enrolled = []

        for course_id in course_ids:
            course = Course.query.get(course_id)
            exists = UserCourseEnrollment.query.filter_by(user_id=user_id, course_id=course_id, role=role).first()
            if not exists:
                db.session.add(UserCourseEnrollment(user_id=user_id, course_id=course_id, role=role))
                enrolled_count += 1
            else:
                already_enrolled.append(f"{course.code} - {course.name}")

        db.session.commit()

        # Feedback to user
        if enrolled_count:
            flash(f"Successfully enrolled in {enrolled_count} new course(s).", "success")
        if already_enrolled:
            flash("Already enrolled in: " + ", ".join(already_enrolled), "info")
        
        return redirect(url_for('course_selection'))


    # Handle GET request to render the enrollment page
    if 'user_id' not in session:
        flash("You need to log in first.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)  # Fetch the user from the database
    available_courses = Course.query.all()  # Fetch available courses
    return render_template('enroll.html', user=user, available_courses=available_courses, active_page='enroll')


def get_enrolled_students_count(course_id):
    # Count the number of students enrolled in the course, excluding lecturers
    return UserCourseEnrollment.query.join(User).filter(
        UserCourseEnrollment.course_id == course_id,
        User.role == 'student'  # Ensure only students are counted
    ).count()


def get_group_count(course_id):
    # Count the number of groups for the specified course
    return Groups.query.filter_by(course_id=course_id).count()


def get_assignments_count(course_id):
    # Count the number of assignments for the specified course
    return Assignments.query.filter_by(course_id=course_id).count()


def get_evaluations_count(user_id, course_id):
    # Get the group membership for the current user
    group_membership = GroupMembers.query.filter_by(user_id=user_id).first()
    
    if not group_membership:
        return 0  # No group membership, return 0 evaluations

    group = Groups.query.get(group_membership.group_id)  # Get the group based on membership
    group_members = GroupMembers.query.filter_by(group_id=group.id).all()  # Fetch all members of the group
    
    # Filter out the current user from the group members
    group_members = [member for member in group_members if member.user_id != user_id]

    # Fetch assignments for the course
    assignments = Assignments.query.filter_by(course_id=course_id).all()

    num_assignments = len(assignments)
    num_group_members = len(group_members)

    # Calculate total group evaluations
    total_group_evaluations = num_group_members * num_assignments  # Total group evaluations needed
   
    total_evaluations = total_group_evaluations + 1  # Always add 1 for the self-evaluation

    return total_evaluations


def get_evaluation_completion_status(course_id):
    # Get total expected evaluations = num of group members × num of assignments
    total_students = UserCourseEnrollment.query.filter_by(course_id=course_id).count()
    total_assignments = Assignments.query.filter_by(course_id=course_id).count()
    expected_evaluations = total_students * total_assignments

    # Actual submitted evaluations
    completed_evaluations = db.session.query(GroupEvaluations).join(Assignments).filter(
        Assignments.course_id == course_id
    ).count()

    pending_evaluations = expected_evaluations - completed_evaluations
    return completed_evaluations, pending_evaluations


@app.route('/course/<int:course_id>')
def course_view(course_id):
    # Fetch the course from the database
    course = Course.query.get(course_id)
    
    # Check if the course exists
    if course is None:
        abort(404)  # Return a 404 error if the course is not found

    # Check if the user is logged in and get their role
    if 'user_id' not in session:
        abort(403)  # Forbidden if the user is not logged in

    user_id = session['user_id']
    user = User.query.get(user_id)  # Fetch the user from the database

    # Check if the user was found
    if user is None:
        abort(403)  # Forbidden if the user is not found

    user_role = session.get('role')  # Assuming role is stored in session

    # Initialize variables
    enrolled_students_count = get_enrolled_students_count(course_id)  # Function to get count of enrolled students
    group_count = get_group_count(course_id)  # Count the number of groups
    assignments_count = get_assignments_count(course_id)  # Count of assignments
    evaluations_count = get_evaluations_count(user_id, course_id)
    # Initialize group name variable
    group_name = None

    # Get the group membership for the current user
    group_membership = GroupMembers.query.filter_by(user_id=user_id).first()
    if group_membership:
        group = Groups.query.get(group_membership.group_id)  # Get the group based on membership
        if group:
            group_name = group.name  # Get the group name

    # Get groups for dropdown
    groups = Groups.query.filter_by(course_id=course_id).all()

    # Handle optional group_id for filtering
    group_id = request.args.get('group_id', type=int)



    # Render different templates or sections based on the user's role
    if user_role == 'lecturer':

        # CHART 1: Average Scores by Assignment Chart
        # Query average scores (add course_id filtering via assignment join if needed)
        query = db.session.query(
            GroupEvaluations.assignment_id,
            Assignments.title.label('assignment_title'),
            db.func.avg(GroupEvaluations.Pavg).label('avg_participation'),
            db.func.avg(GroupEvaluations.Lavg).label('avg_leadership'),
            db.func.avg(GroupEvaluations.Cavg).label('avg_cooperation'),
            db.func.avg(GroupEvaluations.TMavg).label('avg_time_management'),
            db.func.avg(GroupEvaluations.CommAvg).label('avg_communication'),
            db.func.avg(GroupEvaluations.PSavg).label('avg_problem_solving')
        ).join(Assignments, GroupEvaluations.assignment_id == Assignments.id
        ).filter(Assignments.course_id == course_id)

        if group_id:
            query = query.filter(GroupEvaluations.group_id == group_id)
            #query = query.group_by(GroupEvaluations.assignment_id, Assignments.title)


        evaluations = query.group_by(GroupEvaluations.assignment_id, Assignments.title).all()

        # Prepare data for chart
        assignments = [e.assignment_title for e in evaluations]
        avg_participation = [e.avg_participation for e in evaluations]
        avg_leadership = [e.avg_leadership for e in evaluations]
        avg_cooperation = [e.avg_cooperation for e in evaluations]
        avg_time_management = [e.avg_time_management for e in evaluations]
        avg_communication = [e.avg_communication for e in evaluations]
        avg_problem_solving = [e.avg_problem_solving for e in evaluations]

        fig = go.Figure()
        fig.add_trace(go.Bar(x=assignments, y=avg_participation, name='Participation', marker_color='#E0F2F1'))
        fig.add_trace(go.Bar(x=assignments, y=avg_leadership, name='Leadership', marker_color='#B2DFDB'))
        fig.add_trace(go.Bar(x=assignments, y=avg_cooperation, name='Cooperation', marker_color='#80CBC4'))
        fig.add_trace(go.Bar(x=assignments, y=avg_time_management, name='Time Management', marker_color='#4DB6AC'))
        fig.add_trace(go.Bar(x=assignments, y=avg_communication, name='Communication', marker_color='#26A69A'))
        fig.add_trace(go.Bar(x=assignments, y=avg_problem_solving, name='Problem Solving', marker_color='#00897B'))

        fig.update_layout(
            title='Average Scores by Assignment',
            xaxis_title='Assignments',
            yaxis_title='Average Scores',
            barmode='group',
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color='#333333'),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#EEEEEE')
        )

        plot_html = fig.to_html(full_html=False)

        # CHART 2: Completion Status Chart
        completed, pending = get_evaluation_completion_status(course_id)

        fig = go.Figure(data=[go.Pie(
            labels=['Completed', 'Pending'],
            values=[completed, pending],
            hole=.5,
            marker=dict(colors=['#4CAF50', '#C0C0C0'])
        )])
        fig.update_layout(title='Group Evaluation Completion Status')
        completion_html = fig.to_html(full_html=False)


        # CHART 3: Radar Chart: Average scores across all groups in the course
        radar_query = db.session.query(
            func.avg(GroupEvaluations.Pavg).label('participation'),
            func.avg(GroupEvaluations.Lavg).label('leadership'),
            func.avg(GroupEvaluations.Cavg).label('cooperation'),
            func.avg(GroupEvaluations.TMavg).label('time_management'),
            func.avg(GroupEvaluations.CommAvg).label('communication'),
            func.avg(GroupEvaluations.PSavg).label('problem_solving')
        ).join(Groups, Groups.id == GroupEvaluations.group_id
        ).filter(Groups.course_id == course_id)

        if group_id:
            radar_query = radar_query.filter(GroupEvaluations.group_id == group_id)

        radar_scores = radar_query.first()
        categories = ['Participation', 'Leadership', 'Cooperation', 'Time Management', 'Communication', 'Problem Solving']
        scores = [
            radar_scores.participation,
            radar_scores.leadership,
            radar_scores.cooperation,
            radar_scores.time_management,
            radar_scores.communication,
            radar_scores.problem_solving
        ]

        # Replace None with 0
        scores = [s if s is not None else 0 for s in scores]

        radar_fig = go.Figure()
        radar_fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=categories,
            fill='toself',
            name='Average',
            line_color='rgba(34, 94, 168, 0.8)'
        ))

        radar_fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
            showlegend=True,
            title='Overall Group Performance'
        )

        radar_html = radar_fig.to_html(full_html=False)

        return render_template('course_view_lecturer.html', 
                               user=user, 
                               course=course, 
                               enrolled_students_count=enrolled_students_count,
                               group_count=group_count,
                               assignments_count=assignments_count,
                               groups=groups,
                               selected_group_id=group_id,
                               plot_html=plot_html, 
                               completion_html=completion_html,
                               radar_html=radar_html, 
                               active_page='course_view_lecturer')
    
    elif user_role == 'student':
        return render_template('course_view_student.html', 
                                user=user, 
                                course=course,
                                group_name=group_name,
                                assignments_count=assignments_count,
                                evaluations_count=evaluations_count,
                                active_page='course_view_student')
    else:
        abort(403)  # Forbidden if the role is not recognized


@app.route('/course/<int:course_id>/participants')
def participants_view(course_id):
    
    # Fetch the course and participants from the database
    course = Course.query.get(course_id)
    search_term = request.args.get('search', '').lower()
    role_filter = request.args.get('role', 'all')
    page = int(request.args.get('page', 1))
    per_page = 10

    # Fetch participants through the UserCourseEnrollment table
    participants = User.query.join(UserCourseEnrollment).filter(UserCourseEnrollment.course_id == course_id).all()

    if search_term:
        participants = [p for p in participants if search_term in p.name.lower()]

    if role_filter == 'student':
        participants = [p for p in participants if p.role.lower() == 'student']
    elif role_filter == 'lecturer':
        participants = [p for p in participants if p.role.lower() == 'lecturer']

    # Pagination logic
    total = len(participants)
    total_pages = math.ceil(total / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_participants = participants[start:end]

    # Fetch the current user from the session
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None  # Get user if logged in
    
    # Check user role and render the appropriate template
    if user and user.role == 'lecturer':
        return render_template('participants_lecturer.html', 
                                user=user, 
                                course=course, 
                                participants=paginated_participants, 
                                active_page='participants_lecturer',
                                current_page=page,
                                total_pages=total_pages,
                                search_term=search_term,
                                role_filter=role_filter
        )
    
    elif user and user.role == 'student':
        return render_template('participants_student.html', 
                                user=user, 
                                course=course, 
                                participants=paginated_participants, 
                                active_page='participants_student',
                                current_page=page,
                                total_pages=total_pages,
                                search_term=search_term,
                                role_filter=role_filter
        )

    else:
        # Handle case where user is not logged in or role is not recognized
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for('login'))


@app.route('/course/<int:course_id>/group_management')
def group_management(course_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        flash("You need to log in first.", "warning")
        return redirect(url_for('login'))

    # Fetch the user from the session
    user_id = session['user_id']
    user = User.query.get(user_id)

    # Check if the user is a lecturer
    if user.role != 'lecturer':
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for('course_selection'))

    # Fetch the course to ensure it exists
    course = Course.query.get(course_id)
    if course is None:
        abort(404)  # Course not found

    # Fetch group data for the course
    # Fetch group data for the course
    groups = Groups.query.filter_by(course_id=course_id).all()
    group_data = []
    for group in groups:
        members = GroupMembers.query.filter_by(group_id=group.id).all()
        member_names = [User .query.get(member.user_id).name for member in members]
        group_data.append({
            'group_name': group.name,
            'members': member_names
        })

    # Render the group management page
    return render_template('group_management.html', user=user, course=course, group_data=group_data, active_page='group_management')


@app.route('/upload_groups/<int:course_id>', methods=['POST'])
def upload_groups(course_id):
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        # Read the Excel file
        df = pd.read_excel(file)

        # Process the DataFrame to extract group and member information
        for index, row in df.iterrows():
            group_name = row['Group Name']  # Adjust based on your Excel column names
            
            # Check if the group already exists
            existing_group = Groups.query.filter_by(course_id=course_id, name=group_name).first()
            if existing_group:
                new_group = existing_group  # Use the existing group
            else:
                # Create a new group
                new_group = Groups(course_id=course_id, name=group_name)
                db.session.add(new_group)
                db.session.flush()  # Flush to get the new group's ID

            # Iterate through member columns
            for i in range(1, len(row)):  # Start from the second column
                member_name = row[i]
                if pd.notna(member_name):  # Check if the member name is not NaN
                    # Find the user by name (or you could use email/username)
                    user = User.query.filter_by(name=member_name).first()
                    if user:
                        # Check if the user is already a member of the group
                        existing_member = GroupMembers.query.filter_by(group_id=new_group.id, user_id=user.id).first()
                        if not existing_member:
                            # Add the user to the group
                            group_member = GroupMembers(group_id=new_group.id, user_id=user.id)
                            db.session.add(group_member)

        db.session.commit()
        flash('Groups and members uploaded successfully!')

        # Fetch groups and their members for the course to display
        groups = Groups.query.filter_by(course_id=course_id).all()
        group_data = []
        for group in groups:
            members = GroupMembers.query.filter_by(group_id=group.id).all()
            member_names = [User .query.get(member.user_id).name for member in members]
            group_data.append({
                'group_name': group.name,
                'members': member_names
            })

        # Render the group management page with updated group data
        user = User.query.get(session['user_id'])  # Fetch the current user
        course = Course.query.get(course_id)  # Fetch the course
        return render_template('group_management.html', user=user, course=course, active_page='group_management', group_data=group_data)
    
    flash('Invalid file format. Please upload an Excel file.')
    return redirect(request.url)


@app.route('/delete_all_groups_and_members/<int:course_id>', methods=['POST'])
def delete_all_groups_and_members(course_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        flash("You need to log in first.", "warning")
        return redirect(url_for('login'))

    # Check if the user is a lecturer
    user = User.query.get(session['user_id'])
    if user.role != 'lecturer':
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for('course_selection'))

    # Delete all records from GroupMembers related to the course
    GroupMembers.query.filter(GroupMembers.group_id.in_(
        db.session.query(Groups.id).filter(Groups.course_id == course_id)
    )).delete(synchronize_session='fetch')
    
    db.session.commit()

    # Delete all records from Groups related to the course
    Groups.query.filter_by(course_id=course_id).delete()
    db.session.commit()

    flash('All groups and their members related to the course have been deleted successfully!')
    return redirect(url_for('group_management', course_id=course_id))


@app.route('/assignment_management/<int:course_id>', methods=['GET', 'POST'])
def assignment_management(course_id):
    # Fetch the course from the database
    course = Course.query.get(course_id)

    # Check if the course exists
    if course is None:
        abort(404)  # Return a 404 error if the course is not found
    
    # Fetch the current user from the session
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None  # Get user if logged in

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']

        if not title or not description:
            flash('Title and description are required!', 'error')
            return redirect(url_for('assignment_management', course_id=course_id))

        new_assignment = Assignments(title=title, description=description, course_id=course_id)
        db.session.add(new_assignment)
        db.session.commit()
        flash('Assignment added successfully!', 'success')
        # After adding the assignment, you can either redirect or render the same page
        return redirect(url_for('assignment_management', course_id=course_id))

    # Fetch assignments for the course
    assignments = Assignments.query.filter_by(course_id=course_id).all()

    return render_template('assignment_management.html', assignments=assignments, course=course, user=user, active_page='assignment_management')


@app.route('/edit-assignment/<int:course_id>/<int:assignment_id>', methods=['GET', 'POST'])
def edit_assignment(course_id, assignment_id):
    user_id = session['user_id']
    user = User.query.get(user_id)

    assignment = Assignments.query.get_or_404(assignment_id)
    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        assignment.title = request.form['title']
        assignment.description = request.form['description']
        db.session.commit()
        flash('Assignment updated successfully!', 'success')
        return redirect(url_for('assignment_management', course_id=course_id))

    return render_template('edit_assignment.html', user=user, assignment=assignment, course=course)


@app.route('/delete-assignment/<int:course_id>/<int:assignment_id>', methods=['POST'])
def delete_assignment(course_id, assignment_id):
    assignment = Assignments.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    flash('Assignment deleted successfully!', 'success')
    return redirect(url_for('assignment_management', course_id=course_id))


def check_if_user_completed_evaluation(evaluator_id, assignment_id):
    # Check if the user has completed any evaluation for the given assignment
    participation_completed = ParticipationEvaluations.query.filter_by(evaluator_id=evaluator_id, assignment_id=assignment_id).first() is not None
    leadership_completed = LeadershipEvaluations.query.filter_by(evaluator_id=evaluator_id, assignment_id=assignment_id).first() is not None
    cooperation_completed = CooperationEvaluations.query.filter_by(evaluator_id=evaluator_id, assignment_id=assignment_id).first() is not None
    time_management_completed = TimeManagementEvaluations.query.filter_by(evaluator_id=evaluator_id, assignment_id=assignment_id).first() is not None
    communication_completed = CommunicationEvaluations.query.filter_by(evaluator_id=evaluator_id, assignment_id=assignment_id).first() is not None
    problem_solving_completed = ProblemSolvingEvaluations.query.filter_by(evaluator_id=evaluator_id, assignment_id=assignment_id).first() is not None

    # Return True if all evaluation criteria exist, otherwise False
    return (participation_completed and leadership_completed and cooperation_completed and time_management_completed and communication_completed and problem_solving_completed)


def calculate_completed_evaluations(evaluator_id, assignment_id, group_id):
    # Count completed evaluations for the user in the specified group
    # If one criteria is completed, one complete evaluation is count
    completed_count = ProblemSolvingEvaluations.query.filter_by(
        evaluator_id=evaluator_id,
        assignment_id=assignment_id,
        group_id=group_id
    ).count()

    return completed_count


def save_group_evaluation(user_id, assignment_id, group_id, group_members, request):
    try:
        for member in group_members:
            member_id = member.user.id  # Get the member's ID
            print(f"Processing member ID: {member_id}")  

            # Create or fetch the group evaluation
            group_evaluation = GroupEvaluations.query.filter_by(
                assignment_id=assignment_id, 
                group_id=group_id, 
                evaluatee_id=member_id
            ).first()
        
            if not group_evaluation:
                # Create a new group evaluation if it doesn't exist
                group_evaluation = GroupEvaluations(
                    group_id=group_id,
                    assignment_id=assignment_id,
                    evaluatee_id=member_id,
                    Pavg=0.0,
                    Lavg=0.0,
                    Cavg=0.0,
                    TMavg=0.0,
                    CommAvg=0.0,
                    PSavg=0.0
                )
                db.session.add(group_evaluation)
                db.session.commit()
                print(f"Created new GroupEvaluations entry for member ID: {member_id}")
            else:
                print(f"Found existing GroupEvaluations entry for member ID: {member_id}")

        #try:
            # Collect scores for each criterion with validation
            scores = {
                'participation': [int(request.form.get(f'P{i}_{member_id}', 0)) for i in range(1, 5)],
                'leadership': [int(request.form.get(f'L{i}_{member_id}', 0)) for i in range(1, 5)],
                'cooperation': [int(request.form.get(f'C{i}_{member_id}', 0)) for i in range(1, 5)],
                'time_management': [int(request.form.get(f'TM{i}_{member_id}', 0)) for i in range(1, 5)],
                'communication': [int(request.form.get(f'Comm{i}_{member_id}', 0)) for i in range(1, 5)],
                'problem_solving': [int(request.form.get(f'PS{i}_{member_id}', 0)) for i in range(1, 5)],
            }

            # Check if scores are valid (not all zeros)
            if all(score == 0 for score in scores['participation']) and all(score == 0 for score in scores['leadership']):
                print(f"No valid scores for member ID: {member_id}")
                continue  # Skip this member if no valid scores

            # Check if the participation evaluation already exists
            existing_participation_evaluation = ParticipationEvaluations.query.filter_by(
                group_evaluation_id=group_evaluation.id,
                evaluator_id=user_id,
                evaluatee_id=member_id,
                assignment_id=assignment_id
            ).first()

            existing_leadership_evaluation = LeadershipEvaluations.query.filter_by(
                group_evaluation_id=group_evaluation.id,
                evaluator_id=user_id,
                evaluatee_id=member_id,
                assignment_id=assignment_id
            ).first()

            existing_cooperation_evaluation = CooperationEvaluations.query.filter_by(
                group_evaluation_id=group_evaluation.id,
                evaluator_id=user_id,
                evaluatee_id=member_id,
                assignment_id=assignment_id
            ).first()

            existing_time_management_evaluation = TimeManagementEvaluations.query.filter_by(
                group_evaluation_id=group_evaluation.id,
                evaluator_id=user_id,
                evaluatee_id=member_id,
                assignment_id=assignment_id
            ).first()

            existing_communication_evaluation = CommunicationEvaluations.query.filter_by(
                group_evaluation_id=group_evaluation.id,
                evaluator_id=user_id,
                evaluatee_id=member_id,
                assignment_id=assignment_id
            ).first()

            existing_problem_solving_evaluation = ProblemSolvingEvaluations.query.filter_by(
                group_evaluation_id=group_evaluation.id,
                evaluator_id=user_id,
                evaluatee_id=member_id,
                assignment_id=assignment_id
            ).first()

            # Handle ParticipationEvaluations
            if existing_participation_evaluation:
                # Update existing evaluation
                existing_participation_evaluation.P1 = scores['participation'][0]
                existing_participation_evaluation.P2 = scores['participation'][1]
                existing_participation_evaluation.P3 = scores['participation'][2]
                existing_participation_evaluation.P4 = scores['participation'][3]
                print(f"Updated existing ParticipationEvaluations for member ID: {member_id}")
            else:
                # Create a new ParticipationEvaluation entry for each evaluatee
                participation_evaluation = ParticipationEvaluations(
                    group_evaluation_id=group_evaluation.id,
                    evaluator_id=user_id,
                    evaluatee_id=member_id,
                    assignment_id=assignment_id,
                    group_id=group_id,
                    P1=scores['participation'][0],
                    P2=scores['participation'][1],
                    P3=scores['participation'][2],
                    P4=scores['participation'][3],
                )
                db.session.add(participation_evaluation)
                print(f"Created new ParticipationEvaluations entry for member ID: {member_id}")

            # Handle Leadership Evaluations
            if existing_leadership_evaluation:
                # Update existing leadership evaluation
                existing_leadership_evaluation.L1 = scores['leadership'][0]
                existing_leadership_evaluation.L2 = scores['leadership'][1]
                existing_leadership_evaluation.L3 = scores['leadership'][2]
                existing_leadership_evaluation.L4 = scores['leadership'][3]
                print(f"Updated existing LeadershipEvaluations for member ID: {member_id}")
            else:
                # Create a new LeadershipEvaluation entry for each evaluatee
                leadership_evaluation = LeadershipEvaluations(
                    group_evaluation_id=group_evaluation.id,
                    evaluator_id=user_id,
                    evaluatee_id=member_id,
                    assignment_id=assignment_id,
                    group_id=group_id,
                    L1=scores['leadership'][0],
                    L2=scores['leadership'][1],
                    L3=scores['leadership'][2],
                    L4=scores['leadership'][3],
                )
                db.session.add(leadership_evaluation)
                print(f"Created new LeadershipEvaluations entry for member ID: {member_id}")

            # Handle Cooperation Evaluations
            if existing_cooperation_evaluation:
                # Update existing cooperation evaluation
                existing_cooperation_evaluation.C1 = scores['cooperation'][0]
                existing_cooperation_evaluation.C2 = scores['cooperation'][1]
                existing_cooperation_evaluation.C3 = scores['cooperation'][2]
                existing_cooperation_evaluation.C4 = scores['cooperation'][3]
                print(f"Updated existing CooperationEvaluations for member ID: {member_id}")
            else:
                # Create a new CooperationEvaluation entry for each evaluatee
                cooperation_evaluation = CooperationEvaluations(
                    group_evaluation_id=group_evaluation.id,
                    evaluator_id=user_id,
                    evaluatee_id=member_id,
                    assignment_id=assignment_id,
                    group_id=group_id,
                    C1=scores['cooperation'][0],
                    C2=scores['cooperation'][1],
                    C3=scores['cooperation'][2],
                    C4=scores['cooperation'][3],
                )
                db.session.add(cooperation_evaluation)
                print(f"Created new CooperationEvaluations entry for member ID: {member_id}")

            # Handle Time Management Evaluations
            if existing_time_management_evaluation:
                # Update existing time management evaluation
                existing_time_management_evaluation.TM1 = scores['time_management'][0]
                existing_time_management_evaluation.TM2 = scores['time_management'][1]
                existing_time_management_evaluation.TM3 = scores['time_management'][2]
                existing_time_management_evaluation.TM4 = scores['time_management'][3]
                print(f"Updated existing TimeManagementEvaluations for member ID: {member_id}")
            else:
                # Create a new TimeManagementEvaluation entry for each evaluatee
                time_management_evaluation = TimeManagementEvaluations(
                    group_evaluation_id=group_evaluation.id,
                    evaluator_id=user_id,
                    evaluatee_id=member_id,
                    assignment_id=assignment_id,
                    group_id=group_id,
                    TM1=scores['time_management'][0],
                    TM2=scores['time_management'][1],
                    TM3=scores['time_management'][2],
                    TM4=scores['time_management'][3],
                )
                db.session.add(time_management_evaluation)
                print(f"Created new TimeManagementEvaluations entry for member ID: {member_id}")

            # Handle Communication Evaluations
            if existing_communication_evaluation:
                # Update existing communication evaluation
                existing_communication_evaluation.Comm1 = scores['communication'][0]
                existing_communication_evaluation.Comm2 = scores['communication'][1]
                existing_communication_evaluation.Comm3 = scores['communication'][2]
                existing_communication_evaluation.Comm4 = scores['communication'][3]
                print(f"Updated existing CommunicationEvaluations for member ID: {member_id}")
            else:
                # Create a new CommunicationEvaluation entry for each evaluatee
                communication_evaluation = CommunicationEvaluations(
                    group_evaluation_id=group_evaluation.id,
                    evaluator_id=user_id,
                    evaluatee_id=member_id,
                    assignment_id=assignment_id,
                    group_id=group_id,
                    Comm1=scores['communication'][0],
                    Comm2=scores['communication'][1],
                    Comm3=scores['communication'][2],
                    Comm4=scores['communication'][3],
                )
                db.session.add(communication_evaluation)
                print(f"Created new CommunicationEvaluations entry for member ID: {member_id}")

            # Handle Problem Solving Evaluations
            if existing_problem_solving_evaluation:
                # Update existing problem_solving evaluation
                existing_problem_solving_evaluation.PS1 = scores['problem_solving'][0]
                existing_problem_solving_evaluation.PS2 = scores['problem_solving'][1]
                existing_problem_solving_evaluation.PS3 = scores['problem_solving'][2]
                existing_problem_solving_evaluation.PS4 = scores['problem_solving'][3]
                print(f"Updated existing ProblemSolvingEvaluations for member ID: {member_id}")
            else:
                # Create a new ProblemSolvingEvaluation entry for each evaluatee
                problem_solving_evaluation = ProblemSolvingEvaluations(
                    group_evaluation_id=group_evaluation.id,
                    evaluator_id=user_id,
                    evaluatee_id=member_id,
                    assignment_id=assignment_id,
                    group_id=group_id,
                    PS1=scores['problem_solving'][0],
                    PS2=scores['problem_solving'][1],
                    PS3=scores['problem_solving'][2],
                    PS4=scores['problem_solving'][3],
                )
                db.session.add(problem_solving_evaluation)
                print(f"Created new ProblemSolvingEvaluations entry for member ID: {member_id}")
        
        #except ValueError as e:
            #print(f"Error converting scores for member {member_id}: {e}")
            #db.session.rollback()
            #continue

    # Commit all individual evaluations to the database
    #try:
    # Commit all individual evaluations to the database
        db.session.commit()
        print("All evaluations committed successfully.")

        for member in group_members:
            evaluatee_id = member.user.id
            # Calculate averages for each evaluatee
            calculate_average_for_evaluatee(assignment_id, group_id, evaluatee_id)

        # Commit after calculating averages
        db.session.commit()

    except Exception as e:
        db.session.rollback()  # Rollback the session on error
        print(f"Error committing to the database: {e}")
        flash('An error occurred while saving your evaluation: {str(e)}', 'error')


def calculate_average_for_evaluatee(assignment_id, group_id, evaluatee_id):
    # Fetch all participation evaluations for this evaluatee
    participation_evaluations = ParticipationEvaluations.query.filter_by(
        evaluatee_id=evaluatee_id, 
        assignment_id=assignment_id, 
        group_id=group_id
    ).all()

    # Calculate average participation
    if participation_evaluations:
        total_participation = sum(evaluation.P1 + evaluation.P2 + evaluation.P3 + evaluation.P4 for evaluation in participation_evaluations)
        count = len(participation_evaluations) * 4 
        average_participation = total_participation / count if count > 0 else 0

    ######

    # Fetch leadership evaluations
    leadership_evaluations = LeadershipEvaluations.query.filter_by(
        evaluatee_id=evaluatee_id, 
        assignment_id=assignment_id, 
        group_id=group_id
    ).all()
    
    # Calculate average leadership
    if leadership_evaluations:
        total_leadership = sum(evaluation.L1 + evaluation.L2 + evaluation.L3 + evaluation.L4 for evaluation in leadership_evaluations)
        count_leadership = len(leadership_evaluations) * 4  
        average_leadership = total_leadership / count_leadership if count_leadership > 0 else 0

    ######

    # Fetch cooperation evaluations
    cooperation_evaluations = CooperationEvaluations.query.filter_by(
        evaluatee_id=evaluatee_id, 
        assignment_id=assignment_id, 
        group_id=group_id
    ).all()
    
    # Calculate average cooperation
    if cooperation_evaluations:
        total_cooperation = sum(evaluation.C1 + evaluation.C2 + evaluation.C3 + evaluation.C4 for evaluation in cooperation_evaluations)
        count_cooperation = len(cooperation_evaluations) * 4  
        average_cooperation = total_cooperation / count_cooperation if count_cooperation > 0 else 0

    ######

    # Fetch time management evaluations
    time_management_evaluations = TimeManagementEvaluations.query.filter_by(
        evaluatee_id=evaluatee_id, 
        assignment_id=assignment_id, 
        group_id=group_id
    ).all()
    
    # Calculate average time management
    if time_management_evaluations:
        total_time_management = sum(evaluation.TM1 + evaluation.TM2 + evaluation.TM3 + evaluation.TM4 for evaluation in time_management_evaluations)
        count_time_management = len(time_management_evaluations) * 4  
        average_time_management = total_time_management / count_time_management if count_time_management > 0 else 0
    
    ######

    # Fetch communication evaluations
    communication_evaluations = CommunicationEvaluations.query.filter_by(
        evaluatee_id=evaluatee_id, 
        assignment_id=assignment_id, 
        group_id=group_id
    ).all()
    
    # Calculate average communication
    if communication_evaluations:
        total_communication = sum(evaluation.Comm1 + evaluation.Comm2 + evaluation.Comm3 + evaluation.Comm4 for evaluation in communication_evaluations)
        count_communication = len(communication_evaluations) * 4  
        average_communication = total_communication / count_communication if count_communication > 0 else 0

    ######

    # Fetch problem solving evaluations
    problem_solving_evaluations = ProblemSolvingEvaluations.query.filter_by(
        evaluatee_id=evaluatee_id, 
        assignment_id=assignment_id, 
        group_id=group_id
    ).all()
    
    # Calculate average cooperation
    if problem_solving_evaluations:
        total_problem_solving = sum(evaluation.PS1 + evaluation.PS2 + evaluation.PS3 + evaluation.PS4 for evaluation in problem_solving_evaluations)
        count_problem_solving = len(problem_solving_evaluations) * 4  
        average_problem_solving = total_problem_solving / count_problem_solving if count_problem_solving > 0 else 0

    ######

    # Fetch or create the GroupEvaluations entry for this evaluatee
    group_evaluation = GroupEvaluations.query.filter_by(
        assignment_id=assignment_id, 
        group_id=group_id, 
        evaluatee_id=evaluatee_id
    ).first()

    if group_evaluation:
        # Update the averages in the existing GroupEvaluations entry
        group_evaluation.Pavg = average_participation  # Update the average participation score
        group_evaluation.Lavg = average_leadership  # Update the average leadership score
        group_evaluation.Cavg = average_cooperation
        group_evaluation.TMavg = average_time_management
        group_evaluation.CommAvg = average_communication
        group_evaluation.PSavg = average_problem_solving


@app.route('/evaluation/<int:course_id>', methods=['GET', 'POST'])
def evaluation(course_id):

    # Fetch the course from the database
    course = Course.query.get(course_id)

    # Fetch the current user from the session
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None  # Get user if logged in

    # Initialize completed_self_evaluation to None
    completed_self_evaluation = 0

    assignments= []

    # Fetch the user's group membership
    group = None
    group_members = []
    total_evaluations = 0
    total_group_evaluations = 0
    completed_group_evaluations = 0
    group_evaluations_needed = []

    if user:
        # Get the group membership for the current user
        group_membership = GroupMembers.query.filter_by(user_id=user.id).first()
        if group_membership:
            group = Groups.query.get(group_membership.group_id)  # Get the group based on membership
            group_members = GroupMembers.query.filter_by(group_id=group.id).all()  # Fetch all members of the group
            
            # Filter out the current user from the group members
            group_members = [member for member in group_members if member.user_id != user.id]
            print(group_members)  # Debugging line to check the content of group_members

            # Fetch assignments for the course
            assignments = Assignments.query.filter_by(course_id=course_id).all()

            num_assignments = len(assignments)
            num_group_members = len(group_members)

            # Calculate total group evaluations
            total_group_evaluations = num_group_members * num_assignments  # Total group evaluations needed

            # Calculate completed group evaluations
            for assignment in assignments:
                completed = calculate_completed_evaluations(user_id, assignment.id, group.id)
                completed_group_evaluations += completed

            # Prepare group evaluations needed for each member and assignment
            for member in group_members:
                for assignment in assignments:
                    # Check if the user has completed the evaluation for this member and assignment
                    completed = check_if_user_completed_evaluation(user.id, assignment.id)  # This function should return True or False
                    group_evaluations_needed.append({
                        'member_name': User.query.get(member.user_id).name,  # Get the member's name
                        'assignment_title': assignment.title,  # Get the assignment title
                        'completed': completed  # Add completed status
                    })

            # Check if self-evaluation exists
            completed_self_evaluation = SelfEvaluations.query.filter_by(user_id=user_id, course_id=course_id).first()

            # Total evaluations = total group evaluations + 1 for self evaluation
            total_evaluations = total_group_evaluations + (1 if not completed_self_evaluation else 0) # Always add 1 for the self-evaluation

    if request.method == 'POST':
        print("Form submitted")
        print(request.form)  # Log the form data

        # Handle form submissions for group evaluation, self-evaluation, and comments
        if 'submit_group_evaluation' in request.form:

            group_id = request.form.get('group_id')  # Get the current user's group ID
            assignment_id = request.form.get('assignment_id')  # Get the assignment ID

            # Save individual evaluations for all group members
            save_group_evaluation(user_id, assignment_id, group_id, group_members, request)
        
            # Set flash message indicating success
            flash('Group evaluation submitted successfully!', 'success')


        elif 'self_participation' in request.form:
            # Handle self-evaluation submission
            self_participation = request.form.get('self_participation')
            self_leadership = request.form.get('self_leadership')
            self_cooperation = request.form.get('self_cooperation')
            self_time_management = request.form.get('self_time_management')
            self_communication = request.form.get('self_communication')
            self_problem_solving = request.form.get('self_problem_solving')

            if completed_self_evaluation:
                # Update existing self-evaluation
                completed_self_evaluation.P = self_participation
                completed_self_evaluation.L = self_leadership
                completed_self_evaluation.C = self_cooperation
                completed_self_evaluation.TM = self_time_management
                completed_self_evaluation.Comm = self_communication
                completed_self_evaluation.PS = self_problem_solving

                db.session.commit()  # Commit the changes
                flash('Self-evaluation updated successfully!', 'success')

            else:
                # Create a new SelfEvaluations object
                self_evaluation = SelfEvaluations(
                    user_id=user.id,
                    course_id=course.id,
                    P=self_participation,
                    L=self_leadership,
                    C=self_cooperation,
                    TM=self_time_management,
                    Comm=self_communication,
                    PS=self_problem_solving
                )

                # Add to the session and commit to the database
                db.session.add(self_evaluation)
                db.session.commit()
                flash('Self-evaluation submitted successfully!', 'success')

        elif 'comment' in request.form:

            comment = request.form.get('comment')
            group_id = request.form.get('group_id') # Retrieve from form
            print(f"Comment: {comment}, Group ID: {group_id}")

            # Create a new comment object
            new_comment = Comments(
                user_id=user_id,
                course_id=course_id,
                group_id=group_id,
                comment=comment
            )

            # Add to the session and commit to the database
            db.session.add(new_comment)
            db.session.commit()

            flash('Comment submitted successfully!', 'success')

        return redirect(url_for('evaluation', course_id=course_id))  # Redirect to the evaluation page after submission

    # Fetch assignments for the dropdowns
    #assignments = Assignments.query.all()  # Fetch all assignments

    return render_template('evaluation.html', 
                            user=user, 
                            course=course, 
                            group=group, 
                            assignments=assignments, 
                            group_members=group_members,
                            total_evaluations=total_evaluations,
                            completed_group_evaluations=completed_group_evaluations,
                            group_evaluations_needed=group_evaluations_needed,
                            completed_self_evaluation=completed_self_evaluation,
                            active_page='evaluation')


@app.route('/feedback/<int:course_id>', methods=['GET'])
def view_feedback(course_id):
    # Fetch the course from the database
    course = Course.query.get(course_id)

    # Fetch the current user from the session
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None  # Get user if logged in

    # Fetch the user's group membership
    group = None
    if user:
        group_membership = GroupMembers.query.filter_by(user_id=user.id).first()
        if group_membership:
            group = Groups.query.get(group_membership.group_id)  # Get the group based on membership

    # Fetch assignments for the course
    assignments = Assignments.query.filter_by(course_id=course_id).all()

    # Fetch average scores for each assignment based on group and evaluatee
    assignment_average_scores = {}
    if group:
        for assignment in assignments:
            # Fetch evaluations for the current assignment, group, and evaluatee
            evaluations = GroupEvaluations.query.filter_by(
                assignment_id=assignment.id,
                group_id=group.id,
                evaluatee_id=user_id  # Assuming evaluatee_id corresponds to user_id
            ).all()

            if evaluations:
                # Store the scores directly from evaluations
                average_scores = {}
                for eval in evaluations:
                    average_scores['P'] = eval.Pavg
                    average_scores['L'] = eval.Lavg
                    average_scores['C'] = eval.Cavg
                    average_scores['TM'] = eval.TMavg
                    average_scores['Comm'] = eval.CommAvg
                    average_scores['PS'] = eval.PSavg

                # Store the scores in the dictionary with the assignment title
                assignment_average_scores[assignment.title] = average_scores

    # Fetch self evaluations
    self_evaluation = SelfEvaluations.query.filter_by(user_id=user_id, course_id=course_id).first()

    # Fetch comments for the course and group
    comments = Comments.query.filter_by(course_id=course_id, group_id=group.id).all() if group else []

    return render_template('view_feedback.html', 
                           user=user, 
                           course=course,
                           assignments=assignments, 
                           group=group, 
                           assignment_average_scores=assignment_average_scores,
                           self_evaluation=self_evaluation, 
                           comments=comments,
                           active_page='view_feedback')


@app.route('/course/<int:course_id>/evaluations')
def view_evaluations(course_id):
    course = Course.query.get_or_404(course_id)

    # Fetch the current user from the session
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None  # Get user if logged in

    # Get all groups in the course
    groups = Groups.query.filter_by(course_id=course_id).all() 

    if not groups:
        return "No groups found for this course.", 404

    # Get group_id from query parameter or default to the first group
    group_id = request.args.get('group_id', type=int)
    if group_id is None and groups:
        group = groups[0]
    else:
        group = Groups.query.get_or_404(group_id)

    # Get all assignments in this course 
    assignments = Assignments.query.filter_by(course_id=course_id).all()

    grouped_evaluations = {}
    predicted_grades = {}
    possible_grades = {}

    for assignment in assignments:
        # For each assignment, get all group evaluations
        evaluations = GroupEvaluations.query.options(
            joinedload(GroupEvaluations.evaluatee)
        ).filter_by(group_id=group.id, assignment_id=assignment.id).all()
        
        grouped_evaluations[assignment.id] = evaluations
        print(f"Assignment: {assignment.title}, Evaluations: {[{'id': e.evaluatee_id, 'Pavg': e.Pavg, 'Lavg': e.Lavg} for e in evaluations]}")

        for eval in evaluations:
            eval_features = {
                'Pavg': eval.Pavg,
                'Lavg': eval.Lavg,
                'Cavg': eval.Cavg,
                'TMavg': eval.TMavg,
                'CommAvg': eval.CommAvg,
                'PSavg': eval.PSavg
            }

            if all(v is not None for v in eval_features.values()):
                input_series = pd.Series(eval_features)
                score_std = input_series.std()
                input_vector = list(input_series) + [score_std]
                pred_group = grade_model.predict([input_vector])[0]
                predicted_grades[eval.evaluatee_id] = pred_group
                possible_grades[eval.evaluatee_id] = group_to_grades.get(pred_group, ['N/A'])
            else:
                predicted_grades[eval.evaluatee_id] = "N/A"
                possible_grades[eval.evaluatee_id] = ['N/A']

    
    # Group Members
    group_members = GroupMembers.query.filter_by(group_id=group.id).all()
    print(f"Group Members: {[{'id': member.user_id, 'name': member.user.name} for member in group_members]}")

    # Self Evaluations
    member_evals = []
    for member in group_members:
        self_eval = SelfEvaluations.query.filter_by(user_id=member.user_id, course_id=course_id).first()
        member_evals.append({
            'name': member.user.name,
            'self_evaluation': self_eval
        })

    # Comments
    comments = Comments.query.filter_by(group_id=group.id, course_id=course_id).all()

    return render_template('view_evaluations.html',
                            course=course,
                            user=user,
                            group=group,
                            all_groups=groups,
                            group_members=group_members,
                            assignments=assignments,
                            grouped_evaluations=grouped_evaluations,
                            predicted_grades=predicted_grades,
                            possible_grades=possible_grades,
                            member_self_eval=member_evals,
                            comments=comments,
                            active_page='view_evaluations')


def generate_evaluation_pdf(course, group, assignments, grouped_evaluations, group_members, possible_grades, member_self_eval, comments):
    styles = getSampleStyleSheet()
    file_name = f"evaluation_report_{course.code}_{group.name}.pdf"
    file_path = os.path.join("generated_pdfs", file_name)

    # Ensure directory exists
    os.makedirs("generated_pdfs", exist_ok=True)

    doc = SimpleDocTemplate(file_path, pagesize=landscape(A4))
    elements = []

    # Title
    elements.append(Paragraph(f"<b>Evaluations Report</b>", styles['Title']))
    elements.append(Paragraph(f"<b>Course:</b> {course.code} - {course.name}", styles['Normal']))
    elements.append(Paragraph(f"<b>Group:</b> {group.name}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Group Evaluations
    elements.append(Paragraph("Average Group Evaluation Scores", styles['Heading2']))
    for assignment in assignments:
        evaluations = grouped_evaluations.get(assignment.id, [])
        if not evaluations:
            continue

        elements.append(Paragraph(f"<b>Assignment:</b> {assignment.title}", styles['Heading3']))

        data = [
            ['Member', 'Participation', 'Leadership', 'Cooperation', 'Time Management', 'Communication', 'Problem Solving', 'Predicted Grade']
        ]

        for member in group_members:
            eval = next((e for e in evaluations if e['evaluatee_id'] == member['user_id']), None)
            row = [
                member['user']['name'],
                round(eval['Pavg'], 2) if eval and eval['Pavg'] is not None else 'N/A',
                round(eval['Lavg'], 2) if eval and eval['Lavg'] is not None else 'N/A',
                round(eval['Cavg'], 2) if eval and eval['Cavg'] is not None else 'N/A',
                round(eval['TMavg'], 2) if eval and eval['TMavg'] is not None else 'N/A',
                round(eval['CommAvg'], 2) if eval and eval['CommAvg'] is not None else 'N/A',
                round(eval['PSavg'], 2) if eval and eval['PSavg'] is not None else 'N/A',
                ", ".join(possible_grades.get(member['user_id'], ['N/A']))
            ]
            data.append(row)

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8)
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

    # Self Evaluation Scores
    elements.append(PageBreak())
    elements.append(Paragraph("Self Evaluation Scores", styles['Heading2']))
    data = [
        ['Member', 'Participation', 'Leadership', 'Cooperation', 'Time Management', 'Communication', 'Problem Solving']
    ]
    for member in member_self_eval:
        se = member['self_evaluation']
        row = [
            member['name'],
            round(se.get('P', 0), 2) if se and se.get('P') is not None else 'N/A',
            round(se.get('L', 0), 2) if se and se.get('L') is not None else 'N/A',
            round(se.get('C', 0), 2) if se and se.get('C') is not None else 'N/A',
            round(se.get('TM', 0), 2) if se and se.get('TM') is not None else 'N/A',
            round(se.get('Comm', 0), 2) if se and se.get('Comm') is not None else 'N/A',
            round(se.get('PS', 0), 2) if se and se.get('PS') is not None else 'N/A'
        ]
        data.append(row)

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    # Comments
    #elements.append(PageBreak())
    elements.append(Paragraph("Comments", styles['Heading2']))
    if comments:
        for comment in comments:
            elements.append(Paragraph(f"<b>Anonymous:</b> {comment['comment']}", styles['Normal']))
            elements.append(Spacer(1, 6))
    else:
        elements.append(Paragraph("No comments available from group members.", styles['Normal']))

    doc.build(elements)
    return file_path


@app.route('/course/<int:course_id>/evaluations/download')
def download_evaluation_pdf(course_id):
    course = Course.query.get_or_404(course_id)

    group_id = request.args.get('group_id', type=int)
    group = Groups.query.get_or_404(group_id)

    assignments = Assignments.query.filter_by(course_id=course_id).all()

    # Group Evaluations
    grouped_evaluations = {}
    predicted_grades = {}
    possible_grades = {}

    for assignment in assignments:
        evaluations = GroupEvaluations.query.options(
            joinedload(GroupEvaluations.evaluatee)
        ).filter_by(group_id=group.id, assignment_id=assignment.id).all()
        
        grouped_evaluations[assignment.id] = []
        for eval in evaluations:
            eval_features = {
                'Pavg': eval.Pavg,
                'Lavg': eval.Lavg,
                'Cavg': eval.Cavg,
                'TMavg': eval.TMavg,
                'CommAvg': eval.CommAvg,
                'PSavg': eval.PSavg
            }

            if all(v is not None for v in eval_features.values()):
                input_series = pd.Series(eval_features)
                score_std = input_series.std()
                input_vector = list(input_series) + [score_std]
                pred_group = grade_model.predict([input_vector])[0]
                predicted_grades[eval.evaluatee_id] = pred_group
                possible_grades[eval.evaluatee_id] = group_to_grades.get(pred_group, ['N/A'])
            else:
                predicted_grades[eval.evaluatee_id] = "N/A"
                possible_grades[eval.evaluatee_id] = ['N/A']

            grouped_evaluations[assignment.id].append({
                'evaluatee_id': eval.evaluatee_id,
                'Pavg': eval.Pavg,
                'Lavg': eval.Lavg,
                'Cavg': eval.Cavg,
                'TMavg': eval.TMavg,
                'CommAvg': eval.CommAvg,
                'PSavg': eval.PSavg
            })

    # Group Members
    group_members = GroupMembers.query.filter_by(group_id=group.id).all()
    members_list = [{'user_id': m.user_id, 'user': {'name': m.user.name}} for m in group_members]

    # Self Evaluations
    member_evals = []
    for member in group_members:
        se = SelfEvaluations.query.filter_by(user_id=member.user_id, course_id=course_id).first()
        se_data = {}
        if se:
            se_data = {'P': se.P, 'L': se.L, 'C': se.C, 'TM': se.TM, 'Comm': se.Comm, 'PS': se.PS}
        member_evals.append({'name': member.user.name, 'self_evaluation': se_data})

    # Comments
    comments = Comments.query.filter_by(group_id=group.id, course_id=course_id).all()
    comments_data = [{'comment': c.comment} for c in comments]

    # Generate PDF
    pdf_path = generate_evaluation_pdf(
        course=course,
        group=group,
        assignments=assignments,
        grouped_evaluations=grouped_evaluations,
        group_members=members_list,
        possible_grades=possible_grades,
        member_self_eval=member_evals,
        comments=comments_data
    )

    return send_file(pdf_path, as_attachment=True)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

