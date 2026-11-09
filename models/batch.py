from app import db
from datetime import datetime


class PoultryBatch(db.Model):
    __tablename__ = 'poultry_batches'

    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('poultry_farms.id', ondelete='CASCADE'), nullable=False)
    batch_name = db.Column(db.String(100), nullable=False)
    breed_name = db.Column(db.String(100), nullable=False)
    poultry_type = db.Column(db.String(50), nullable=False)  # Broiler, Layer, Turkey, Duck, etc.
    number_of_birds = db.Column(db.Integer, nullable=False, default=0)
    bird_age_weeks = db.Column(db.Integer, default=0)
    arrival_date = db.Column(db.Date, nullable=False)
    expected_harvest_date = db.Column(db.Date)
    source = db.Column(db.String(150))  # Hatchery / supplier name
    purchase_price_per_bird = db.Column(db.Float, default=0.0)
    batch_status = db.Column(db.String(30), default='Active')  # Active, Harvested, Closed
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    health_records = db.relationship('PoultryHealthRecord', backref='batch', lazy='dynamic',
                                     cascade='all, delete-orphan')
    vaccinations = db.relationship('VaccinationRecord', backref='batch', lazy='dynamic',
                                   cascade='all, delete-orphan')
    predictions = db.relationship('DiseasePrediction', backref='batch', lazy='dynamic',
                                  cascade='all, delete-orphan')

    POULTRY_TYPES = ['Broiler', 'Layer', 'Turkey', 'Duck', 'Quail', 'Geese', 'Other']
    BATCH_STATUSES = ['Active', 'Harvested', 'Sold', 'Closed', 'Quarantined']

    def __repr__(self):
        return f'<PoultryBatch {self.batch_name}>'


class PoultryBreed(db.Model):
    __tablename__ = 'poultry_breeds'

    id = db.Column(db.Integer, primary_key=True)
    breed_name = db.Column(db.String(100), unique=True, nullable=False)
    poultry_type = db.Column(db.String(50))
    description = db.Column(db.Text)
    avg_weight_kg = db.Column(db.Float)
    egg_production = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PoultryBreed {self.breed_name}>'

