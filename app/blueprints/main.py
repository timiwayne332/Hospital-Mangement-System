"""
Main Blueprint - Handles dashboard and general routes
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import (
    User, Patient, Doctor, Appointment, BillingRecord, 
    Medicine, LabTest, Bed, UserRole, Department, AppointmentStatus, db
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
    """Main dashboard for all users"""
    
    # Get statistics based on user role
    stats = {}
    
    if current_user.role == UserRole.ADMIN:
        # Admin dashboard statistics
        stats['total_patients'] = Patient.query.count()
        stats['total_doctors'] = Doctor.query.count()
        stats['total_users'] = User.query.count()
        stats['total_appointments'] = Appointment.query.count()
        stats['pending_bills'] = BillingRecord.query.filter_by(payment_status='pending').count()
        stats['total_medicines'] = Medicine.query.count()
        stats['low_stock_medicines'] = Medicine.query.filter(
            Medicine.quantity <= Medicine.min_stock_level
        ).count()
        stats['available_beds'] = Bed.query.filter_by(is_available=True).count()
        stats['total_beds'] = Bed.query.count()
        
        # Today's appointments
        today = datetime.utcnow().date()
        today_appointments = Appointment.query.filter(
            func.date(Appointment.appointment_date) == today
        ).all()
        
        # Recent billing records
        recent_bills = BillingRecord.query.order_by(
            BillingRecord.created_at.desc()
        ).limit(5).all()

        status_counts = [
            {
                'status': status.value.replace('_', ' ').title(),
                'count': Appointment.query.filter_by(status=status.value).count()
            }
            for status in AppointmentStatus
        ]

        department_data = db.session.query(
            Department.name,
            func.count(Doctor.id)
        ).join(Doctor, Doctor.department_id == Department.id).group_by(Department.id).all()

        department_counts = [
            {'department': name, 'count': count}
            for name, count in department_data
        ]
        
        return render_template('admin/dashboard.html', 
                             stats=stats, 
                             today_appointments=today_appointments,
                             recent_bills=recent_bills,
                             status_counts=status_counts,
                             department_counts=department_counts)
    
    elif current_user.role == UserRole.DOCTOR:
        # Doctor dashboard statistics
        doctor = current_user.doctor
        if doctor:
            stats['total_patients'] = Appointment.query.filter_by(
                doctor_id=doctor.id
            ).distinct(Appointment.patient_id).count()
            stats['pending_appointments'] = Appointment.query.filter_by(
                doctor_id=doctor.id,
                status='scheduled'
            ).count()
            stats['completed_appointments'] = Appointment.query.filter_by(
                doctor_id=doctor.id,
                status='completed'
            ).count()
            
            # Today's appointments
            today = datetime.utcnow().date()
            stats['today_appointments'] = Appointment.query.filter_by(
                doctor_id=doctor.id,
                status='scheduled'
            ).filter(
                func.date(Appointment.appointment_date) == today
            ).all()
        
        return render_template('doctor/dashboard.html', stats=stats)
    
    elif current_user.role == UserRole.RECEPTIONIST:
        # Receptionist dashboard statistics
        stats['total_patients'] = Patient.query.count()
        stats['total_appointments'] = Appointment.query.count()
        stats['pending_appointments'] = Appointment.query.filter_by(
            status='scheduled'
        ).count()
        stats['pending_bills'] = BillingRecord.query.filter_by(
            payment_status='pending'
        ).count()
        
        # Today's appointments
        today = datetime.utcnow().date()
        stats['today_appointments'] = Appointment.query.filter(
            func.date(Appointment.appointment_date) == today
        ).all()
        
        return render_template('receptionist/dashboard.html', stats=stats)
    
    else:
        # Patient dashboard
        patient = current_user.patient
        if patient:
            stats['upcoming_appointments'] = Appointment.query.filter_by(
                patient_id=patient.id,
                status='scheduled'
            ).filter(
                Appointment.appointment_date >= datetime.utcnow()
            ).all()
            stats['pending_bills'] = BillingRecord.query.filter_by(
                patient_id=patient.id,
                payment_status='pending'
            ).all()
            stats['lab_results'] = patient.lab_results
            stats['medical_records'] = patient.medical_records
        
        return render_template('patient/dashboard.html', stats=stats)
