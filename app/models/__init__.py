"""
Database models for Hospital Management System
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

db = SQLAlchemy()


class UserRole(enum.Enum):
    """User roles in the system"""
    ADMIN = 'admin'
    DOCTOR = 'doctor'
    RECEPTIONIST = 'receptionist'
    LAB_STAFF = 'lab_staff'
    PATIENT = 'patient'


class AppointmentStatus(enum.Enum):
    """Appointment status workflow states"""
    SCHEDULED = 'scheduled'
    CONFIRMED = 'confirmed'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    NO_SHOW = 'no_show'
    RESCHEDULED = 'rescheduled'


class User(UserMixin, db.Model):
    """User model for all users in the system"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    phone = db.Column(db.String(20))
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.PATIENT)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', uselist=False, back_populates='user', foreign_keys='Patient.user_id')
    doctor = db.relationship('Doctor', uselist=False, back_populates='user', foreign_keys='Doctor.user_id')
    lab_staff = db.relationship('LabStaff', uselist=False, back_populates='user', foreign_keys='LabStaff.user_id')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def __repr__(self):
        return f'<User {self.username}>'


class Patient(db.Model):
    """Patient model"""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_id = db.Column(db.String(20), unique=True, nullable=False)  # Medical record number
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))  # Male, Female, Other
    blood_group = db.Column(db.String(5))
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(120))
    emergency_contact_phone = db.Column(db.String(20))
    insurance_provider = db.Column(db.String(120))
    insurance_number = db.Column(db.String(50))
    allergies = db.Column(db.Text)
    medical_history = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='patient', foreign_keys=[user_id])
    appointments = db.relationship('Appointment', back_populates='patient', cascade='all, delete-orphan')
    medical_records = db.relationship('MedicalRecord', back_populates='patient', cascade='all, delete-orphan')
    admissions = db.relationship('Admission', back_populates='patient', cascade='all, delete-orphan')
    lab_results = db.relationship('LabResult', back_populates='patient', cascade='all, delete-orphan')
    billing_records = db.relationship('BillingRecord', back_populates='patient', cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', back_populates='patient', foreign_keys='Prescription.patient_id', cascade='all, delete-orphan')
    discharge_summaries = db.relationship('DischargeSummary', back_populates='patient', cascade='all, delete-orphan')
    patient_insurances = db.relationship('PatientInsurance', back_populates='patient', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Patient {self.patient_id}>'


class Doctor(db.Model):
    """Doctor model"""
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    doctor_id = db.Column(db.String(20), unique=True, nullable=False)
    specialization = db.Column(db.String(120), nullable=False)
    license_number = db.Column(db.String(50), unique=True)
    qualification = db.Column(db.Text)
    bio = db.Column(db.Text)
    consultation_fee = db.Column(db.Float, default=500.0)
    is_available = db.Column(db.Boolean, default=True)
    working_hours = db.Column(db.String(100))  # e.g., "09:00-17:00"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='doctor', foreign_keys=[user_id])
    department = db.relationship('Department', back_populates='doctors', foreign_keys=[department_id])
    appointments = db.relationship('Appointment', back_populates='doctor', cascade='all, delete-orphan')
    medical_records = db.relationship('MedicalRecord', back_populates='doctor', cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', back_populates='doctor', foreign_keys='Prescription.doctor_id', cascade='all, delete-orphan')
    discharge_summaries = db.relationship('DischargeSummary', back_populates='doctor', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Doctor {self.doctor_id}>'


class LabStaff(db.Model):
    """Lab Staff model"""
    __tablename__ = 'lab_staff'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lab_staff_id = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(120))
    certification = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='lab_staff', foreign_keys=[user_id])

    def __repr__(self):
        return f'<LabStaff {self.lab_staff_id}>'


class Appointment(db.Model):
    """Appointment model"""
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default=AppointmentStatus.SCHEDULED.value, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='appointments')
    doctor = db.relationship('Doctor', back_populates='appointments')
    
    def __repr__(self):
        return f'<Appointment {self.id} - {self.appointment_date}>'


class MedicalRecord(db.Model):
    """Medical Record model"""
    __tablename__ = 'medical_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    treatment = db.Column(db.Text)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)
    visit_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    prescriptions = db.relationship('Prescription', back_populates='medical_record', foreign_keys='Prescription.medical_record_id', cascade='all, delete-orphan')
    
    # Relationships
    patient = db.relationship('Patient', back_populates='medical_records')
    doctor = db.relationship('Doctor', back_populates='medical_records')
    
    def __repr__(self):
        return f'<MedicalRecord {self.id}>'


class Admission(db.Model):
    """Admission model for patient admissions"""
    __tablename__ = 'admissions'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    bed_id = db.Column(db.Integer, db.ForeignKey('beds.id'))
    admission_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    discharge_date = db.Column(db.DateTime)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='admitted')  # admitted, discharged
    notes = db.Column(db.Text)
    discharge_summary = db.relationship('DischargeSummary', back_populates='admission', uselist=False, cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='admissions')
    bed = db.relationship('Bed', back_populates='admissions')
    
    def __repr__(self):
        return f'<Admission {self.id}>'


class Bed(db.Model):
    """Bed model for bed management"""
    __tablename__ = 'beds'
    
    id = db.Column(db.Integer, primary_key=True)
    bed_number = db.Column(db.String(20), unique=True, nullable=False)
    room_number = db.Column(db.String(20))
    ward = db.Column(db.String(50), nullable=False)  # ICU, General, Pediatric, etc.
    bed_type = db.Column(db.String(50))  # Normal, ICU, Isolation
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    admissions = db.relationship('Admission', back_populates='bed')
    
    def __repr__(self):
        return f'<Bed {self.bed_number}>'


class BillingRecord(db.Model):
    """Billing Record model"""
    __tablename__ = 'billing_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    bill_number = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, partial
    payment_date = db.Column(db.DateTime)
    payment_method = db.Column(db.String(50))  # cash, card, cheque, insurance
    bill_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='billing_records')
    
    def __repr__(self):
        return f'<BillingRecord {self.bill_number}>'


class Medicine(db.Model):
    """Medicine/Drug inventory model"""
    __tablename__ = 'medicines'
    
    id = db.Column(db.Integer, primary_key=True)
    medicine_code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    generic_name = db.Column(db.String(120))
    manufacturer = db.Column(db.String(120))
    quantity = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(20))  # tablet, ml, capsule, etc.
    price_per_unit = db.Column(db.Float, nullable=False)
    expiry_date = db.Column(db.Date)
    batch_number = db.Column(db.String(50))
    side_effects = db.Column(db.Text)
    usage = db.Column(db.Text)
    min_stock_level = db.Column(db.Integer, default=10)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    medicine_logs = db.relationship('MedicineLog', back_populates='medicine', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Medicine {self.name}>'


class MedicineLog(db.Model):
    """Medicine dispensing log"""
    __tablename__ = 'medicine_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    quantity_dispensed = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(20), default='dispensed')  # dispensed, restocked
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    medicine = db.relationship('Medicine', back_populates='medicine_logs')
    
    def __repr__(self):
        return f'<MedicineLog {self.id}>'


class LabTest(db.Model):
    """Lab Test model"""
    __tablename__ = 'lab_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    test_code = db.Column(db.String(30), unique=True, nullable=False)
    test_name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    normal_range = db.Column(db.String(100))
    unit = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False)
    turnaround_time = db.Column(db.String(50))  # e.g., "2-3 days"
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    lab_results = db.relationship('LabResult', back_populates='lab_test', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<LabTest {self.test_name}>'


class LabResult(db.Model):
    """Lab Result model"""
    __tablename__ = 'lab_results'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    lab_test_id = db.Column(db.Integer, db.ForeignKey('lab_tests.id'), nullable=False)
    result_value = db.Column(db.String(100))
    normal_range = db.Column(db.String(100))
    status = db.Column(db.String(20))  # normal, abnormal
    notes = db.Column(db.Text)
    test_date = db.Column(db.DateTime, default=datetime.utcnow)
    result_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='lab_results')
    lab_test = db.relationship('LabTest', back_populates='lab_results')
    
    def __repr__(self):
        return f'<LabResult {self.id}>'


# ======================== NEW MODELS FOR UPGRADES ========================

class Department(db.Model):
    """Department model for hospital departments"""
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    head_of_department = db.Column(db.String(120))  # Doctor name
    location = db.Column(db.String(100))  # Floor/Building
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    doctors = db.relationship('Doctor', back_populates='department')
    
    def __repr__(self):
        return f'<Department {self.name}>'


class Prescription(db.Model):
    """Prescription model - separate from medical records"""
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'))
    prescription_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    prescribed_duration = db.Column(db.String(100))  # e.g., "10 days", "2 weeks"
    instructions = db.Column(db.Text)  # Special instructions (take with food, etc.)
    status = db.Column(db.String(20), default='active')  # active, dispensed, expired, cancelled
    expiry_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='prescriptions', foreign_keys=[patient_id])
    doctor = db.relationship('Doctor', back_populates='prescriptions', foreign_keys=[doctor_id])
    medical_record = db.relationship('MedicalRecord', back_populates='prescriptions', foreign_keys=[medical_record_id])
    prescription_items = db.relationship('PrescriptionItem', back_populates='prescription', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Prescription {self.id}>'


class PrescriptionItem(db.Model):
    """Individual medicine items in a prescription"""
    __tablename__ = 'prescription_items'
    
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(20))  # tablet, ml, capsule, etc.
    dosage = db.Column(db.String(100))  # e.g., "500mg", "10ml"
    frequency = db.Column(db.String(100), nullable=False)  # e.g., "2 times daily", "3 times daily after meals"
    route = db.Column(db.String(50))  # oral, injection, topical, etc.
    is_dispensed = db.Column(db.Boolean, default=False)
    dispensed_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    prescription = db.relationship('Prescription', back_populates='prescription_items')
    medicine = db.relationship('Medicine')
    
    def __repr__(self):
        return f'<PrescriptionItem {self.id}>'


class DischargeSummary(db.Model):
    """Discharge Summary for admitted patients"""
    __tablename__ = 'discharge_summaries'
    
    id = db.Column(db.Integer, primary_key=True)
    admission_id = db.Column(db.Integer, db.ForeignKey('admissions.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    discharge_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    chief_complaint = db.Column(db.Text, nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    treatment_given = db.Column(db.Text)
    procedures_performed = db.Column(db.Text)
    final_status = db.Column(db.String(50))  # improved, stable, critical, etc.
    discharge_advice = db.Column(db.Text)
    follow_up_instructions = db.Column(db.Text)
    discharged_by = db.Column(db.String(120))  # Doctor name
    medications_on_discharge = db.Column(db.Text)
    pdf_path = db.Column(db.String(255))  # Path to generated PDF
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    admission = db.relationship('Admission', back_populates='discharge_summary')
    patient = db.relationship('Patient', back_populates='discharge_summaries')
    doctor = db.relationship('Doctor', back_populates='discharge_summaries')
    
    def __repr__(self):
        return f'<DischargeSummary {self.id}>'


class AuditLog(db.Model):
    """Audit log for tracking system changes"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(255), nullable=False)  # Created, Updated, Deleted, Viewed
    entity_type = db.Column(db.String(100), nullable=False)  # User, Patient, Appointment, etc.
    entity_id = db.Column(db.Integer)
    old_values = db.Column(db.JSON)  # For updates - old data
    new_values = db.Column(db.JSON)  # For updates/creates - new data
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    details = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<AuditLog {self.action} on {self.entity_type}>'


class Insurance(db.Model):
    """Insurance/HMO management"""
    __tablename__ = 'insurances'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    code = db.Column(db.String(30), unique=True, nullable=False)
    insurance_type = db.Column(db.String(50))  # HMO, PPO, Group, Individual
    contact_person = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    coverage_percentage = db.Column(db.Float, default=80.0)  # Percentage of bill covered
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient_insurances = db.relationship('PatientInsurance', back_populates='insurance', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Insurance {self.name}>'


class PatientInsurance(db.Model):
    """Patient-Insurance relationship with policy details"""
    __tablename__ = 'patient_insurances'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    insurance_id = db.Column(db.Integer, db.ForeignKey('insurances.id'), nullable=False)
    policy_number = db.Column(db.String(100), unique=True, nullable=False)
    member_id = db.Column(db.String(100))
    start_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='patient_insurances')
    insurance = db.relationship('Insurance', back_populates='patient_insurances')
    
    def __repr__(self):
        return f'<PatientInsurance {self.policy_number}>'


class Permission(db.Model):
    """Granular permissions for fine-grained access control"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    resource = db.Column(db.String(100), nullable=False)  # patient, appointment, prescription, etc.
    action = db.Column(db.String(50), nullable=False)  # create, read, update, delete, export
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    role_permissions = db.relationship('RolePermission', back_populates='permission', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Permission {self.name}>'


class RolePermission(db.Model):
    """Mapping between roles and permissions"""
    __tablename__ = 'role_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.Enum(UserRole), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    permission = db.relationship('Permission', back_populates='role_permissions')
    
    __table_args__ = (db.UniqueConstraint('role', 'permission_id', name='_role_permission_uc'),)
    
    def __repr__(self):
        return f'<RolePermission {self.role.value}>'


# ======================== CHAT SYSTEM ========================

class Message(db.Model):
    """Chat messages between users (doctors and admins)"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')
    
    def __repr__(self):
        return f'<Message {self.id} from {self.sender.username} to {self.recipient.username}>'


class PaymentNotification(db.Model):
    """Payment notifications for receptionists"""
    __tablename__ = 'payment_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bill_id = db.Column(db.Integer, db.ForeignKey('billing_records.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='payment_notifications')
    bill = db.relationship('BillingRecord', foreign_keys=[bill_id])
    patient = db.relationship('Patient', foreign_keys=[patient_id])
    
    def __repr__(self):
        return f'<PaymentNotification {self.id} - {self.amount_paid}>'
