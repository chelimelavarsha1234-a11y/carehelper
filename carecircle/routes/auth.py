from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models.user import User, ElderlyProfile, FamilyRelationship, HelperProfile

auth_bp = Blueprint('auth', __name__)


def redirect_to_dashboard(user):
    if user.role == 'elderly':
        return redirect(url_for('elderly.dashboard'))
    if user.role == 'family':
        return redirect(url_for('family.dashboard'))
    if user.role == 'helper':
        return redirect(url_for('helper.dashboard'))
    if user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('index'))


def handle_login(role):
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if not user or user.role != role:
            flash('Invalid email or password for this portal.', 'danger')
            return render_template('login.html', role=role, portal_title=f'{role.title()} Portal')

        if not check_password_hash(user.password_hash, password):
            flash('Invalid email or password for this portal.', 'danger')
            return render_template('login.html', role=role, portal_title=f'{role.title()} Portal')

        login_user(user)
        flash('Welcome back!', 'success')
        return redirect_to_dashboard(user)

    return render_template('login.html', role=role, portal_title=f'{role.title()} Portal')


@auth_bp.route('/register', methods=['GET'])
def register():
    return render_template('register.html')


@auth_bp.route('/register/<role>', methods=['GET', 'POST'])
def register_role(role):
    if role not in ['elderly', 'family', 'helper']:
        abort(404)

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        location = request.form.get('location')

        if not name or not email or not password:
            flash('Please complete the required fields.', 'danger')
            return render_template('register_role.html', role=role)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register_role.html', role=role)

        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'danger')
            return render_template('register_role.html', role=role)

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            phone=phone,
            address=address,
            location=location,
            role=role,
        )
        db.session.add(user)
        db.session.flush()

        if role == 'elderly':
            db.session.add(ElderlyProfile(
                user_id=user.id,
                age=request.form.get('age', 65),
                preferred_language=request.form.get('preferred_language', 'English'),
                emergency_contact=request.form.get('emergency_contact', 'Family')
            ))
        elif role == 'family':
            relationship = request.form.get('relationship', 'Family Member')
            db.session.add(FamilyRelationship(
                family_user_id=user.id,
                elderly_user_id=request.form.get('elderly_user_id', user.id),
                relationship=relationship,
                permission_level='full'
            ))
        elif role == 'helper':
            db.session.add(HelperProfile(
                user_id=user.id,
                skills=request.form.get('skills', 'General Support'),
                experience=request.form.get('experience', 'New'),
                service_area=request.form.get('service_area', location),
                availability=request.form.get('availability', 'Flexible'),
                verification_status='pending'
            ))

        db.session.commit()
        flash('Registration successful. Please log in to continue.', 'success')
        return redirect(url_for('auth.' + f'{role}_login'))

    return render_template('register_role.html', role=role)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html', role='general', portal_title='Choose a portal')


@auth_bp.route('/elderly/login', methods=['GET', 'POST'])
def elderly_login():
    return handle_login('elderly')


@auth_bp.route('/family/login', methods=['GET', 'POST'])
def family_login():
    return handle_login('family')


@auth_bp.route('/helper/login', methods=['GET', 'POST'])
def helper_login():
    return handle_login('helper')


@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    return handle_login('admin')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))
