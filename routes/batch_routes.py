from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from models.farm import PoultryFarm
from models.batch import PoultryBatch
from models.health import PoultryHealthRecord
from routes.decorators import farmer_required

batch_bp = Blueprint('batch', __name__)


def _get_farmer_farms():
    return PoultryFarm.query.filter_by(farmer_id=current_user.id).all()


def _check_batch_access(batch):
    if current_user.role == 'admin':
        return True
    farm = PoultryFarm.query.get(batch.farm_id)
    return farm and farm.farmer_id == current_user.id


@batch_bp.route('/')
@login_required
@farmer_required
def list_batches():
    farms = _get_farmer_farms()
    farm_ids = [f.id for f in farms]
    q = request.args.get('q', '')
    query = PoultryBatch.query.filter(PoultryBatch.farm_id.in_(farm_ids)) if farm_ids else PoultryBatch.query.filter_by(id=None)
    if q:
        query = query.filter(
            (PoultryBatch.batch_name.ilike(f'%{q}%')) |
            (PoultryBatch.breed_name.ilike(f'%{q}%')) |
            (PoultryBatch.poultry_type.ilike(f'%{q}%'))
        )
    batches = query.order_by(PoultryBatch.created_at.desc()).all()
    return render_template('batches/list.html', batches=batches, q=q)


@batch_bp.route('/add', methods=['GET', 'POST'])
@login_required
@farmer_required
def add_batch():
    farms = _get_farmer_farms()
    if not farms:
        flash('Please add a farm first before creating a batch.', 'warning')
        return redirect(url_for('farm.add_farm'))

    if request.method == 'POST':
        farm_id = int(request.form.get('farm_id', 0))
        farm = PoultryFarm.query.get(farm_id)
        if not farm or farm.farmer_id != current_user.id:
            flash('Invalid farm selection.', 'danger')
            return render_template('batches/form.html', batch=None, farms=farms)

        try:
            arrival_date = datetime.strptime(request.form.get('arrival_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash('Invalid arrival date.', 'danger')
            return render_template('batches/form.html', batch=None, farms=farms)

        expected_harvest = None
        eh_str = request.form.get('expected_harvest_date', '').strip()
        if eh_str:
            try:
                expected_harvest = datetime.strptime(eh_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        batch = PoultryBatch(
            farm_id=farm_id,
            batch_name=request.form.get('batch_name', '').strip(),
            breed_name=request.form.get('breed_name', '').strip(),
            poultry_type=request.form.get('poultry_type', 'Broiler'),
            number_of_birds=int(request.form.get('number_of_birds', 0) or 0),
            bird_age_weeks=int(request.form.get('bird_age_weeks', 0) or 0),
            arrival_date=arrival_date,
            expected_harvest_date=expected_harvest,
            source=request.form.get('source', '').strip(),
            purchase_price_per_bird=float(request.form.get('purchase_price_per_bird', 0) or 0),
            batch_status=request.form.get('batch_status', 'Active'),
            notes=request.form.get('notes', '').strip()
        )

        if not batch.batch_name:
            flash('Batch name is required.', 'danger')
            return render_template('batches/form.html', batch=None, farms=farms)

        db.session.add(batch)
        db.session.commit()
        flash(f'Batch "{batch.batch_name}" created successfully!', 'success')
        return redirect(url_for('batch.list_batches'))

    return render_template('batches/form.html', batch=None, farms=farms,
                           poultry_types=PoultryBatch.POULTRY_TYPES,
                           batch_statuses=PoultryBatch.BATCH_STATUSES)


@batch_bp.route('/<int:batch_id>')
@login_required
def view_batch(batch_id):
    batch = PoultryBatch.query.get_or_404(batch_id)
    if not _check_batch_access(batch):
        flash('Access denied.', 'danger')
        return redirect(url_for('batch.list_batches'))
    health_records = batch.health_records.order_by(
        PoultryHealthRecord.record_date.desc()).all()
    return render_template('batches/view.html', batch=batch, health_records=health_records)


@batch_bp.route('/<int:batch_id>/edit', methods=['GET', 'POST'])
@login_required
@farmer_required
def edit_batch(batch_id):
    batch = PoultryBatch.query.get_or_404(batch_id)
    if not _check_batch_access(batch):
        flash('Access denied.', 'danger')
        return redirect(url_for('batch.list_batches'))

    farms = _get_farmer_farms()

    if request.method == 'POST':
        farm_id = int(request.form.get('farm_id', batch.farm_id))
        farm = PoultryFarm.query.get(farm_id)
        if not farm or farm.farmer_id != current_user.id:
            flash('Invalid farm selection.', 'danger')
            return render_template('batches/form.html', batch=batch, farms=farms)

        try:
            arrival_date = datetime.strptime(request.form.get('arrival_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash('Invalid arrival date.', 'danger')
            return render_template('batches/form.html', batch=batch, farms=farms)

        batch.farm_id = farm_id
        batch.batch_name = request.form.get('batch_name', '').strip()
        batch.breed_name = request.form.get('breed_name', '').strip()
        batch.poultry_type = request.form.get('poultry_type', 'Broiler')
        batch.number_of_birds = int(request.form.get('number_of_birds', 0) or 0)
        batch.bird_age_weeks = int(request.form.get('bird_age_weeks', 0) or 0)
        batch.arrival_date = arrival_date
        batch.source = request.form.get('source', '').strip()
        batch.purchase_price_per_bird = float(request.form.get('purchase_price_per_bird', 0) or 0)
        batch.batch_status = request.form.get('batch_status', 'Active')
        batch.notes = request.form.get('notes', '').strip()
        db.session.commit()
        flash('Batch updated successfully!', 'success')
        return redirect(url_for('batch.list_batches'))

    return render_template('batches/form.html', batch=batch, farms=farms,
                           poultry_types=PoultryBatch.POULTRY_TYPES,
                           batch_statuses=PoultryBatch.BATCH_STATUSES)


@batch_bp.route('/<int:batch_id>/delete', methods=['POST'])
@login_required
@farmer_required
def delete_batch(batch_id):
    batch = PoultryBatch.query.get_or_404(batch_id)
    if not _check_batch_access(batch):
        flash('Access denied.', 'danger')
        return redirect(url_for('batch.list_batches'))
    db.session.delete(batch)
    db.session.commit()
    flash('Batch deleted successfully.', 'success')
    return redirect(url_for('batch.list_batches'))

