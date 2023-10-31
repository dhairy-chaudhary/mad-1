from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from flask_login import LoginManager
from flask_mail import Mail
from flask_restful import Api

app = Flask(__name__)
app.config.update()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
'''app.config['SQLALCHEMY_BINDS'] = {'db2' : 'sqlite:///orders.db','db3' : 'sqlite:///products.db',
                                    'db4' : 'sqlite:///admin.db', 'db5' : 'sqlite:///contact.db',
                                    'db6' : 'sqlite:///category.db','db7': 'sqlite:///cart.db' }'''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '3cf3b3734fd56cddf1c707e2f1b1b71f'

app.permanent_session_lifetime = timedelta(minutes=30)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
api = Api(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

app.config['MAIL_SERVER']= 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'dhairy.demo.28@gmail.com'
app.config['MAIL_PASSWORD'] = '**********'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

from grocery import routes
