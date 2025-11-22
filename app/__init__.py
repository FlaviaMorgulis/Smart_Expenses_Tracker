from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from datetime import datetime
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

from app.models import User 

def create_app():
    app = Flask(__name__)
    
    # Config
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize Flask-Admin with security boundaries
    from app.admin import init_admin
    init_admin(app, db)
    
    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.transactions.routes import transactions_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(transactions_bp, url_prefix='/transactions')
    
    @app.context_processor
    def utility_processor():
        return dict(now=datetime.now)
    
    return app
