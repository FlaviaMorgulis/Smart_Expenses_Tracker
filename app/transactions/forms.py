from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional
from datetime import datetime

class TransactionForm(FlaskForm):
    amount = DecimalField('Amount', 
                         validators=[DataRequired(), NumberRange(min=0.01, message="Amount must be greater than 0")],
                         places=2)
    
    transaction_type = SelectField('Type', 
                                  choices=[('income', 'Income'), ('expense', 'Expense')],
                                  validators=[DataRequired()])
    
    category_id = SelectField('Category', 
                             coerce=int,
                             validators=[Optional()])
    
    transaction_date = DateField('Date', 
                                validators=[DataRequired()],
                                default=datetime.today)
    
    submit = SubmitField('Add Transaction')

class EditTransactionForm(FlaskForm):
    amount = DecimalField('Amount', 
                         validators=[DataRequired(), NumberRange(min=0.01, message="Amount must be greater than 0")],
                         places=2)
    
    transaction_type = SelectField('Type', 
                                  choices=[('income', 'Income'), ('expense', 'Expense')],
                                  validators=[DataRequired()])
    
    category_id = SelectField('Category', 
                             coerce=int,
                             validators=[Optional()])
    
    transaction_date = DateField('Date', 
                                validators=[DataRequired()])
    
    submit = SubmitField('Update Transaction')
