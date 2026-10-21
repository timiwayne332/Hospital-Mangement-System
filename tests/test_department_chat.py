import unittest
from datetime import date, datetime, timedelta

from app import create_app
from app.models import db, User, UserRole, Patient, Doctor, Appointment, Message


class DepartmentChatSystemTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()

            admin = User(
                username='admin_user',
                email='admin@example.com',
                first_name='Admin',
                last_name='User',
                role=UserRole.ADMIN,
            )
            admin.set_password('secret123')

            doctor = User(
                username='doctor_user',
                email='doctor@example.com',
                first_name='Doctor',
                last_name='User',
                role=UserRole.DOCTOR,
            )
            doctor.set_password('secret123')

            lab = User(
                username='lab_user',
                email='lab@example.com',
                first_name='Lab',
                last_name='User',
                role=UserRole.LAB_STAFF,
            )
            lab.set_password('secret123')

            db.session.add_all([admin, doctor, lab])
            db.session.commit()

            patient = Patient(
                user_id=doctor.id,
                patient_id='PAT00001',
                date_of_birth=date(1990, 1, 15),
                gender='Male',
                blood_group='O+',
            )

            doctor_profile = Doctor(
                user_id=doctor.id,
                doctor_id='DOC00001',
                specialization='General Medicine',
                license_number='LIC-00001',
                qualification='MBBS',
                consultation_fee=500.0,
                is_available=True,
            )

            db.session.add_all([patient, doctor_profile])
            db.session.commit()

            appointment_completed = Appointment(
                patient_id=patient.id,
                doctor_id=doctor_profile.id,
                appointment_date=datetime.utcnow() + timedelta(days=1),
                reason='Follow-up consultation',
                status='completed',
                notes='Patient recovered well',
                created_at=datetime.utcnow(),
            )
            appointment_scheduled = Appointment(
                patient_id=patient.id,
                doctor_id=doctor_profile.id,
                appointment_date=datetime.utcnow() + timedelta(days=3),
                reason='Routine checkup',
                status='scheduled',
                notes='Routine evaluation',
                created_at=datetime.utcnow(),
            )

            db.session.add_all([appointment_completed, appointment_scheduled])
            db.session.commit()

            self.admin_id = admin.id
            self.doctor_id = doctor.id
            self.lab_id = lab.id

    def test_lab_staff_can_message_other_departments(self):
        self.client.post('/auth/login', data={'username': 'lab_user', 'password': 'secret123'})

        response = self.client.post(
            f'/labstaff/messages/send/{self.admin_id}',
            data={'content': 'Need the radiology status for patient 42.'},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Lab result sent successfully.', response.data)

    def test_lab_staff_can_create_lab_test(self):
        self.client.post('/auth/login', data={'username': 'lab_user', 'password': 'secret123'})

        response = self.client.post(
            '/labstaff/lab-tests/create',
            data={
                'test_code': 'CBC-001',
                'test_name': 'Complete Blood Count',
                'description': 'Routine CBC profile',
                'normal_range': '4.5-11.0',
                'unit': 'K/uL',
                'price': '1500',
                'turnaround_time': '2-3 days',
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Lab test created successfully', response.data)

        with self.app.app_context():
            from app.models import LabTest
            self.assertTrue(LabTest.query.filter_by(test_code='CBC-001').first())

    def test_lab_staff_can_delete_lab_test(self):
        self.client.post('/auth/login', data={'username': 'lab_user', 'password': 'secret123'})

        with self.app.app_context():
            from app.models import LabTest
            test = LabTest(
                test_code='DELETE-001',
                test_name='Delete Me Test',
                description='Temporary test',
                price=10.0,
                is_active=True,
            )
            self.app.extensions['sqlalchemy'].db.session.add(test)
            self.app.extensions['sqlalchemy'].db.session.commit()
            test_id = test.id

        response = self.client.post(f'/labstaff/lab-tests/{test_id}/delete', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Delete Me Test', response.data)
        self.assertIn(b'deleted successfully', response.data.lower())

        with self.app.app_context():
            from app.models import LabTest
            self.assertIsNone(LabTest.query.get(test_id))

    def test_unauthorized_admin_access_is_logged(self):
        self.client.post('/auth/login', data={'username': 'doctor_user', 'password': 'secret123'})

        response = self.client.get('/admin/users', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'permission', response.data.lower())

        with self.app.app_context():
            from app.models import AuditLog
            self.assertGreater(AuditLog.query.count(), 0)

    def test_admin_can_delete_doctor_account(self):
        with self.app.app_context():
            doctor_user = User(
                username='delete_doctor',
                email='delete_doctor@example.com',
                first_name='Delete',
                last_name='Doctor',
                role=UserRole.DOCTOR,
            )
            doctor_user.set_password('secret123')
            db.session.add(doctor_user)
            db.session.commit()

            doctor_profile = Doctor(
                user_id=doctor_user.id,
                doctor_id='DOC00099',
                specialization='Neurology',
                license_number='LIC-00099',
                qualification='MD',
                consultation_fee=600.0,
                is_available=True,
            )
            db.session.add(doctor_profile)
            db.session.commit()
            doctor_user_id = doctor_user.id

        self.client.post('/auth/login', data={'username': 'admin_user', 'password': 'secret123'})
        response = self.client.post(f'/admin/users/{doctor_user_id}/delete', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'deleted successfully', response.data.lower())

        with self.app.app_context():
            self.assertIsNone(User.query.filter_by(username='delete_doctor').first())
            self.assertIsNone(Doctor.query.filter_by(doctor_id='DOC00099').first())

    def test_admin_can_delete_user_with_messages(self):
        with self.app.app_context():
            doctor_user = User(
                username='message_doctor',
                email='message_doctor@example.com',
                first_name='Message',
                last_name='Doctor',
                role=UserRole.DOCTOR,
            )
            doctor_user.set_password('secret123')
            db.session.add(doctor_user)
            db.session.commit()

            doctor_profile = Doctor(
                user_id=doctor_user.id,
                doctor_id='DOC00098',
                specialization='Cardiology',
                license_number='LIC-00098',
                qualification='MD',
                consultation_fee=700.0,
                is_available=True,
            )
            db.session.add(doctor_profile)
            db.session.commit()

            message = Message(
                sender_id=self.admin_id,
                recipient_id=doctor_user.id,
                content='Please review the latest patient update.',
            )
            db.session.add(message)
            db.session.commit()
            doctor_user_id = doctor_user.id

        self.client.post('/auth/login', data={'username': 'admin_user', 'password': 'secret123'})
        response = self.client.post(f'/admin/users/{doctor_user_id}/delete', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'deleted successfully', response.data.lower())

        with self.app.app_context():
            self.assertIsNone(User.query.filter_by(username='message_doctor').first())
            self.assertEqual(Message.query.filter_by(recipient_id=doctor_user_id).count(), 0)

    def test_admin_reports_show_hospital_summary(self):
        self.client.post('/auth/login', data={'username': 'admin_user', 'password': 'secret123'})

        response = self.client.get('/admin/reports', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Total Patients', response.data)
        self.assertIn(b'Active Admissions', response.data)
        self.assertIn(b'Total Revenue', response.data)
        self.assertIn(b'Completed', response.data)
        self.assertIn(b'Scheduled', response.data)


if __name__ == '__main__':
    unittest.main()
