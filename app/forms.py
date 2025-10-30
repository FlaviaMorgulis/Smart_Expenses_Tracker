from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, DateTimeField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Length, ValidationError
from wtforms.widgets import DateTimeLocalInput
from datetime import datetime

class TransactionForm(FlaskForm):
    amount = DecimalField('Amount', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='Amount must be greater than 0')
    ], places=2)
    
    transaction_type = SelectField('Type', choices=[
        ('income', 'Income'),
        ('expense', 'Expense')
    ], validators=[DataRequired()])
    
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    
    transaction_date = DateTimeField('Date', 
        widget=DateTimeLocalInput(),
        default=datetime.now,
        validators=[DataRequired()]
    )
    
    description = TextAreaField('Description (Optional)', validators=[Length(max=500)])
    submit = SubmitField('Add Transaction')
    
    def __init__(self, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)
        # Populate categories from database
        from app.models import Category
        self.category_id.choices = [(c.category_id, c.category_name) for c in Category.get_all_categories()]

class MemberForm(FlaskForm):
    name = StringField('Member Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    
    relationship = StringField('Relationship', validators=[
        DataRequired(),
        Length(min=2, max=50, message='Relationship must be between 2 and 50 characters')
    ])
    
    submit = SubmitField('Add Member')

class MemberTransactionForm(FlaskForm):
    member_id = SelectField('Member', coerce=int, validators=[DataRequired()])
    
    amount = DecimalField('Amount', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='Amount must be greater than 0')
    ], places=2)
    
    transaction_type = SelectField('Type', choices=[
        ('income', 'Income'),
        ('expense', 'Expense')
    ], validators=[DataRequired()])
    
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    
    transaction_date = DateTimeField('Date', 
        widget=DateTimeLocalInput(),
        default=datetime.now,
        validators=[DataRequired()]
    )
    
    description = TextAreaField('Description (Optional)', validators=[Length(max=500)])
    submit = SubmitField('Add Member Transaction')
    
    def __init__(self, user_members=None, *args, **kwargs):
        super(MemberTransactionForm, self).__init__(*args, **kwargs)
        # Populate categories from database
        from app.models import Category
        self.category_id.choices = [(c.category_id, c.category_name) for c in Category.get_all_categories()]
        
        # Populate members for the current user
        if user_members:
            self.member_id.choices = [(m.member_id, m.name) for m in user_members]
        else:
            self.member_id.choices = []

class ProfileUpdateForm(FlaskForm):
    name = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(),
        Length(max=255)
    ])
    
    current_password = StringField('Current Password (required for changes)', validators=[
        DataRequired()
    ])
    
    new_password = StringField('New Password (leave blank to keep current)')
    
    submit = SubmitField('Update Profile')

class DateRangeForm(FlaskForm):
    start_date = DateTimeField('Start Date', 
        widget=DateTimeLocalInput(),
        validators=[DataRequired()]
    )
    
    end_date = DateTimeField('End Date', 
        widget=DateTimeLocalInput(),
        validators=[DataRequired()]
    )
    
    submit = SubmitField('Filter')

class DeleteConfirmForm(FlaskForm):
    confirm_text = StringField('Type "DELETE" to confirm', validators=[
        DataRequired()
    ])
    
    submit = SubmitField('Delete Permanently')
    
    def validate_confirm_text(self, field):
        if field.data != 'DELETE':
            raise ValidationError('You must type "DELETE" to confirm')