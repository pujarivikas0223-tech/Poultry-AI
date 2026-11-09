from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from models.user import Admin, Farmer
from models.farm import PoultryFarm
from models.batch import PoultryBatch
from models.health import PoultryHealthRecord
from models.disease import Disease, DiseasePrediction
from models.vaccination import VaccinationRecord
from routes.decorators import admin_required
from werkzeug.security import generate_password_hash
import json

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Real counts from database
    total_farmers = Farmer.query.filter_by(is_active=True).count()
    total_farms = PoultryFarm.query.count()
    total_batches = PoultryBatch.query.count()
    total_birds = db.session.query(db.func.sum(PoultryBatch.number_of_birds)).scalar() or 0
    total_health_records = PoultryHealthRecord.query.count()
    total_predictions = DiseasePrediction.query.count()
    total_vaccinations = VaccinationRecord.query.count()

    # Recent activities (last 10 health records)
    recent_records = (PoultryHealthRecord.query
                      .join(PoultryBatch, PoultryHealthRecord.batch_id == PoultryBatch.id)
                      .join(PoultryFarm, PoultryHealthRecord.farm_id == PoultryFarm.id)
                      .order_by(PoultryHealthRecord.created_at.desc())
                      .limit(10).all())

    # Upcoming vaccinations
    upcoming_vaccinations = (VaccinationRecord.query
                             .filter(VaccinationRecord.next_vaccination_date >= date.today(),
                                     VaccinationRecord.status == 'Upcoming')
                             .order_by(VaccinationRecord.next_vaccination_date.asc())
                             .limit(5).all())

    # Disease prediction distribution for chart
    pred_counts = {}
    predictions = DiseasePrediction.query.all()
    for p in predictions:
        d = p.final_prediction or 'Unknown'
        pred_counts[d] = pred_counts.get(d, 0) + 1

    # Health condition stats
    condition_counts = {}
    for record in PoultryHealthRecord.query.all():
        c = record.health_condition or 'Unknown'
        condition_counts[c] = condition_counts.get(c, 0) + 1

    # Recent farmers
    recent_farmers = Farmer.query.order_by(Farmer.created_at.desc()).limit(5).all()

    # Recent predictions for activity feed
    recent_predictions = DiseasePrediction.query.order_by(DiseasePrediction.prediction_date.desc()).limit(5).all()

    # Vaccination status breakdown for analytics
    vacc_completed = VaccinationRecord.query.filter_by(status='Completed').count()
    vacc_upcoming = VaccinationRecord.query.filter(VaccinationRecord.next_vaccination_date >= date.today(), VaccinationRecord.status == 'Upcoming').count()
    vacc_missed = VaccinationRecord.query.filter(VaccinationRecord.next_vaccination_date < date.today(), VaccinationRecord.status == 'Upcoming').count()
    vacc_stats = {'Completed': vacc_completed, 'Upcoming': vacc_upcoming, 'Missed': vacc_missed}

    return render_template('admin/dashboard.html',
                           total_farmers=total_farmers,
                           total_farms=total_farms,
                           total_batches=total_batches,
                           total_birds=total_birds,
                           total_health_records=total_health_records,
                           total_predictions=total_predictions,
                           total_vaccinations=total_vaccinations,
                           recent_records=recent_records,
                           upcoming_vaccinations=upcoming_vaccinations,
                           recent_predictions=recent_predictions,
                           vacc_stats=json.dumps(vacc_stats),
                           pred_counts=json.dumps(pred_counts),
                           condition_counts=json.dumps(condition_counts),
                           recent_farmers=recent_farmers,
                           now=datetime.now())


# ─── FARMER MANAGEMENT ───────────────────────────────────────────────────────

@admin_bp.route('/farmers')
@login_required
@admin_required
def farmers_list():
    q = request.args.get('q', '')
    query = Farmer.query
    if q:
        query = query.filter(
            (Farmer.full_name.ilike(f'%{q}%')) |
            (Farmer.email.ilike(f'%{q}%')) |
            (Farmer.phone.ilike(f'%{q}%'))
        )
    farmers = query.order_by(Farmer.created_at.desc()).all()
    return render_template('admin/farmers.html', farmers=farmers, q=q)


@admin_bp.route('/farmers/<int:farmer_id>')
@login_required
@admin_required
def farmer_detail(farmer_id):
    farmer = Farmer.query.get_or_404(farmer_id)
    farms = farmer.farms.all()
    batches = PoultryBatch.query.join(PoultryFarm).filter(PoultryFarm.farmer_id == farmer_id).all()
    predictions = DiseasePrediction.query.filter_by(farmer_id=farmer_id).order_by(
        DiseasePrediction.prediction_date.desc()).limit(10).all()
    return render_template('admin/farmer_detail.html', farmer=farmer, farms=farms,
                           batches=batches, predictions=predictions)


@admin_bp.route('/farmers/<int:farmer_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_farmer(farmer_id):
    farmer = Farmer.query.get_or_404(farmer_id)
    farmer.is_active = not farmer.is_active
    db.session.commit()
    status = 'activated' if farmer.is_active else 'deactivated'
    flash(f'Farmer {farmer.full_name} has been {status}.', 'success')
    return redirect(url_for('admin.farmers_list'))


@admin_bp.route('/farmers/<int:farmer_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_farmer(farmer_id):
    farmer = Farmer.query.get_or_404(farmer_id)
    db.session.delete(farmer)
    db.session.commit()
    flash('Farmer and all related data deleted.', 'success')
    return redirect(url_for('admin.farmers_list'))


# ─── FARM MANAGEMENT ─────────────────────────────────────────────────────────

@admin_bp.route('/farms')
@login_required
@admin_required
def all_farms():
    q = request.args.get('q', '')
    query = PoultryFarm.query.join(Farmer)
    if q:
        query = query.filter(
            (PoultryFarm.farm_name.ilike(f'%{q}%')) |
            (PoultryFarm.location.ilike(f'%{q}%')) |
            (Farmer.full_name.ilike(f'%{q}%'))
        )
    farms = query.order_by(PoultryFarm.created_at.desc()).all()
    return render_template('admin/farms.html', farms=farms, q=q)


# ─── BATCH MANAGEMENT ────────────────────────────────────────────────────────

@admin_bp.route('/batches')
@login_required
@admin_required
def all_batches():
    q = request.args.get('q', '')
    query = PoultryBatch.query.join(PoultryFarm)
    if q:
        query = query.filter(
            (PoultryBatch.batch_name.ilike(f'%{q}%')) |
            (PoultryBatch.breed_name.ilike(f'%{q}%')) |
            (PoultryFarm.farm_name.ilike(f'%{q}%'))
        )
    batches = query.order_by(PoultryBatch.created_at.desc()).all()
    return render_template('admin/batches.html', batches=batches, q=q)


# ─── HEALTH RECORDS ──────────────────────────────────────────────────────────

@admin_bp.route('/health-records')
@login_required
@admin_required
def all_health_records():
    records = (PoultryHealthRecord.query
               .join(PoultryBatch, PoultryHealthRecord.batch_id == PoultryBatch.id)
               .order_by(PoultryHealthRecord.record_date.desc()).all())
    return render_template('admin/health_records.html', records=records)


# ─── DISEASE MANAGEMENT ──────────────────────────────────────────────────────

@admin_bp.route('/diseases')
@login_required
@admin_required
def diseases_list():
    diseases = Disease.query.order_by(Disease.name).all()
    return render_template('admin/diseases.html', diseases=diseases)


@admin_bp.route('/diseases/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_disease():
    if request.method == 'POST':
        disease = Disease(
            name=request.form.get('name'),
            description=request.form.get('description'),
            symptoms=request.form.get('symptoms'),
            prevention=request.form.get('prevention'),
            hygiene_recommendations=request.form.get('hygiene_recommendations'),
            biosecurity_measures=request.form.get('biosecurity_measures'),
            isolation_guidance=request.form.get('isolation_guidance'),
            veterinary_advice=request.form.get('veterinary_advice'),
            severity=request.form.get('severity', 'Medium')
        )
        db.session.add(disease)
        db.session.commit()
        flash('Disease information added successfully.', 'success')
        return redirect(url_for('admin.diseases_list'))
    return render_template('admin/disease_form.html', disease=None)


@admin_bp.route('/diseases/<int:disease_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_disease(disease_id):
    disease = Disease.query.get_or_404(disease_id)
    if request.method == 'POST':
        disease.name = request.form.get('name')
        disease.description = request.form.get('description')
        disease.symptoms = request.form.get('symptoms')
        disease.prevention = request.form.get('prevention')
        disease.hygiene_recommendations = request.form.get('hygiene_recommendations')
        disease.biosecurity_measures = request.form.get('biosecurity_measures')
        disease.isolation_guidance = request.form.get('isolation_guidance')
        disease.veterinary_advice = request.form.get('veterinary_advice')
        disease.severity = request.form.get('severity', 'Medium')
        db.session.commit()
        flash('Disease information updated.', 'success')
        return redirect(url_for('admin.diseases_list'))
    return render_template('admin/disease_form.html', disease=disease)


@admin_bp.route('/diseases/<int:disease_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_disease(disease_id):
    disease = Disease.query.get_or_404(disease_id)
    db.session.delete(disease)
    db.session.commit()
    flash('Disease record deleted.', 'success')
    return redirect(url_for('admin.diseases_list'))


# ─── PREDICTIONS ──────────────────────────────────────────────────────────────

@admin_bp.route('/predictions')
@login_required
@admin_required
def all_predictions():
    predictions = (DiseasePrediction.query
                   .join(PoultryBatch, DiseasePrediction.batch_id == PoultryBatch.id)
                   .order_by(DiseasePrediction.prediction_date.desc()).all())
    return render_template('admin/predictions.html', predictions=predictions)


# ─── VACCINATIONS ────────────────────────────────────────────────────────────

@admin_bp.route('/vaccinations')
@login_required
@admin_required
def all_vaccinations():
    vaccinations = (VaccinationRecord.query
                    .join(PoultryBatch, VaccinationRecord.batch_id == PoultryBatch.id)
                    .order_by(VaccinationRecord.vaccination_date.desc()).all())
    return render_template('admin/vaccinations.html', vaccinations=vaccinations)


# ─── REPORTS ─────────────────────────────────────────────────────────────────

@admin_bp.route('/reports')
@login_required
@admin_required
def reports_home():
    """Admin reports overview – shows aggregated data for all farmers."""
    from models.health import PoultryHealthRecord
    from models.vaccination import VaccinationRecord as VR
    total_farmers = Farmer.query.count()
    total_farms = PoultryFarm.query.count()
    total_batches = PoultryBatch.query.count()
    total_health_records = PoultryHealthRecord.query.count()
    total_predictions = DiseasePrediction.query.count()
    total_vaccinations = VR.query.count()

    # Health condition distribution
    condition_counts = {}
    for record in PoultryHealthRecord.query.all():
        c = record.health_condition or 'Unknown'
        condition_counts[c] = condition_counts.get(c, 0) + 1

    # Disease prediction distribution
    pred_counts = {}
    for p in DiseasePrediction.query.all():
        d = p.final_prediction or 'Unknown'
        pred_counts[d] = pred_counts.get(d, 0) + 1

    return render_template('admin/reports.html',
                           total_farmers=total_farmers,
                           total_farms=total_farms,
                           total_batches=total_batches,
                           total_health_records=total_health_records,
                           total_predictions=total_predictions,
                           total_vaccinations=total_vaccinations,
                           condition_counts=json.dumps(condition_counts),
                           pred_counts=json.dumps(pred_counts))

