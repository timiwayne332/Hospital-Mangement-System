"""
Prescription Blueprint - Handles prescription management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import (
    db, Prescription, PrescriptionItem, Patient, Doctor, Medicine, 
    MedicalRecord, UserRole
)
from app.utils.decorators import role_required, doctor_required, staff_required
from app.utils.pdf_generator import generate_prescription_pdf
from app.utils.audit_logger import log_prescription_create, log_prescription_dispensed
from datetime import datetime, timedelta

prescription_bp = Blueprint('prescription', __name__, url_prefix='/prescription', template_folder='../templates')


# ======================== Doctor Views ========================

@prescription_bp.route('/create/<int:patient_id>', methods=['GET', 'POST'])
@login_required
@doctor_required
def create_prescription(patient_id):
    """Create a new prescription for a patient"""
    patient = Patient.query.get_or_404(patient_id)
    doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            prescribed_duration = request.form.get('prescribed_duration')
            instructions = request.form.get('instructions')
            medical_record_id = request.form.get('medical_record_id')
            
            # Create prescription
            prescription = Prescription(
                patient_id=patient_id,
                doctor_id=doctor.id,
                medical_record_id=int(medical_record_id) if medical_record_id else None,
                prescribed_duration=prescribed_duration,
                instructions=instructions,
                status='active',
                expiry_date=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(prescription)
            db.session.flush()  # Get the ID without committing
            
            # Add prescription items
            medicine_ids = request.form.getlist('medicine_id')
            quantities = request.form.getlist('quantity')
            dosages = request.form.getlist('dosage')
            frequencies = request.form.getlist('frequency')
            routes = request.form.getlist('route')
            units = request.form.getlist('unit')
            
            for i, medicine_id in enumerate(medicine_ids):
                if medicine_id:
                    item = PrescriptionItem(
                        prescription_id=prescription.id,
                        medicine_id=int(medicine_id),
                        quantity=int(quantities[i]) if quantities[i] else 1,
                        unit=units[i] if units[i] else 'tablet',
                        dosage=dosages[i],
                        frequency=frequencies[i],
                        route=routes[i] if routes[i] else 'oral'
                    )
                    db.session.add(item)
            
            db.session.commit()
            
            # Log audit
            log_prescription_create(
                prescription.id,
                new_values={'patient_id': patient_id, 'doctor_id': doctor.id},
                details=f"Prescription created for {patient.user.get_full_name()}"
            )
            
            flash('Prescription created successfully.', 'success')
            return redirect(url_for('doctor.patient_detail', patient_id=patient_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating prescription: {str(e)}', 'danger')
    
    medicines = Medicine.query.filter_by(is_available=True).all()
    medical_records = MedicalRecord.query.filter_by(
        patient_id=patient_id
    ).order_by(MedicalRecord.visit_date.desc()).limit(5).all()
    
    return render_template('prescription/create.html',
                         patient=patient,
                         medicines=medicines,
                         medical_records=medical_records)


@prescription_bp.route('/<int:prescription_id>/edit', methods=['GET', 'POST'])
@login_required
@doctor_required
def edit_prescription(prescription_id):
    """Edit a prescription"""
    prescription = Prescription.query.get_or_404(prescription_id)
    doctor = Doctor.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Only the prescribing doctor can edit
    if prescription.doctor_id != doctor.id:
        flash('You can only edit your own prescriptions.', 'danger')
        return redirect(url_for('prescription.view_prescription', prescription_id=prescription_id))
    
    if request.method == 'POST':
        try:
            prescription.prescribed_duration = request.form.get('prescribed_duration')
            prescription.instructions = request.form.get('instructions')
            
            # Update prescription items
            db.session.query(PrescriptionItem).filter_by(
                prescription_id=prescription_id
            ).delete()
            
            medicine_ids = request.form.getlist('medicine_id')
            quantities = request.form.getlist('quantity')
            dosages = request.form.getlist('dosage')
            frequencies = request.form.getlist('frequency')
            routes = request.form.getlist('route')
            units = request.form.getlist('unit')
            
            for i, medicine_id in enumerate(medicine_ids):
                if medicine_id:
                    item = PrescriptionItem(
                        prescription_id=prescription.id,
                        medicine_id=int(medicine_id),
                        quantity=int(quantities[i]) if quantities[i] else 1,
                        unit=units[i] if units[i] else 'tablet',
                        dosage=dosages[i],
                        frequency=frequencies[i],
                        route=routes[i] if routes[i] else 'oral'
                    )
                    db.session.add(item)
            
            prescription.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash('Prescription updated successfully.', 'success')
            return redirect(url_for('prescription.view_prescription', prescription_id=prescription_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating prescription: {str(e)}', 'danger')
    
    medicines = Medicine.query.filter_by(is_available=True).all()
    return render_template('prescription/edit.html',
                         prescription=prescription,
                         medicines=medicines)


@prescription_bp.route('/<int:prescription_id>')
@login_required
@staff_required
def view_prescription(prescription_id):
    """View a prescription"""
    prescription = Prescription.query.get_or_404(prescription_id)
    
    # Access control: doctors can view own prescriptions, patients can view own
    if current_user.role == UserRole.DOCTOR:
        doctor = Doctor.query.filter_by(user_id=current_user.id).first()
        if doctor and prescription.doctor_id != doctor.id:
            flash('You can only view your own prescriptions.', 'danger')
            return redirect(url_for('main.dashboard'))
    elif current_user.role == UserRole.PATIENT:
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        if patient and prescription.patient_id != patient.id:
            flash('You can only view your own prescriptions.', 'danger')
            return redirect(url_for('main.dashboard'))
    
    return render_template('prescription/view.html', prescription=prescription)


@prescription_bp.route('/<int:prescription_id>/pdf')
@login_required
def download_prescription_pdf(prescription_id):
    """Download prescription as PDF"""
    prescription = Prescription.query.get_or_404(prescription_id)
    
    # Access control
    if current_user.role == UserRole.PATIENT:
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        if patient and prescription.patient_id != patient.id:
            flash('You can only download your own prescriptions.', 'danger')
            return redirect(url_for('main.dashboard'))
    elif current_user.role == UserRole.DOCTOR:
        doctor = Doctor.query.filter_by(user_id=current_user.id).first()
        if doctor and prescription.doctor_id != doctor.id:
            flash('You can only download your own prescriptions.', 'danger')
            return redirect(url_for('main.dashboard'))
    
    try:
        pdf_path = generate_prescription_pdf(prescription)
        return redirect(url_for('static', filename=f'../uploads/{pdf_path.split(chr(92))[-1]}'))
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        return redirect(url_for('prescription.view_prescription', prescription_id=prescription_id))


@prescription_bp.route('/<int:prescription_id>/mark-dispensed', methods=['POST'])
@login_required
@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST)
def mark_dispensed(prescription_id):
    """Mark prescription as dispensed"""
    prescription = Prescription.query.get_or_404(prescription_id)
    
    try:
        prescription.status = 'dispensed'
        
        # Mark all items as dispensed
        for item in prescription.prescription_items:
            item.is_dispensed = True
            item.dispensed_date = datetime.utcnow()
        
        db.session.commit()
        
        log_prescription_dispensed(prescription_id, details="Marked as dispensed")
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Prescription marked as dispensed'})
        else:
            flash('Prescription marked as dispensed.', 'success')
            return redirect(url_for('prescription.view_prescription', prescription_id=prescription_id))
    
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'message': str(e)}), 400
        else:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('prescription.view_prescription', prescription_id=prescription_id))


@prescription_bp.route('/patient/<int:patient_id>')
@login_required
@staff_required
def patient_prescriptions(patient_id):
    """View all prescriptions for a patient"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Access control
    if current_user.role == UserRole.PATIENT:
        patient_obj = Patient.query.filter_by(user_id=current_user.id).first()
        if patient_obj and patient.id != patient_obj.id:
            flash('You can only view your own prescriptions.', 'danger')
            return redirect(url_for('main.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    prescriptions = Prescription.query.filter_by(
        patient_id=patient_id
    ).order_by(Prescription.prescription_date.desc()).paginate(page=page, per_page=10)
    
    return render_template('prescription/patient_prescriptions.html',
                         patient=patient,
                         prescriptions=prescriptions)


@prescription_bp.route('/list')
@login_required
@staff_required
def list_prescriptions():
    """View all prescriptions (admin/doctor/receptionist)"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = Prescription.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if current_user.role == UserRole.DOCTOR:
        doctor = Doctor.query.filter_by(user_id=current_user.id).first()
        if doctor:
            query = query.filter_by(doctor_id=doctor.id)
    
    prescriptions = query.order_by(
        Prescription.prescription_date.desc()
    ).paginate(page=page, per_page=15)
    
    return render_template('prescription/list.html', prescriptions=prescriptions)
