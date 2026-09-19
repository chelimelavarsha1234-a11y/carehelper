from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash
import os

from extensions import db

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-me'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database', 'carecircle.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Import models after db initialization
from models.user import User, ElderlyProfile, FamilyRelationship, HelperProfile
from models.request import HelpRequest
from models.appointment import Appointment
from models.chat import ChatMessage
from models.notification import Notification
from models.helper import CareLog

# Register Blueprints
from routes.auth import auth_bp
from routes.elderly import elderly_bp
from routes.family import family_bp
from routes.helper import helper_bp
from routes.admin import admin_bp
from routes.chatbot import chatbot_bp

app.register_blueprint(auth_bp)
app.register_blueprint(elderly_bp)
app.register_blueprint(family_bp)
app.register_blueprint(helper_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(chatbot_bp)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'elderly':
        return redirect(url_for('elderly.dashboard'))
    if current_user.role == 'family':
        return redirect(url_for('family.dashboard'))
    if current_user.role == 'helper':
        return redirect(url_for('helper.dashboard'))
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    logout_user()
    flash('Invalid account role. Please log in again.', 'danger')
    return redirect(url_for('index'))

def ensure_database_schema():
    inspector = db.inspect(db.engine)
    table_names = set(inspector.get_table_names())

    if 'help_requests' in table_names:
        help_columns = inspector.get_columns('help_requests')
        help_column_names = {col['name'] for col in help_columns}
        if 'elder_name' not in help_column_names:
            db.session.execute(db.text('ALTER TABLE help_requests ADD COLUMN elder_name VARCHAR(120)'))
        if 'elder_phone' not in help_column_names:
            db.session.execute(db.text('ALTER TABLE help_requests ADD COLUMN elder_phone VARCHAR(30)'))
        if 'elder_age' not in help_column_names:
            db.session.execute(db.text('ALTER TABLE help_requests ADD COLUMN elder_age INTEGER'))
        if 'elder_details' not in help_column_names:
            db.session.execute(db.text('ALTER TABLE help_requests ADD COLUMN elder_details TEXT'))
        if 'assigned_helper_name' not in help_column_names:
            db.session.execute(db.text('ALTER TABLE help_requests ADD COLUMN assigned_helper_name VARCHAR(120)'))
        if 'accepted_at' not in help_column_names:
            db.session.execute(db.text('ALTER TABLE help_requests ADD COLUMN accepted_at DATETIME'))
        if 'started_at' not in help_column_names:
            db.session.execute(db.text('ALTER TABLE help_requests ADD COLUMN started_at DATETIME'))
        if 'completed_at' not in help_column_names:
            db.session.execute(db.text('ALTER TABLE help_requests ADD COLUMN completed_at DATETIME'))
        if 'completion_note' not in help_column_names:
            db.session.execute(db.text('ALTER TABLE help_requests ADD COLUMN completion_note TEXT'))

    if 'dedicated_care' in table_names:
        care_columns = inspector.get_columns('dedicated_care')
        care_column_names = {col['name'] for col in care_columns}
        if 'accepted_at' not in care_column_names:
            db.session.execute(db.text('ALTER TABLE dedicated_care ADD COLUMN accepted_at DATETIME'))
        if 'check_in_time' not in care_column_names:
            db.session.execute(db.text('ALTER TABLE dedicated_care ADD COLUMN check_in_time VARCHAR(30)'))
        if 'check_out_time' not in care_column_names:
            db.session.execute(db.text('ALTER TABLE dedicated_care ADD COLUMN check_out_time VARCHAR(30)'))
        if 'care_note' not in care_column_names:
            db.session.execute(db.text('ALTER TABLE dedicated_care ADD COLUMN care_note TEXT'))
        if 'created_at' not in care_column_names:
            db.session.execute(db.text('ALTER TABLE dedicated_care ADD COLUMN created_at DATETIME'))

    db.session.commit()


# Database initialization
with app.app_context():
    db.create_all()
    ensure_database_schema()

    # Demo seed data for project presentation scenario
    if not User.query.filter_by(email='admin@carecircle.com').first():
        admin = User(
            name='CareCircle Admin',
            email='admin@carecircle.com',
            password_hash=generate_password_hash('admin123'),
            phone='9999999999',
            address='HQ',
            location='Hyderabad',
            role='admin'
        )
        db.session.add(admin)

    if not User.query.filter_by(email='lakshmi@carecircle.com').first():
        elderly = User(
            name='Lakshmi Rao',
            email='lakshmi@carecircle.com',
            password_hash=generate_password_hash('lakshmi123'),
            phone='9876543210',
            address='Plot 12, Banjara Hills',
            location='Hyderabad',
            role='elderly'
        )
        db.session.add(elderly)
        db.session.flush()
        db.session.add(ElderlyProfile(user_id=elderly.id, age=72, preferred_language='Telugu', emergency_contact='Anjali Rao'))

    demo_elders = [
        {
            'name': 'Arun',
            'email': 'arun@gmail.com',
            'phone': '9000000001',
            'address': 'Madhapur',
            'location': 'Hyderabad',
            'age': 68,
            'language': 'English',
            'emergency_contact': 'Family Contact',
        },
        {
            'name': 'Deepanth',
            'email': 'deepu@gmail.com',
            'phone': '9000000002',
            'address': 'Kondapur',
            'location': 'Hyderabad',
            'age': 70,
            'language': 'English',
            'emergency_contact': 'Family Contact',
        },
    ]

    for elder_data in demo_elders:
        elder = User.query.filter_by(email=elder_data['email']).first()
        if not elder:
            elder = User(
                name=elder_data['name'],
                email=elder_data['email'],
                password_hash=generate_password_hash('123'),
                phone=elder_data['phone'],
                address=elder_data['address'],
                location=elder_data['location'],
                role='elderly'
            )
            db.session.add(elder)
            db.session.flush()

        elder.role = 'elderly'
        if not ElderlyProfile.query.filter_by(user_id=elder.id).first():
            db.session.add(ElderlyProfile(
                user_id=elder.id,
                age=elder_data['age'],
                preferred_language=elder_data['language'],
                emergency_contact=elder_data['emergency_contact']
            ))

    if not User.query.filter_by(email='anjali@carecircle.com').first():
        family = User(
            name='Anjali Rao',
            email='anjali@carecircle.com',
            password_hash=generate_password_hash('anjali123'),
            phone='9876543211',
            address='Madhapur',
            location='Hyderabad',
            role='family'
        )
        db.session.add(family)
        db.session.flush()
        db.session.add(FamilyRelationship(family_user_id=family.id, elderly_user_id=User.query.filter_by(email='lakshmi@carecircle.com').first().id, relationship='Daughter', permission_level='full'))

    if not User.query.filter_by(email='anitha@carecircle.com').first():
        helper = User(
            name='Anitha Kumar',
            email='anitha@carecircle.com',
            password_hash=generate_password_hash('anitha123'),
            phone='9123456780',
            address='Gachibowli',
            location='Hyderabad',
            role='helper'
        )
        db.session.add(helper)
        db.session.flush()
        db.session.add(HelperProfile(
            user_id=helper.id,
            skills='Grocery, Meal Assistance, Companionship, Appointment Assistance',
            experience='3 years',
            service_area='Hyderabad',
            availability='Available',
            verification_status='verified'
        ))

    demo_helpers = [
        {
            'name': 'Sindhu Reddy',
            'email': 'sindhu@gmail.com',
            'password': '123',
            'phone': '9988776655',
            'address': 'Madhapur',
            'location': 'Hyderabad',
            'skills': 'Grocery Assistance, Companionship, Appointment Assistance, Digital Assistance',
            'experience': '4 years',
            'availability': 'Available',
            'service_area': 'Hyderabad',
        },
        {
            'name': 'Jhansi Nair',
            'email': 'jhansi@gmail.com',
            'password': '123',
            'phone': '9988776654',
            'address': 'Banjara Hills',
            'location': 'Hyderabad',
            'skills': 'Grocery Assistance, Companionship, Appointment Assistance, Digital Assistance',
            'experience': '3 years',
            'availability': 'Available',
            'service_area': 'Hyderabad',
        },
        {
            'name': 'Asma Begum',
            'email': 'asma@gmail.com',
            'password': '123',
            'phone': '9988776653',
            'address': 'Gachibowli',
            'location': 'Hyderabad',
            'skills': 'Grocery Assistance, Companionship, Appointment Assistance, Digital Assistance',
            'experience': '5 years',
            'availability': 'Available',
            'service_area': 'Hyderabad',
        },
    ]

    for helper_data in demo_helpers:
        if not User.query.filter_by(email=helper_data['email']).first():
            helper = User(
                name=helper_data['name'],
                email=helper_data['email'],
                password_hash=generate_password_hash(helper_data['password']),
                phone=helper_data['phone'],
                address=helper_data['address'],
                location=helper_data['location'],
                role='helper'
            )
            db.session.add(helper)
            db.session.flush()
            db.session.add(HelperProfile(
                user_id=helper.id,
                skills=helper_data['skills'],
                experience=helper_data['experience'],
                service_area=helper_data['service_area'],
                availability=helper_data['availability'],
                verification_status='verified'
            ))

    # Keep the documented demo helper accounts usable across existing databases.
    for helper_email in ['sindhu@gmail.com', 'jhansi@gmail.com', 'asma@gmail.com']:
        demo_helper = User.query.filter_by(email=helper_email).first()
        if demo_helper:
            demo_helper.role = 'helper'
            helper_profile = HelperProfile.query.filter_by(user_id=demo_helper.id).first()
            if not helper_profile:
                helper_profile = HelperProfile(user_id=demo_helper.id)
                db.session.add(helper_profile)
            helper_profile.verification_status = 'verified'

    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
