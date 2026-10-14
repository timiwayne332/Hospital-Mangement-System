"""
Pharmacy Blueprint - Handles medication inventory and dispensing workflows.
"""
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.models import (
    Medicine,
    PharmacyPayment,
    PharmacyPurchase,
    PharmacyPurchaseItem,
    PharmacySale,
    PharmacySaleItem,
    Prescription,
    PrescriptionItem,
    Supplier,
    UserRole,
    db,
)
from app.utils.decorators import pharmacist_required

pharmacy_bp = Blueprint('pharmacy', __name__, url_prefix='/pharmacy', template_folder='../templates')


def _get_cart():
    cart = session.get('pharmacy_cart', [])
    if not isinstance(cart, list):
        return []
    return cart


def _save_cart(cart):
    session['pharmacy_cart'] = cart


@pharmacy_bp.route('/dashboard')
@login_required
@pharmacist_required
def dashboard():
    """Pharmacy dashboard with inventory and operational metrics."""
    medicines = Medicine.query.order_by(Medicine.name).all()
    low_stock = Medicine.query.filter(Medicine.quantity <= Medicine.min_stock_level).order_by(Medicine.quantity.asc()).all()
    active_prescriptions = Prescription.query.filter_by(status='active').count()
    stats = {
        'total_medicines': Medicine.query.count(),
        'low_stock_medicines': len(low_stock),
        'active_prescriptions': active_prescriptions,
        'available_medicines': Medicine.query.filter_by(is_available=True).count(),
        'recent_medicines': medicines[:5],
        'low_stock_items': low_stock[:5],
    }
    return render_template('pharmacy/dashboard.html', stats=stats, low_stock=low_stock, medicines=medicines[:5])


@pharmacy_bp.route('/inventory')
@login_required
@pharmacist_required
def inventory():
    """Display inventory for stock review and replenishment."""
    search = request.args.get('q', '').strip()
    query = Medicine.query
    if search:
        query = query.filter(
            or_(
                Medicine.name.ilike(f'%{search}%'),
                Medicine.generic_name.ilike(f'%{search}%'),
                Medicine.medicine_code.ilike(f'%{search}%')
            )
        )
    medicines = query.order_by(Medicine.name).all()
    return render_template('pharmacy/inventory.html', medicines=medicines, search=search)


@pharmacy_bp.route('/medicines/new', methods=['GET', 'POST'])
@login_required
@pharmacist_required
def new_medicine():
    """Create a new medicine entry."""
    if request.method == 'POST':
        medicine_code = request.form.get('medicine_code', '').strip()
        name = request.form.get('name', '').strip()
        generic_name = request.form.get('generic_name', '').strip()
        manufacturer = request.form.get('manufacturer', '').strip()
        unit = request.form.get('unit', '').strip() or 'unit'
        quantity = int(request.form.get('quantity', 0) or 0)
        price_per_unit = float(request.form.get('price_per_unit', 0) or 0)
        expiry_date = request.form.get('expiry_date')
        min_stock_level = int(request.form.get('min_stock_level', 10) or 10)

        if not medicine_code or not name:
            flash('Medicine code and name are required.', 'danger')
            return redirect(url_for('pharmacy.new_medicine'))

        if Medicine.query.filter_by(medicine_code=medicine_code).first():
            flash('A medicine with that code already exists.', 'danger')
            return redirect(url_for('pharmacy.new_medicine'))

        medicine = Medicine(
            medicine_code=medicine_code,
            name=name,
            generic_name=generic_name,
            manufacturer=manufacturer,
            unit=unit,
            quantity=quantity,
            price_per_unit=price_per_unit,
            expiry_date=datetime.strptime(expiry_date, '%Y-%m-%d').date() if expiry_date else None,
            min_stock_level=min_stock_level,
            is_available=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(medicine)
        db.session.commit()
        flash('Medicine added successfully.', 'success')
        return redirect(url_for('pharmacy.inventory'))

    return render_template('pharmacy/add_medicine.html')


@pharmacy_bp.route('/medicines/<int:medicine_id>/edit', methods=['GET', 'POST'])
@login_required
@pharmacist_required
def edit_medicine(medicine_id):
    """Update medicine details and stock."""
    medicine = Medicine.query.get_or_404(medicine_id)

    if request.method == 'POST':
        medicine.medicine_code = request.form.get('medicine_code', medicine.medicine_code).strip()
        medicine.name = request.form.get('name', medicine.name).strip()
        medicine.generic_name = request.form.get('generic_name', medicine.generic_name).strip()
        medicine.manufacturer = request.form.get('manufacturer', medicine.manufacturer).strip()
        medicine.unit = request.form.get('unit', medicine.unit).strip() or medicine.unit or 'unit'
        medicine.quantity = int(request.form.get('quantity', medicine.quantity) or medicine.quantity)
        medicine.price_per_unit = float(request.form.get('price_per_unit', medicine.price_per_unit) or medicine.price_per_unit)
        medicine.min_stock_level = int(request.form.get('min_stock_level', medicine.min_stock_level) or medicine.min_stock_level)
        medicine.is_available = request.form.get('is_available') == 'on'

        expiry_date = request.form.get('expiry_date')
        if expiry_date:
            medicine.expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()

        medicine.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Medicine updated successfully.', 'success')
        return redirect(url_for('pharmacy.inventory'))

    return render_template('pharmacy/edit_medicine.html', medicine=medicine)


@pharmacy_bp.route('/medicines/<int:medicine_id>/delete', methods=['POST'])
@login_required
@pharmacist_required
def delete_medicine(medicine_id):
    """Delete a medicine record."""
    medicine = Medicine.query.get_or_404(medicine_id)
    db.session.delete(medicine)
    db.session.commit()
    flash('Medicine deleted successfully.', 'success')
    return redirect(url_for('pharmacy.inventory'))


@pharmacy_bp.route('/restock', methods=['GET', 'POST'])
@login_required
@pharmacist_required
def restock_medicine():
    """Record a medicine restock and increase available quantity."""
    medicines = Medicine.query.order_by(Medicine.name).all()

    if request.method == 'POST':
        medicine_id = request.form.get('medicine_id')
        quantity = int(request.form.get('quantity', 0) or 0)
        unit_cost = float(request.form.get('unit_cost', 0) or 0)
        supplier = request.form.get('supplier', '').strip()

        if not medicine_id or quantity <= 0:
            flash('Please select a medicine and enter a valid restock quantity.', 'danger')
            return redirect(url_for('pharmacy.restock_medicine'))

        medicine = Medicine.query.get_or_404(int(medicine_id))
        medicine.quantity += quantity
        if unit_cost > 0:
            medicine.price_per_unit = unit_cost
        if supplier:
            medicine.manufacturer = supplier
        medicine.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'{medicine.name} restocked by {quantity} units.', 'success')
        return redirect(url_for('pharmacy.inventory'))

    return render_template('pharmacy/restock.html', medicines=medicines)


@pharmacy_bp.route('/sales')
@login_required
@pharmacist_required
def sales():
    """POS sales screen with a live cart."""
    medicines = Medicine.query.filter_by(is_available=True).order_by(Medicine.name).all()
    cart = _get_cart()
    total = 0.0
    for item in cart:
        total += item.get('quantity', 0) * float(item.get('unit_price', 0))
    return render_template('pharmacy/sales.html', medicines=medicines, cart=cart, total=total)


@pharmacy_bp.route('/sales/add', methods=['POST'])
@login_required
@pharmacist_required
def add_to_cart():
    """Add an item to the cart for sale."""
    medicine_id = request.form.get('medicine_id')
    quantity = int(request.form.get('quantity', 1) or 1)

    if not medicine_id:
        flash('Select a medicine before adding it to the cart.', 'danger')
        return redirect(url_for('pharmacy.sales'))

    medicine = Medicine.query.get_or_404(int(medicine_id))
    if not medicine.is_available:
        flash(f'{medicine.name} is unavailable for sale.', 'warning')
        return redirect(url_for('pharmacy.sales'))

    if quantity <= 0:
        flash('Quantity must be greater than zero.', 'danger')
        return redirect(url_for('pharmacy.sales'))

    cart = _get_cart()
    for item in cart:
        if int(item['medicine_id']) == medicine.id:
            item['quantity'] += quantity
            _save_cart(cart)
            flash(f'{medicine.name} quantity updated in cart.', 'success')
            return redirect(url_for('pharmacy.sales'))

    cart.append({
        'medicine_id': medicine.id,
        'name': medicine.name,
        'unit': medicine.unit or 'unit',
        'quantity': quantity,
        'unit_price': float(medicine.price_per_unit or 0),
    })
    _save_cart(cart)
    flash(f'{medicine.name} added to the sales cart.', 'success')
    return redirect(url_for('pharmacy.sales'))


@pharmacy_bp.route('/sales/remove/<int:medicine_id>', methods=['POST'])
@login_required
@pharmacist_required
def remove_from_cart(medicine_id):
    """Remove a medicine from the current sales cart."""
    cart = _get_cart()
    updated_cart = [item for item in cart if int(item.get('medicine_id')) != medicine_id]
    _save_cart(updated_cart)
    flash('Item removed from cart.', 'success')
    return redirect(url_for('pharmacy.sales'))


@pharmacy_bp.route('/sales/checkout', methods=['POST'])
@login_required
@pharmacist_required
def checkout_sale():
    """Finalize a sale by recording payment, reducing stock, and clearing the cart."""
    cart = _get_cart()
    if not cart:
        flash('The cart is empty.', 'warning')
        return redirect(url_for('pharmacy.sales'))

    payment_method = request.form.get('payment_method', 'cash')
    amount_paid = float(request.form.get('amount_paid', 0) or 0)
    reference_number = (request.form.get('reference_number') or '').strip()
    notes = (request.form.get('notes') or '').strip()

    for item in cart:
        medicine = Medicine.query.get(item.get('medicine_id'))
        if not medicine:
            flash('One or more medicines are no longer available.', 'danger')
            return redirect(url_for('pharmacy.sales'))
        if medicine.quantity < item.get('quantity', 0):
            flash(f'Insufficient stock for {medicine.name}. Available: {medicine.quantity}', 'danger')
            return redirect(url_for('pharmacy.sales'))

    subtotal = sum(float(item.get('quantity', 0)) * float(item.get('unit_price', 0)) for item in cart)
    if amount_paid <= 0:
        amount_paid = subtotal

    sale = PharmacySale(
        invoice_number=f'PH-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}-{current_user.id}',
        user_id=current_user.id,
        sale_date=datetime.utcnow(),
        subtotal=subtotal,
        total_amount=subtotal,
        amount_paid=amount_paid,
        payment_method=payment_method,
        payment_status='paid' if amount_paid >= subtotal else 'partial',
        notes=notes,
    )
    db.session.add(sale)
    db.session.flush()

    for item in cart:
        medicine = Medicine.query.get(item.get('medicine_id'))
        quantity = int(item.get('quantity', 0))
        unit_price = float(item.get('unit_price', 0))
        subtotal_line = quantity * unit_price

        sale_item = PharmacySaleItem(
            sale_id=sale.id,
            medicine_id=medicine.id,
            medicine_name=medicine.name,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal_line,
        )
        db.session.add(sale_item)

        medicine.quantity -= quantity
        medicine.updated_at = datetime.utcnow()

    payment = PharmacyPayment(
        sale_id=sale.id,
        payment_method=payment_method,
        amount=amount_paid,
        reference_number=reference_number or None,
        status='completed' if amount_paid >= subtotal else 'pending',
        paid_at=datetime.utcnow(),
    )
    db.session.add(payment)

    _save_cart([])
    db.session.commit()
    flash(f'Sale completed successfully. Receipt No: {sale.invoice_number}', 'success')
    return redirect(url_for('pharmacy.sale_receipt', sale_id=sale.id))


@pharmacy_bp.route('/sales/<int:sale_id>/receipt')
@login_required
@pharmacist_required
def sale_receipt(sale_id):
    """Generate an itemized receipt for a completed sale."""
    sale = PharmacySale.query.get_or_404(sale_id)
    return render_template('pharmacy/receipt.html', sale=sale)


@pharmacy_bp.route('/payments')
@login_required
@pharmacist_required
def payment_dashboard():
    """Display pharmacy payment status and collections summary."""
    sales = PharmacySale.query.order_by(PharmacySale.sale_date.desc()).all()
    metrics = {
        'total_sales': sum(sale.total_amount for sale in sales),
        'total_collected': sum(sale.amount_paid for sale in sales),
        'paid': sum(1 for sale in sales if sale.payment_status == 'paid'),
        'partial': sum(1 for sale in sales if sale.payment_status == 'partial'),
        'pending': sum(1 for sale in sales if sale.payment_status == 'pending'),
    }
    recent_payments = (
        db.session.query(PharmacySale, PharmacyPayment)
        .join(PharmacyPayment, PharmacyPayment.sale_id == PharmacySale.id)
        .order_by(PharmacyPayment.paid_at.desc())
        .all()
    )
    return render_template('pharmacy/payments.html', sales=sales, metrics=metrics, recent_payments=recent_payments)


@pharmacy_bp.route('/purchases')
@login_required
@pharmacist_required
def purchases():
    """View supplier purchase ledger and stock acquisition history."""
    purchases = PharmacyPurchase.query.order_by(PharmacyPurchase.purchase_date.desc()).all()
    return render_template('pharmacy/purchases.html', purchases=purchases)


@pharmacy_bp.route('/suppliers')
@login_required
@pharmacist_required
def suppliers():
    """List pharmacy suppliers and their purchase activity."""
    suppliers = Supplier.query.order_by(Supplier.name).all()
    return render_template('pharmacy/suppliers.html', suppliers=suppliers)


@pharmacy_bp.route('/prescriptions')
@login_required
@pharmacist_required
def prescriptions():
    """List active outpatient prescriptions that are ready for dispensing."""
    prescriptions = Prescription.query.filter_by(status='active').order_by(Prescription.prescription_date.desc()).all()
    return render_template('pharmacy/prescriptions.html', prescriptions=prescriptions)


@pharmacy_bp.route('/prescriptions/<int:prescription_id>/dispense', methods=['POST'])
@login_required
@pharmacist_required
def dispense_prescription(prescription_id):
    """Dispense a prescription by reducing inventory and marking items as completed."""
    prescription = Prescription.query.get_or_404(prescription_id)

    for item in prescription.prescription_items:
        medicine = Medicine.query.get(item.medicine_id)
        if not medicine:
            flash('One or more medicines no longer exist in inventory.', 'danger')
            return redirect(url_for('pharmacy.prescriptions'))
        if medicine.quantity < item.quantity:
            flash(f'Insufficient stock for {medicine.name}.', 'danger')
            return redirect(url_for('pharmacy.prescriptions'))

    for item in prescription.prescription_items:
        medicine = Medicine.query.get(item.medicine_id)
        medicine.quantity -= item.quantity
        medicine.updated_at = datetime.utcnow()
        item.is_dispensed = True
        item.dispensed_date = datetime.utcnow()

    prescription.status = 'dispensed'
    prescription.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Prescription dispensed successfully.', 'success')
    return redirect(url_for('pharmacy.prescriptions'))
