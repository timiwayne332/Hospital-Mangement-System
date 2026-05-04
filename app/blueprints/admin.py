"""
Admin Blueprint - Handles admin dashboard and management functions
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import (
    db, User, Patient, Doctor, LabStaff, Appointment, UserRole, Bed, 
    BillingRecord, Medicine, LabTest, Department, Insurance, AuditLog, Message
)
from app.utils.audit_logger import log_audit
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='../templates')


def admin_required(f):
    """Decorator to check if user is admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    from app.blueprints.main import dashboard as main_dashboard
    return main_dashboard()


# ======================== User Management ========================

@admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    """View all users"""
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', 'all')
    
    query = User.query
    
    if role_filter != 'all':
        try:
            role = UserRole[role_filter.upper()]
            query = query.filter_by(role=role)
        except KeyError:
            pass
    
    users = query.paginate(page=page, per_page=10)
    return render_template('admin/users_list.html', users=users, role_filter=role_filter)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create new user"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        role = request.form.get('role')
        
        # Validate input
        if not all([username, email, password, role]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin.create_user'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.create_user'))
        
        try:
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=UserRole[role.upper()]
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            log_audit('Created', 'User', user.id, new_values={
                'username': username,
                'email': email,
                'role': role
            }, details='New user created by admin')
            
            # Create doctor record if role is doctor
            if role.upper() == 'DOCTOR':
                doctor = Doctor(
                    user_id=user.id,
                    doctor_id=f"DOC{user.id:05d}"
                )
                db.session.add(doctor)
                db.session.commit()
            elif role.upper() == 'LAB_STAFF':
                lab_staff = LabStaff(
                    user_id=user.id,
                    lab_staff_id=f"LAB{user.id:05d}"
                )
                db.session.add(lab_staff)
                db.session.commit()
            
            flash(f'User {username} created successfully!', 'success')
            return redirect(url_for('admin.users_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'danger')
    
    return render_template('admin/create_user.html')


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user details"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        old_values = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'is_active': user.is_active
        }

        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        user.is_active = request.form.get('is_active') == 'on'
        
        if request.form.get('password'):
            user.set_password(request.form.get('password'))
        
        try:
            db.session.commit()
            new_values = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'is_active': user.is_active
            }
            log_audit('Updated', 'User', user.id, old_values=old_values, new_values=new_values, details='Admin updated user profile')
            flash('User updated successfully!', 'success')
            return redirect(url_for('admin.users_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'danger')
    
    return render_template('admin/edit_user.html', user=user)


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user"""
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users_list'))
    
    user = User.query.get_or_404(user_id)
    
    try:
        db.session.delete(user)
        db.session.commit()
        log_audit('Deleted', 'User', user_id, details=f'Admin deleted user {user.username}')
        flash(f'User {user.username} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users_list'))


# ======================== Doctor Management ========================

@admin_bp.route('/doctors')
@login_required
@admin_required
def doctors_list():
    """View all doctors"""
    page = request.args.get('page', 1, type=int)
    doctors = Doctor.query.paginate(page=page, per_page=10)
    return render_template('admin/doctors_list.html', doctors=doctors)


@admin_bp.route('/doctors/<int:doctor_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_doctor(doctor_id):
    """Edit doctor details"""
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if request.method == 'POST':
        doctor.specialization = request.form.get('specialization')
        doctor.license_number = request.form.get('license_number')
        doctor.qualification = request.form.get('qualification')
        doctor.bio = request.form.get('bio')
        doctor.consultation_fee = float(request.form.get('consultation_fee', 0))
        doctor.is_available = request.form.get('is_available') == 'on'
        doctor.working_hours = request.form.get('working_hours')
        
        try:
            db.session.commit()
            flash('Doctor updated successfully!', 'success')
            return redirect(url_for('admin.doctors_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating doctor: {str(e)}', 'danger')
    
    return render_template('admin/edit_doctor.html', doctor=doctor)


# ======================== Bed Management ========================

@admin_bp.route('/beds')
@login_required
@admin_required
def beds_list():
    """View all beds"""
    page = request.args.get('page', 1, type=int)
    beds = Bed.query.paginate(page=page, per_page=10)
    return render_template('admin/beds_list.html', beds=beds)


@admin_bp.route('/beds/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_bed():
    """Create new bed"""
    if request.method == 'POST':
        bed_number = request.form.get('bed_number')
        room_number = request.form.get('room_number')
        ward = request.form.get('ward')
        bed_type = request.form.get('bed_type')
        
        if Bed.query.filter_by(bed_number=bed_number).first():
            flash('Bed number already exists.', 'danger')
            return redirect(url_for('admin.create_bed'))
        
        try:
            bed = Bed(
                bed_number=bed_number,
                room_number=room_number,
                ward=ward,
                bed_type=bed_type
            )
            db.session.add(bed)
            db.session.commit()
            log_audit('Created', 'Bed', bed.id, new_values={
                'bed_number': bed_number,
                'ward': ward,
                'bed_type': bed_type
            }, details='New bed added by admin')
            flash('Bed created successfully!', 'success')
            return redirect(url_for('admin.beds_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating bed: {str(e)}', 'danger')
    
    return render_template('admin/create_bed.html')


# ======================== Lab Test Management ========================

@admin_bp.route('/lab-tests')
@login_required
@admin_required
def lab_tests_list():
    """View all lab tests"""
    page = request.args.get('page', 1, type=int)
    tests = LabTest.query.paginate(page=page, per_page=10)
    return render_template('admin/lab_tests_list.html', tests=tests)


@admin_bp.route('/lab-tests/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_lab_test():
    """Create new lab test"""
    if request.method == 'POST':
        test_code = request.form.get('test_code')
        test_name = request.form.get('test_name')
        description = request.form.get('description')
        normal_range = request.form.get('normal_range')
        unit = request.form.get('unit')
        price = float(request.form.get('price', 0))
        turnaround_time = request.form.get('turnaround_time')
        
        if LabTest.query.filter_by(test_code=test_code).first():
            flash('Test code already exists.', 'danger')
            return redirect(url_for('admin.create_lab_test'))
        
        try:
            test = LabTest(
                test_code=test_code,
                test_name=test_name,
                description=description,
                normal_range=normal_range,
                unit=unit,
                price=price,
                turnaround_time=turnaround_time
            )
            db.session.add(test)
            db.session.commit()
            log_audit('Created', 'LabTest', test.id, new_values={
                'test_code': test_code,
                'test_name': test_name,
                'price': price
            }, details='New lab test created by admin')
            flash('Lab test created successfully!', 'success')
            return redirect(url_for('admin.lab_tests_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating lab test: {str(e)}', 'danger')
    
    return render_template('admin/create_lab_test.html')


# ======================== Department Management ========================

@admin_bp.route('/departments')
@login_required
@admin_required
def departments_list():
    """View all departments"""
    page = request.args.get('page', 1, type=int)
    departments = Department.query.paginate(page=page, per_page=10)
    return render_template('admin/departments_list.html', departments=departments)


@admin_bp.route('/departments/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_department():
    """Create a new department"""
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        description = request.form.get('description')
        head = request.form.get('head_of_department')
        location = request.form.get('location')
        phone = request.form.get('phone')

        if Department.query.filter_by(code=code).first():
            flash('Department code already exists.', 'danger')
            return redirect(url_for('admin.create_department'))

        try:
            department = Department(
                name=name,
                code=code,
                description=description,
                head_of_department=head,
                location=location,
                phone=phone
            )
            db.session.add(department)
            db.session.commit()
            log_audit('Created', 'Department', department.id, new_values={
                'name': name,
                'code': code
            }, details='New department created by admin')
            flash('Department created successfully!', 'success')
            return redirect(url_for('admin.departments_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating department: {str(e)}', 'danger')

    return render_template('admin/create_department.html')


# ======================== Insurance Management ========================

@admin_bp.route('/insurances')
@login_required
@admin_required
def insurances_list():
    """View all insurance/HMO partners"""
    page = request.args.get('page', 1, type=int)
    insurances = Insurance.query.paginate(page=page, per_page=10)
    return render_template('admin/insurances_list.html', insurances=insurances)


@admin_bp.route('/insurances/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_insurance():
    """Create a new insurance/HMO record"""
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        insurance_type = request.form.get('insurance_type')
        contact_person = request.form.get('contact_person')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        coverage_percentage = float(request.form.get('coverage_percentage', 80))

        if Insurance.query.filter_by(code=code).first():
            flash('Insurance code already exists.', 'danger')
            return redirect(url_for('admin.create_insurance'))

        try:
            insurance = Insurance(
                name=name,
                code=code,
                insurance_type=insurance_type,
                contact_person=contact_person,
                phone=phone,
                email=email,
                address=address,
                coverage_percentage=coverage_percentage
            )
            db.session.add(insurance)
            db.session.commit()
            log_audit('Created', 'Insurance', insurance.id, new_values={
                'name': name,
                'code': code,
                'coverage_percentage': coverage_percentage
            }, details='New insurance partner created by admin')
            flash('Insurance partner created successfully!', 'success')
            return redirect(url_for('admin.insurances_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating insurance partner: {str(e)}', 'danger')

    return render_template('admin/create_insurance.html')


# ======================== Audit Log Viewer ========================

@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    """View audit log entries"""
    page = request.args.get('page', 1, type=int)
    entity_type = request.args.get('entity_type', '')
    user_id = request.args.get('user_id', type=int)

    query = AuditLog.query
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    if user_id:
        query = query.filter_by(user_id=user_id)

    logs = query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=15)
    return render_template('admin/audit_logs.html', logs=logs, entity_type=entity_type, user_id=user_id)


# ======================== System Reports ========================

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """System reports"""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # Financial reports
    total_revenue = db.session.query(func.sum(BillingRecord.total_amount)).filter(
        BillingRecord.payment_status == 'paid'
    ).scalar() or 0
    
    pending_amount = db.session.query(func.sum(BillingRecord.total_amount)).filter(
        BillingRecord.payment_status == 'pending'
    ).scalar() or 0
    
    # Appointment statistics
    month_start = datetime.utcnow().replace(day=1)
    month_appointments = Appointment.query.filter(
        Appointment.appointment_date >= month_start
    ).count()
    
    return render_template('admin/reports.html',
                         total_revenue=total_revenue,
                         pending_amount=pending_amount,
                         month_appointments=month_appointments)


# ======================== Chat System ========================

@admin_bp.route('/messages')
@login_required
@admin_required
def messages():
    """View all messages"""
    admin = current_user
    # Get conversations
    sent_messages = Message.query.filter_by(sender_id=admin.id).all()
    received_messages = Message.query.filter_by(recipient_id=admin.id).all()
    
    # Get unread count
    unread_count = Message.query.filter_by(recipient_id=admin.id, is_read=False).count()
    
    return render_template('admin/messages.html',
                         sent_messages=sent_messages,
                         received_messages=received_messages,
                         unread_count=unread_count)


@admin_bp.route('/messages/conversation/<int:user_id>')
@login_required
@admin_required
def conversation(user_id):
    """View conversation with a specific user"""
    other_user = User.query.get_or_404(user_id)
    admin = current_user
    
    # Get all messages between admin and other user
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == admin.id, Message.recipient_id == user_id),
            db.and_(Message.sender_id == user_id, Message.recipient_id == admin.id)
        )
    ).order_by(Message.created_at.asc()).all()
    
    # Mark received messages as read
    for msg in messages:
        if msg.recipient_id == admin.id and not msg.is_read:
            msg.is_read = True
    db.session.commit()
    
    # Get list of doctors
    doctors = User.query.filter_by(role=UserRole.DOCTOR).all()
    
    return render_template('admin/conversation.html',
                         messages=messages,
                         other_user=other_user,
                         doctors=doctors)


@admin_bp.route('/messages/send/<int:recipient_id>', methods=['POST'])
@login_required
@admin_required
def send_message(recipient_id):
    """Send a message"""
    admin = current_user
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Message cannot be empty.', 'danger')
        return redirect(url_for('admin.conversation', user_id=recipient_id))
    
    try:
        message = Message(
            sender_id=admin.id,
            recipient_id=recipient_id,
            content=content
        )
        db.session.add(message)
        db.session.commit()
        log_audit('Created', 'Message', message.id, new_values={'recipient_id': recipient_id}, details='Admin sent a message')
        flash('Message sent successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error sending message: {str(e)}', 'danger')
    
    return redirect(url_for('admin.conversation', user_id=recipient_id))


@admin_bp.route('/api/messages/<int:user_id>')
@login_required
@admin_required
def get_messages_api(user_id):
    """API endpoint to get messages for AJAX"""
    admin = current_user
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == admin.id, Message.recipient_id == user_id),
            db.and_(Message.sender_id == user_id, Message.recipient_id == admin.id)
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
