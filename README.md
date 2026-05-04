# Hospital Management System

A comprehensive Hospital Management System built with Flask, SQLAlchemy, and Bootstrap. This application provides complete management for hospitals including patient management, doctor scheduling, appointments, medical records, billing with PDF receipts, pharmacy inventory, lab tests, and administrative reporting.

## Features

### 🔐 Authentication & Authorization
- Role-based access control (Admin, Doctor, Receptionist, Patient)
- User registration and login with Flask-Login
- Password encryption with Werkzeug
- Session management

### 👥 User Modules

#### Admin Dashboard
- Dashboard with system statistics
- User management (create, edit, delete)
- Doctor management and specialization
- Bed and ward management
- Lab test configuration
- Financial reports and analytics
- System monitoring

#### Doctor Module
- View and manage appointments
- Access patient information
- Create and manage medical records
- Request lab tests for patients
- View lab results
- Patient history and medical notes

#### Receptionist Module
- Schedule and manage appointments
- Patient registration and information
- Admission/discharge management
- Bed allocation
- Billing and payment processing
- Generate PDF receipts
- Patient scheduling

#### Patient Module
- View upcoming appointments
- Access medical records
- View lab results
- Manage billing information
- Update personal health information
- Emergency contacts
- Insurance information

### 📊 Core Features

#### Appointments
- Schedule appointments between patients and doctors
- View appointment history
- Cancel appointments
- Track appointment status

#### Medical Records
- Comprehensive patient medical history
- Doctor's notes and diagnosis
- Treatment plans and prescriptions
- Secure storage

#### Bed Management
- Track available beds by ward
- Manage bed assignments
- Monitor bed occupancy
- Support multiple ward types (ICU, General, Pediatric)

#### Admissions & Discharge
- Patient admission process
- Bed assignment
- Discharge management
- Track admission duration and reason

#### Billing System
- Create and manage bills
- Track payment status
- Multiple payment methods
- PDF receipt generation

#### Pharmacy Inventory
- Medicine inventory management
- Stock level tracking
- Medicine information (usage, side effects)
- Low stock alerts

#### Lab Tests
- Configure lab tests
- Request lab tests for patients
- Track lab results
- View test results

#### Dashboard & Reports
- Real-time statistics
- Financial reports
- Appointment analytics
- Patient statistics
- Inventory reports

## Technology Stack

- **Backend**: Flask 2.3.x
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Bootstrap 5, Jinja2 Templates
- **Authentication**: Flask-Login
- **PDF Generation**: ReportLab
- **Forms**: HTML5 Forms with Bootstrap styling

## Project Structure

```
Hospital Management System/
├── app/
│   ├── blueprints/          # Feature modules
│   │   ├── auth.py          # Authentication
│   │   ├── admin.py         # Admin functions
│   │   ├── doctor.py        # Doctor functions
│   │   ├── receptionist.py  # Receptionist functions
│   │   ├── patient.py       # Patient functions
│   │   └── main.py          # Main dashboard
│   ├── models/              # Database models
│   │   └── __init__.py      # SQLAlchemy models
│   ├── templates/           # Jinja2 templates
│   │   ├── layouts/
│   │   │   └── base.html    # Base template
│   │   ├── auth/            # Auth templates
│   │   ├── admin/           # Admin templates
│   │   ├── doctor/          # Doctor templates
│   │   ├── receptionist/    # Receptionist templates
│   │   └── patient/         # Patient templates
│   ├── static/              # CSS & JavaScript
│   │   ├── css/
│   │   └── js/
│   ├── utils/               # Utility functions
│   └── __init__.py          # App factory
├── config.py                # Configuration settings
├── run.py                   # Application entry point
├── seed_database.py         # Database seeding script
├── requirements.txt         # Dependencies
└── README.md               # Documentation
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Step 1: Clone Repository
```bash
cd "Hospital Mangement System"
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Create Database & Seed Data
```bash
python seed_database.py
```

This will create the database and populate it with sample data including:
- 1 Admin account
- 5 Doctor accounts
- 1 Receptionist account
- 10 Patient accounts
- 50 Beds across different wards
- Sample medicines, lab tests, and appointments

### Step 5: Run Application
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## Test Accounts

After running the seed script, you can log in with these credentials:

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Doctor | doctor1 | doctor123 |
| Receptionist | receptionist | receptionist123 |
| Patient | patient1 | patient123 |

## Usage Guide

### Admin Functions
1. Navigate to Admin Dashboard
2. Manage users, doctors, and staff
3. Configure beds and lab tests
4. View system reports and analytics

### Doctor Functions
1. View scheduled appointments
2. Create medical records for patients
3. Request lab tests
4. Access patient medical history

### Receptionist Functions
1. Schedule appointments
2. Manage patient admissions and discharges
3. Create and manage billing records
4. Generate PDF receipts

### Patient Functions
1. View forthcoming appointments
2. Access medical records
3. Check lab results
4. Review billing information
5. Update personal profile

## Database Models

### Core Models
- **User**: All system users with roles
- **Patient**: Patient information and health data
- **Doctor**: Doctor specialization and details
- **Appointment**: Appointment scheduling
- **MedicalRecord**: Doctor's notes and diagnosis
- **Admission**: Patient hospital admission
- **Bed**: Hospital bed management
- **BillingRecord**: Financial transactions
- **Medicine**: Pharmacy inventory
- **LabTest**: Laboratory test types
- **LabResult**: Patient lab results

## Configuration

Edit `config.py` to customize:
- Database location
- Session duration
- Upload folder
- Debug mode
- Secret key

### Production Deployment
1. Set `DEBUG = False` in production config
2. Change `SECRET_KEY` to a secure random string
3. Use a production database (PostgreSQL recommended)
4. Set `REMEMBER_COOKIE_SECURE = True` for HTTPS
5. Use environment variables for sensitive data

## Features Implemented

✅ Multi-role authentication
✅ Patient management system
✅ Doctor scheduling
✅ Appointment management
✅ Medical records
✅ Bed management
✅ Admission/Discharge tracking
✅ Billing with invoicing
✅ PDF receipt generation
✅ Pharmacy inventory
✅ Lab tests & results
✅ Dashboard analytics
✅ Responsive Bootstrap UI
✅ Database ORM with SQLAlchemy
✅ Seed data for testing

## Future Enhancements

- Email notifications
- SMS alerts
- Advanced reporting (charts, graphs)
- Mobile app version
- Prescription printing
- Insurance integration
- Appointment calendar view
- Payment gateway integration
- Two-factor authentication
- Audit logging

## Troubleshooting

### Database not found
```bash
# Delete existing database
rm hospital_mgmt.db

# Re-seed database
python seed_database.py
```

### Port already in use
Edit `run.py` and change port:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change 5000 to another port
```

### Import errors
```bash
# Ensure virtual environment is activated
# Reinstall requirements
pip install --upgrade pip
pip install -r requirements.txt
```

## Security Notes

- Change default admin password after first login
- Use HTTPS in production
- Implement CSRF protection for sensitive operations
- Regular database backups
- Secure sensitive data in environment variables
- Implement rate limiting
- Validate all user inputs

## Contributing

To extend the system:

1. Create new blueprints in `app/blueprints/`
2. Add models in `app/models/__init__.py`
3. Create templates in `app/templates/`
4. Register blueprints in `app/__init__.py`
5. Test thoroughly before deployment

## License

This project is provided as-is for educational and personal use.

## Support

For issues or questions:
1. Check the README and documentation
2. Review the code comments
3. Check Flask and SQLAlchemy documentation
4. Verify database connection
5. Check application logs

## Changelog

### Version 1.0.0
- Initial release
- Complete Hospital Management System
- All core features implemented
- Bootstrap 5 responsive design
- SQLite database
- Role-based access control

---

**Last Updated**: 2024
**Status**: Ready for Production
**Python**: 3.8+
**Flask**: 2.3.x


## Test Credentials

| Role | Username | Password |
|------|----------|----------|
| **Admin** | `admin` | `admin123` |
| **Doctor 1** | `doctor1` | `doctor123` |
| **Doctor 2** | `doctor2` | `doctor123` |
| **Doctor 3** | `doctor3` | `doctor123` |
| **Doctor 4** | `doctor4` | `doctor123` |
| **Doctor 5** | `doctor5` | `doctor123` |
| **Receptionist** | `receptionist` | `receptionist123` |
| **Patient 1** | `patient1` | `patient123` |
| **Patient 2** | `patient2` | `patient123` |
| **Patient 3** | `patient3` | `patient123` |
| **Patient 4** | `patient4` | `patient123` |
| **Patient 5** | `patient5` | `patient123` |
| **Patient 6** | `patient6` | `patient123` |
| **Patient 7** | `patient7` | `patient123` |
| **Patient 8** | `patient8` | `patient123` |
| **Patient 9** | `patient9` | `patient123` |
| **Patient 10** | `patient10` | `patient123` |

All doctors use `doctor123` and all patients use `patient123` as their password.