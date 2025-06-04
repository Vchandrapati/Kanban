from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    # Use environment variable for secret key in production
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

    # Database configuration - works for both local and deployed
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        # Production database (PostgreSQL from Railway/Heroku)
        if database_url.startswith('postgres://'):
            # Fix Railway's PostgreSQL URL format
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Local development database (SQLite)
        basedir = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(basedir, '..', 'taskflow.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import main
    app.register_blueprint(main)

    # Create database tables automatically on startup
    with app.app_context():
        db.create_all()

        # Create a default user if none exist (for first deployment)
        if not User.query.first():
            from .models import Swimlane
            admin_user = User(username='admin')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.flush()

            # Create default swimlane for admin
            default_swimlane = Swimlane(name='General', user_id=admin_user.id)
            db.session.add(default_swimlane)
            db.session.commit()

            print("Created default admin user: admin / admin123")

    return app