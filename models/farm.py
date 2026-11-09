from app import db
from datetime import datetime


class PoultryFarm(db.Model):
    __tablename__ = 'poultry_farms'

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    farm_name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(200))
    address = db.Column(db.Text)
    farm_size = db.Column(db.String(50))  # e.g., "5 acres"
    total_capacity = db.Column(db.Integer, default=0)
    contact_number = db.Column(db.String(20))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    batches = db.relationship('PoultryBatch', backref='farm', lazy='dynamic',
                              cascade='all, delete-orphan')

    @property
    def total_birds(self):
        return sum(b.number_of_birds for b in self.batches.filter_by(is_active=True).all())

    @property
    def active_batches_count(self):
        return self.batches.filter_by(is_active=True).count()

    def __repr__(self):
        return f'<PoultryFarm {self.farm_name}>'

