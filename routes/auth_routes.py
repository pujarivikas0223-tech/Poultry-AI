from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime
from app import db
from models.user import Admin, Farmer

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        if hasattr(current_user, 'role') and current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('farmer.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        login_type = request.form.get('login_type', 'farmer')
        password = request.form.get('password', '').strip()

        if login_type == 'admin':
            identifier = request.form.get('username', '').strip()
            user = Admin.query.filter(
                (Admin.username == identifier) | (Admin.email == identifier)
            ).first()
        else:
            identifier = request.form.get('identifier', '').strip()
            user = Farmer.query.filter(
                (Farmer.email == identifier) | (Farmer.phone == identifier)
            ).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=request.form.get('remember_me'))
            user.last_login = datetime.utcnow()
            db.session.commit()

            flash(f'Welcome back, {user.full_name if hasattr(user, "full_name") else user.username}!', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('farmer.dashboard'))
        else:
            flash('Invalid credentials or account not active. Please try again.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not email or '@' not in email:
            errors.append('A valid email is required.')
        if not phone or len(phone) < 10:
            errors.append('A valid phone number is required.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if Farmer.query.filter_by(email=email).first():
            errors.append('Email is already registered.')
        if Farmer.query.filter_by(phone=phone).first():
            errors.append('Phone number is already registered.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('auth/register.html',
                                   form_data={'full_name': full_name, 'email': email,
                                              'phone': phone, 'address': address})

        farmer = Farmer(
            full_name=full_name,
            email=email,
            phone=phone,
            address=address
        )
        farmer.set_password(password)
        db.session.add(farmer)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form_data={})


@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

