from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DateField, SelectField, EmailField, FileField
from wtforms.validators import DataRequired, Length, Email, ValidationError
from grocery.models import Products, Category, Store_manager, Users
    
class ProductForm(FlaskForm):
    name = StringField(label='Name',validators=[DataRequired()])
    detail = StringField(label='Product Discription')
    price = IntegerField(label='Price', validators=[DataRequired()])
    stock = IntegerField(label='Stock',validators=[DataRequired()])
    expiry = DateField(label='Expiry Date',format="%Y-%m-%d")
    unit = SelectField(label='Choose a Unit', validators=[DataRequired()], choices=['Rs/kg','Rs/gram','Rs/dozen','Rs/Liter','Rs/piece'])
    submit = SubmitField('Add')

    def validate_name(self, name):
        product = Products.query.filter_by(product_name=name.data).first()
        if product:
            raise ValidationError('Product name already exist')
    
class CategoryForm(FlaskForm):
    name = StringField(label='Category name',validators=[DataRequired()])
    detail = StringField('Category Details')
    submit = SubmitField('Add')

    def validate_name(self, name):
        cate = Category.query.filter_by(name=name.data).first()
        if cate:
            raise ValidationError('Category already exist')
    
class AdminForm(FlaskForm):
    username = StringField(label='usename', validators=[DataRequired()])
    password = PasswordField(label='password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SupportForm(FlaskForm):
    name = StringField(label='name', validators=[DataRequired()])
    email = StringField(label='Email address', validators=[DataRequired(), Email()])
    message = StringField(label='Message', validators=[DataRequired()])
    submit = SubmitField('submit')

class ManagerForm(FlaskForm):
    username = StringField(label='Username', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ManagerRegisterForm(FlaskForm):
    name = StringField(label='Name', validators=[DataRequired()])
    username = StringField(label='Username', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        manager = Store_manager.query.filter_by(username=username.data).first()
        if manager:
            raise ValidationError('Product name already exist')

class ManagerPswResetFrom(FlaskForm):
    username = StringField(label='Username', validators=[DataRequired()])
    password = PasswordField(label='New Password', validators=[DataRequired()])
    submit = SubmitField('Change Password')

class UserPswResetForm(FlaskForm):
    email = EmailField(label='Enter Email', validators=[DataRequired(),Email()])
    password = PasswordField(label='New password', validators=[DataRequired()])
    submit = SubmitField('Change Password')

    def validate_email(self, email):
        user = Users.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('No account associate with this email')

class UserForgetPswForm(FlaskForm):
    email = EmailField(label='Enter Email', validators=[DataRequired()])
    submit = SubmitField('Request')

    def validate_email(self, email):
        user = Users.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('No account associate with this email')
        
class UserRegistration(FlaskForm):
    name = StringField(label='Name', validators=[DataRequired()])
    username = StringField(label='Username', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    email = EmailField(label='Email Address', validators=[DataRequired(),Email()])
    address = StringField(label='Address',validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = Users.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exist')
        
    def validate_email(self, email):
        user = Users.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already exist')

class SectionFrom(FlaskForm):
    name = StringField(label='Section name', validators=[DataRequired()])
    image = FileField(label='Section Image')
    submit = SubmitField('Add')