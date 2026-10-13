import unittest

from app import create_app
from app.models import db, User, UserRole


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

    def test_unauthorized_admin_access_is_logged(self):
        self.client.post('/auth/login', data={'username': 'doctor_user', 'password': 'secret123'})

        response = self.client.get('/admin/users', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'permission', response.data.lower())

        with self.app.app_context():
            from app.models import AuditLog
            self.assertGreater(AuditLog.query.count(), 0)


if __name__ == '__main__':
    unittest.main()
