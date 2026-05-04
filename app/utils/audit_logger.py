"""
Audit logging utility for tracking system changes
Usage: log_audit(action, entity_type, entity_id, old_values, new_values, details)
"""
from flask import request
from flask_login import current_user
from app.models import db, AuditLog
from datetime import datetime
import json


def log_audit(action, entity_type, entity_id=None, old_values=None, new_values=None, details=None):
    """
    Log an audit trail entry
    
    Args:
        action (str): Action performed (e.g., 'Created', 'Updated', 'Deleted', 'Viewed', 'Exported')
        entity_type (str): Type of entity (e.g., 'Patient', 'Appointment', 'User')
        entity_id (int, optional): ID of the entity
        old_values (dict, optional): Old values for updates
        new_values (dict, optional): New values for creates/updates
        details (str, optional): Additional details about the action
    
    Returns:
        AuditLog: The created audit log entry
    """
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        ip_address = request.remote_addr if request else None
        
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            timestamp=datetime.utcnow(),
            details=details
        )
        
        db.session.add(audit_entry)
        db.session.commit()
        
        return audit_entry
    except Exception as e:
        # Log silently to avoid breaking application flow
        print(f"Audit logging error: {str(e)}")
        return None


def log_patient_view(patient_id, details=None):
    """Log when a patient record is viewed"""
    return log_audit('Viewed', 'Patient', patient_id, details=details)


def log_patient_create(patient_id, new_values=None, details=None):
    """Log when a patient is created"""
    return log_audit('Created', 'Patient', patient_id, new_values=new_values, details=details)


def log_patient_update(patient_id, old_values=None, new_values=None, details=None):
    """Log when a patient is updated"""
    return log_audit('Updated', 'Patient', patient_id, old_values=old_values, new_values=new_values, details=details)


def log_appointment_create(appointment_id, new_values=None, details=None):
    """Log when an appointment is created"""
    return log_audit('Created', 'Appointment', appointment_id, new_values=new_values, details=details)


def log_appointment_update(appointment_id, old_values=None, new_values=None, details=None):
    """Log when an appointment is updated"""
    return log_audit('Updated', 'Appointment', appointment_id, old_values=old_values, new_values=new_values, details=details)


def log_prescription_create(prescription_id, new_values=None, details=None):
    """Log when a prescription is created"""
    return log_audit('Created', 'Prescription', prescription_id, new_values=new_values, details=details)


def log_prescription_dispensed(prescription_id, details=None):
    """Log when a prescription is dispensed"""
    return log_audit('Dispensed', 'Prescription', prescription_id, details=details)


def log_discharge_summary_create(discharge_summary_id, new_values=None, details=None):
    """Log when a discharge summary is created"""
    return log_audit('Created', 'DischargeSummary', discharge_summary_id, new_values=new_values, details=details)


def get_audit_logs(entity_type=None, entity_id=None, user_id=None, limit=50):
    """
    Retrieve audit logs with optional filters
    
    Args:
        entity_type (str, optional): Filter by entity type
        entity_id (int, optional): Filter by entity ID
        user_id (int, optional): Filter by user ID
        limit (int): Limit number of results
    
    Returns:
        list: List of AuditLog entries
    """
    query = AuditLog.query
    
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    if entity_id:
        query = query.filter_by(entity_id=entity_id)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
