from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
        os.path.abspath(os.path.dirname(__file__)), '../instance/expenses.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Create instance folder
    instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../instance')
    os.makedirs(instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        # Import and register blueprints
        from app.main.routes import main
        from app.auth.routes import auth_bp
        
        app.register_blueprint(main)
        app.register_blueprint(auth_bp, url_prefix='/auth')

    return app