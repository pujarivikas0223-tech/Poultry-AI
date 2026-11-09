from app import db
from datetime import datetime, date


class VaccinationRecord(db.Model):
    __tablename__ = 'vaccination_records'

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('poultry_batches.id', ondelete='CASCADE'), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)

    vaccine_name = db.Column(db.String(150), nullable=False)
    vaccination_date = db.Column(db.Date, nullable=False)
    next_vaccination_date = db.Column(db.Date)
    dosage = db.Column(db.String(100))
    route = db.Column(db.String(50))  # Drinking water, Spray, Eye drop, Injection
    batch_lot_number = db.Column(db.String(100))
    administered_by = db.Column(db.String(150))
    status = db.Column(db.String(30), default='Completed')  # Completed, Upcoming, Missed
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ROUTES = ['Drinking water', 'Spray', 'Eye drop', 'Intranasal', 'Injection', 'Wing web', 'Other']
    STATUSES = ['Completed', 'Upcoming', 'Missed']

    @property
    def is_upcoming(self):
        if self.next_vaccination_date:
            return self.next_vaccination_date >= date.today() and self.status == 'Upcoming'
        return False

    @property
    def is_missed(self):
        if self.next_vaccination_date:
            return self.next_vaccination_date < date.today() and self.status == 'Upcoming'
        return False

    # Relationship to farmer
    farmer = db.relationship('Farmer', backref='vaccination_records', lazy=True)

    def __repr__(self):
        return f'<VaccinationRecord {self.vaccine_name} batch={self.batch_id}>'


class VaccinationSchedule(db.Model):
    __tablename__ = 'vaccination_schedules'

    id = db.Column(db.Integer, primary_key=True)
    poultry_type = db.Column(db.String(50), nullable=False)  # Broiler, Layer, etc.
    vaccine_name = db.Column(db.String(150), nullable=False)
    recommended_age_weeks = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    route = db.Column(db.String(50))
    notes = db.Column(db.Text)
    is_mandatory = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<VaccinationSchedule {self.vaccine_name} at {self.recommended_age_weeks} weeks>'

