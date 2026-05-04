"""
Decorators for role-based and permission-based access control
"""
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from app.models import UserRole


def role_required(*roles):
    """
    Decorator to check if user has one of the required roles
    
    Usage:
        @role_required(UserRole.ADMIN, UserRole.DOCTOR)
        def my_view():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator to check if user is admin"""
    return role_required(UserRole.ADMIN)(f)


def doctor_required(f):
    """Decorator to check if user is doctor"""
    return role_required(UserRole.DOCTOR)(f)


def receptionist_required(f):
    """Decorator to check if user is receptionist"""
    return role_required(UserRole.RECEPTIONIST)(f)


def patient_required(f):
    """Decorator to check if user is patient"""
    return role_required(UserRole.PATIENT)(f)


def staff_required(f):
    """Decorator to check if user is staff (admin, doctor, or receptionist)"""
    return role_required(UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST)(f)
