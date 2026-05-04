"""
Analytics utilities for dashboard calculations and reporting
"""
from sqlalchemy import func, and_
from app.models import (
    Patient, Doctor, Appointment, MedicalRecord, LabResult, 
    BillingRecord, Admission, Prescription, AppointmentStatus, UserRole
)
from datetime import datetime, timedelta


def get_dashboard_summary():
    """Get overall system summary statistics"""
    return {
        'total_patients': Patient.query.count(),
        'total_doctors': Doctor.query.count(),
        'active_admissions': Admission.query.filter_by(status='admitted').count(),
        'pending_bills': BillingRecord.query.filter_by(payment_status='pending').count(),
        'total_revenue': get_total_revenue(),
    }


def get_patient_statistics():
    """Get patient-related statistics"""
    total_patients = Patient.query.count()
    new_patients_this_month = Patient.query.filter(
        Patient.created_at >= datetime.utcnow().replace(day=1)
    ).count()
    
    return {
        'total_patients': total_patients,
        'new_this_month': new_patients_this_month,
        'by_gender': get_patients_by_gender(),
    }


def get_patients_by_gender():
    """Get patient count by gender"""
    genders = Patient.query.with_entities(
        Patient.gender,
        func.count(Patient.id).label('count')
    ).group_by(Patient.gender).all()
    
    return {gender: count for gender, count in genders if gender}


def get_appointment_statistics(days=30):
    """Get appointment statistics for the last N days"""
    from_date = datetime.utcnow() - timedelta(days=days)
    
    total = Appointment.query.filter(
        Appointment.created_at >= from_date
    ).count()
    
    status_counts = Appointment.query.filter(
        Appointment.created_at >= from_date
    ).with_entities(
        Appointment.status,
        func.count(Appointment.id).label('count')
    ).group_by(Appointment.status).all()
    
    return {
        'total': total,
        'by_status': {status.value if hasattr(status, 'value') else status: count 
                     for status, count in status_counts}
    }


def get_appointment_by_date(days=30):
    """Get appointment count by date for chart"""
    from_date = datetime.utcnow() - timedelta(days=days)
    
    appointments = Appointment.query.filter(
        Appointment.created_at >= from_date
    ).with_entities(
        func.date(Appointment.created_at).label('date'),
        func.count(Appointment.id).label('count')
    ).group_by(func.date(Appointment.created_at)).all()
    
    return {str(date): count for date, count in appointments}


def get_revenue_statistics(days=30):
    """Get revenue statistics"""
    from_date = datetime.utcnow() - timedelta(days=days)
    
    total_bills = BillingRecord.query.filter(
        BillingRecord.bill_date >= from_date
    ).with_entities(
        func.sum(BillingRecord.total_amount)
    ).scalar() or 0
    
    paid_amount = BillingRecord.query.filter(
        and_(
            BillingRecord.bill_date >= from_date,
            BillingRecord.payment_status == 'paid'
        )
    ).with_entities(
        func.sum(BillingRecord.total_amount)
    ).scalar() or 0
    
    pending_amount = BillingRecord.query.filter(
        and_(
            BillingRecord.bill_date >= from_date,
            BillingRecord.payment_status == 'pending'
        )
    ).with_entities(
        func.sum(BillingRecord.total_amount)
    ).scalar() or 0
    
    return {
        'total_amount': float(total_bills),
        'paid_amount': float(paid_amount),
        'pending_amount': float(pending_amount),
        'paid_percentage': (float(paid_amount) / float(total_bills) * 100) if total_bills > 0 else 0,
    }


def get_total_revenue():
    """Get total revenue from all paid bills"""
    total = BillingRecord.query.filter_by(
        payment_status='paid'
    ).with_entities(
        func.sum(BillingRecord.total_amount)
    ).scalar() or 0
    
    return float(total)


def get_doctor_performance(days=30):
    """Get doctor performance metrics"""
    from_date = datetime.utcnow() - timedelta(days=days)
    
    doctors_data = []
    doctors = Doctor.query.all()
    
    for doctor in doctors:
        appointments = Appointment.query.filter(
            and_(
                Appointment.doctor_id == doctor.id,
                Appointment.created_at >= from_date
            )
        ).count()
        
        completed = Appointment.query.filter(
            and_(
                Appointment.doctor_id == doctor.id,
                Appointment.status == AppointmentStatus.COMPLETED,
                Appointment.created_at >= from_date
            )
        ).count()
        
        doctors_data.append({
            'name': doctor.user.get_full_name(),
            'specialization': doctor.specialization,
            'total_appointments': appointments,
            'completed_appointments': completed,
        })
    
    return doctors_data


def get_laboratory_statistics(days=30):
    """Get lab result statistics"""
    from_date = datetime.utcnow() - timedelta(days=days)
    
    total_tests = LabResult.query.filter(
        LabResult.test_date >= from_date
    ).count()
    
    abnormal_tests = LabResult.query.filter(
        and_(
            LabResult.test_date >= from_date,
            LabResult.status == 'abnormal'
        )
    ).count()
    
    normal_tests = LabResult.query.filter(
        and_(
            LabResult.test_date >= from_date,
            LabResult.status == 'normal'
        )
    ).count()
    
    return {
        'total_tests': total_tests,
        'normal': normal_tests,
        'abnormal': abnormal_tests,
        'normal_percentage': (normal_tests / total_tests * 100) if total_tests > 0 else 0,
    }


def get_admission_statistics(days=30):
    """Get admission statistics"""
    from_date = datetime.utcnow() - timedelta(days=days)
    
    total_admissions = Admission.query.filter(
        Admission.admission_date >= from_date
    ).count()
    
    current_admissions = Admission.query.filter_by(status='admitted').count()
    
    discharged = Admission.query.filter(
        and_(
            Admission.discharge_date >= from_date,
            Admission.status == 'discharged'
        )
    ).count()
    
    return {
        'total_admissions': total_admissions,
        'current_admitted': current_admissions,
        'discharged_this_period': discharged,
    }


def get_prescription_statistics(days=30):
    """Get prescription statistics"""
    from_date = datetime.utcnow() - timedelta(days=days)
    
    total_prescriptions = Prescription.query.filter(
        Prescription.prescription_date >= from_date
    ).count()
    
    active_prescriptions = Prescription.query.filter(
        and_(
            Prescription.prescription_date >= from_date,
            Prescription.status == 'active'
        )
    ).count()
    
    dispensed = Prescription.query.filter(
        and_(
            Prescription.prescription_date >= from_date,
            Prescription.status == 'dispensed'
        )
    ).count()
    
    return {
        'total': total_prescriptions,
        'active': active_prescriptions,
        'dispensed': dispensed,
    }


def get_top_departments(limit=5):
    """Get top departments by number of appointments"""
    # Department popularity based on doctors
    departments = {}
    doctors = Doctor.query.all()
    
    for doctor in doctors:
        if doctor.department:
            dept_name = doctor.department.name
            if dept_name not in departments:
                departments[dept_name] = 0
            
            appointments = Appointment.query.filter_by(
                doctor_id=doctor.id
            ).count()
            departments[dept_name] += appointments
    
    sorted_depts = sorted(departments.items(), key=lambda x: x[1], reverse=True)
    return dict(sorted_depts[:limit])


def get_payment_method_distribution(days=30):
    """Get distribution of payment methods"""
    from_date = datetime.utcnow() - timedelta(days=days)
    
    methods = BillingRecord.query.filter(
        and_(
            BillingRecord.bill_date >= from_date,
            BillingRecord.payment_status == 'paid'
        )
    ).with_entities(
        BillingRecord.payment_method,
        func.count(BillingRecord.id).label('count')
    ).group_by(BillingRecord.payment_method).all()
    
    return {method: count for method, count in methods if method}
