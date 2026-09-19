from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from extensions import db
from models.user import User, HelperProfile, Complaint
from models.request import HelpRequest, DedicatedCare

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        abort(403)

    total_elderly = User.query.filter_by(role='elderly').count()
    total_family = User.query.filter_by(role='family').count()
    total_helpers = User.query.filter_by(role='helper').count()
    verified = HelperProfile.query.filter_by(verification_status='verified').count()
    pending = HelperProfile.query.filter_by(verification_status='pending').count()
    active_requests = HelpRequest.query.filter_by(status='open').count()
    completed_requests = HelpRequest.query.filter_by(status='completed').count()
    active_care = DedicatedCare.query.filter_by(status='accepted').count()
    complaints = Complaint.query.count()

    return render_template('admin/dashboard.html',
        total_elderly=total_elderly,
        total_family=total_family,
        total_helpers=total_helpers,
        verified=verified,
        pending=pending,
        active_requests=active_requests,
        completed_requests=completed_requests,
        active_care=active_care,
        complaints=complaints)


@admin_bp.route('/admin/helpers')
def helpers():
    profiles = HelperProfile.query.all()
    users = User.query.filter_by(role='helper').all()
    return render_template('admin/helpers.html', profiles=profiles, users=users)


@admin_bp.route('/admin/helper/<int:id>/verify')
def verify_helper(id):
    profile = HelperProfile.query.get_or_404(id)
    profile.verification_status = 'verified'
    db.session.commit()
    flash('Helper verified successfully.', 'success')
    return redirect(url_for('admin.helpers'))


@admin_bp.route('/admin/helper/<int:id>/reject')
def reject_helper(id):
    profile = HelperProfile.query.get_or_404(id)
    profile.verification_status = 'rejected'
    db.session.commit()
    flash('Helper rejected.', 'warning')
    return redirect(url_for('admin.helpers'))
