# models.py

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum as SQLAlchemyEnum


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'User'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Store hashed passwords
    role = db.Column(SQLAlchemyEnum('student', 'lecturer', 'admin', name='user_roles'), nullable=False)
    #role = db.Column(db.Enum('student', 'lecturer', name='user_roles'), nullable=False)

    # Relationship with course enrollments
    enrollments = db.relationship('UserCourseEnrollment', back_populates='user')

    # Relationship to GroupEvaluations
    group_evaluations = db.relationship('GroupEvaluations', back_populates='evaluatee', lazy=True)  # Add this line


class Course(db.Model):
    __tablename__ = 'Course'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)

    # Relationship with enrollments
    enrollments = db.relationship('UserCourseEnrollment', back_populates='course')

    # Relationship to Assignments
    assignments = db.relationship('Assignments', back_populates='course')

    # Relationship to Assignments
    self_evaluations = db.relationship('SelfEvaluations', back_populates='course')

    comments = db.relationship('Comments', back_populates='course')


class UserCourseEnrollment(db.Model):
    __tablename__ = 'UserCourseEnrollment'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('Course.id'), nullable=False)
    role = db.Column(db.Enum('student', 'lecturer', name='user_roles'), nullable=False)

    # Relationship to User
    user = db.relationship('User', back_populates='enrollments')

    # Relationship to Course
    course = db.relationship('Course', back_populates='enrollments')

    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', 'role', name='uq_user_course_role'),)


class Groups(db.Model):
    __tablename__ = 'Groups'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('Course.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    # Relationship to Course
    course = db.relationship('Course', backref='groups')

    # Relationship to GroupMembers
    members = db.relationship('GroupMembers', back_populates='group')

    # Relationship to GroupEvaluations
    group_evaluations = db.relationship('GroupEvaluations', back_populates='group', lazy=True)

    # Relationship to ParticipationEvaluations
    participation_evaluations = db.relationship('ParticipationEvaluations', back_populates='group', lazy=True)  # Add this line
    leadership_evaluations = db.relationship('LeadershipEvaluations', back_populates='group', lazy=True)
    cooperation_evaluations = db.relationship('CooperationEvaluations', back_populates='group', lazy=True)
    time_management_evaluations = db.relationship('TimeManagementEvaluations', back_populates='group', lazy=True)
    communication_evaluations = db.relationship('CommunicationEvaluations', back_populates='group', lazy=True)
    problem_solving_evaluations = db.relationship('ProblemSolvingEvaluations', back_populates='group', lazy=True)


class GroupMembers(db.Model):
    __tablename__ = 'GroupMembers'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('Groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)

    # Relationship to Groups
    group = db.relationship('Groups', back_populates='members')
    
    # Relationship to User
    user = db.relationship('User')

    __table_args__ = (db.UniqueConstraint('group_id', 'user_id', name='uq_group_user'),)  # Prevent duplicate members in the same group


class Assignments(db.Model):
    __tablename__ = 'Assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('Course.id'), nullable=False)

    # Relationship to Course
    course = db.relationship('Course', back_populates='assignments')

    # Relationship to GroupEvaluations
    group_evaluations = db.relationship('GroupEvaluations', back_populates='assignment', lazy=True)  # Add this line

    participation_evaluations = db.relationship('ParticipationEvaluations', back_populates='assignment', lazy=True)
    leadership_evaluations = db.relationship('LeadershipEvaluations', back_populates='assignment', lazy=True)
    cooperation_evaluations = db.relationship('CooperationEvaluations', back_populates='assignment', lazy=True)
    time_management_evaluations = db.relationship('TimeManagementEvaluations', back_populates='assignment', lazy=True)
    communication_evaluations = db.relationship('CommunicationEvaluations', back_populates='assignment', lazy=True)
    problem_solving_evaluations = db.relationship('ProblemSolvingEvaluations', back_populates='assignment', lazy=True)


class GroupEvaluations(db.Model):
    __tablename__ = 'GroupEvaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('Assignments.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('Groups.id'), nullable=False)
    evaluatee_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    
    Pavg = db.Column(db.Float, nullable=True)  # Average Participation
    Lavg = db.Column(db.Float, nullable=True)  # Average Leadership
    Cavg = db.Column(db.Float, nullable=True)  # Average Cooperation
    TMavg = db.Column(db.Float, nullable=True)  # Average Time Management
    CommAvg = db.Column(db.Float, nullable=True)  # Average Communication
    PSavg = db.Column(db.Float, nullable=True)  # Average Problem Solving

    assignment = db.relationship('Assignments', back_populates='group_evaluations')  # Relationship to Assignments
    group = db.relationship('Groups', back_populates='group_evaluations')  # Relationship to Groups
    evaluatee = db.relationship('User', back_populates='group_evaluations')  # Relationship to User
    
    # Relationships
    participation_evaluations = db.relationship('ParticipationEvaluations', back_populates='group_evaluation', lazy=True)
    leadership_evaluations = db.relationship('LeadershipEvaluations', back_populates='group_evaluation', lazy=True)
    cooperation_evaluations = db.relationship('CooperationEvaluations', back_populates='group_evaluation', lazy=True)
    time_management_evaluations = db.relationship('TimeManagementEvaluations', back_populates='group_evaluation', lazy=True)
    communication_evaluations = db.relationship('CommunicationEvaluations', back_populates='group_evaluation', lazy=True)
    problem_solving_evaluations = db.relationship('ProblemSolvingEvaluations', back_populates='group_evaluation', lazy=True)


class ParticipationEvaluations(db.Model):
    __tablename__ = 'ParticipationEvaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    group_evaluation_id = db.Column(db.Integer, db.ForeignKey('GroupEvaluations.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    evaluatee_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('Assignments.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('Groups.id'), nullable=False) 
    
    P1 = db.Column(db.Float, nullable=True)
    P2 = db.Column(db.Float, nullable=True)
    P3 = db.Column(db.Float, nullable=True)
    P4 = db.Column(db.Float, nullable=True)

    # Relationships
    assignment = db.relationship('Assignments', back_populates='participation_evaluations')
    group = db.relationship('Groups', back_populates='participation_evaluations')
    group_evaluation = db.relationship('GroupEvaluations', back_populates='participation_evaluations')


class LeadershipEvaluations(db.Model):
    __tablename__ = 'LeadershipEvaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    group_evaluation_id = db.Column(db.Integer, db.ForeignKey('GroupEvaluations.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    evaluatee_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('Assignments.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('Groups.id'), nullable=False)
    
    L1 = db.Column(db.Float, nullable=True)
    L2 = db.Column(db.Float, nullable=True)
    L3 = db.Column(db.Float, nullable=True)
    L4 = db.Column(db.Float, nullable=True)

    # Relationships
    assignment = db.relationship('Assignments', back_populates='leadership_evaluations')
    group = db.relationship('Groups', back_populates='leadership_evaluations')
    group_evaluation = db.relationship('GroupEvaluations', back_populates='leadership_evaluations')


class CooperationEvaluations(db.Model):
    __tablename__ = 'CooperationEvaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    group_evaluation_id = db.Column(db.Integer, db.ForeignKey('GroupEvaluations.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    evaluatee_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('Assignments.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('Groups.id'), nullable=False)
    
    C1 = db.Column(db.Float, nullable=True)
    C2 = db.Column(db.Float, nullable=True)
    C3 = db.Column(db.Float, nullable=True)
    C4 = db.Column(db.Float, nullable=True)

    # Relationships
    assignment = db.relationship('Assignments', back_populates='cooperation_evaluations')
    group = db.relationship('Groups', back_populates='cooperation_evaluations')
    group_evaluation = db.relationship('GroupEvaluations', back_populates='cooperation_evaluations')


class TimeManagementEvaluations(db.Model):
    __tablename__ = 'TimeManagementEvaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    group_evaluation_id = db.Column(db.Integer, db.ForeignKey('GroupEvaluations.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    evaluatee_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)    
    assignment_id = db.Column(db.Integer, db.ForeignKey('Assignments.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('Groups.id'), nullable=False)

    TM1 = db.Column(db.Float, nullable=True)
    TM2 = db.Column(db.Float, nullable=True)
    TM3 = db.Column(db.Float, nullable=True)
    TM4 = db.Column(db.Float, nullable=True)

    # Relationships
    assignment = db.relationship('Assignments', back_populates='time_management_evaluations')
    group = db.relationship('Groups', back_populates='time_management_evaluations')
    group_evaluation = db.relationship('GroupEvaluations', back_populates='time_management_evaluations')


class CommunicationEvaluations(db.Model):
    __tablename__ = 'CommunicationEvaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    group_evaluation_id = db.Column(db.Integer, db.ForeignKey('GroupEvaluations.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    evaluatee_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('Assignments.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('Groups.id'), nullable=False)
    
    Comm1 = db.Column(db.Float, nullable=True)
    Comm2 = db.Column(db.Float, nullable=True)
    Comm3 = db.Column(db.Float, nullable=True)
    Comm4 = db.Column(db.Float, nullable=True)

    # Relationships
    assignment = db.relationship('Assignments', back_populates='communication_evaluations')
    group = db.relationship('Groups', back_populates='communication_evaluations')
    group_evaluation = db.relationship('GroupEvaluations', back_populates='communication_evaluations')


class ProblemSolvingEvaluations(db.Model):
    __tablename__ = 'ProblemSolvingEvaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    group_evaluation_id = db.Column(db.Integer, db.ForeignKey('GroupEvaluations.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    evaluatee_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('Assignments.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('Groups.id'), nullable=False)
    
    PS1 = db.Column(db.Float, nullable=True)
    PS2 = db.Column(db.Float, nullable=True)
    PS3 = db.Column(db.Float, nullable=True)
    PS4 = db.Column(db.Float, nullable=True)

    # Relationships
    assignment = db.relationship('Assignments', back_populates='problem_solving_evaluations')
    group = db.relationship('Groups', back_populates='problem_solving_evaluations')
    group_evaluation = db.relationship('GroupEvaluations', back_populates='problem_solving_evaluations')


class SelfEvaluations(db.Model):
    __tablename__ = 'SelfEvaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('Course.id'), nullable=False)

    P = db.Column(db.Float, nullable=True)  # Self-evaluation Participation
    L = db.Column(db.Float, nullable=True)  # Self-evaluation Leadership
    C = db.Column(db.Float, nullable=True)  # Self-evaluation Cooperation
    TM = db.Column(db.Float, nullable=True)  # Self-evaluation Time Management
    Comm = db.Column(db.Float, nullable=True)  # Self-evaluation Communication
    PS = db.Column(db.Float, nullable=True)  # Self-evaluation Problem Solving

    # Relationships
    course = db.relationship('Course', back_populates='self_evaluations')


class Comments(db.Model):
    __tablename__ = 'Comments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('Course.id'), nullable=False) 
    group_id = db.Column(db.Integer, db.ForeignKey('Groups.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)

    # Relationships
    course = db.relationship('Course', back_populates='comments')
    group = db.relationship('Groups', backref='comments')

