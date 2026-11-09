from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from models.farm import PoultryFarm
from models.batch import PoultryBatch
from models.health import PoultryHealthRecord
from routes.decorators import farmer_required

health_bp = Blueprint('health', __name__)


def _get_farmer_batch_ids():
    farms = PoultryFarm.query.filter_by(farmer_id=current_user.id).all()
    farm_ids = [f.id for f in farms]
    if not farm_ids:
        return [], []
    batches = PoultryBatch.query.filter(PoultryBatch.farm_id.in_(farm_ids)).all()
    return farm_ids, [b.id for b in batches]


def _check_record_access(record):
    if current_user.role == 'admin':
        return True
    farm = PoultryFarm.query.get(record.farm_id)
    return farm and farm.farmer_id == current_user.id


@health_bp.route('/')
@login_required
@farmer_required
def list_records():
    farm_ids, batch_ids = _get_farmer_batch_ids()
    q = request.args.get('q', '')
    query = (PoultryHealthRecord.query
             .filter(PoultryHealthRecord.farm_id.in_(farm_ids))
             if farm_ids else PoultryHealthRecord.query.filter_by(id=None))
    records = query.order_by(PoultryHealthRecord.record_date.desc()).all()
    return render_template('health/list.html', records=records, q=q)


@health_bp.route('/add', methods=['GET', 'POST'])
@login_required
@farmer_required
def add_record():
    farms = PoultryFarm.query.filter_by(farmer_id=current_user.id).all()
    if not farms:
        flash('Please add a farm and batch first.', 'warning')
        return redirect(url_for('farm.add_farm'))

    all_batches = PoultryBatch.query.filter(
        PoultryBatch.farm_id.in_([f.id for f in farms])
    ).filter_by(is_active=True).all()

    if request.method == 'POST':
        farm_id = int(request.form.get('farm_id', 0))
        batch_id = int(request.form.get('batch_id', 0))

        farm = PoultryFarm.query.get(farm_id)
        batch = PoultryBatch.query.get(batch_id)
        if not farm or farm.farmer_id != current_user.id:
            flash('Invalid farm selection.', 'danger')
            return render_template('health/form.html', record=None, farms=farms, batches=all_batches)
        if not batch or batch.farm_id != farm_id:
            flash('Invalid batch selection.', 'danger')
            return render_template('health/form.html', record=None, farms=farms, batches=all_batches)

        number_of_birds = int(request.form.get('number_of_birds', 0) or 0)
        mortality_count = int(request.form.get('mortality_count', 0) or 0)
        if mortality_count > number_of_birds:
            flash('Mortality count cannot exceed number of birds.', 'danger')
            return render_template('health/form.html', record=None, farms=farms, batches=all_batches)

        try:
            record_date = datetime.strptime(request.form.get('record_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            record_date = date.today()

        def _safe_float(val):
            try:
                return float(val) if val else None
            except ValueError:
                return None

        record = PoultryHealthRecord(
            batch_id=batch_id,
            farm_id=farm_id,
            number_of_birds=number_of_birds,
            bird_age_weeks=int(request.form.get('bird_age_weeks', 0) or 0),
            body_temperature=_safe_float(request.form.get('body_temperature')),
            feed_consumption_kg=_safe_float(request.form.get('feed_consumption_kg')),
            water_consumption_litres=_safe_float(request.form.get('water_consumption_litres')),
            bird_weight_kg=_safe_float(request.form.get('bird_weight_kg')),
            mortality_count=mortality_count,
            symptoms=request.form.get('symptoms', '').strip(),
            health_condition=request.form.get('health_condition', 'Good'),
            record_date=record_date,
            notes=request.form.get('notes', '').strip(),
            recorded_by=current_user.id
        )
        db.session.add(record)
        db.session.commit()
        flash('Health record added successfully!', 'success')
        return redirect(url_for('health.list_records'))

    return render_template('health/form.html', record=None, farms=farms,
                           batches=all_batches,
                           health_conditions=PoultryHealthRecord.HEALTH_CONDITIONS,
                           today=date.today().isoformat())


@health_bp.route('/<int:record_id>')
@login_required
def view_record(record_id):
    record = PoultryHealthRecord.query.get_or_404(record_id)
    if not _check_record_access(record):
        flash('Access denied.', 'danger')
        return redirect(url_for('health.list_records'))
    return render_template('health/view.html', record=record)


@health_bp.route('/<int:record_id>/edit', methods=['GET', 'POST'])
@login_required
@farmer_required
def edit_record(record_id):
    record = PoultryHealthRecord.query.get_or_404(record_id)
    if not _check_record_access(record):
        flash('Access denied.', 'danger')
        return redirect(url_for('health.list_records'))

    farms = PoultryFarm.query.filter_by(farmer_id=current_user.id).all()
    all_batches = PoultryBatch.query.filter(
        PoultryBatch.farm_id.in_([f.id for f in farms])
    ).all()

    if request.method == 'POST':
        number_of_birds = int(request.form.get('number_of_birds', record.number_of_birds) or 0)
        mortality_count = int(request.form.get('mortality_count', 0) or 0)
        if mortality_count > number_of_birds:
            flash('Mortality count cannot exceed number of birds.', 'danger')
            return render_template('health/form.html', record=record, farms=farms, batches=all_batches)

        def _safe_float(val):
            try:
                return float(val) if val else None
            except ValueError:
                return None

        try:
            record_date = datetime.strptime(request.form.get('record_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            record_date = record.record_date

        record.number_of_birds = number_of_birds
        record.bird_age_weeks = int(request.form.get('bird_age_weeks', 0) or 0)
        record.body_temperature = _safe_float(request.form.get('body_temperature'))
        record.feed_consumption_kg = _safe_float(request.form.get('feed_consumption_kg'))
        record.water_consumption_litres = _safe_float(request.form.get('water_consumption_litres'))
        record.bird_weight_kg = _safe_float(request.form.get('bird_weight_kg'))
        record.mortality_count = mortality_count
        record.symptoms = request.form.get('symptoms', '').strip()
        record.health_condition = request.form.get('health_condition', 'Good')
        record.record_date = record_date
        record.notes = request.form.get('notes', '').strip()
        db.session.commit()
        flash('Health record updated successfully!', 'success')
        return redirect(url_for('health.list_records'))

    return render_template('health/form.html', record=record, farms=farms,
                           batches=all_batches,
                           health_conditions=PoultryHealthRecord.HEALTH_CONDITIONS)


@health_bp.route('/<int:record_id>/delete', methods=['POST'])
@login_required
@farmer_required
def delete_record(record_id):
    record = PoultryHealthRecord.query.get_or_404(record_id)
    if not _check_record_access(record):
        flash('Access denied.', 'danger')
        return redirect(url_for('health.list_records'))
    db.session.delete(record)
    db.session.commit()
    flash('Health record deleted.', 'success')
    return redirect(url_for('health.list_records'))

