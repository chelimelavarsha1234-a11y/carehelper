from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from extensions import db
from models.user import User, FamilyRelationship
from models.request import HelpRequest, DedicatedCare
from models.appointment import Appointment
from models.notification import Notification
from models.helper import MedicineReminder

elderly_bp = Blueprint('elderly', __name__)


@elderly_bp.route('/elderly/dashboard')
@login_required
def dashboard():
    if current_user.role != 'elderly':
        abort(403)

    family_members = User.query.join(FamilyRelationship, FamilyRelationship.family_user_id == User.id).filter(FamilyRelationship.elderly_user_id == current_user.id).all()
    helper_requests = HelpRequest.query.filter_by(elderly_id=current_user.id).order_by(HelpRequest.created_at.desc()).limit(5).all()
    appointments = Appointment.query.filter_by(elderly_id=current_user.id).order_by(Appointment.date.desc()).limit(5).all()
    reminders = MedicineReminder.query.filter_by(elderly_id=current_user.id).order_by(MedicineReminder.id.desc()).limit(5).all()
    dedicated = DedicatedCare.query.filter_by(elderly_id=current_user.id).order_by(DedicatedCare.id.desc()).first()
    return render_template('elderly/dashboard.html', family_members=family_members, helper_requests=helper_requests, appointments=appointments, reminders=reminders, dedicated=dedicated)


@elderly_bp.route('/elderly/request-help', methods=['GET', 'POST'])
def request_help():
    if request.method == 'POST':
        category = request.form.get('category')
        description = request.form.get('description')
        elder_name = request.form.get('elder_name') or current_user.name
        elder_phone = request.form.get('elder_phone') or current_user.phone
        elder_age = request.form.get('elder_age') or 65
        elder_details = request.form.get('elder_details') or ''
        location = request.form.get('location', current_user.location)
        req_date = request.form.get('date') or 'Today'
        req_time = request.form.get('time') or 'ASAP'

        full_details = (
            f"{description or 'No extra details provided.'}\n\n"
            f"Elder Name: {elder_name}\n"
            f"Phone: {elder_phone or 'Not provided'}\n"
            f"Age: {elder_age}\n"
            f"Additional Details: {elder_details or 'None'}"
        )

        help_request = HelpRequest(
            elderly_id=current_user.id,
            created_by=current_user.id,
            category=category,
            description=full_details,
            elder_name=elder_name,
            elder_phone=elder_phone,
            elder_age=elder_age,
            elder_details=elder_details,
            location=location,
            date=req_date,
            time=req_time,
            status='open'
        )
        db.session.add(help_request)
        db.session.commit()

        flash('Your help request has been submitted. A verified helper will review it.', 'success')
        return redirect(url_for('elderly.dashboard'))

    return render_template('elderly/request_help.html')


@elderly_bp.route('/elderly/my-requests')
def my_requests():
    requests = HelpRequest.query.filter_by(elderly_id=current_user.id).order_by(HelpRequest.created_at.desc()).all()
    return render_template('elderly/my_requests.html', requests=requests)


@elderly_bp.route('/elderly/my-helper')
def my_helper():
    current_request = HelpRequest.query.filter_by(elderly_id=current_user.id).order_by(HelpRequest.created_at.desc()).first()
    helper = None
    if current_request and current_request.assigned_helper_id:
        helper = User.query.get(current_request.assigned_helper_id)
    return render_template('elderly/my_helper.html', helper=helper, request=current_request)


@elderly_bp.route('/elderly/emergency')
def emergency():
    return render_template('elderly/emergency.html')


@elderly_bp.route('/elderly/dedicated-care')
def dedicated_care():
    current_request = HelpRequest.query.filter_by(elderly_id=current_user.id).order_by(HelpRequest.created_at.desc()).first()
    assigned_helper = None
    if current_request and current_request.assigned_helper_id:
        assigned_helper = User.query.get(current_request.assigned_helper_id)
    return render_template('elderly/dedicated_care.html', request=current_request, helper=assigned_helper)


@elderly_bp.route('/elderly/appointments', methods=['GET', 'POST'])
def appointments():
    if request.method == 'POST':
        hospital = request.form.get('hospital')
        doctor = request.form.get('doctor')
        date = request.form.get('date')
        time = request.form.get('time')
        location = request.form.get('location')
        notes = request.form.get('notes')
        need_companion = bool(request.form.get('need_companion'))

        db.session.add(Appointment(
            elderly_id=current_user.id,
            created_by=current_user.id,
            hospital=hospital,
            doctor=doctor,
            date=date,
            time=time,
            location=location,
            notes=notes,
            need_companion=need_companion
        ))
        db.session.commit()
        flash('Appointment added successfully.', 'success')
        return redirect(url_for('elderly.appointments'))

    appts = Appointment.query.filter_by(elderly_id=current_user.id).all()
    return render_template('elderly/appointments.html', appointments=appts)


@elderly_bp.route('/elderly/medicine-reminders', methods=['GET', 'POST'])
def medicine_reminders():
    if request.method == 'POST':
        med = request.form.get('medicine_name')
        reminder_time = request.form.get('reminder_time')
        frequency = request.form.get('frequency')
        notes = request.form.get('notes')

        db.session.add(MedicineReminder(
            elderly_id=current_user.id,
            medicine_name=med,
            reminder_time=reminder_time,
            frequency=frequency,
            notes=notes,
        ))
        db.session.commit()
        flash('Medicine reminder created.', 'success')
        return redirect(url_for('elderly.medicine_reminders'))

    reminders = MedicineReminder.query.filter_by(elderly_id=current_user.id).all()
    return render_template('elderly/medicine_reminders.html', reminders=reminders)


@elderly_bp.route('/elderly/notifications')
def notifications():
    items = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('elderly/notifications.html', notifications=items)
