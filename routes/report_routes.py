from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from models.farm import PoultryFarm
from models.batch import PoultryBatch
from models.health import PoultryHealthRecord
from models.disease import DiseasePrediction
from models.vaccination import VaccinationRecord
from routes.decorators import farmer_required
import csv
import io

report_bp = Blueprint('report', __name__)


def _get_farmer_context():
    farms = PoultryFarm.query.filter_by(farmer_id=current_user.id).all()
    farm_ids = [f.id for f in farms]
    batches = PoultryBatch.query.filter(PoultryBatch.farm_id.in_(farm_ids)).all() if farm_ids else []
    batch_ids = [b.id for b in batches]
    return farms, farm_ids, batches, batch_ids


@report_bp.route('/')
@login_required
@farmer_required
def reports_home():
    farms, farm_ids, batches, batch_ids = _get_farmer_context()
    return render_template('reports/home.html', farms=farms, batches=batches)


@report_bp.route('/health-summary')
@login_required
@farmer_required
def health_summary():
    farms, farm_ids, batches, batch_ids = _get_farmer_context()
    if not farm_ids:
        records = []
    else:
        records = (PoultryHealthRecord.query
                   .filter(PoultryHealthRecord.farm_id.in_(farm_ids))
                   .order_by(PoultryHealthRecord.record_date.desc()).all())
    return render_template('reports/health_summary.html', records=records, farms=farms)


@report_bp.route('/prediction-report')
@login_required
@farmer_required
def prediction_report():
    predictions = (DiseasePrediction.query
                   .filter_by(farmer_id=current_user.id)
                   .order_by(DiseasePrediction.prediction_date.desc()).all())
    return render_template('reports/prediction_report.html', predictions=predictions)


@report_bp.route('/vaccination-report')
@login_required
@farmer_required
def vaccination_report():
    farms, farm_ids, batches, batch_ids = _get_farmer_context()
    today = date.today()
    vaccinations = []
    if batch_ids:
        vaccinations = (VaccinationRecord.query
                        .filter(VaccinationRecord.batch_id.in_(batch_ids))
                        .order_by(VaccinationRecord.vaccination_date.desc()).all())
    return render_template('reports/vaccination_report.html',
                           vaccinations=vaccinations, today=today)


@report_bp.route('/export/health-csv')
@login_required
@farmer_required
def export_health_csv():
    farms, farm_ids, batches, batch_ids = _get_farmer_context()
    if not farm_ids:
        flash('No data to export.', 'warning')
        return redirect(url_for('report.reports_home'))

    records = (PoultryHealthRecord.query
               .filter(PoultryHealthRecord.farm_id.in_(farm_ids))
               .order_by(PoultryHealthRecord.record_date.desc()).all())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Farm', 'Batch', 'Birds', 'Age(wks)',
                     'Temperature(C)', 'Feed(kg)', 'Water(L)',
                     'Weight(kg)', 'Mortality', 'Mortality%',
                     'Condition', 'Symptoms', 'Notes'])

    for r in records:
        batch = PoultryBatch.query.get(r.batch_id)
        farm = PoultryFarm.query.get(r.farm_id)
        writer.writerow([
            r.record_date, farm.farm_name if farm else '', batch.batch_name if batch else '',
            r.number_of_birds, r.bird_age_weeks,
            r.body_temperature or '', r.feed_consumption_kg or '',
            r.water_consumption_litres or '', r.bird_weight_kg or '',
            r.mortality_count, r.mortality_rate,
            r.health_condition, r.symptoms or '', r.notes or ''
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = (
        f'attachment; filename=health_records_{date.today().isoformat()}.csv'
    )
    response.headers['Content-Type'] = 'text/csv'
    return response


@report_bp.route('/export/vaccination-csv')
@login_required
@farmer_required
def export_vaccination_csv():
    farms, farm_ids, batches, batch_ids = _get_farmer_context()
    if not batch_ids:
        flash('No data to export.', 'warning')
        return redirect(url_for('report.reports_home'))

    vaccinations = (VaccinationRecord.query
                    .filter(VaccinationRecord.batch_id.in_(batch_ids))
                    .order_by(VaccinationRecord.vaccination_date.desc()).all())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Vaccine', 'Batch', 'Vaccination Date', 'Next Date',
                     'Dosage', 'Route', 'Status', 'Administered By', 'Notes'])

    for v in vaccinations:
        batch = PoultryBatch.query.get(v.batch_id)
        writer.writerow([
            v.vaccine_name, batch.batch_name if batch else '',
            v.vaccination_date, v.next_vaccination_date or '',
            v.dosage or '', v.route or '', v.status,
            v.administered_by or '', v.notes or ''
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = (
        f'attachment; filename=vaccination_records_{date.today().isoformat()}.csv'
    )
    response.headers['Content-Type'] = 'text/csv'
    return response

