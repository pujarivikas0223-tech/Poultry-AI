from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models.farm import PoultryFarm
from models.batch import PoultryBatch
from routes.decorators import farmer_required

farm_bp = Blueprint('farm', __name__)


def _check_farm_ownership(farm):
    """Ensure the farm belongs to the current farmer."""
    if current_user.role == 'admin':
        return True
    return farm.farmer_id == current_user.id


@farm_bp.route('/')
@login_required
@farmer_required
def list_farms():
    farms = PoultryFarm.query.filter_by(farmer_id=current_user.id).order_by(
        PoultryFarm.created_at.desc()).all()
    return render_template('farms/list.html', farms=farms)


@farm_bp.route('/add', methods=['GET', 'POST'])
@login_required
@farmer_required
def add_farm():
    if request.method == 'POST':
        farm = PoultryFarm(
            farmer_id=current_user.id,
            farm_name=request.form.get('farm_name', '').strip(),
            location=request.form.get('location', '').strip(),
            address=request.form.get('address', '').strip(),
            farm_size=request.form.get('farm_size', '').strip(),
            total_capacity=int(request.form.get('total_capacity', 0) or 0),
            contact_number=request.form.get('contact_number', '').strip(),
            description=request.form.get('description', '').strip()
        )
        if not farm.farm_name:
            flash('Farm name is required.', 'danger')
            return render_template('farms/form.html', farm=None)
        db.session.add(farm)
        db.session.commit()
        flash(f'Farm "{farm.farm_name}" added successfully!', 'success')
        return redirect(url_for('farm.list_farms'))
    return render_template('farms/form.html', farm=None)


@farm_bp.route('/<int:farm_id>')
@login_required
def view_farm(farm_id):
    farm = PoultryFarm.query.get_or_404(farm_id)
    if not _check_farm_ownership(farm):
        flash('Access denied.', 'danger')
        return redirect(url_for('farm.list_farms'))
    batches = farm.batches.order_by(PoultryBatch.created_at.desc()).all()  # all batches
    return render_template('farms/view.html', farm=farm, batches=batches)


@farm_bp.route('/<int:farm_id>/edit', methods=['GET', 'POST'])
@login_required
@farmer_required
def edit_farm(farm_id):
    farm = PoultryFarm.query.get_or_404(farm_id)
    if not _check_farm_ownership(farm):
        flash('Access denied.', 'danger')
        return redirect(url_for('farm.list_farms'))

    if request.method == 'POST':
        farm.farm_name = request.form.get('farm_name', '').strip()
        farm.location = request.form.get('location', '').strip()
        farm.address = request.form.get('address', '').strip()
        farm.farm_size = request.form.get('farm_size', '').strip()
        farm.total_capacity = int(request.form.get('total_capacity', 0) or 0)
        farm.contact_number = request.form.get('contact_number', '').strip()
        farm.description = request.form.get('description', '').strip()
        db.session.commit()
        flash('Farm updated successfully!', 'success')
        return redirect(url_for('farm.list_farms'))

    return render_template('farms/form.html', farm=farm)


@farm_bp.route('/<int:farm_id>/delete', methods=['POST'])
@login_required
@farmer_required
def delete_farm(farm_id):
    farm = PoultryFarm.query.get_or_404(farm_id)
    if not _check_farm_ownership(farm):
        flash('Access denied.', 'danger')
        return redirect(url_for('farm.list_farms'))
    db.session.delete(farm)
    db.session.commit()
    flash('Farm deleted successfully.', 'success')
    return redirect(url_for('farm.list_farms'))

