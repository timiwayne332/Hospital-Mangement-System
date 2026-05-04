"""
Patient Blueprint - Handles patient-specific functions
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from app.models import (
    db, UserRole, Appointment, MedicalRecord, BillingRecord,
    LabResult, Patient
)
from datetime import datetime, date

patient_bp = Blueprint('patient', __name__, url_prefix='/patient', template_folder='../templates')


def patient_required(f):
    """Decorator to check if user is patient"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.PATIENT:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@patient_bp.route('/dashboard')
@login_required
@patient_required
def dashboard():
    """Patient dashboard"""
    from app.blueprints.main import dashboard as main_dashboard
    return main_dashboard()


# ======================== Appointment Management ========================

@patient_bp.route('/appointments')
@login_required
@patient_required
def appointments():
    """View patient's appointments"""
    patient = current_user.patient
    page = request.args.get('page', 1, type=int)
    
    appointments_list = Appointment.query.filter_by(patient_id=patient.id).order_by(
        Appointment.appointment_date.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('patient/appointments.html', appointments=appointments_list)


@patient_bp.route('/appointment/<int:appointment_id>')
@login_required
@patient_required
def view_appointment(appointment_id):
    """View appointment details"""
    patient = current_user.patient
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.patient_id != patient.id:
        flash('You do not have permission to view this appointment.', 'danger')
        return redirect(url_for('patient.appointments'))
    
    return render_template('patient/appointment_detail.html', appointment=appointment)


@patient_bp.route('/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@patient_required
def cancel_appointment(appointment_id):
    """Cancel appointment"""
    patient = current_user.patient
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.patient_id != patient.id:
        flash('You do not have permission to cancel this appointment.', 'danger')
        return redirect(url_for('patient.appointments'))
    
    if appointment.status != 'scheduled':
        flash('Only scheduled appointments can be cancelled.', 'danger')
        return redirect(url_for('patient.appointments'))
    
    appointment.status = 'cancelled'
    
    try:
        db.session.commit()
        flash('Appointment cancelled successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelling appointment: {str(e)}', 'danger')
    
    return redirect(url_for('patient.appointments'))


# ======================== Medical Records ========================

@patient_bp.route('/medical-records')
@login_required
@patient_required
def medical_records():
    """View patient's medical records"""
    patient = current_user.patient
    page = request.args.get('page', 1, type=int)
    
    records = MedicalRecord.query.filter_by(patient_id=patient.id).order_by(
        MedicalRecord.created_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('patient/medical_records.html', records=records)


@patient_bp.route('/medical-record/<int:record_id>')
@login_required
@patient_required
def view_medical_record(record_id):
    """View specific medical record"""
    patient = current_user.patient
    record = MedicalRecord.query.get_or_404(record_id)
    
    if record.patient_id != patient.id:
        flash('You do not have permission to view this record.', 'danger')
        return redirect(url_for('patient.medical_records'))
    
    return render_template('patient/view_medical_record.html', record=record)


# ======================== Lab Results ========================

@patient_bp.route('/lab-results')
@login_required
@patient_required
def lab_results():
    """View patient's lab results"""
    patient = current_user.patient
    page = request.args.get('page', 1, type=int)
    
    results = LabResult.query.filter_by(patient_id=patient.id).order_by(
        LabResult.created_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('patient/lab_results.html', results=results)


@patient_bp.route('/lab-result/<int:result_id>')
@login_required
@patient_required
def view_lab_result(result_id):
    """View specific lab result"""
    patient = current_user.patient
    result = LabResult.query.get_or_404(result_id)
    
    if result.patient_id != patient.id:
        flash('You do not have permission to view this result.', 'danger')
        return redirect(url_for('patient.lab_results'))
    
    return render_template('patient/view_lab_result.html', result=result)


# ======================== Billing ========================

@patient_bp.route('/billing')
@login_required
@patient_required
def billing():
    """View patient's billing records"""
    patient = current_user.patient
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = BillingRecord.query.filter_by(patient_id=patient.id)
    
    if status_filter != 'all':
        query = query.filter_by(payment_status=status_filter)
    
    bills = query.order_by(
        BillingRecord.created_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('patient/billing.html', bills=bills, status_filter=status_filter)


@patient_bp.route('/bill/<int:bill_id>')
@login_required
@patient_required
def view_bill(bill_id):
    """View bill details"""
    patient = current_user.patient
    bill = BillingRecord.query.get_or_404(bill_id)
    
    if bill.patient_id != patient.id:
        flash('You do not have permission to view this bill.', 'danger')
        return redirect(url_for('patient.billing'))
    
    return render_template('patient/view_bill.html', bill=bill)


# ======================== Patient Profile ========================

@patient_bp.route('/profile')
@login_required
@patient_required
def profile():
    """View and edit patient profile"""
    patient = current_user.patient
    return render_template('patient/profile.html', patient=patient)


@patient_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@patient_required
def edit_profile():
    """Edit patient profile"""
    patient = current_user.patient
    user = current_user
    
    if request.method == 'POST':
        # Update user information
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        
        # Update patient information
        # Parse date_of_birth from string to date object
        dob_str = request.form.get('date_of_birth')
        if dob_str:
            try:
                patient.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD', 'danger')
                return redirect(url_for('patient.edit_profile'))
        
        patient.gender = request.form.get('gender')
        patient.blood_group = request.form.get('blood_group')
        patient.address = request.form.get('address')
        patient.emergency_contact = request.form.get('emergency_contact')
        patient.emergency_contact_phone = request.form.get('emergency_contact_phone')
        patient.insurance_provider = request.form.get('insurance_provider')
        patient.insurance_number = request.form.get('insurance_number')
        patient.allergies = request.form.get('allergies')
        patient.medical_history = request.form.get('medical_history')
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('patient.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
    
    return render_template('patient/edit_profile.html', patient=patient)
