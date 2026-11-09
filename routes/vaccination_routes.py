from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, date
from calendar import monthcalendar, month_name
from app import db
from models.farm import PoultryFarm
from models.batch import PoultryBatch
from models.vaccination import VaccinationRecord
from routes.decorators import farmer_required

vaccination_bp = Blueprint('vaccination', __name__)


def _get_farmer_batches():
    farms = PoultryFarm.query.filter_by(farmer_id=current_user.id).all()
    farm_ids = [f.id for f in farms]
    if not farm_ids:
        return []
    return PoultryBatch.query.filter(PoultryBatch.farm_id.in_(farm_ids)).all()


def _check_vaccination_access(vacc):
    if current_user.role == 'admin':
        return True
    return vacc.farmer_id == current_user.id


@vaccination_bp.route('/')
@login_required
@farmer_required
def list_vaccinations():
    batches = _get_farmer_batches()
    batch_ids = [b.id for b in batches]
    tab = request.args.get('tab', 'all')

    query = (VaccinationRecord.query
             .filter(VaccinationRecord.batch_id.in_(batch_ids))
             if batch_ids else VaccinationRecord.query.filter_by(id=None))

    today = date.today()
    all_vacc = query.order_by(VaccinationRecord.vaccination_date.desc()).all()

    # Categorize
    completed = [v for v in all_vacc if v.status == 'Completed' or
                 (v.vaccination_date and v.vaccination_date <= today and v.status != 'Missed')]
    upcoming = [v for v in all_vacc if v.next_vaccination_date and
                v.next_vaccination_date >= today and v.status == 'Upcoming']
    missed = [v for v in all_vacc if v.next_vaccination_date and
              v.next_vaccination_date < today and v.status == 'Upcoming']

    return render_template('vaccinations/list.html',
                           all_vacc=all_vacc,
                           completed=completed,
                           upcoming=upcoming,
                           missed=missed,
                           tab=tab)


@vaccination_bp.route('/add', methods=['GET', 'POST'])
@login_required
@farmer_required
def add_vaccination():
    batches = _get_farmer_batches()
    if not batches:
        flash('Please add a farm and batch first.', 'warning')
        return redirect(url_for('batch.add_batch'))

    if request.method == 'POST':
        batch_id = int(request.form.get('batch_id', 0))
        batch = PoultryBatch.query.get(batch_id)
        farm = PoultryFarm.query.get(batch.farm_id) if batch else None
        if not batch or not farm or farm.farmer_id != current_user.id:
            flash('Invalid batch.', 'danger')
            return render_template('vaccinations/form.html', vacc=None, batches=batches)

        try:
            vacc_date = datetime.strptime(request.form.get('vaccination_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash('Invalid vaccination date.', 'danger')
            return render_template('vaccinations/form.html', vacc=None, batches=batches)

        next_vacc_date = None
        nv_str = request.form.get('next_vaccination_date', '').strip()
        if nv_str:
            try:
                next_vacc_date = datetime.strptime(nv_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        status = request.form.get('status', 'Completed')
        if next_vacc_date and next_vacc_date > date.today() and status == 'Completed':
            # Next date is in the future, auto-create "upcoming" reminder
            pass

        vacc = VaccinationRecord(
            batch_id=batch_id,
            farmer_id=current_user.id,
            vaccine_name=request.form.get('vaccine_name', '').strip(),
            vaccination_date=vacc_date,
            next_vaccination_date=next_vacc_date,
            dosage=request.form.get('dosage', '').strip(),
            route=request.form.get('route', 'Drinking water'),
            batch_lot_number=request.form.get('batch_lot_number', '').strip(),
            administered_by=request.form.get('administered_by', '').strip(),
            status=status,
            notes=request.form.get('notes', '').strip()
        )
        if not vacc.vaccine_name:
            flash('Vaccine name is required.', 'danger')
            return render_template('vaccinations/form.html', vacc=None, batches=batches)

        db.session.add(vacc)

        # If next_vaccination_date is set, add an upcoming reminder record
        if next_vacc_date:
            reminder = VaccinationRecord(
                batch_id=batch_id,
                farmer_id=current_user.id,
                vaccine_name=vacc.vaccine_name,
                vaccination_date=next_vacc_date,
                dosage=vacc.dosage,
                route=vacc.route,
                administered_by='',
                status='Upcoming',
                notes=f'Scheduled from vaccination on {vacc_date}'
            )
            db.session.add(reminder)

        db.session.commit()
        flash('Vaccination record added successfully!', 'success')
        return redirect(url_for('vaccination.list_vaccinations'))

    return render_template('vaccinations/form.html', vacc=None, batches=batches,
                           routes=VaccinationRecord.ROUTES,
                           statuses=VaccinationRecord.STATUSES,
                           today=date.today().isoformat())


@vaccination_bp.route('/<int:vacc_id>/edit', methods=['GET', 'POST'])
@login_required
@farmer_required
def edit_vaccination(vacc_id):
    vacc = VaccinationRecord.query.get_or_404(vacc_id)
    if not _check_vaccination_access(vacc):
        flash('Access denied.', 'danger')
        return redirect(url_for('vaccination.list_vaccinations'))

    batches = _get_farmer_batches()

    if request.method == 'POST':
        try:
            vacc_date = datetime.strptime(request.form.get('vaccination_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            vacc_date = vacc.vaccination_date

        next_vacc_date = None
        nv_str = request.form.get('next_vaccination_date', '').strip()
        if nv_str:
            try:
                next_vacc_date = datetime.strptime(nv_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        vacc.vaccine_name = request.form.get('vaccine_name', '').strip()
        vacc.vaccination_date = vacc_date
        vacc.next_vaccination_date = next_vacc_date
        vacc.dosage = request.form.get('dosage', '').strip()
        vacc.route = request.form.get('route', vacc.route)
        vacc.batch_lot_number = request.form.get('batch_lot_number', '').strip()
        vacc.administered_by = request.form.get('administered_by', '').strip()
        vacc.status = request.form.get('status', vacc.status)
        vacc.notes = request.form.get('notes', '').strip()
        db.session.commit()
        flash('Vaccination record updated!', 'success')
        return redirect(url_for('vaccination.list_vaccinations'))

    return render_template('vaccinations/form.html', vacc=vacc, batches=batches,
                           routes=VaccinationRecord.ROUTES,
                           statuses=VaccinationRecord.STATUSES)


@vaccination_bp.route('/<int:vacc_id>/delete', methods=['POST'])
@login_required
@farmer_required
def delete_vaccination(vacc_id):
    vacc = VaccinationRecord.query.get_or_404(vacc_id)
    if not _check_vaccination_access(vacc):
        flash('Access denied.', 'danger')
        return redirect(url_for('vaccination.list_vaccinations'))
    db.session.delete(vacc)
    db.session.commit()
    flash('Vaccination record deleted.', 'success')
    return redirect(url_for('vaccination.list_vaccinations'))


@vaccination_bp.route('/calendar')
@login_required
@farmer_required
def calendar_view():
    # Month/year navigation
    today = date.today()
    year = int(request.args.get('year', today.year))
    month = int(request.args.get('month', today.month))

    # Clamp navigation
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    # Get this farmer's vaccinations for the month
    batches = _get_farmer_batches()
    batch_ids = [b.id for b in batches]

    vacc_events = {}
    if batch_ids:
        from sqlalchemy import extract
        records = (VaccinationRecord.query
                   .filter(VaccinationRecord.batch_id.in_(batch_ids))
                   .filter(
                       db.or_(
                           db.and_(
                               extract('month', VaccinationRecord.vaccination_date) == month,
                               extract('year', VaccinationRecord.vaccination_date) == year
                           ),
                           db.and_(
                               VaccinationRecord.next_vaccination_date.isnot(None),
                               extract('month', VaccinationRecord.next_vaccination_date) == month,
                               extract('year', VaccinationRecord.next_vaccination_date) == year
                           )
                       )
                   ).all())

        for r in records:
            # Main vaccination date
            if r.vaccination_date and r.vaccination_date.month == month and r.vaccination_date.year == year:
                day = r.vaccination_date.day
                vacc_events.setdefault(day, []).append({
                    'name': r.vaccine_name,
                    'status': r.status,
                    'id': r.id
                })
            # Next vaccination date
            if r.next_vaccination_date and r.next_vaccination_date.month == month and r.next_vaccination_date.year == year:
                day = r.next_vaccination_date.day
                vacc_events.setdefault(day, []).append({
                    'name': f'{r.vaccine_name} (due)',
                    'status': 'Upcoming',
                    'id': r.id
                })

    cal_weeks = monthcalendar(year, month)

    # Prev/next
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    return render_template('vaccinations/calendar.html',
                           cal_weeks=cal_weeks,
                           vacc_events=vacc_events,
                           year=year,
                           month=month,
                           month_name=month_name[month],
                           today=today,
                           prev_month=prev_month,
                           prev_year=prev_year,
                           next_month=next_month,
                           next_year=next_year)

