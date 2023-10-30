from grocery import db, login_manager, app
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from datetime import datetime
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

class Users(db.Model, UserMixin):
    '''name, email, username, password, address'''
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    image_file = db.Column(db.String(50), nullable=False, default='/img/user/avator.png')

    '''@property
    def password(self):
        raise AttributeError('Password is not visual')
    @password.setter
    def password(self, password):
        self.password = generate_password_hash(password)
    def verify_password(self, password):
        return check_password_hash(self.password, password)
    
    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'],expires_sec)
        return s.dumps({'user_id':self.id})
    
    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return Users.query.get(user_id)
    
    def __repr__(self):
        return '<Name %r>' % self.name'''

class Orders(db.Model):
    #__bind_key__ = 'db2'
    __tablename__ = 'orders'
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(120),nullable=False)
    product_list = db.Column(db.String,nullable=False)
    order_time = db.Column(db.DateTime, default=datetime.now())
    payment = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(256), nullable=False)
    unit = db.Column(db.Integer)

    #def __repr__(self):
    #    return f"Orders('{self.product_list}','{self.username}')"
    
class Order_report(db.Model):
   # __bind_key__ = 'db2'
    __tablename__ = 'order_report'
    id = db.Column(db.Integer,primary_key=True)
    product = db.Column(db.String(50))
    category = db.Column(db.String(50))
    count = db.Column(db.Integer)

    #def __repr__(self):
    #    return f"Order_report('{self.product}','{self.category}','{self.count}')"
    
class Category(db.Model):
    '''name, detail, img, '''
    #__bind_key__ = 'db6'
    __tablename__ = 'category'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    image = db.Column(db.String, default='/img/category/default.png')
    details = db.Column(db.String(256))

    #def __repr__(self):
    #    return f"Category('{self.name}','{self.details}','{self.image}')"

class Section(db.Model):
    '''category, section_name, image'''
    __tablename__ = 'section'
    id = db.Column(db.Integer,primary_key=True)
    category = db.Column(db.String(120),nullable=False)
    section_name = db.Column(db.String(120),nullable=False,unique=True)
    image = db.Column(db.String, default='/img/section/default.png')

class Products(db.Model):
    '''image store the path of the image'''
    #__bind_key__ = 'db3'
    __tablename__ = 'productlist'
    id = db.Column(db.Integer,primary_key=True)
    product_name = db.Column(db.String(50), unique=True, nullable=False)
    detail = db.Column(db.String(255))
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.REAL, nullable=False)
    image = db.Column(db.String,default='/img/product/default.png')
    stock = db.Column(db.Integer, nullable=False)
    expiry = db.Column(db.DATE)
    unit = db.Column(db.String(20))
    section_name = db.Column(db.String(120))
    
class Contact(db.Model):
    '''name, email, message'''
    #__bind_key__  = 'db5'
    __tablename__ = 'CallforSupport'
    id = db.Column('id', db.Integer,primary_key=True)
    name = db.Column('name', db.String(50), nullable=False)
    email = db.Column('email', db.String(120), nullable=False)
    message = db.Column('message', db.String(255), nullable=False)
    date = db.Column('date', db.DateTime, default=datetime.now())

class Report(db.Model):
    '''remark, status'''
    #__bind_key__ = 'db5'
    __tablename__ = 'report'
    id = db.Column('id', db.Integer, primary_key=True)
    remark = db.Column('remark', db.CHAR(50))
    status = db.Column(db.Boolean, nullable=False)
    date = db.Column('date', db.DateTime, default=datetime.now())
    name = db.Column('name', db.String(50))
    
class Cart(db.Model):
    '''itemtag, stock, price '''
    #__bind_key__ = 'db7'
    __tablename__ = 'present'
    id = db.Column(db.Integer,primary_key=True)
    product_name = db.Column(db.String(50),nullable=False)
    stock = db.Column(db.REAL)
    price = db.Column(db.REAL)
    username = db.Column(db.String(50),nullable=False)
    
    
class Admin(db.Model):
    '''name, username, password'''
    #__bind_key__ = 'db4'
    __tablename__ = 'log'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50),nullable=False)
    adminUser = db.Column(db.String(50),nullable=False)
    adminPass = db.Column(db.String(120),nullable=False)

    #def __repr__(self):
    #    return f"('{self.adminUser}')"

class Store_manager(db.Model):
    """name, usename, password"""
    #__bind_key__ = 'db4'
    __tablename__ = 'manager'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50),nullable=False)
    username = db.Column(db.String(50),unique=True,nullable=False)
    password = db.Column(db.String(120),nullable=False)
    status = db.Column(db.Boolean,default=0)

class Approvels(db.Model):
    '''request to delete a product or category'''
    __tablename__ = 'approvels'
    id = db.Column(db.Integer,primary_key=True)
    type = db.Column(db.String(50))
    name = db.Column(db.String(50))
    manager_name = db.Column(db.String(50))
    request_time = db.Column(db.DateTime,default=datetime.now())
    respond_time = db.Column(db.DateTime)
    respond_status = db.Column(db.String, default=0)

    