"""
Doctor Blueprint - Handles doctor-specific functions
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import (
    db, UserRole, Doctor, Appointment, AppointmentStatus, MedicalRecord, 
    Patient, LabResult, LabTest, Message, User
)
from datetime import datetime

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor', template_folder='../templates')


def doctor_required(f):
    """Decorator to check if user is doctor"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.DOCTOR:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@doctor_bp.route('/dashboard')
@login_required
@doctor_required
def dashboard():
    """Doctor dashboard"""
    from app.blueprints.main import dashboard as main_dashboard
    return main_dashboard()


# ======================== Appointment Management ========================

@doctor_bp.route('/appointments')
@login_required
@doctor_required
def appointments():
    """View doctor's appointments"""
    doctor = current_user.doctor
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = Appointment.query.filter_by(doctor_id=doctor.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    appointments_list = query.order_by(
        Appointment.appointment_date.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('doctor/appointments.html',
                         appointments=appointments_list,
                         status_filter=status_filter)


@doctor_bp.route('/appointment/<int:appointment_id>')
@login_required
@doctor_required
def view_appointment(appointment_id):
    """View appointment details"""
    doctor = current_user.doctor
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.doctor_id != doctor.id:
        flash('You do not have permission to view this appointment.', 'danger')
        return redirect(url_for('doctor.appointments'))
    
    # Get medical records for this patient
    medical_records = MedicalRecord.query.filter_by(patient_id=appointment.patient_id, doctor_id=doctor.id).all()
    
    return render_template('doctor/appointment_detail.html', appointment=appointment, medical_records=medical_records)


@doctor_bp.route('/appointment/<int:appointment_id>/complete', methods=['POST'])
@login_required
@doctor_required
def complete_appointment(appointment_id):
    """Mark appointment as completed"""
    doctor = current_user.doctor
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.doctor_id != doctor.id:
        flash('You do not have permission to modify this appointment.', 'danger')
        return redirect(url_for('doctor.appointments'))
    
    appointment.status = AppointmentStatus.COMPLETED.value
    
    try:
        db.session.commit()
        flash('Appointment marked as completed.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating appointment: {str(e)}', 'danger')
    
    return redirect(url_for('doctor.appointments'))


# ======================== Medical Records ========================

@doctor_bp.route('/medical-records')
@login_required
@doctor_required
def medical_records():
    """View medical records created by doctor"""
    doctor = current_user.doctor
    page = request.args.get('page', 1, type=int)
    
    records = MedicalRecord.query.filter_by(doctor_id=doctor.id).order_by(
        MedicalRecord.created_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('doctor/medical_records.html', records=records)


@doctor_bp.route('/appointment/<int:appointment_id>/add-record', methods=['GET', 'POST'])
@login_required
@doctor_required
def add_medical_record(appointment_id):
    """Add medical record for appointment"""
    doctor = current_user.doctor
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.doctor_id != doctor.id:
        flash('You do not have permission to add a record for this appointment.', 'danger')
        return redirect(url_for('doctor.appointments'))
    
    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis')
        treatment = request.form.get('treatment')
        prescription = request.form.get('prescription')
        notes = request.form.get('notes')
        
        if not diagnosis:
            flash('Diagnosis is required.', 'danger')
            return redirect(url_for('doctor.add_medical_record', appointment_id=appointment_id))
        
        try:
            record = MedicalRecord(
                patient_id=appointment.patient_id,
                doctor_id=doctor.id,
                diagnosis=diagnosis,
                treatment=treatment,
                prescription=prescription,
                notes=notes,
                visit_date=datetime.utcnow()
            )
            db.session.add(record)
            
            # Mark appointment as completed
            appointment.status = 'completed'
            
            db.session.commit()
            flash('Medical record created successfully!', 'success')
            return redirect(url_for('doctor.appointments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating medical record: {str(e)}', 'danger')
    
    # Calculate patient age
    today = datetime.now().date()
    patient = appointment.patient
    if patient.date_of_birth:
        age = today.year - patient.date_of_birth.year - (
            (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
        )
    else:
        age = None
    
    return render_template('doctor/add_medical_record.html', appointment=appointment, patient_age=age)


@doctor_bp.route('/medical-record/<int:record_id>/view')
@login_required
@doctor_required
def view_medical_record(record_id):
    """View medical record"""
    doctor = current_user.doctor
    record = MedicalRecord.query.get_or_404(record_id)
    
    if record.doctor_id != doctor.id:
        flash('You do not have permission to view this record.', 'danger')
        return redirect(url_for('doctor.medical_records'))
    
    return render_template('doctor/view_medical_record.html', record=record)


# ======================== Patient Management ========================

@doctor_bp.route('/patients')
@login_required
@doctor_required
def patients():
    """View patients who have appointments with this doctor"""
    doctor = current_user.doctor
    page = request.args.get('page', 1, type=int)
    
    # Get distinct patients from appointments
    patients_list = db.session.query(Patient).join(
        Appointment, Patient.id == Appointment.patient_id
    ).filter(
        Appointment.doctor_id == doctor.id
    ).distinct().paginate(page=page, per_page=10)
    
    # Calculate ages for patients
    today = datetime.now().date()
    for patient in patients_list.items:
        if patient.date_of_birth:
            patient.age = today.year - patient.date_of_birth.year - (
                (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
            )
        else:
            patient.age = None
    
    return render_template('doctor/patients.html', patients=patients_list)


@doctor_bp.route('/patient/<int:patient_id>')
@login_required
@doctor_required
def view_patient(patient_id):
    """View patient details"""
    doctor = current_user.doctor
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if doctor has seen this patient
    has_appointment = Appointment.query.filter_by(
        patient_id=patient_id,
        doctor_id=doctor.id
    ).first()
    
    if not has_appointment:
        flash('You do not have permission to view this patient.', 'danger')
        return redirect(url_for('doctor.patients'))
    
    medical_records = MedicalRecord.query.filter_by(patient_id=patient_id).all()
    lab_results = LabResult.query.filter_by(patient_id=patient_id).all()
    
    return render_template('doctor/patient_detail.html',
                         patient=patient,
                         medical_records=medical_records,
                         lab_results=lab_results)


# ======================== Lab Results ========================

@doctor_bp.route('/patient/<int:patient_id>/request-lab-test', methods=['GET', 'POST'])
@login_required
@doctor_required
def request_lab_test(patient_id):
    """Request lab test for patient"""
    doctor = current_user.doctor
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if doctor has seen this patient
    has_appointment = Appointment.query.filter_by(
        patient_id=patient_id,
        doctor_id=doctor.id
    ).first()
    
    if not has_appointment:
        flash('You do not have permission to request tests for this patient.', 'danger')
        return redirect(url_for('doctor.patients'))
    
    if request.method == 'POST':
        test_id = request.form.get('test_id')
        
        try:
            lab_result = LabResult(
                patient_id=patient_id,
                lab_test_id=test_id,
                test_date=datetime.utcnow()
            )
            db.session.add(lab_result)
            db.session.commit()
            flash('Lab test requested successfully!', 'success')
            return redirect(url_for('doctor.view_patient', patient_id=patient_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error requesting lab test: {str(e)}', 'danger')
    
    available_tests = LabTest.query.filter_by(is_active=True).all()
    return render_template('doctor/request_lab_test.html',
                         patient=patient,
                         available_tests=available_tests)


@doctor_bp.route('/patient/<int:patient_id>/lab-results')
@login_required
@doctor_required
def patient_lab_results(patient_id):
    """View patient's lab results"""
    doctor = current_user.doctor
    patient = Patient.query.get_or_404(patient_id)
    
    has_appointment = Appointment.query.filter_by(
        patient_id=patient_id,
        doctor_id=doctor.id
    ).first()
    
    if not has_appointment:
        flash('You do not have permission to view this patient.', 'danger')
        return redirect(url_for('doctor.patients'))
    
    lab_results = LabResult.query.filter_by(patient_id=patient_id).all()
    return render_template('doctor/patient_lab_results.html',
                         patient=patient,
                         lab_results=lab_results)


# ======================== Chat System ========================

@doctor_bp.route('/messages')
@login_required
@doctor_required
def messages():
    """View all messages"""
    doctor = current_user
    # Get conversations (unique recipients and senders)
    sent_messages = Message.query.filter_by(sender_id=doctor.id).all()
    received_messages = Message.query.filter_by(recipient_id=doctor.id).all()
    
    # Get unread count
    unread_count = Message.query.filter_by(recipient_id=doctor.id, is_read=False).count()
    
    return render_template('doctor/messages.html',
                         sent_messages=sent_messages,
                         received_messages=received_messages,
                         unread_count=unread_count)


@doctor_bp.route('/messages/conversation/<int:user_id>')
@login_required
@doctor_required
def conversation(user_id):
    """View conversation with a specific user"""
    other_user = User.query.get_or_404(user_id)
    doctor = current_user
    
    # Get all messages between doctor and other user
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == doctor.id, Message.recipient_id == user_id),
            db.and_(Message.sender_id == user_id, Message.recipient_id == doctor.id)
        )
    ).order_by(Message.created_at.asc()).all()
    
    # Mark received messages as read
    for msg in messages:
        if msg.recipient_id == doctor.id and not msg.is_read:
            msg.is_read = True
    db.session.commit()
    
    # Get list of admins or other doctors for sidebar
    admins = User.query.filter_by(role=UserRole.ADMIN).all()
    other_doctors = User.query.filter(
        User.role == UserRole.DOCTOR,
        User.id != doctor.id
    ).all()
    
    return render_template('doctor/conversation.html',
                         messages=messages,
                         other_user=other_user,
                         admins=admins,
                         other_doctors=other_doctors)


@doctor_bp.route('/messages/send/<int:recipient_id>', methods=['POST'])
@login_required
@doctor_required
def send_message(recipient_id):
    """Send a message"""
    doctor = current_user
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Message cannot be empty.', 'danger')
        return redirect(url_for('doctor.conversation', user_id=recipient_id))
    
    try:
        message = Message(
            sender_id=doctor.id,
            recipient_id=recipient_id,
            content=content
        )
        db.session.add(message)
        db.session.commit()
        flash('Message sent successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error sending message: {str(e)}', 'danger')
    
    return redirect(url_for('doctor.conversation', user_id=recipient_id))


@doctor_bp.route('/api/messages/<int:user_id>')
@login_required
@doctor_required
def get_messages_api(user_id):
    """API endpoint to get messages for AJAX"""
    doctor = current_user
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == doctor.id, Message.recipient_id == user_id),
            db.and_(Message.sender_id == user_id, Message.recipient_id == doctor.id)
        )
    ).order_by(Message.created_at.asc()).all()
    
    return jsonify([{
        'id': m.id,
        'sender_id': m.sender_id,
        'sender_name': m.sender.get_full_name(),
        'content': m.content,
        'created_at': m.created_at.isoformat(),
        'is_read': m.is_read
    } for m in messages])
