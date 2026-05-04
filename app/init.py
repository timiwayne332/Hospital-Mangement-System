"""
Hospital Management System Flask Application Factory
"""
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config
from app.models import db, User


login_manager = LoginManager()
migrate = Migrate()


def create_app(config_name='development'):
    """
    Application factory function
    
    Args:
        config_name: Configuration environment (development, testing, production)
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login"""
        return User.query.get(int(user_id))
    
    # Create database tables within application context
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.doctor import doctor_bp
    from app.blueprints.receptionist import receptionist_bp
    from app.blueprints.patient import patient_bp
    from app.blueprints.main import main_bp
    from app.blueprints.prescription import prescription_bp
    from app.blueprints.labstaff import labstaff_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(receptionist_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(prescription_bp)
    app.register_blueprint(labstaff_bp)
    
    return app
