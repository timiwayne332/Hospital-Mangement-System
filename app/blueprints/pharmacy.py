"""
Pharmacy Blueprint - Manage drugs, assignments and pharmacist messaging
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import db, UserRole, User, Drug, PatientDrugAssignment, Patient, Pharmacist, Message
from datetime import datetime

pharmacy_bp = Blueprint('pharmacy', __name__, url_prefix='/pharmacy', template_folder='../templates')


def pharmacist_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.PHARMACIST:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


@pharmacy_bp.route('/dashboard')
@login_required
@pharmacist_required
def dashboard():
    # show quick stats
    total_drugs = Drug.query.count()
    pending_assignments = PatientDrugAssignment.query.filter_by(status='prescribed').count()
    return render_template('pharmacy/dashboard.html', total_drugs=total_drugs, pending_assignments=pending_assignments)


@pharmacy_bp.route('/drugs')
@login_required
@pharmacist_required
def drugs():
    drugs = Drug.query.order_by(Drug.name).all()
    return render_template('pharmacy/drugs.html', drugs=drugs)


@pharmacy_bp.route('/drugs/add', methods=['GET', 'POST'])
@login_required
@pharmacist_required
def add_drug():
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        quantity = int(request.form.get('quantity', 0))
        unit_price = float(request.form.get('unit_price', 0))
        unit = request.form.get('unit', 'pcs')
        description = request.form.get('description')

        if not name or not code:
            flash('Name and code are required.', 'danger')
            return redirect(url_for('pharmacy.add_drug'))

        drug = Drug(name=name, code=code, quantity=quantity, unit_price=unit_price, unit=unit, description=description)
        try:
            db.session.add(drug)
            db.session.commit()
            flash('Drug added successfully.', 'success')
            return redirect(url_for('pharmacy.drugs'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding drug: {e}', 'danger')
    return render_template('pharmacy/add_drug.html')


@pharmacy_bp.route('/assign', methods=['GET', 'POST'])
@login_required
@pharmacist_required
def assign_drug():
    patients = Patient.query.join(User).all()
    drugs = Drug.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        patient_id = int(request.form.get('patient_id'))
        drug_id = int(request.form.get('drug_id'))
        quantity = int(request.form.get('quantity', 1))
        notes = request.form.get('notes')

        assignment = PatientDrugAssignment(drug_id=drug_id, patient_id=patient_id, pharmacist_id=current_user.pharmacist.id if hasattr(current_user, 'pharmacist') and current_user.pharmacist else None, quantity=quantity, notes=notes)
        try:
            db.session.add(assignment)
            db.session.commit()
            flash('Drug assigned to patient.', 'success')
            return redirect(url_for('pharmacy.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error assigning drug: {e}', 'danger')
    return render_template('pharmacy/assign_drug.html', patients=patients, drugs=drugs)


@pharmacy_bp.route('/assignments')
@login_required
@pharmacist_required
def assignments():
    assignments = PatientDrugAssignment.query.order_by(PatientDrugAssignment.created_at.desc()).all()
    return render_template('pharmacy/assignments.html', assignments=assignments)


# Messaging endpoints (reuse message model)
@pharmacy_bp.route('/messages')
@login_required
@pharmacist_required
def messages():
    user = current_user
    sent_messages = Message.query.filter_by(sender_id=user.id).all()
    received_messages = Message.query.filter_by(recipient_id=user.id).all()
    unread_count = Message.query.filter_by(recipient_id=user.id, is_read=False).count()
    return render_template('pharmacy/messages.html', sent_messages=sent_messages, received_messages=received_messages, unread_count=unread_count)


@pharmacy_bp.route('/messages/conversation/<int:user_id>')
@login_required
@pharmacist_required
def conversation(user_id):
    other_user = User.query.get_or_404(user_id)
    user = current_user
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == user.id, Message.recipient_id == user_id),
            db.and_(Message.sender_id == user_id, Message.recipient_id == user.id)
        )
    ).order_by(Message.created_at.asc()).all()

    for msg in messages:
        if msg.recipient_id == user.id and not msg.is_read:
            msg.is_read = True
    db.session.commit()

    # contacts: doctors, admins, receptionists, lab staff
    users = User.query.filter(User.id != user.id).all()
    doctors = [u for u in users if u.role == UserRole.DOCTOR]
    admins = [u for u in users if u.role == UserRole.ADMIN]
    receptionists = [u for u in users if u.role == UserRole.RECEPTIONIST]
    lab_staff = [u for u in users if u.role == UserRole.LAB_STAFF]

    return render_template('pharmacy/conversation.html', messages=messages, other_user=other_user, doctors=doctors, admins=admins, receptionists=receptionists, lab_staff=lab_staff)


@pharmacy_bp.route('/messages/send/<int:recipient_id>', methods=['POST'])
@login_required
@pharmacist_required
def send_message(recipient_id):
    user = current_user
    content = request.form.get('content', '').strip()
    if not content:
        flash('Message cannot be empty.', 'danger')
        return redirect(url_for('pharmacy.conversation', user_id=recipient_id))
    try:
        message = Message(sender_id=user.id, recipient_id=recipient_id, content=content)
        db.session.add(message)
        db.session.commit()
        flash('Message sent.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error sending message: {e}', 'danger')
    return redirect(url_for('pharmacy.conversation', user_id=recipient_id))


@pharmacy_bp.route('/api/messages/<int:user_id>')
@login_required
@pharmacist_required
def get_messages_api(user_id):
    user = current_user
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == user.id, Message.recipient_id == user_id),
            db.and_(Message.sender_id == user_id, Message.recipient_id == user.id)
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
