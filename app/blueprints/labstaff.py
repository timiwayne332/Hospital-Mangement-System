"""
Lab Staff Blueprint - Handles lab staff access to lab results
"""
from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, UserRole, LabResult, Patient, Message, User, LabTest

labstaff_bp = Blueprint('labstaff', __name__, url_prefix='/labstaff', template_folder='../templates')


def lab_staff_required(f):
    """Decorator to check if user is lab staff."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.LAB_STAFF:
            flash('Access restricted to lab staff only.', 'danger')
            return redirect(url_for('auth.lab_login'))
        return f(*args, **kwargs)
    return decorated_function


@labstaff_bp.route('/dashboard')
@login_required
@lab_staff_required
def dashboard():
    """Lab staff dashboard with recent lab results."""
    total_results = LabResult.query.count()
    pending_results = LabResult.query.filter((LabResult.status == None) | (LabResult.status == '')).count()
    recent_results = LabResult.query.order_by(LabResult.test_date.desc()).limit(10).all()
    return render_template(
        'labstaff/dashboard.html',
        total_results=total_results,
        pending_results=pending_results,
        recent_results=recent_results
    )


@labstaff_bp.route('/lab-tests')
@login_required
@lab_staff_required
def lab_tests_list():
    """List all available lab tests managed by the lab department."""
    tests = LabTest.query.order_by(LabTest.test_name.asc()).all()
    return render_template('labstaff/lab_tests_list.html', tests=tests)


@labstaff_bp.route('/lab-tests/<int:test_id>/delete', methods=['POST'])
@login_required
@lab_staff_required
def delete_lab_test(test_id):
    """Delete a lab test definition from the catalog."""
    test = LabTest.query.get_or_404(test_id)

    try:
        db.session.delete(test)
        db.session.commit()
        flash(f'Lab test "{test.test_name}" deleted successfully.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Error deleting lab test: {str(exc)}', 'danger')

    return redirect(url_for('labstaff.lab_tests_list'))


@labstaff_bp.route('/lab-tests/create', methods=['GET', 'POST'])
@login_required
@lab_staff_required
def create_lab_test():
    """Create a new lab test definition."""
    if request.method == 'POST':
        test_code = (request.form.get('test_code') or '').strip()
        test_name = (request.form.get('test_name') or '').strip()
        description = (request.form.get('description') or '').strip()
        normal_range = (request.form.get('normal_range') or '').strip()
        unit = (request.form.get('unit') or '').strip()
        turnaround_time = (request.form.get('turnaround_time') or '').strip()

        try:
            price = float(request.form.get('price', 0) or 0)
        except ValueError:
            flash('Price must be a valid number.', 'danger')
            return redirect(url_for('labstaff.create_lab_test'))

        if not test_code or not test_name:
            flash('Test code and name are required.', 'danger')
            return redirect(url_for('labstaff.create_lab_test'))

        if LabTest.query.filter_by(test_code=test_code).first():
            flash('A lab test with that code already exists.', 'danger')
            return redirect(url_for('labstaff.create_lab_test'))

        try:
            test = LabTest(
                test_code=test_code,
                test_name=test_name,
                description=description or None,
                normal_range=normal_range or None,
                unit=unit or None,
                price=price,
                turnaround_time=turnaround_time or None,
                is_active=True,
            )
            db.session.add(test)
            db.session.commit()
            flash('Lab test created successfully!', 'success')
            return redirect(url_for('labstaff.lab_tests_list'))
        except Exception as exc:
            db.session.rollback()
            flash(f'Error creating lab test: {str(exc)}', 'danger')

    return render_template('labstaff/create_lab_test.html')


@labstaff_bp.route('/results')
@login_required
@lab_staff_required
def lab_results():
    """List lab results with an optional patient filter."""
    patient_id = request.args.get('patient_id', type=int)
    query = LabResult.query.order_by(LabResult.test_date.desc())
    if patient_id:
        query = query.filter_by(patient_id=patient_id)
    results = query.all()
    return render_template('labstaff/lab_results.html', lab_results=results, patient_id=patient_id)


@labstaff_bp.route('/results/<int:result_id>/send', methods=['POST'])
@login_required
@lab_staff_required
def send_lab_result(result_id):
    """Send a lab result notification to a doctor or receptionist."""
    lab_result = LabResult.query.get_or_404(result_id)
    recipient_id = request.form.get('recipient_id', type=int)
    message_text = request.form.get('message', '').strip()

    if not recipient_id or not message_text:
        flash('Please select a recipient and enter a message.', 'danger')
        return redirect(url_for('labstaff.view_lab_result', result_id=result_id))

    recipient = User.query.get(recipient_id)
    if not recipient or recipient.role not in [UserRole.DOCTOR, UserRole.RECEPTIONIST]:
        flash('Invalid recipient selected.', 'danger')
        return redirect(url_for('labstaff.view_lab_result', result_id=result_id))

    try:
        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            content=message_text
        )
        db.session.add(message)

        if not lab_result.result_date:
            lab_result.result_date = datetime.utcnow()

        db.session.commit()
        flash('Lab result sent successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error sending lab result: {str(e)}', 'danger')

    return redirect(url_for('labstaff.view_lab_result', result_id=result_id))


@labstaff_bp.route('/results/<int:result_id>')
@login_required
@lab_staff_required
def view_lab_result(result_id):
    """View a single lab result record."""
    lab_result = LabResult.query.get_or_404(result_id)
    doctors = User.query.filter_by(role=UserRole.DOCTOR).all()
    receptionists = User.query.filter_by(role=UserRole.RECEPTIONIST).all()
    return render_template('labstaff/view_lab_result.html', result=lab_result, doctors=doctors, receptionists=receptionists)


# ======================== Department Chat System ========================

@labstaff_bp.route('/messages')
@login_required
@lab_staff_required
def messages():
    """View all department chat conversations for lab staff."""
    sent_messages = Message.query.filter_by(sender_id=current_user.id).all()
    received_messages = Message.query.filter_by(recipient_id=current_user.id).all()
    unread_count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    staff_members = User.query.filter(
        User.id != current_user.id,
        User.role.in_([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST, UserRole.LAB_STAFF])
    ).all()

    return render_template(
        'labstaff/messages.html',
        sent_messages=sent_messages,
        received_messages=received_messages,
        unread_count=unread_count,
        staff_members=staff_members,
    )


@labstaff_bp.route('/messages/conversation/<int:user_id>')
@login_required
@lab_staff_required
def conversation(user_id):
    """View a direct conversation with another department user."""
    other_user = User.query.get_or_404(user_id)
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user.id, Message.recipient_id == user_id),
            db.and_(Message.sender_id == user_id, Message.recipient_id == current_user.id),
        )
    ).order_by(Message.created_at.asc()).all()

    for msg in messages:
        if msg.recipient_id == current_user.id and not msg.is_read:
            msg.is_read = True
    db.session.commit()

    staff_members = User.query.filter(
        User.id != current_user.id,
        User.role.in_([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST, UserRole.LAB_STAFF])
    ).all()

    return render_template(
        'labstaff/conversation.html',
        messages=messages,
        other_user=other_user,
        staff_members=staff_members,
    )


@labstaff_bp.route('/messages/send/<int:recipient_id>', methods=['POST'])
@login_required
@lab_staff_required
def send_message(recipient_id):
    """Send a message to another department."""
    content = request.form.get('content', '').strip()
    if not content:
        flash('Message cannot be empty.', 'danger')
        return redirect(url_for('labstaff.conversation', user_id=recipient_id))

    recipient = User.query.get(recipient_id)
    if not recipient or recipient.id == current_user.id:
        flash('Invalid recipient selected.', 'danger')
        return redirect(url_for('labstaff.messages'))

    if recipient.role not in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST, UserRole.LAB_STAFF]:
        flash('You can only message other hospital departments.', 'danger')
        return redirect(url_for('labstaff.messages'))

    try:
        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            content=content,
        )
        db.session.add(message)
        db.session.commit()
        flash('Lab result sent successfully.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(f'Error sending message: {str(exc)}', 'danger')

    return redirect(url_for('labstaff.conversation', user_id=recipient_id))


@labstaff_bp.route('/api/messages/<int:user_id>')
@login_required
@lab_staff_required
def get_messages_api(user_id):
    """Return message history for another department user."""
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user.id, Message.recipient_id == user_id),
            db.and_(Message.sender_id == user_id, Message.recipient_id == current_user.id),
        )
    ).order_by(Message.created_at.asc()).all()

    return jsonify([{
        'id': m.id,
        'sender_id': m.sender_id,
        'sender_name': m.sender.get_full_name(),
        'content': m.content,
        'created_at': m.created_at.isoformat(),
        'is_read': m.is_read,
    } for m in messages])
