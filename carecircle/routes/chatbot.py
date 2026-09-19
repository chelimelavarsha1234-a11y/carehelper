from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from extensions import db
from models.chat import ChatMessage
from models.notification import Notification
from models.user import User
from models.request import HelpRequest, DedicatedCare
from models.appointment import Appointment

chatbot_bp = Blueprint('chatbot', __name__)


@chatbot_bp.route('/chatbot')
@login_required
def chatbot_index():
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user.id) | (ChatMessage.receiver_id == current_user.id))
    ).order_by(ChatMessage.created_at.asc()).all()
    return render_template('chatbot/index.html', messages=messages)


@chatbot_bp.route('/chatbot/ask', methods=['POST'])
def chatbot_ask():
    message = request.form.get('message', '').strip()
    if not message:
        if request.form.get('ajax') == '1':
            return jsonify({'reply': 'Please type a message first.'})
        return redirect(url_for('chatbot.chatbot_index'))

    response = generate_response(current_user, message)
    db.session.add(ChatMessage(sender_id=current_user.id, receiver_id=current_user.id, message=message, message_type='user'))
    db.session.add(ChatMessage(sender_id=current_user.id, receiver_id=current_user.id, message=response, message_type='assistant'))
    db.session.commit()

    if request.form.get('ajax') == '1':
        return jsonify({'reply': response})

    flash(response, 'info')
    return redirect(url_for('chatbot.chatbot_index'))


def generate_response(user, message):
    text = message.lower()
    if 'medical' in text or 'medicine dosage' in text or 'diagnose' in text:
        return 'I can help with care coordination, but I cannot provide medical advice. Please contact a qualified healthcare professional.'
    if 'grocery' in text or 'help buying' in text:
        return 'I can help you create a grocery assistance request. Please use the Request Help button on your dashboard.'
    if 'appointment' in text:
        appointment = Appointment.query.filter_by(elderly_id=user.id).order_by(Appointment.date.asc()).first()
        if appointment:
            return f'Your next appointment is {appointment.date} at {appointment.time} at {appointment.hospital}.'
        return 'You do not have any upcoming appointments recorded.'
    if 'helper' in text or 'assigned' in text:
        care = DedicatedCare.query.filter_by(elderly_id=user.id).order_by(DedicatedCare.id.desc()).first()
        if care and care.helper_id:
            helper = User.query.get(care.helper_id)
            return f'Yes. {helper.name} is assigned for the care period from {care.start_time} to {care.end_time}.'
        pending = HelpRequest.query.filter_by(elderly_id=user.id, status='open').first()
        if pending:
            return 'Your request is still waiting for a helper to accept it.'
        return 'No helper is assigned yet.'
    if 'care status' in text or 'status' in text:
        care = DedicatedCare.query.filter_by(elderly_id=user.id).order_by(DedicatedCare.id.desc()).first()
        if care:
            return f'Your care status is {care.status}. The scheduled support is {care.support_requirements}.'
        return 'There is no active dedicated care assignment.'
    if 'dedicated care' in text or 'arrange care' in text:
        return 'I can help you start a dedicated care request. Please use the Arrange Dedicated Care option from your dashboard.'
    if 'notification' in text:
        return 'You can view notifications from your dashboard to see new updates and request status.'
    if 'family' in text:
        return 'Your trusted family members can stay informed through your dashboard and care updates.'
    if 'emergency' in text or 'sos' in text:
        return 'CareCircle does not replace emergency services. Please call local emergency services or your emergency contacts immediately.'
    return 'I can help with care coordination requests, appointments, helper status, notifications, and dedicated care support.'
