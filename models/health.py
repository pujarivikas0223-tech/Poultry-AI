from app import db
from datetime import datetime


class PoultryHealthRecord(db.Model):
    __tablename__ = 'poultry_health_records'

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('poultry_batches.id', ondelete='CASCADE'), nullable=False)
    farm_id = db.Column(db.Integer, db.ForeignKey('poultry_farms.id', ondelete='CASCADE'), nullable=False)

    # Measurements
    number_of_birds = db.Column(db.Integer, nullable=False)
    bird_age_weeks = db.Column(db.Integer, nullable=False)
    body_temperature = db.Column(db.Float)          # Celsius
    feed_consumption_kg = db.Column(db.Float)       # kg/day
    water_consumption_litres = db.Column(db.Float)  # litres/day
    bird_weight_kg = db.Column(db.Float)            # avg kg/bird
    mortality_count = db.Column(db.Integer, default=0)

    # Clinical
    symptoms = db.Column(db.Text)
    health_condition = db.Column(db.String(50))  # Good, Fair, Poor, Critical
    record_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('farmers.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    HEALTH_CONDITIONS = ['Excellent', 'Good', 'Fair', 'Poor', 'Critical']

    @property
    def mortality_rate(self):
        if self.number_of_birds and self.number_of_birds > 0:
            return round((self.mortality_count / self.number_of_birds) * 100, 2)
        return 0.0

    def __repr__(self):
        return f'<HealthRecord batch={self.batch_id} date={self.record_date}>'

