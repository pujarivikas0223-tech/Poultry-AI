from app import db
from datetime import datetime


class Disease(db.Model):
    __tablename__ = 'diseases'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text)
    symptoms = db.Column(db.Text)
    prevention = db.Column(db.Text)
    hygiene_recommendations = db.Column(db.Text)
    biosecurity_measures = db.Column(db.Text)
    isolation_guidance = db.Column(db.Text)
    veterinary_advice = db.Column(db.Text)
    severity = db.Column(db.String(20), default='Medium')  # Low, Medium, High, Critical
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    predictions = db.relationship('DiseasePrediction', backref='disease_info',
                                  lazy='dynamic', foreign_keys='DiseasePrediction.disease_id')

    def __repr__(self):
        return f'<Disease {self.name}>'


class DiseasePrediction(db.Model):
    __tablename__ = 'disease_predictions'

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('poultry_batches.id', ondelete='CASCADE'), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    disease_id = db.Column(db.Integer, db.ForeignKey('diseases.id'), nullable=True)

    # Input features used for prediction
    bird_age_weeks = db.Column(db.Integer)
    body_temperature = db.Column(db.Float)
    feed_consumption_kg = db.Column(db.Float)
    water_consumption_litres = db.Column(db.Float)
    bird_weight_kg = db.Column(db.Float)
    mortality_count = db.Column(db.Integer, default=0)
    symptoms_input = db.Column(db.Text)

    # Predictions
    xgboost_prediction = db.Column(db.String(150))
    xgboost_confidence = db.Column(db.Float)
    decision_tree_prediction = db.Column(db.String(150))
    decision_tree_confidence = db.Column(db.Float)
    final_prediction = db.Column(db.String(150))

    # Status
    prediction_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_confirmed = db.Column(db.Boolean, default=False)
    veterinary_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to farmer
    farmer = db.relationship('Farmer', backref='predictions', lazy=True)

    def __repr__(self):
        return f'<DiseasePrediction batch={self.batch_id} disease={self.final_prediction}>'

