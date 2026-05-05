"""
Seed Data Script - Populate database with sample data
Run: python seed_database.py
"""
from app import create_app, db
from app.models import (
    User, Patient, Doctor, LabStaff, Appointment, MedicalRecord, 
    Medicine, LabTest, Bed, BillingRecord, UserRole
)
from datetime import datetime, timedelta
import random


def seed_database():
    """Populate database with seed data"""
    app = create_app('development')
    
    with app.app_context():
        # Drop all tables and recreate
        print("Creating database tables...")
        db.drop_all()
        db.create_all()
        
        # Create Admin User
        print("Creating admin user...")
        admin = User(
            username='admin',
            email='admin@hospital.com',
            first_name='Admin',
            last_name='User',
            phone='07039932390',
            role=UserRole.ADMIN
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        # Create Doctors
        print("Creating doctors...")
        doctors_data = [
            {'name': ('Dr. John', 'Smith'), 'spec': 'Cardiology', 'license': 'DLN001'},
            {'name': ('Dr. Sarah', 'Johnson'), 'spec': 'Pediatrics', 'license': 'DLN002'},
            {'name': ('Dr. Mike', 'williams'), 'spec': 'Orthopedics', 'license': 'DLN003'},
            {'name': ('Dr. Emma', 'Brown'), 'spec': 'Neurology', 'license': 'DLN004'},
            {'name': ('Dr. James', 'Davis'), 'spec': 'General Surgery', 'license': 'DLN005'},
            {'name': ('Dr Jones', 'Dave'), 'spec': 'General Surgery', 'license': 'DL3932'},
        ]
        
        doctors = []
        for i, doctor_data in enumerate(doctors_data):
            user = User(
                username=f'doctor{i+1}',
                email=f'doctor{i+1}@hospital.com',
                first_name=doctor_data['name'][0],
                last_name=doctor_data['name'][1],
                phone=f'111111{i:04d}',
                role=UserRole.DOCTOR
            )
            user.set_password('doctor123')
            db.session.add(user)
            db.session.commit()
            
            doctor = Doctor(
                user_id=user.id,
                doctor_id=f'DOC{user.id:05d}',
                specialization=doctor_data['spec'],
                license_number=doctor_data['license'],
                qualification='MBBS, MD',
                consultation_fee=500.0
            )
            db.session.add(doctor)
            doctors.append(doctor)
        
        db.session.commit()
        
        # Create Receptionist
        print("Creating receptionist...")
        receptionist = User(
            username='receptionist',
            email='receptionist@hospital.com',
            first_name='Lisa',
            last_name='Anderson',
            phone='2222222222',
            role=UserRole.RECEPTIONIST
        )
        receptionist.set_password('receptionist123')
        db.session.add(receptionist)
        db.session.commit()

        # Create Lab Staff
        print("Creating lab staff...")
        lab_staff_user = User(
            username='labstaff',
            email='labstaff@hospital.com',
            first_name='Lab',
            last_name='Staff',
            phone='3333333333',
            role=UserRole.LAB_STAFF
        )
        lab_staff_user.set_password('labstaff123')
        db.session.add(lab_staff_user)
        db.session.commit()

        lab_staff = LabStaff(
            user_id=lab_staff_user.id,
            lab_staff_id=f'LAB{lab_staff_user.id:05d}',
            department='Laboratory',
            certification='Certified Medical Laboratory Technician'
        )
        db.session.add(lab_staff)
        db.session.commit()
        
        # Create Patients
        print("Creating patients...")
        patient_names = [
            ('John', 'Doe'), ('Jane', 'Smith'), ('Robert', 'Johnson'),
            ('Mary', 'Williams'), ('Michael', 'Brown'), ('Patricia', 'Jones'),
            ('David', 'Garcia'), ('Linda', 'Miller'), ('James', 'Davis'),
            ('Barbara', 'Rodriguez')
        ]
        
        patients = []
        for i, (first, last) in enumerate(patient_names):
            user = User(
                username=f'patient{i+1}',
                email=f'patient{i+1}@email.com',
                first_name=first,
                last_name=last,
                phone=f'555555{i:04d}',
                role=UserRole.PATIENT
            )
            user.set_password('patient123')
            db.session.add(user)
            db.session.commit()
            
            patient = Patient(
                user_id=user.id,
                patient_id=f'PAT{user.id:05d}',
                date_of_birth=datetime(1990, 1, 1) - timedelta(days=random.randint(1000, 12000)),
                gender=random.choice(['Male', 'Female']),
                blood_group=random.choice(['A+', 'B+', 'O+', 'AB+']),
                address=f'{random.randint(1, 999)} Main Street',
                emergency_contact='999999999',
                insurance_provider='Health Insurance Co.',
                insurance_number=f'HI{i:06d}'
            )
            db.session.add(patient)
            patients.append(patient)
        
        db.session.commit()
        
        # Create Appointments
        print("Creating appointments...")
        for i in range(20):
            appointment = Appointment(
                patient_id=random.choice(patients).id,
                doctor_id=random.choice(doctors).id,
                appointment_date=datetime.utcnow() + timedelta(days=random.randint(1, 30)),
                reason=random.choice(['Regular Checkup', 'Follow-up', 'Emergency', 'Consultation']),
                status=random.choice(['scheduled', 'completed'])
            )
            db.session.add(appointment)
        
        db.session.commit()
        
        # Create Medical Records
        print("Creating medical records...")
        for i in range(10):
            record = MedicalRecord(
                patient_id=random.choice(patients).id,
                doctor_id=random.choice(doctors).id,
                diagnosis='Sample Diagnosis',
                treatment='Sample Treatment',
                prescription='Sample Prescription',
                notes='Sample Notes'
            )
            db.session.add(record)
        
        db.session.commit()
        
        # Create Medicines
        print("Creating medicines...")
        medicines_data = [
            {'name': 'Aspirin', 'generic': 'Acetylsalicylic acid', 'manufacturer': 'Pharma Inc', 'price': 5.0},
            {'name': 'Amoxicillin', 'generic': 'Amoxicillin trihydrate', 'manufacturer': 'Bio Labs', 'price': 15.0},
            {'name': 'Paracetamol', 'generic': 'Paracetamol', 'manufacturer': 'Pharma Inc', 'price': 3.0},
            {'name': 'Ibuprofen', 'generic': 'Ibuprofen', 'manufacturer': 'Med Corp', 'price': 8.0},
            {'name': 'Lisinopril', 'generic': 'Lisinopril', 'manufacturer': 'Card Pharma', 'price': 25.0},
        ]
        
        for i, med_data in enumerate(medicines_data):
            medicine = Medicine(
                medicine_code=f'MED{i:04d}',
                name=med_data['name'],
                generic_name=med_data['generic'],
                manufacturer=med_data['manufacturer'],
                quantity=random.randint(50, 500),
                unit='tablet',
                price_per_unit=med_data['price'],
                expiry_date=datetime.utcnow() + timedelta(days=365)
            )
            db.session.add(medicine)
        
        db.session.commit()
        
        # Create Lab Tests
        print("Creating lab tests...")
        tests_data = [
            {'code': 'BT001', 'name': 'Blood Count', 'range': '4.5-11.0', 'unit': 'K/uL', 'price': 50.0},
            {'code': 'BT002', 'name': 'Blood Sugar', 'range': '70-100', 'unit': 'mg/dL', 'price': 30.0},
            {'code': 'BT003', 'name': 'Cholesterol', 'range': '<200', 'unit': 'mg/dL', 'price': 40.0},
            {'code': 'BT004', 'name': 'Thyroid Profile', 'range': 'Normal', 'unit': 'mIU/L', 'price': 60.0},
            {'code': 'BT005', 'name': 'Liver Function Test', 'range': 'Normal', 'unit': 'U/L', 'price': 75.0},
        ]
        
        for test_data in tests_data:
            test = LabTest(
                test_code=test_data['code'],
                test_name=test_data['name'],
                normal_range=test_data['range'],
                unit=test_data['unit'],
                price=test_data['price'],
                turnaround_time='2-3 days'
            )
            db.session.add(test)
        
        db.session.commit()
        
        # Create Beds
        print("Creating beds...")
        wards = ['ICU', 'General Ward', 'Pediatric Ward', 'Critical Care']
        bed_types = ['Normal', 'ICU', 'Isolation']
        
        for i in range(50):
            bed = Bed(
                bed_number=f'BED{i+1:03d}',
                room_number=f'Room{(i // 5) + 1}',
                ward=random.choice(wards),
                bed_type=random.choice(bed_types),
                is_available=random.choice([True, True, False])  # Higher chance of available
            )
            db.session.add(bed)
        
        db.session.commit()
        
        # Create Billing Records
        print("Creating billing records...")
        for i in range(15):
            amount = random.randint(100, 5000)
            tax = amount * 0.1
            billing = BillingRecord(
                patient_id=random.choice(patients).id,
                bill_number=f'BILL{datetime.utcnow().strftime("%Y%m%d")}{i:04d}',
                description='Medical Services',
                amount=amount,
                tax=tax,
                total_amount=amount + tax,
                payment_status=random.choice(['paid', 'pending', 'partial']),
                payment_method=random.choice(['cash', 'card', 'insurance'])
            )
            db.session.add(billing)
        
        db.session.commit()
        
        print("\n✓ Database seeded successfully!")
        print("\n📋 Test Accounts:")
        print("   Admin: admin / admin123")
        print("   Doctor: doctor1 / doctor123")
        print("   Receptionist: receptionist / receptionist123")
        print("   Lab Staff: labstaff / labstaff123")
        print("   Patient: patient1 / patient123")
        print("\nAll tables populated with sample data.")


if __name__ == '__main__':
    seed_database()
