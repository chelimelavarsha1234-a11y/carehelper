from extensions import db


class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    elderly_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    hospital = db.Column(db.String(120), nullable=False)
    doctor = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(180), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    need_companion = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
