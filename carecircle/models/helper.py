from extensions import db


class MedicineReminder(db.Model):
    __tablename__ = 'medicine_reminders'
    id = db.Column(db.Integer, primary_key=True)
    elderly_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    medicine_name = db.Column(db.String(120), nullable=False)
    reminder_time = db.Column(db.String(20), nullable=False)
    frequency = db.Column(db.String(40), nullable=False)
    notes = db.Column(db.Text, nullable=True)


class CheckIn(db.Model):
    __tablename__ = 'check_ins'
    id = db.Column(db.Integer, primary_key=True)
    elderly_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    family_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(30), default='pending')
    response_time = db.Column(db.String(30), nullable=True)


class CareLog(db.Model):
    __tablename__ = 'care_logs'
    id = db.Column(db.Integer, primary_key=True)
    dedicated_care_id = db.Column(db.Integer, db.ForeignKey('dedicated_care.id'), nullable=False)
    helper_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    check_in_time = db.Column(db.String(30), nullable=True)
    check_out_time = db.Column(db.String(30), nullable=True)
    daily_note = db.Column(db.Text, nullable=True)
