"""
Authentication Blueprint - Handles user login, register, and logout
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Patient, Doctor, UserRole
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth', template_folder='../templates')


@auth_bp.before_request
def before_request():
    """Redirect authenticated users to dashboard"""
    if current_user.is_authenticated and request.endpoint == 'auth.login':
        return redirect(url_for('main.dashboard'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page and handler"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate input
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Contact administrator.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=request.form.get('remember_me'))
            
            # Redirect based on role
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            
            if user.role == UserRole.ADMIN:
                return redirect(url_for('admin.dashboard'))
            elif user.role == UserRole.DOCTOR:
                return redirect(url_for('doctor.dashboard'))
            elif user.role == UserRole.RECEPTIONIST:
                return redirect(url_for('receptionist.dashboard'))
            elif user.role == UserRole.LAB_STAFF:
                return redirect(url_for('labstaff.dashboard'))
            else:
                return redirect(url_for('patient.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('auth/login.html')


@auth_bp.route('/lab-login', methods=['GET', 'POST'])
def lab_login():
    """Login page dedicated for lab staff."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username and password are required.', 'danger')
            return redirect(url_for('auth.lab_login'))

        user = User.query.filter_by(username=username, role=UserRole.LAB_STAFF).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Contact administrator.', 'danger')
                return redirect(url_for('auth.lab_login'))

            login_user(user, remember=request.form.get('remember_me'))
            return redirect(url_for('labstaff.dashboard'))

        flash('Invalid lab staff credentials.', 'danger')

    return render_template('auth/lab_login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration for patients"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        
        # Validate input
        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        if not email or '@' not in email:
            errors.append('Valid email is required.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already exists.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('auth.register'))
        
        try:
            # Create new user
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=UserRole.PATIENT
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Create patient record
            patient = Patient(
                user_id=user.id,
                patient_id=f"PAT{user.id:05d}"
            )
            db.session.add(patient)
            db.session.commit()
            
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {str(e)}', 'danger')
    
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout current user"""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))
