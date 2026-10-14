import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.models import UserRole


def test_pharmacist_role_exists():
    assert hasattr(UserRole, 'PHARMACIST')
    assert UserRole.PHARMACIST.value == 'pharmacist'


def test_pharmacy_dashboard_is_registered():
    app = create_app()
    client = app.test_client()
    response = client.get('/pharmacy/dashboard')
    assert response.status_code in (200, 302)


def test_pharmacy_sale_payment_models_exist():
    from app.models import PharmacySale, PharmacyPayment, PharmacySaleItem

    assert PharmacySale is not None
    assert PharmacyPayment is not None
    assert PharmacySaleItem is not None


def test_pharmacy_checkout_records_payment_and_sale():
    from app.models import Medicine, PharmacyPayment, PharmacySale, User, UserRole, db

    app = create_app()
    with app.app_context():
        db.session.query(PharmacyPayment).delete()
        db.session.query(PharmacySale).delete()
        db.session.query(Medicine).delete()
        db.session.query(User).filter_by(username='pharmacy_checkout_user').delete()
        db.session.commit()

        user = User(
            username='pharmacy_checkout_user',
            email='pharmacy_checkout_user@test.com',
            first_name='Pos',
            last_name='User',
            role=UserRole.PHARMACIST,
        )
        user.set_password('secret123')
        db.session.add(user)

        medicine = Medicine(
            medicine_code='PHARM-001',
            name='Paracetamol',
            generic_name='Acetaminophen',
            quantity=10,
            price_per_unit=5.0,
            min_stock_level=2,
            is_available=True,
        )
        db.session.add(medicine)
        db.session.commit()

        with app.test_client() as client:
            login = client.post('/auth/login', data={'username': 'pharmacy_checkout_user', 'password': 'secret123'})
            assert login.status_code in (200, 302)

            with client.session_transaction() as sess:
                sess['pharmacy_cart'] = [{
                    'medicine_id': medicine.id,
                    'name': medicine.name,
                    'quantity': 2,
                    'unit_price': 5.0,
                }]

            response = client.post(
                '/pharmacy/sales/checkout',
                data={'payment_method': 'cash', 'amount_paid': '10.00', 'reference_number': 'REF-123', 'notes': 'test sale'},
                follow_redirects=False,
            )
            assert response.status_code == 302
            assert PharmacySale.query.count() == 1
            assert PharmacyPayment.query.count() == 1
            sale = PharmacySale.query.first()
            assert sale.amount_paid == 10.0
            assert sale.payment_status == 'paid'


def test_pharmacy_receipt_and_payment_dashboard_routes_exist():
    from app.models import Medicine, PharmacyPayment, PharmacySale, User, UserRole, db

    app = create_app()
    with app.app_context():
        db.session.query(PharmacyPayment).delete()
        db.session.query(PharmacySale).delete()
        db.session.query(Medicine).delete()
        db.session.query(User).filter_by(username='receipt_user').delete()
        db.session.commit()

        user = User(
            username='receipt_user',
            email='receipt_user@test.com',
            first_name='Receipt',
            last_name='User',
            role=UserRole.PHARMACIST,
        )
        user.set_password('secret123')
        db.session.add(user)

        medicine = Medicine(
            medicine_code='PHARM-002',
            name='Vitamin C',
            quantity=5,
            price_per_unit=15.0,
            min_stock_level=2,
            is_available=True,
        )
        db.session.add(medicine)
        db.session.commit()

        sale = PharmacySale(
            invoice_number='PH-REC-001',
            user_id=user.id,
            subtotal=30.0,
            total_amount=30.0,
            amount_paid=30.0,
            payment_method='cash',
            payment_status='paid',
        )
        db.session.add(sale)
        db.session.flush()

        db.session.add(PharmacyPayment(
            sale_id=sale.id,
            payment_method='cash',
            amount=30.0,
            reference_number='R-001',
            status='completed',
        ))
        db.session.commit()

        with app.test_client() as client:
            login = client.post('/auth/login', data={'username': 'receipt_user', 'password': 'secret123'})
            assert login.status_code in (200, 302)
            receipt = client.get(f'/pharmacy/sales/{sale.id}/receipt')
            assert receipt.status_code == 200
            payments = client.get('/pharmacy/payments')
            assert payments.status_code == 200


def test_supplier_purchase_ledger_routes_exist():
    from app.models import Supplier, PharmacyPurchase, PharmacyPurchaseItem, User, UserRole, db

    app = create_app()
    with app.app_context():
        db.session.query(PharmacyPurchaseItem).delete()
        db.session.query(PharmacyPurchase).delete()
        db.session.query(Supplier).delete()
        db.session.query(User).filter_by(username='supplier_user').delete()
        db.session.commit()

        user = User(
            username='supplier_user',
            email='supplier_user@test.com',
            first_name='Supplier',
            last_name='User',
            role=UserRole.PHARMACIST,
        )
        user.set_password('secret123')
        db.session.add(user)

        supplier = Supplier(
            name='CareMed Ltd',
            contact_person='Jane Smith',
            phone='08000000000',
            email='orders@caremed.example',
            address='Main Street',
        )
        db.session.add(supplier)
        db.session.commit()

        purchase = PharmacyPurchase(
            supplier_id=supplier.id,
            invoice_number='PO-1001',
            total_amount=250.0,
            amount_paid=120.0,
            payment_status='partial',
        )
        db.session.add(purchase)
        db.session.commit()

        with app.test_client() as client:
            login = client.post('/auth/login', data={'username': 'supplier_user', 'password': 'secret123'})
            assert login.status_code in (200, 302)

            response = client.get('/pharmacy/purchases')
            assert response.status_code == 200
            supplier_response = client.get('/pharmacy/suppliers')
            assert supplier_response.status_code == 200
