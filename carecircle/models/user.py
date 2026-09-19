from flask_login import UserMixin
from extensions import db


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(80), nullable=True)
    role = db.Column(db.String(30), nullable=False, default='elderly')
    created_at = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f'<User {self.name}>'


class ElderlyProfile(db.Model):
    __tablename__ = 'elderly_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=True)
    preferred_language = db.Column(db.String(80), default='English')
    emergency_contact = db.Column(db.String(120), nullable=True)


class FamilyRelationship(db.Model):
    __tablename__ = 'family_relationships'
    id = db.Column(db.Integer, primary_key=True)
    family_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    elderly_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    relationship = db.Column(db.String(80), nullable=False)
    permission_level = db.Column(db.String(30), default='limited')


class HelperProfile(db.Model):
    __tablename__ = 'helper_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    skills = db.Column(db.String(255), nullable=True)
    experience = db.Column(db.String(80), nullable=True)
    service_area = db.Column(db.String(120), nullable=True)
    availability = db.Column(db.String(120), nullable=True)
    verification_status = db.Column(db.String(30), default='pending')


class Complaint(db.Model):
    __tablename__ = 'complaints'
    id = db.Column(db.Integer, primary_key=True)
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reported_against = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default='open')
    created_at = db.Column(db.DateTime, default=db.func.now())
