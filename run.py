"""
Hospital Management System - Application Entry Point
"""
import os
from app import create_app, db
from app.models import (
    User, Patient, Doctor, Appointment, MedicalRecord, 
    Medicine, LabTest, BillingRecord, Department, Prescription,
    PrescriptionItem, DischargeSummary, Admission, Bed, AuditLog,
    Insurance, PatientInsurance, Permission, RolePermission
)

app = create_app(os.getenv('FLASK_ENV', 'development'))


@app.shell_context_processor
def make_shell_context():
    """Register models with Flask shell"""
    return {
        'db': db,
        'User': User,
        'Patient': Patient,
        'Doctor': Doctor,
        'Appointment': Appointment,
        'MedicalRecord': MedicalRecord,
        'Medicine': Medicine,
        'LabTest': LabTest,
        'BillingRecord': BillingRecord,
        'Department': Department,
        'Prescription': Prescription,
        'PrescriptionItem': PrescriptionItem,
        'DischargeSummary': DischargeSummary,
        'Admission': Admission,
        'Bed': Bed,
        'AuditLog': AuditLog,
        'Insurance': Insurance,
        'PatientInsurance': PatientInsurance,
        'Permission': Permission,
        'RolePermission': RolePermission,
    }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
