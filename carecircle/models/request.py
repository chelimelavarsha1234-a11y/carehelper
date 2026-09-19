from extensions import db


class HelpRequest(db.Model):
    __tablename__ = 'help_requests'
    id = db.Column(db.Integer, primary_key=True)
    elderly_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=True)
    elder_name = db.Column(db.String(120), nullable=True)
    elder_phone = db.Column(db.String(30), nullable=True)
    elder_age = db.Column(db.Integer, nullable=True)
    elder_details = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(120), nullable=True)
    date = db.Column(db.String(20), nullable=True)
    time = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(30), default='requested')
    assigned_helper_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_helper_name = db.Column(db.String(120), nullable=True)
    accepted_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    completion_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())


class DedicatedCare(db.Model):
    __tablename__ = 'dedicated_care'
    id = db.Column(db.Integer, primary_key=True)
    elderly_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    family_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    helper_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    start_date = db.Column(db.String(20), nullable=False)
    end_date = db.Column(db.String(20), nullable=True)
    start_time = db.Column(db.String(20), nullable=False)
    end_time = db.Column(db.String(20), nullable=False)
    support_requirements = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='requested')
    accepted_at = db.Column(db.DateTime, nullable=True)
    check_in_time = db.Column(db.String(30), nullable=True)
    check_out_time = db.Column(db.String(30), nullable=True)
    care_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
