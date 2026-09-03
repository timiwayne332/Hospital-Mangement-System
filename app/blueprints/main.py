"""
Main Blueprint - Handles dashboard and general routes
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import (
    User, Patient, Doctor, Appointment, BillingRecord, 
    Medicine, LabTest, Bed, UserRole, Department, AppointmentStatus, db,
    PatientDrugAssignment
)
from sqlalchemy import func
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__, template_folder='../templates')


@main_bp.route('/')
def index():
    """Home page - redirect to login if not authenticated"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Unified dashboard showing role-specific panels on one page."""

    # Admin stats
    admin_stats = {
        'total_patients': Patient.query.count(),
        'total_doctors': Doctor.query.count(),
        'total_users': User.query.count(),
        'total_appointments': Appointment.query.count(),
        'pending_bills': BillingRecord.query.filter_by(payment_status='pending').count(),
        'total_medicines': Medicine.query.count(),
        'low_stock_medicines': Medicine.query.filter(Medicine.quantity <= Medicine.min_stock_level).count() if hasattr(Medicine, 'min_stock_level') else 0,
        'available_beds': Bed.query.filter_by(is_available=True).count(),
        'total_beds': Bed.query.count()
    }

    # Doctor stats (for current user's doctor record)
    doctor_stats = {}
    if current_user.role == UserRole.DOCTOR and hasattr(current_user, 'doctor') and current_user.doctor:
        doc = current_user.doctor
        doctor_stats = {
            'total_patients': Appointment.query.filter_by(doctor_id=doc.id).distinct(Appointment.patient_id).count(),
            'pending_appointments': Appointment.query.filter_by(doctor_id=doc.id, status='scheduled').count(),
            'completed_appointments': Appointment.query.filter_by(doctor_id=doc.id, status='completed').count(),
        }

    # Receptionist stats
    receptionist_stats = {
        'total_patients': Patient.query.count(),
        'total_appointments': Appointment.query.count(),
        'pending_appointments': Appointment.query.filter_by(status='scheduled').count(),
        'pending_bills': BillingRecord.query.filter_by(payment_status='pending').count()
    }

    # Pharmacist stats
    pharmacist_stats = {
        'total_drugs': Medicine.query.count(),
        'low_stock': Medicine.query.filter(Medicine.quantity <= Medicine.min_stock_level).count() if hasattr(Medicine, 'min_stock_level') else 0,
        'pending_assignments': PatientDrugAssignment.query.filter_by(status='pending').count() if 'PatientDrugAssignment' in globals() else 0
    }

    # Patient stats (for current user's patient record)
    patient_stats = {}
    if current_user.role == UserRole.PATIENT and hasattr(current_user, 'patient') and current_user.patient:
        p = current_user.patient
        patient_stats = {
            'upcoming_appointments': Appointment.query.filter_by(patient_id=p.id, status='scheduled').filter(Appointment.appointment_date >= datetime.utcnow()).all(),
            'pending_bills': BillingRecord.query.filter_by(patient_id=p.id, payment_status='pending').all(),
            'lab_results': p.lab_results,
            'medical_records': p.medical_records
        }

    return render_template('main/merged_dashboard.html',
                           admin=admin_stats,
                           doctor=doctor_stats,
                           receptionist=receptionist_stats,
                           pharmacist=pharmacist_stats,
                           patient=patient_stats)
            stats['pending_bills'] = BillingRecord.query.filter_by(
                patient_id=patient.id,
                payment_status='pending'
            ).all()
            stats['lab_results'] = patient.lab_results
            stats['medical_records'] = patient.medical_records
        
        return render_template('patient/dashboard.html', stats=stats)
