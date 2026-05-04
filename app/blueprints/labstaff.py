"""
Lab Staff Blueprint - Handles lab staff access to lab results
"""
from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, UserRole, LabResult, Patient, Message, User

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
