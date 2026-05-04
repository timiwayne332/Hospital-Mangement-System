"""
Receptionist Blueprint - Handles receptionist functions
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import (
    db, UserRole, Patient, Doctor, Appointment, Admission, 
    BillingRecord, Bed, User, AppointmentStatus, LabTest, LabResult, Message, PaymentNotification
)
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
import io

receptionist_bp = Blueprint('receptionist', __name__, url_prefix='/receptionist', template_folder='../templates')


def receptionist_required(f):
    """Decorator to check if user is receptionist"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.RECEPTIONIST:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@receptionist_bp.route('/dashboard')
@login_required
@receptionist_required
def dashboard():
    """Receptionist dashboard"""
    from app.blueprints.main import dashboard as main_dashboard
    return main_dashboard()


# ======================== Appointment Management ========================

@receptionist_bp.route('/appointments')
@login_required
@receptionist_required
def appointments():
    """View and manage appointments"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = Appointment.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    appointments_list = query.order_by(
        Appointment.appointment_date.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('receptionist/appointments.html',
                         appointments=appointments_list,
                         status_filter=status_filter)


@receptionist_bp.route('/appointments/create', methods=['GET', 'POST'])
@login_required
@receptionist_required
def create_appointment():
    """Create new appointment"""
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        doctor_id = request.form.get('doctor_id')
        appointment_date_str = request.form.get('appointment_date')
        reason = request.form.get('reason')
        
        if not all([patient_id, doctor_id, appointment_date_str]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('receptionist.create_appointment'))
        
        try:
            appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%dT%H:%M')
            
            appointment = Appointment(
                patient_id=int(patient_id),
                doctor_id=int(doctor_id),
                appointment_date=appointment_date,
                reason=reason,
                status=AppointmentStatus.SCHEDULED.value
            )
            db.session.add(appointment)
            db.session.commit()
            flash('Appointment created successfully!', 'success')
            return redirect(url_for('receptionist.appointments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating appointment: {str(e)}', 'danger')
    
    patients = Patient.query.all()
    doctors = Doctor.query.filter_by(is_available=True).all()
    return render_template('receptionist/create_appointment.html',
                         patients=patients,
                         doctors=doctors)


@receptionist_bp.route('/appointment/<int:appointment_id>/status', methods=['POST'])
@login_required
@receptionist_required
def update_appointment_status(appointment_id):
    """Update appointment workflow status"""
    appointment = Appointment.query.get_or_404(appointment_id)
    new_status = request.form.get('status')
    allowed_statuses = {
        AppointmentStatus.CONFIRMED.value,
        AppointmentStatus.IN_PROGRESS.value,
        AppointmentStatus.COMPLETED.value,
        AppointmentStatus.CANCELLED.value,
        AppointmentStatus.NO_SHOW.value,
        AppointmentStatus.RESCHEDULED.value,
    }

    if new_status not in allowed_statuses:
        flash('Invalid appointment status.', 'danger')
        return redirect(url_for('receptionist.appointments'))

    appointment.status = new_status
    try:
        db.session.commit()
        flash('Appointment status updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating appointment: {str(e)}', 'danger')

    return redirect(url_for('receptionist.appointments'))


@receptionist_bp.route('/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@receptionist_required
def cancel_appointment(appointment_id):
    """Cancel appointment"""
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = AppointmentStatus.CANCELLED.value
    
    try:
        db.session.commit()
        flash('Appointment cancelled successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelling appointment: {str(e)}', 'danger')
    
    return redirect(url_for('receptionist.appointments'))


# ======================== Patient Management ========================

@receptionist_bp.route('/patients')
@login_required
@receptionist_required
def patients():
    """View all patients"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Patient.query
    
    if search:
        query = query.filter(
            db.or_(
                Patient.patient_id.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        ).join(User)
    
    patients_list = query.paginate(page=page, per_page=10)
    return render_template('receptionist/patients.html',
                         patients=patients_list,
                         search=search)


@receptionist_bp.route('/patient/<int:patient_id>')
@login_required
@receptionist_required
def view_patient(patient_id):
    """View patient details"""
    patient = Patient.query.get_or_404(patient_id)
    appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(
        Appointment.appointment_date.desc()
    ).all()
    
    return render_template('receptionist/patient_detail.html',
                         patient=patient,
                         appointments=appointments)


@receptionist_bp.route('/lab-tests/request', methods=['GET', 'POST'])
@login_required
@receptionist_required
def request_lab_test():
    """Request a lab test for a patient"""
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        lab_test_id = request.form.get('lab_test_id')
        notes = request.form.get('notes')

        if not all([patient_id, lab_test_id]):
            flash('Please select both a patient and a lab test.', 'danger')
            return redirect(url_for('receptionist.request_lab_test'))

        try:
            lab_result = LabResult(
                patient_id=int(patient_id),
                lab_test_id=int(lab_test_id),
                test_date=datetime.utcnow(),
                notes=notes,
                status='pending'
            )
            db.session.add(lab_result)
            db.session.commit()
            flash('Lab test requested successfully!', 'success')
            return redirect(url_for('receptionist.patients'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error requesting lab test: {str(e)}', 'danger')

    patients = Patient.query.all()
    available_tests = LabTest.query.filter_by(is_active=True).all()
    return render_template('receptionist/request_lab_test.html',
                         patients=patients,
                         available_tests=available_tests)


# ======================== Admission/Bed Management ========================

@receptionist_bp.route('/admissions')
@login_required
@receptionist_required
def admissions():
    """View admissions"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = Admission.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    admissions_list = query.order_by(
        Admission.admission_date.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('receptionist/admissions.html',
                         admissions=admissions_list,
                         status_filter=status_filter)


@receptionist_bp.route('/admit-patient', methods=['GET', 'POST'])
@login_required
@receptionist_required
def admit_patient():
    """Admit patient"""
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        bed_id = request.form.get('bed_id')
        reason = request.form.get('reason')
        notes = request.form.get('notes')
        
        if not all([patient_id, bed_id, reason]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('receptionist.admit_patient'))
        
        try:
            admission = Admission(
                patient_id=int(patient_id),
                bed_id=int(bed_id),
                reason=reason,
                notes=notes,
                status='admitted'
            )
            
            # Update bed availability
            bed = Bed.query.get(int(bed_id))
            if bed:
                bed.is_available = False
            
            db.session.add(admission)
            db.session.commit()
            flash('Patient admitted successfully!', 'success')
            return redirect(url_for('receptionist.admissions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error admitting patient: {str(e)}', 'danger')
    
    patients = Patient.query.all()
    available_beds = Bed.query.filter_by(is_available=True).all()
    return render_template('receptionist/admit_patient.html',
                         patients=patients,
                         available_beds=available_beds)


@receptionist_bp.route('/discharge-patient/<int:admission_id>', methods=['POST'])
@login_required
@receptionist_required
def discharge_patient(admission_id):
    """Discharge patient"""
    admission = Admission.query.get_or_404(admission_id)
    
    try:
        admission.status = 'discharged'
        admission.discharge_date = datetime.utcnow()
        
        # Free up bed
        if admission.bed:
            admission.bed.is_available = True
        
        db.session.commit()
        flash('Patient discharged successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error discharging patient: {str(e)}', 'danger')
    
    return redirect(url_for('receptionist.admissions'))


# ======================== Billing & Receipts ========================

@receptionist_bp.route('/billing')
@login_required
@receptionist_required
def billing():
    """View billing records"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = BillingRecord.query
    
    if status_filter != 'all':
        query = query.filter_by(payment_status=status_filter)
    
    bills = query.order_by(
        BillingRecord.created_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('receptionist/billing.html',
                         bills=bills,
                         status_filter=status_filter)


@receptionist_bp.route('/create-bill', methods=['GET', 'POST'])
@login_required
@receptionist_required
def create_bill():
    """Create new billing record"""
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        description = request.form.get('description')
        amount = float(request.form.get('amount', 0))
        tax = float(request.form.get('tax', 0))
        
        if not all([patient_id, description, amount]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('receptionist.create_bill'))
        
        try:
            total_amount = amount + tax
            bill_number = f"BILL{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            billing_record = BillingRecord(
                patient_id=int(patient_id),
                bill_number=bill_number,
                description=description,
                amount=amount,
                tax=tax,
                total_amount=total_amount,
                payment_status='pending'
            )
            db.session.add(billing_record)
            db.session.commit()
            flash('Billing record created successfully!', 'success')
            return redirect(url_for('receptionist.billing'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating billing record: {str(e)}', 'danger')
    
    patients = Patient.query.all()
    return render_template('receptionist/create_bill.html', patients=patients)


@receptionist_bp.route('/bill/<int:bill_id>/payment', methods=['POST'])
@login_required
@receptionist_required
def record_payment(bill_id):
    """Record payment for bill"""
    bill = BillingRecord.query.get_or_404(bill_id)
    payment_method = request.form.get('payment_method', 'cash')
    amount_paid = float(request.form.get('amount_paid', bill.total_amount))
    
    try:
        bill.payment_method = payment_method
        bill.payment_date = datetime.utcnow()
        
        if amount_paid >= bill.total_amount:
            bill.payment_status = 'paid'
        else:
            bill.payment_status = 'partial'
        
        db.session.commit()
        
        # Create payment notifications for all receptionists
        receptionists = User.query.filter_by(role=UserRole.RECEPTIONIST).all()
        patient = Patient.query.get(bill.patient_id)
        
        for receptionist in receptionists:
            notification = PaymentNotification(
                recipient_id=receptionist.id,
                bill_id=bill.id,
                patient_id=bill.patient_id,
                amount_paid=amount_paid,
                payment_method=payment_method,
                message=f"Payment of ₦{amount_paid:,.2f} received from {patient.user.get_full_name()} (Bill: {bill.bill_number})"
            )
            db.session.add(notification)
        
        db.session.commit()
        
        flash('Payment recorded successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error recording payment: {str(e)}', 'danger')
    
    return redirect(url_for('receptionist.billing'))


@receptionist_bp.route('/bill/<int:bill_id>/receipt')
@login_required
@receptionist_required
def generate_receipt(bill_id):
    """Generate PDF receipt"""
    bill = BillingRecord.query.get_or_404(bill_id)
    patient = Patient.query.get(bill.patient_id)
    
    # Create PDF in memory
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77d2'),
        spaceAfter=30,
        alignment=1
    )
    
    # Title
    elements.append(Paragraph('HOSPITAL RECEIPT', title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Receipt details
    receipt_data = [
        ['Receipt Number:', bill.bill_number],
        ['Invoice Date:', bill.bill_date.strftime('%Y-%m-%d %H:%M')],
        ['', ''],
        ['Patient Information:', ''],
        ['Name:', patient.user.get_full_name()],
        ['Patient ID:', patient.patient_id],
        ['', ''],
        ['Bill Details:', ''],
        ['Description:', bill.description],
        ['Amount:', f'${bill.amount:.2f}'],
        ['Tax:', f'${bill.tax:.2f}'],
        ['Total Amount:', f'${bill.total_amount:.2f}'],
        ['', ''],
        ['Payment Status:', bill.payment_status.upper()],
        ['Payment Method:', bill.payment_method or 'Not Yet Paid'],
    ]
    
    table = Table(receipt_data, colWidths=[2.5*inch, 2.5*inch])
    table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 2), (-1, 2), colors.lightgrey),
        ('LINEBELOW', (0, 2), (-1, 2), 2, colors.black),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=1
    )
    elements.append(Paragraph(
        'Thank you for your visit. Please contact the accounting department for further assistance.',
        footer_style
    ))
    
    # Build PDF
    doc.build(elements)
    pdf_buffer.seek(0)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'Receipt_{bill.bill_number}.pdf'
    )


# ======================== Chat System ========================

@receptionist_bp.route('/messages')
@login_required
@receptionist_required
def messages():
    """View all messages"""
    receptionist = current_user
    # Get conversations
    sent_messages = Message.query.filter_by(sender_id=receptionist.id).all()
    received_messages = Message.query.filter_by(recipient_id=receptionist.id).all()
    
    # Get unread count
    unread_count = Message.query.filter_by(recipient_id=receptionist.id, is_read=False).count()
    
    return render_template('receptionist/messages.html',
                         sent_messages=sent_messages,
                         received_messages=received_messages,
                         unread_count=unread_count)


@receptionist_bp.route('/messages/conversation/<int:user_id>')
@login_required
@receptionist_required
def conversation(user_id):
    """View conversation with a specific user"""
    other_user = User.query.get_or_404(user_id)
    receptionist = current_user
    
    # Get all messages between receptionist and other user
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == receptionist.id, Message.recipient_id == user_id),
            db.and_(Message.sender_id == user_id, Message.recipient_id == receptionist.id)
        )
    ).order_by(Message.created_at.asc()).all()
    
    # Mark received messages as read
    for msg in messages:
        if msg.recipient_id == receptionist.id and not msg.is_read:
            msg.is_read = True
    db.session.commit()
    
    # Get list of doctors and admins
    doctors = User.query.filter_by(role=UserRole.DOCTOR).all()
    admins = User.query.filter_by(role=UserRole.ADMIN).all()
    
    return render_template('receptionist/conversation.html',
                         messages=messages,
                         other_user=other_user,
                         doctors=doctors,
                         admins=admins)


@receptionist_bp.route('/messages/send/<int:recipient_id>', methods=['POST'])
@login_required
@receptionist_required
def send_message(recipient_id):
    """Send a message"""
    receptionist = current_user
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Message cannot be empty.', 'danger')
        return redirect(url_for('receptionist.conversation', user_id=recipient_id))
    
    try:
        message = Message(
            sender_id=receptionist.id,
            recipient_id=recipient_id,
            content=content
        )
        db.session.add(message)
        db.session.commit()
        flash('Message sent successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error sending message: {str(e)}', 'danger')
    
    return redirect(url_for('receptionist.conversation', user_id=recipient_id))


@receptionist_bp.route('/api/messages/<int:user_id>')
@login_required
@receptionist_required
def get_messages_api(user_id):
    """API endpoint to get messages for AJAX"""
    receptionist = current_user
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == receptionist.id, Message.recipient_id == user_id),
            db.and_(Message.sender_id == user_id, Message.recipient_id == receptionist.id)
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


@receptionist_bp.route('/api/notifications')
@login_required
@receptionist_required
def get_notifications_api():
    """API endpoint to get payment notifications for AJAX"""
    notifications = PaymentNotification.query.filter_by(
        recipient_id=current_user.id,
        is_read=False
    ).order_by(PaymentNotification.created_at.desc()).all()
    
    return jsonify([{
        'id': n.id,
        'bill_id': n.bill_id,
        'patient_name': n.patient.user.get_full_name() if n.patient else 'N/A',
        'amount_paid': n.amount_paid,
        'payment_method': n.payment_method,
        'message': n.message,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for n in notifications])


@receptionist_bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
@receptionist_required
def mark_notification_read_api(notification_id):
    """API endpoint to mark a notification as read"""
    notification = PaymentNotification.query.get_or_404(notification_id)
    
    if notification.recipient_id == current_user.id:
        notification.is_read = True
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Unauthorized'}), 403
