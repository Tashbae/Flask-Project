from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # faculty, lecturer, student

class Lecturer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100))
    units_teaching = db.Column(db.String(200))

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    reg_no = db.Column(db.String(30), unique=True)
    course = db.Column(db.String(100))
    units_taken = db.Column(db.String(300))
    date_of_birth = db.Column(db.String(20))
    stage = db.Column(db.String(20))
    phone_number = db.Column(db.String(20))

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reg_no = db.Column(db.String(30))
    unit = db.Column(db.String(100))
    score = db.Column(db.Float)
