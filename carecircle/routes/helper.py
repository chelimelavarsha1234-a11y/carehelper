from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import or_, and_

from extensions import db
from models.user import User, HelperProfile, ElderlyProfile
from models.request import HelpRequest, DedicatedCare
from models.notification import Notification
from models.chat import ChatMessage
from models.helper import CareLog

helper_bp = Blueprint('helper', __name__)


def normalize_status(value):
    if not value:
        return 'Requested'
    return value.replace('_', ' ').replace('-', ' ').title()


def build_request_context(request_obj):
    elder = db.session.get(User, request_obj.elderly_id)
    creator = db.session.get(User, request_obj.created_by)
    elderly_profile = ElderlyProfile.query.filter_by(user_id=request_obj.elderly_id).first()
    family_member = creator if creator and creator.id != request_obj.elderly_id else None
    if request_obj.created_by == request_obj.elderly_id:
        family_member = None
    return {
        'request': request_obj,
        'elder': elder,
        'elderly_profile': elderly_profile,
        'creator': creator,
        'family_member': family_member,
    }


@helper_bp.route('/helper/dashboard')
@login_required
def dashboard():
    if current_user.role != 'helper':
        abort(403)

    profile = HelperProfile.query.filter_by(user_id=current_user.id).first()
    new_requests = HelpRequest.query.filter(
        HelpRequest.assigned_helper_id.is_(None),
        HelpRequest.status.in_(['requested', 'open'])
    ).order_by(HelpRequest.created_at.desc()).all()
    new_request_cards = [build_request_context(req) for req in new_requests if req.assigned_helper_id is None]

    accepted_requests = HelpRequest.query.filter_by(assigned_helper_id=current_user.id).order_by(HelpRequest.created_at.desc()).all()
    accepted_request_cards = [build_request_context(req) for req in accepted_requests]
    active_request_cards = [card for card in accepted_request_cards if card['request'].status in ['accepted', 'in_progress', 'in progress', 'in-progress']]
    completed_request_cards = [card for card in accepted_request_cards if card['request'].status == 'completed']
    assignments = DedicatedCare.query.filter(
        or_(
            DedicatedCare.helper_id == current_user.id,
            and_(DedicatedCare.helper_id.is_(None), DedicatedCare.status.in_(['requested', 'open']))
        )
    ).order_by(DedicatedCare.created_at.desc()).all()
    assignment_cards = [
        {
            'care': care,
            'elder': db.session.get(User, care.elderly_id),
            'family': db.session.get(User, care.family_id),
        }
        for care in assignments
    ]
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(8).all()
    completed_count = HelpRequest.query.filter_by(assigned_helper_id=current_user.id, status='completed').count()
    today_support = HelpRequest.query.filter(
        HelpRequest.assigned_helper_id == current_user.id,
        HelpRequest.status.in_(['accepted', 'in_progress', 'in progress', 'in-progress'])
    ).count()

    return render_template(
        'helper/dashboard.html',
        profile=profile,
        new_request_cards=new_request_cards,
        accepted_request_cards=accepted_request_cards,
        active_request_cards=active_request_cards,
        completed_request_cards=completed_request_cards,
        assignments=assignments,
        assignment_cards=assignment_cards,
        notifications=notifications,
        completed_count=completed_count,
        today_support=today_support,
        current_date=datetime.utcnow().strftime('%d %b %Y'),
    )


@helper_bp.route('/helper/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        profile = HelperProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            profile = HelperProfile(user_id=current_user.id)
            db.session.add(profile)
        profile.skills = request.form.get('skills')
        profile.experience = request.form.get('experience')
        profile.service_area = request.form.get('service_area')
        profile.availability = request.form.get('availability')
        profile.verification_status = 'verified'
        db.session.commit()
        flash('Your helper profile has been submitted for verification.', 'success')
        return redirect(url_for('helper.dashboard'))
    return render_template('helper/apply.html')


@helper_bp.route('/helper/request/<int:request_id>')
@login_required
def request_details(request_id):
    if current_user.role != 'helper':
        abort(403)

    request_obj = HelpRequest.query.get_or_404(request_id)
    if request_obj.assigned_helper_id not in [None, current_user.id]:
        flash('This request is not assigned to you.', 'warning')
        return redirect(url_for('helper.dashboard'))

    context = build_request_context(request_obj)
    context['helper'] = current_user
    return render_template('helper/request_details.html', **context)


@helper_bp.route('/helper/request/<int:request_id>/accept', methods=['POST'])
@login_required
def accept_request(request_id):
    if current_user.role != 'helper':
        abort(403)
    help_request = HelpRequest.query.get_or_404(request_id)
    if help_request.assigned_helper_id and help_request.assigned_helper_id != current_user.id:
        flash('This request is already assigned to another helper.', 'warning')
        return redirect(url_for('helper.dashboard'))

    if help_request.assigned_helper_id is not None:
        flash('This request has already been accepted.', 'warning')
        return redirect(url_for('helper.dashboard'))

    help_request.status = 'accepted'
    help_request.assigned_helper_id = current_user.id
    help_request.assigned_helper_name = current_user.name
    help_request.accepted_at = datetime.utcnow()
    help_request.created_at = help_request.created_at or datetime.utcnow()
    db.session.add(Notification(
        user_id=help_request.elderly_id,
        message=f'{current_user.name} accepted the help request for {help_request.category}.',
        type='helper_accepted'
    ))

    if help_request.created_by and help_request.created_by != help_request.elderly_id:
        family_member = User.query.get(help_request.created_by)
        if family_member:
            db.session.add(Notification(
                user_id=family_member.id,
                message=f'{current_user.name} accepted the help request for {help_request.category}.',
                type='helper_accepted'
            ))

    db.session.commit()
    flash(f'Help request accepted by {current_user.name}.', 'success')
    return redirect(url_for('helper.dashboard'))


@helper_bp.route('/helper/request/<int:request_id>/start', methods=['POST'])
@login_required
def start_request(request_id):
    if current_user.role != 'helper':
        abort(403)
    help_request = HelpRequest.query.get_or_404(request_id)
    if help_request.assigned_helper_id != current_user.id:
        flash('You can only start your own accepted requests.', 'warning')
        return redirect(url_for('helper.dashboard'))
    if help_request.status not in ['accepted', 'in_progress', 'in progress', 'in-progress']:
        flash('This request must be accepted before it can start.', 'warning')
        return redirect(url_for('helper.dashboard'))

    help_request.status = 'in_progress'
    help_request.started_at = datetime.utcnow()
    db.session.add(Notification(user_id=help_request.elderly_id, message=f'{current_user.name} started support for {help_request.category}.', type='support_started'))
    if help_request.created_by and help_request.created_by != help_request.elderly_id:
        family_member = User.query.get(help_request.created_by)
        if family_member:
            db.session.add(Notification(user_id=family_member.id, message=f'{current_user.name} started support for {help_request.category}.', type='support_started'))
    db.session.commit()
    flash('Support started successfully.', 'success')
    return redirect(url_for('helper.request_details', request_id=request_id))


@helper_bp.route('/helper/request/<int:request_id>/complete', methods=['POST'])
@login_required
def complete_request(request_id):
    if current_user.role != 'helper':
        abort(403)
    help_request = HelpRequest.query.get_or_404(request_id)
    if help_request.assigned_helper_id != current_user.id:
        flash('You can only complete your own accepted requests.', 'warning')
        return redirect(url_for('helper.dashboard'))
    if help_request.status not in ['accepted', 'in_progress', 'in progress', 'in-progress']:
        flash('Only active requests can be completed.', 'warning')
        return redirect(url_for('helper.dashboard'))

    help_request.status = 'completed'
    help_request.completed_at = datetime.utcnow()
    help_request.completion_note = request.form.get('completion_note') or 'Support completed successfully.'
    db.session.add(Notification(user_id=help_request.elderly_id, message=f'{current_user.name} completed the support request for {help_request.category}.', type='support_completed'))
    if help_request.created_by and help_request.created_by != help_request.elderly_id:
        family_member = User.query.get(help_request.created_by)
        if family_member:
            db.session.add(Notification(user_id=family_member.id, message=f'{current_user.name} completed the support request for {help_request.category}.', type='support_completed'))
    db.session.commit()
    flash('Support request marked as completed.', 'success')
    return redirect(url_for('helper.request_details', request_id=request_id))


@helper_bp.route('/helper/my-accepted-requests')
@login_required
def my_accepted_requests():
    if current_user.role != 'helper':
        abort(403)

    status_filter = request.args.get('status', 'all')
    query = HelpRequest.query.filter_by(assigned_helper_id=current_user.id)
    if status_filter != 'all':
        query = query.filter(HelpRequest.status == status_filter)
    requests = query.order_by(HelpRequest.created_at.desc()).all()
    return render_template('helper/accepted_requests.html', requests=requests, status_filter=status_filter, normalize_status=normalize_status)


@helper_bp.route('/helper/dedicated/<int:id>/accept', methods=['POST'])
@login_required
def accept_dedicated(id):
    if current_user.role != 'helper':
        abort(403)
    care = DedicatedCare.query.get_or_404(id)
    if care.helper_id and care.helper_id != current_user.id:
        flash('This assignment is already assigned to another helper.', 'warning')
        return redirect(url_for('helper.dashboard'))

    care.helper_id = current_user.id
    care.status = 'accepted'
    care.accepted_at = datetime.utcnow()
    db.session.add(Notification(user_id=care.elderly_id, message=f'{current_user.name} accepted the dedicated care assignment for you.', type='assignment_accepted'))
    if care.family_id and care.family_id != care.elderly_id:
        db.session.add(Notification(user_id=care.family_id, message=f'{current_user.name} accepted the dedicated care assignment.', type='assignment_accepted'))
    db.session.commit()
    flash('Dedicated care assignment accepted.', 'success')
    return redirect(url_for('helper.dashboard'))


@helper_bp.route('/helper/dedicated/<int:care_id>/checkin', methods=['POST'])
@login_required
def checkin(care_id):
    if current_user.role != 'helper':
        abort(403)
    note = request.form.get('daily_note', '')
    care = DedicatedCare.query.get_or_404(care_id)
    if care.helper_id != current_user.id:
        flash('You can only check in for your own care assignments.', 'warning')
        return redirect(url_for('helper.dashboard'))

    log = CareLog.query.filter_by(dedicated_care_id=care.id).first()
    check_in_time = datetime.utcnow().strftime('%d %b %Y, %H:%M')
    if not log:
        log = CareLog(dedicated_care_id=care.id, helper_id=current_user.id, check_in_time=check_in_time, daily_note=note)
        db.session.add(log)
    else:
        log.check_in_time = check_in_time
        log.daily_note = note

    care.status = 'in_progress'
    care.check_in_time = check_in_time
    care.care_note = note or care.care_note
    db.session.add(Notification(user_id=care.elderly_id, message=f'{current_user.name} checked in for the dedicated care assignment.', type='check_in'))
    db.session.commit()
    flash('Check-in recorded.', 'success')
    return redirect(url_for('helper.dashboard'))


@helper_bp.route('/helper/dedicated/<int:care_id>/note', methods=['POST'])
@login_required
def add_care_note(care_id):
    if current_user.role != 'helper':
        abort(403)
    care = DedicatedCare.query.get_or_404(care_id)
    if care.helper_id != current_user.id:
        abort(403)
    care.care_note = request.form.get('care_note', '').strip() or care.care_note
    db.session.commit()
    flash('Care note saved.', 'success')
    return redirect(url_for('helper.dashboard'))


@helper_bp.route('/helper/dedicated/<int:care_id>/checkout', methods=['POST'])
@login_required
def checkout(care_id):
    if current_user.role != 'helper':
        abort(403)
    care = DedicatedCare.query.get_or_404(care_id)
    if care.helper_id != current_user.id:
        abort(403)
    check_out_time = datetime.utcnow().strftime('%d %b %Y, %H:%M')
    care.check_out_time = check_out_time
    care.status = 'completed'
    log = CareLog.query.filter_by(dedicated_care_id=care.id).first()
    if log:
        log.check_out_time = check_out_time
    db.session.add(Notification(user_id=care.elderly_id, message=f'{current_user.name} checked out from the dedicated care assignment.', type='check_out'))
    if care.family_id and care.family_id != care.elderly_id:
        db.session.add(Notification(user_id=care.family_id, message=f'{current_user.name} completed the dedicated care assignment.', type='check_out'))
    db.session.commit()
    flash('Check-out recorded.', 'success')
    return redirect(url_for('helper.dashboard'))


@helper_bp.route('/helper/chat/<int:user_id>')
def chat(user_id):
    if not current_user.is_authenticated or current_user.role != 'helper':
        abort(403)
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user.id) & (ChatMessage.receiver_id == user_id)) |
        ((ChatMessage.sender_id == user_id) & (ChatMessage.receiver_id == current_user.id))
    ).order_by(ChatMessage.created_at.asc()).all()
    return render_template('helper/chat.html', user_id=user_id, messages=messages)
