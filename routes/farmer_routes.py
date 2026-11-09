from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from models.farm import PoultryFarm
from models.batch import PoultryBatch
from models.health import PoultryHealthRecord
from models.disease import DiseasePrediction
from models.vaccination import VaccinationRecord
from routes.decorators import farmer_required
import json

farmer_bp = Blueprint('farmer', __name__)


@farmer_bp.route('/dashboard')
@login_required
@farmer_required
def dashboard():
    farmer_id = current_user.id

    farms = PoultryFarm.query.filter_by(farmer_id=farmer_id).all()
    farm_ids = [f.id for f in farms]

    total_farms = len(farms)
    batches = PoultryBatch.query.filter(PoultryBatch.farm_id.in_(farm_ids)).all() if farm_ids else []
    total_batches = len(batches)
    batch_ids = [b.id for b in batches]

    total_birds = sum(b.number_of_birds for b in batches)
    total_health_records = (PoultryHealthRecord.query
                            .filter(PoultryHealthRecord.farm_id.in_(farm_ids))
                            .count() if farm_ids else 0)
    total_predictions = (DiseasePrediction.query
                         .filter_by(farmer_id=farmer_id).count())

    # Upcoming vaccinations
    upcoming_vaccinations = []
    missed_vaccinations = []
    if batch_ids:
        upcoming_vaccinations = (VaccinationRecord.query
                                 .filter(VaccinationRecord.batch_id.in_(batch_ids),
                                         VaccinationRecord.next_vaccination_date >= date.today(),
                                         VaccinationRecord.status == 'Upcoming')
                                 .order_by(VaccinationRecord.next_vaccination_date.asc())
                                 .limit(5).all())
        missed_vaccinations = (VaccinationRecord.query
                               .filter(VaccinationRecord.batch_id.in_(batch_ids),
                                       VaccinationRecord.next_vaccination_date < date.today(),
                                       VaccinationRecord.status == 'Upcoming')
                               .count())

    # Recent health records
    recent_health = []
    if farm_ids:
        recent_health = (PoultryHealthRecord.query
                         .filter(PoultryHealthRecord.farm_id.in_(farm_ids))
                         .order_by(PoultryHealthRecord.created_at.desc())
                         .limit(5).all())

    # Recent predictions
    recent_predictions = (DiseasePrediction.query
                          .filter_by(farmer_id=farmer_id)
                          .order_by(DiseasePrediction.prediction_date.desc())
                          .limit(5).all())

    # Health trend for chart
    health_data = {}
    for record in PoultryHealthRecord.query.filter(PoultryHealthRecord.farm_id.in_(farm_ids)).all() if farm_ids else []:
        c = record.health_condition or 'Unknown'
        health_data[c] = health_data.get(c, 0) + 1

    return render_template('farmer/dashboard.html',
                           total_farms=total_farms,
                           total_batches=total_batches,
                           total_birds=total_birds,
                           total_health_records=total_health_records,
                           total_predictions=total_predictions,
                           upcoming_vaccinations=upcoming_vaccinations,
                           missed_vaccinations=missed_vaccinations,
                           recent_health=recent_health,
                           recent_predictions=recent_predictions,
                           farms=farms,
                           batches=batches[:5],
                           health_data=json.dumps(health_data),
                           now=datetime.utcnow())

