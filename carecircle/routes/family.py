from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from extensions import db
from models.user import User, FamilyRelationship
from models.request import HelpRequest, DedicatedCare
from models.notification import Notification
from models.chat import ChatMessage

family_bp = Blueprint('family', __name__)


@family_bp.route('/family/dashboard')
@login_required
def dashboard():
    if current_user.role != 'family':
        abort(403)

    linked_elders = User.query.join(FamilyRelationship, FamilyRelationship.elderly_user_id == User.id).filter(FamilyRelationship.family_user_id == current_user.id).all()
    dedicated = DedicatedCare.query.filter_by(family_id=current_user.id).order_by(DedicatedCare.id.desc()).first()
    return render_template('family/dashboard.html', linked_elders=linked_elders, dedicated=dedicated)


@family_bp.route('/family/arrange-care', methods=['GET', 'POST'])
@login_required
def arrange_care():
    if current_user.role != 'family':
        abort(403)

    linked_elders = User.query.join(FamilyRelationship, FamilyRelationship.elderly_user_id == User.id).filter(FamilyRelationship.family_user_id == current_user.id).all()

    if request.method == 'POST':
        elderly_id = request.form.get('elderly_id')
        if not elderly_id:
            flash('Please select an elderly person first.', 'warning')
            return render_template('family/arrange_care.html', linked_elders=linked_elders)

        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date') or start_date
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        support = request.form.get('support_requirements')

        care = DedicatedCare(
            elderly_id=elderly_id,
            family_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            support_requirements=support,
            status='requested'
        )
        db.session.add(care)
        db.session.commit()

        flash('Dedicated care request created. Matching verified helpers is available in the demo flow.', 'success')
        return redirect(url_for('family.dashboard'))

    return render_template('family/arrange_care.html', linked_elders=linked_elders)


@family_bp.route('/family/request-help', methods=['GET', 'POST'])
@login_required
def request_help():
    if current_user.role != 'family':
        abort(403)

    linked_elders = User.query.join(FamilyRelationship, FamilyRelationship.elderly_user_id == User.id).filter(FamilyRelationship.family_user_id == current_user.id).all()

    if request.method == 'POST':
        elderly_id = request.form.get('elderly_id')
        if not elderly_id:
            flash('Please select an elderly person before submitting a request.', 'warning')
            return render_template('family/request_help.html', linked_elders=linked_elders)

        elderly = User.query.get(elderly_id)
        category = request.form.get('category')
        description = request.form.get('description')
        location = request.form.get('location') or (elderly.location if elderly else '')

        db.session.add(HelpRequest(
            elderly_id=elderly_id,
            created_by=current_user.id,
            category=category,
            description=description,
            elder_name=elderly.name if elderly else None,
            elder_phone=elderly.phone if elderly else None,
            elder_age=(db.session.get(User, elderly_id) and None) if False else None,
            elder_details=f"Care request submitted by {current_user.name}.",
            location=location,
            date='Today',
            time='ASAP',
            status='open'
        ))
        db.session.commit()
        flash('Help request submitted with a verified-helper matching flow.', 'success')
        return redirect(url_for('family.dashboard'))

    return render_template('family/request_help.html', linked_elders=linked_elders)


@family_bp.route('/family/chat/<int:elderly_id>')
def chat(elderly_id):
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user.id) & (ChatMessage.receiver_id == elderly_id)) |
        ((ChatMessage.sender_id == elderly_id) & (ChatMessage.receiver_id == current_user.id))
    ).order_by(ChatMessage.created_at.asc()).all()
    return render_template('family/chat.html', elderly_id=elderly_id, messages=messages)
