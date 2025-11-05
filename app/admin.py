from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for
from .models import User, Transaction, Category

class SecureAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_administrator():
            return redirect(url_for('main.index'))
        return super(SecureAdminIndexView, self).index()

class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_administrator()
    
    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return redirect(url_for('main.index'))

class SafeUserView(AdminModelView):
    column_exclude_list = ['password_hash']
    can_delete = False

class ReadOnlyTransactionView(AdminModelView):
    can_create = False
    can_edit = False
    can_delete = False

def init_admin(app, db):
    admin = Admin(app, name='Smart Expenses Admin', 
                 index_view=SecureAdminIndexView())
    admin.add_view(SafeUserView(User, db.session))
    admin.add_view(ReadOnlyTransactionView(Transaction, db.session))
    admin.add_view(AdminModelView(Category, db.session))
    return admin