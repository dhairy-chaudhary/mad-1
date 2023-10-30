#imports-----------------------------------------------------------------------------------
from ast import literal_eval
from datetime import datetime
import json
from flask import flash, render_template, session, url_for, redirect, request, make_response
from PIL import Image
from grocery.forms import (AdminForm, ProductForm, CategoryForm, SectionFrom, SupportForm, ManagerForm, 
                           ManagerRegisterForm, ManagerPswResetFrom, UserPswResetForm, UserForgetPswForm, UserRegistration)
from grocery.models import (Users, Orders, Products, Contact, Report, Cart, Section, 
                            Admin, Category, Order_report, Store_manager, Approvels)
from flask_login import  login_required, login_user, current_user, logout_user
from grocery import app, db, mail, api
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import secrets
import os
from sqlalchemy import and_, or_
from flask_mail import Message
from flask_httpauth import HTTPBasicAuth
from flask_restful import Resource, reqparse, fields, marshal_with, inputs
from werkzeug.security import check_password_hash, generate_password_hash
#functions----------------------------------------------------------------------------------
auth = HTTPBasicAuth()
#function to get dict of product
def product_check(username):
    result = []
    data = Cart.query.filter_by(username=username)
    for da in data:
        buffer = []
        buffer.append(da.product_name)
        p = Products.query.filter_by(product_name=da.product_name).first()
        buffer.append(da.stock)
        buffer.append(da.price)
        buffer.append(p.unit)
        result.append(buffer)
    return result
#function for stock change
def stock_cml(l):
    #[[product_name,quantity(stock),price,unit],[....],...,[....]]
    for i in l:
        data = Products.query.filter_by(product_name=i[0]).first()
        if data.stock > 0:
            stock = int(data.stock) - int(i[1])
            if stock >= 0:
                Products.query.filter_by(product_name=i[0]).update(dict(stock=stock))
            else :
                flash(f'{data.product_name} is in limited no. stock:{data.stock}, please update order to cont...', 'warning')
        else:
            flash(f'{data.product_name} is out of stock please remove to continue','danger')

        entry = Order_report(product=i[0],category=data.category,count=i[1])
        db.session.add(entry)
        db.session.commit()
        db.session.close()
#function to verify promocode
def code_verify(code):
    codes = str(code)
    all_promo = ['NEW-15', 'ALL-5', 'EXIST-5', 'FIRST-15', 'SPECIAL-20', 'FIRST-30', 'FIRST-45']
    if codes in all_promo:
        promo = codes.strip().split('-')
        promo.append(code)
    return promo
#function to total cart order value
def total(username,p):
    result = 0
    item = Cart.query.filter_by(username=username)
    for i in item :
        result += i.stock*i.price
    try:
        num = int(p[1])
        dis = (result*num)/100
    except:
        dis = 0
    result -= dis
    return result
#function to save product image
def save_pro(image):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(image.filename)
    name = random_hex + f_ext
    image_path = os.path.join(app.root_path, 'static/img/product', name)

    output_size = (350, 350)
    i = Image.open(image)
    i.thumbnail(output_size)
    i.save(image_path)

    return f'/img/product/{name}'
#function to save category image
def save_cat(image):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(image.filename)
    name = random_hex + f_ext
    image_path = os.path.join(app.root_path, 'static/img/category', name)

    output_size = (350,350)
    i = Image.open(image)
    i.thumbnail(output_size)
    i.save(image_path)

    return f'/img/category/{name}'
#function to save category image
def save_sec(image):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(image.filename)
    name = random_hex + f_ext
    image_path = os.path.join(app.root_path, 'static/img/section', name)

    output_size = (350, 350)
    i = Image.open(image)
    i.thumbnail(output_size)
    i.save(image_path)

    return f'/img/section/{name}'

#function to save profile image
def save(profile):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(profile.filename)
    profile_fn = random_hex + f_ext
    image_path = os.path.join(app.root_path, 'static/img/user', profile_fn)

    output_size = (150, 150)
    i = Image.open(profile)
    i.thumbnail(output_size)
    i.save(image_path)

    return profile_fn
#function to delete image
def delete(img):
    path = os.path.abspath(app.root_path)

    image_path = path+'\static'+img
    os.remove(image_path)

#function to get customers details
def user_detail(email):
    users = Users.query.all()
    for data in users:
        if data.email == email:
            return data
    return {'name': 'not existing'}
#function to get cart count
def cart_count():
    try:
        n = Cart.query.filter_by(username=current_user.username).count()
    except:
        n=0
    return n
#function-to-create-graph-----------------------------------------
def sell_graph_p():
    name = 'product.png'
    image_path = os.path.join(app.root_path, 'static/img/report', name)
    data = Order_report.query.all()
    prod, count = [], []
    for row in data:
        prod.append(row.product)
        count.append(row.count)

    # Plot data
    plt.bar(prod, count)
    plt.legend(['1 Unit'])
    plt.xlabel('Product')
    plt.ylabel('Value')
    plt.title('Product and total sells')
    plt.savefig(image_path)
    plt.close()

def sell_graph_c():
    name = 'category.png'
    image_path = os.path.join(app.root_path, 'static/img/report', name)
    data = Order_report.query.all()
    cate = []
    for row in data:
        cate.append(row.category)
    # Plot data
    plt.hist(cate)
    plt.legend(['1 Unit'])
    plt.xlabel('Category')
    plt.ylabel('Value')
    plt.title('Category and total sell count')
    plt.savefig(image_path)
    plt.close()
#routes----------------------------------------------------------------------------
@app.errorhandler(404)
def page_no_found(error):
    return render_template('errorpage.html'), 404
@app.route("/")
def home() :
    n = cart_count()
    cate = Category.query.all()
    return render_template('home.html', n=n, cate=cate)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        data = request.form.get('search')
        data = '%'+data+'%'
        try:
            query = Products.query.filter(or_(
                Products.category.like(data),
                Products.product_name.like(data),
                Products.detail.like(data),
                Products.expiry.like(data),
                Products.section_name.like(data))).all()
            test = query[0].category
        except:
            query = [{'category':'Not Found'}]
        return render_template('product.html', data=query)

@app.route('/section/<string:cate>')
def section_cat(cate):
    try:
        data = Section.query.filter_by(category=cate).all()
        test = data[0].category
    except:
        data = [{'category':'Not Available'}]
    return render_template('section.html', data=data)

@app.route("/product/<string:sec>", methods=['GET', 'POST'])
def product(sec) :
    n = cart_count()
    data = Products.query.filter_by(section_name=sec).all()
    if request.method == 'POST':
        if current_user.is_authenticated :
            username = current_user.username
            name = request.form.get('name')
            price = request.form.get('price')
            stock = request.form.get('stock')
            entry = Cart(product_name=name,stock=int(stock),price=float(price),username=username)
            db.session.add(entry)
            db.session.commit()
            db.session.close()
            flash('Added to cart', 'success')
            return redirect(f'/product/{sec}')
        else :
            return redirect(f'/login.html?next=/product/{sec}')
    try:
        data[0].category
    except:
        data = [{'category':'Not Found'}]
    return render_template('product.html', data=data, n=n)

@app.route("/checkout.html",methods=['GET','POST'])
@login_required
def checkout() :
    n = cart_count()
    code = request.args.get('promo')
    if code :
        p = code_verify(code)
    else :
        p = None
    user = current_user.username
    data = Cart.query.filter_by(username=user)
    t = total(user,p=p)
    if request.method == 'POST':
        l = product_check(user)
        ads1 = request.form.get('address1')
        try:
            ads2 = request.form.get('address2')
        except:
            ads2 = ''
        pin = request.form.get('pincode')
        payment = request.form.get('paymentMethod')
        address = ads1 + ads2 + pin
        entry = Orders(username=user,payment=payment,address=address,product_list=str(l))
        stock_cml(l)
        db.session.add(entry)
        Cart.query.filter_by(username=user).delete()
        db.session.commit()
        db.session.close()
        flash('Order Confirms', 'success')
        return redirect(url_for('home'))
    return render_template('checkout.html', data=data, total=t, promo=p, n=n)
@app.route('/cart', methods=['GET', 'POST'])
def cart_update():
    d = request.args.get('id')
    a = request.args.get('action')
    #print(d,a)
    if request.method == 'POST':
        stock = request.form.get('stock')
        Cart.query.filter_by(id=d).update(dict(stock=stock))
        db.session.commit()
        db.session.close()
        return redirect(url_for('checkout'))
    if a == 'delete':
        Cart.query.filter_by(id=d).delete()
        db.session.commit()
        db.session.close()
        return redirect(url_for('checkout'))
    elif a == 'edit':
        data = Cart.query.filter_by(id=int(d)).first()
        return render_template('cart.html', data=data)
    else:
        redirect(url_for('home'))

@app.route('/promocode', methods=['GET', 'POST'])
def check_promo():
    if request.method == 'POST':
        promo = request.form.get('promo')
        if promo == 'FIRST-15':
            return redirect('/checkout.html?promo=FIRST-15')
        elif promo == 'ALL-5':
            return redirect('/checkout.html?promo=ALL-5')
        elif promo in ['FIRST-30', 'FIRST-45']:
            return redirect(f'/checkout.html?promo={promo}')
        else:
            flash('Invalide promocode, please use ALL-5', 'danger')
    pass

@app.route("/login.html", methods=['GET','POST'])
def login() :
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    elif request.method == 'POST' :
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')
        user = Users.query.filter_by(email=email).first()
        if user and check_password_hash(user.password ,password):
            #print('ok')
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            print(next_page)
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else :
            flash('Login Unsuccessful, Please check the email and password', 'danger')
            return render_template('login.html')
    return render_template('login.html')


@app.route("/signin.html", methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = UserRegistration()
    if request.method == 'POST':
        if form.validate_on_submit():
            name = request.form.get('name')
            password = request.form.get('password')
            pwhash = generate_password_hash(password=password)
            #print(pwhash)------------------------------------------------------------------------
            entry = Users(name=form.name.data, email=form.email.data, username=form.username.data,
                        password=pwhash, address=form.address.data)
            db.session.add(entry)
            db.session.commit()
            db.session.close()
            flash(f'Welcome {name} to Grocery, have a nice day', 'success')
            return redirect(url_for('login'))
        else:
            flash('Please Fill details correctly', 'warning')
            return render_template('signin.html', form=form)
    return render_template('signin.html', form=form)
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))
#reset-password-for-varified-users
@app.route('/user/pswreset', methods=['GET', 'POST'])
def user_pswreset():
    if current_user.is_authenticated:
        form = UserPswResetForm()
        if form.validate_on_submit():
            Users.query.filter_by(email=form.email.data).update(dict(password=form.password.data))
            db.session.commit()
            db.session.close()
            flash('Password Successfully Changed', 'success')
            return redirect(url_for('login'))
        return render_template('user-pswreset.html',form=form)
#forget-password-option
@app.route('/user/forgetpsw', methods=['GET', 'POST'])
def forget_psw():
    form = UserForgetPswForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            password = secrets.token_urlsafe(6)
            pwhash = generate_password_hash(password=password)
            data = Users.query.filter_by(email=form.email.data)
            Users.query.filter_by(email=form.email.data).update(dict(password=pwhash))
            db.session.commit()
            db.session.close()
            msg = Message('Password Reset', sender = 'dhairy.demo.28@gmail.com', recipients = [form.email.data])
            msg.body = f'Password Succssfully changed. Password={password}'
            mail.send(msg)
            flash('New password have been send to mail', 'success')
            return redirect(url_for('login'))
        else:
            flash('Please Enter Right Email', 'warning')
    return render_template('user-forgetpsw.html',form=form)

@app.route("/myprofile.html", methods=['GET', 'POST'])
@login_required
def myaccount() :
    if request.method == 'POST' :
        image = request.files['image_file']
        email = request.form.get('email')
        file_name = save(image)
        Users.query.filter_by(email=email).update(dict(image_file=f'static/img/user/{file_name}'))
        try:
            username = request.form.get('username')
            Users.query.filter_by(email=email).update(dict(username=username))
        except:
            pass
        try:
            address = request.form.get('address')
            Users.query.filter_by(email=email).update(dict(address=address))
        except:
            pass
        db.session.commit()
        db.session.close()
    if isinstance(current_user, Users):
        data = user_detail(current_user.email)
    return render_template('myprofile.html', data=data)

@app.route("/support", methods=['GET', 'POST'])
def support() :
    form = SupportForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            '''Add to the database'''
            name = request.form.get('name')
            email = request.form.get('email')
            message = request.form.get('message')
            entry = Contact(name=name, email=email, message=message)
            db.session.add(entry)
            db.session.commit()
            db.session.close()
            flash('Message send', 'success')
            return redirect(url_for('home'))
        else:
            flash('Please Fill all fields carefully', 'danger')
    return render_template('support.html', form=form)

def order_view(username):
    data = Orders.query.filter_by(username=username).all()
    '''0:id, 1:product_list, 2:order_time, 3:payment, 4:address'''
    #product_list: [[product_name,quantity(stock),price,unit],[....],...,[....]]
    result = list()
    for da in data:
        pdl = literal_eval(da.product_list)
        buffer = [da.id, pdl, da.order_time, da.payment, da.address]
        result.append(buffer)
    return result

@app.route("/orders.html")
@login_required
def orders() :
    user = current_user.username
    data = order_view(user)
    return render_template('orders.html', data=data)

@app.route("/today.html")
def today():
    return render_template('today.html')

#admin-route--------------------------------------------------------------------------
@app.route("/admin")
def admin():
    return render_template('admin.html',log=session)

#-----------------------admin-login---------------------------------------------------
@app.route("/admin/login", methods=['GET','POST'])
def admin_log():
    form = AdminForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(adminUser=form.username.data).first()
        if admin and check_password_hash(admin.adminPass, form.password.data):
            session['admin'] = True
            session['id'] = admin.id
            session['name'] = admin.adminUser
            flash('Logged-in', 'success')
            return redirect(url_for('admin'))
        else :
            flash(f'Login Unsuccessful. Please check username or password!', 'danger')
    return render_template('adminlog.html', form=form, log=session)

@app.route('/admin/logout')
def adminlogout():
    session.pop('admin', None)
    session.pop('id', None)
    session.pop('name', None)
    flash('Successfully logout','success')
    return redirect(url_for('admin_log'))
#--------------------------------------------------------------------------------------

#-----------------------store-manager-login--------------------------------------------
@app.route('/admin/manager/login', methods=['GET', 'POST'])
def manager_login():
    form = ManagerForm()
    if form.validate_on_submit():
        manager = Store_manager.query.filter_by(username=form.username.data).first()
        if manager and check_password_hash(manager.password, form.password.data):
            session['manager'] = True
            session['name'] = manager.name
            session['status'] = manager.status
            flash('Login successfully','success')
            return redirect(url_for('admin'))
        else :
            flash('Please enter correct username and password', 'warning')
            return redirect('/admin/manager/login')
    return render_template('manager-login.html', form=form, log=session)
@app.route('/admin/manager/signin', methods=['GET','POST'])
def manager_signin():
    form = ManagerRegisterForm()
    if form.validate_on_submit():
        password = request.form.get('password')
        pwhash = generate_password_hash(password=password)
        entry = Store_manager(name=form.name.data,username=form.username.data,password=pwhash)
        db.session.add(entry)
        db.session.commit()
        db.session.close()
        flash('Registration successful waiting for admin varification','success')
        return redirect(url_for('manager_login'))
    return render_template('manager-signin.html', log=session, form=form)
@app.route('/admin/manager/resetpsw', methods=['GET', 'POST'])
def manager_psw():
    form = ManagerPswResetFrom()
    if form.validate_on_submit():
        mana = Store_manager.query.filter_by(username=form.username.data).first()
        if mana :
            password = request.form.get('password')
            pwhash = generate_password_hash(password=password)
            Store_manager.query.filter_by(username=form.username.data).update(dict(password=pwhash,status=0))
            db.session.commit()
            db.session.close()
            flash('Waiting for Admin approval','warning')
            return redirect(url_for('admin'))
        else:
            flash('Enter correct username','danger')
            return redirect(url_for('manager_psw'))
    return render_template('manager-pswreset.html', log=session ,form=form)
@app.route('/manager/logout')
def manager_logout():
    session.pop('manager',None)
    session.pop('name',None)
    session.pop('status',None)
    flash('Successfully logout','success')
    return redirect(url_for('admin'))
#-------------------------------------------------------------------------------------
#support
@app.route("/admin/support", methods=['GET','POST'])
def page():
    if 'admin' in session or 'manager' in session:
        reports = Report.query.all()
        contacts = Contact.query.all()
        if(request.method=='POST'):
            '''Add to the database'''
            remark = request.form.get('remark')
            status = request.form.get('status', type=int)
            name =request.form.get('name')
            entry = Report(remark=remark, status=status, name=name)
            db.session.add(entry)
            db.session.commit()
            db.session.close()
            return redirect(url_for('admin'))
        return render_template('/admin-support.html', reports=reports, contacts=contacts, log=session)
    else:
        return redirect(url_for('admin'))

#------------admin-dashbord-------------------------------------
@app.route('/admin/dashboard')
def view():
    if 'admin' in session:
        sell_graph_p()
        sell_graph_c()
        manager = Store_manager.query.all()
        cate = Approvels.query.all()
        return render_template('admin-dashboard.html', log=session, pro=manager, cate=cate)
    elif 'manager' in session:
        flash('Only Admin can view this section', 'danger')
        return redirect(url_for('admin'))
    else :
        flash('Authorization required', 'warning')
        return redirect(url_for('admin_log'))
#approve store manager
@app.route('/admin/approve/store-manager/<int:id>', methods=['GET','POST'])
def approve(id):
    if 'admin' in session:
        act = request.args.get('act')
        if act == 'accept':
            Store_manager.query.filter_by(id=id).update(dict(status=1))
            db.session.commit()
            db.session.close()
            flash('Approved Successfully', 'success')
            return redirect('/admin/dashboard')
        if act == 'decline':
            Store_manager.query.filter_by(id=id).update(dict(status=0))
            db.session.commit()
            db.session.close()
            flash('Permissions decline', 'success')
            return redirect('/admin/dashboard')
    else:
        flash('Authorization required','warning')
        return redirect('admin_log')
#approve-delete-requests------admin-only-----------------------------
@app.route('/admin/approve/delete-req/<string:type>/<string:name>')
def delete_approve(type,name):
    if 'admin' in session:
        act = request.args.get('act')
        id = request.args.get('id')
        if act == 'accept':
            Approvels.query.filter_by(id=id).update(dict(respond_status='Approve',respond_time=datetime.now()))
            db.session.commit()
            db.session.close()
            if type == 'category':
                return redirect(f'/admin/category/delete/{name}')
            if type == 'product':
                daa = Products.query.filter_by(product_name=name).first()
                category = daa.category
                return redirect(f'/admin/product/delete/{name}/{category}')
            if type == 'section':
                return redirect(f'/admin/section/delete/{name}')
        if act == 'decline':
            Approvels.query.filter_by(id=id).update(dict(respond_status='Decline',respond_time=datetime.now()))
            db.session.commit()
            db.session.close()
            return redirect(url_for('view'))
        return redirect(url_for('admin'))
    else:
        flash('admin login required','danger')
        return redirect(url_for('admin_log'))
#store-manager-------deletion-request----------------------------
@app.route('/admin/delete-request/<string:types>/<string:name>')
def manager_req(types,name):
    if 'manager' in session and session['status'] == 1:
        by = request.args.get('by')
        entry = Approvels(type=types,name=name,manager_name=by)
        db.session.add(entry)
        db.session.commit()
        db.session.close()
        #edit-required----------
        flash('Successfully requested', 'success')
        return redirect(url_for('add_cate'))
#-----------------------------------------------------------------
@app.route('/admin/category', methods=['GET','POST'])
def add_cate():
    if 'admin' in session or ('manager' in session and session['status']==1):
        data = Category.query.all()
        form = CategoryForm()
        if request.method == 'POST':
            category_name = request.form.get('name')
            cat_detail = request.form.get('detail')
            img = request.files['image']
            file_name = save_cat(image=img)
            entry = Category(name=category_name,image=file_name,details=cat_detail)
            db.session.add(entry)
            db.session.commit()
            db.session.close()
            flash(f'Category successfully updated', 'success')
            return redirect(url_for('add_cate'))
        return render_template('admin-category.html', form=form, log=session, data=data)
    else:
        flash('Authorization required','danger')
        return redirect(url_for('admin'))
#-----------section-add-edit-------------------------------------------------
@app.route('/admin/section/<string:cate>', methods=['GET', 'POST'])
def add_sec(cate):
    if 'admin' in session or ('manager' in session and session['status']==1):
        form = SectionFrom()
        data = Section.query.filter_by(category=cate)
        if request.method == 'POST':
            if form.validate_on_submit():
                category = cate
                section_name = form.name.data
                try:
                    image = form.image.data
                    image_path = save_sec(image=image)
                except:
                    image_path = '/img/section/default.png'
                entry = Section(category=category,section_name=section_name,image=image_path)
                db.session.add(entry)
                db.session.commit()
                db.session.close()
                flash('Section successfully added', 'success')
                return redirect(f'/admin/section/{cate}')
            else:
                flash('Please fill the form correctly', 'success')
                return redirect(f'/admin/section/{cate}')
        return render_template('admin-section.html', data=data, form=form, log=session)
    else:
        flash('Authorization required','danger')
        return redirect(url_for('admin-section.html'))
#edit section admin or store manager
@app.route('/admin/section/edit/<string:sec>',methods=['GET','POST'])
def edit_sec(sec):
    if 'admin' in session or ('manager' in session and session['status']==1):
        data = Section.query.filter_by(section_name=sec).first()
        cate = data.category
        if request.method == 'POST':
            section_name = request.form.get('name')
            category = request.form.get('category')
            try:
                img = request.files['image']
                try:
                    delete(data.image)
                except:
                    pass
                file_name = save_cat(img)
                Section.query.filter_by(section_name=sec).update(dict(image=file_name))
            except:
                pass
            if section_name:
                Section.query.filter_by(section_name=sec).update(dict(section_name=section_name))
            if category:
                Section.query.filter_by(section_name=sec).update(dict(category=category))
            db.session.commit()
            db.session.close()
            flash('Successfully Edited', 'success')
            return redirect(f'/admin/section/{cate}')
        return render_template('admin-section-edit.html', log=session, data=data)
    else:
        flash('Authorization required','warning')
        return redirect(url_for('admin'))
#------------------------------------------------------------------------------------------------

@app.route('/admin/products/<string:sec>', methods=['GET', 'POST'])
def add_prod(sec):
    if 'admin' in session or ('manager' in session and session['status']==1):
        form = ProductForm()
        if form.validate_on_submit():
            da = Section.query.filter_by(section_name=sec).first()
            product_name = form.name.data
            product_d = form.detail.data
            price = form.price.data
            expiry = form.expiry.data
            stock = form.stock.data
            unit = form.unit.data
            image = request.files['image']
            f_name = save_pro(image)
            entry = Products(product_name=product_name,detail=product_d,category=da.category,price=price,image=f_name,stock=stock,expiry=expiry,unit=unit, section_name=sec)
            db.session.add(entry)
            db.session.commit()
            db.session.close()
            flash(f'Product is added for {form.name.data}!', 'success')
            return redirect(f'/admin/products/view/{sec}')
        return render_template('admin-product.html', form=form, log=session)
    else:
        flash('Authorization required','danger')
        return redirect(url_for('admin'))

@app.route('/admin/products/view/<string:name>', methods=['GET','POST'])
def method_name(name):
    if 'admin' in session or ('manager' in session and session['status']==1):
        form = ProductForm()
        data = Products.query.filter_by(section_name=name)
        if form.validate_on_submit():
            da = Section.query.filter_by(section_name=name).first()
            product_name = form.name.data
            product_d = form.detail.data
            price = form.price.data
            expiry = form.expiry.data
            stock = form.stock.data
            unit = form.unit.data
            image = request.files['image']
            f_name = save_pro(image)
            entry = Products(product_name=product_name,detail=product_d,category=da.category,price=price,image=f_name,stock=stock,expiry=expiry,unit=unit, section_name=name)
            db.session.add(entry)
            db.session.commit()
            db.session.close()
            flash(f'Product is added for {form.name.data}!', 'success')
            return redirect(f'/admin/products/view/{name}')
        return render_template('admin-product-view.html', data=data, form=form, a=name, log=session)
    else:
        flash('Authorization required','danger')
        return redirect(url_for('admin'))
@app.route('/admin/product/edit/<string:a>', methods=['GET','POST'])
def edit_product(a):
    if 'admin' in session or ('manager' in session and session['status']==1):
        data = Products.query.filter_by(product_name=a).first()
        sec = data.section_name
        #print(a)
        if request.method == 'POST':
            product_name = request.form.get('name')
            detail = request.form.get('details')
            price = request.form.get('price')
            stock = request.form.get('stock')
            expiry = request.form.get('expiry')
            unit = request.form.get('unit')
            try:
                img = request.files['image']
                file_name = save_pro(img)
                Products.query.filter_by(product_name=a).update(dict(image=file_name))
            except:
                pass
            if product_name:
                Products.query.filter_by(product_name=a).update(dict(product_name=product_name))
            if detail:
                Products.query.filter_by(product_name=a).update(dict(detail=detail))
            if price:
                Products.query.filter_by(product_name=a).update(dict(price=price))
            if stock:
                Products.query.filter_by(product_name=a).update(dict(stock=stock))
            if expiry:
                Products.query.filter_by(product_name=a).update(dict(expiry=expiry))
            if unit:
                Products.query.filter_by(product_name=a).update(dict(unit=unit))
            db.session.commit()
            db.session.close()
            flash('Successfully updated', 'success')
            return redirect(f'/admin/products/view/{sec}')
        return render_template('admin-edit.html', data=data, log=session)
    else:
        flash('Authorization required','danger')
        return redirect(url_for('admin_log'))
@app.route('/product/all')
def show_all():
    if 'admin' in session or 'manager' in session:
        data = Products.query.all()
        return render_template('admin-product-view.html', data=data, log=session)
    else:
        flash('Authorization required','danger')
        return redirect(url_for('admin'))

#delete-----------admin-can-only-delete--------------manager-request---------------------
#product delete
@app.route('/admin/product/delete/<string:a>/<string:b>')
def delete_product(a,b):
    if 'admin' in session or ('manager' in session and session['status']==1):
        if 'admin' in session:
            d = Products.query.filter_by(product_name=a).first()
            Products.query.filter_by(product_name=a).delete()
            delete(d.image)
            db.session.commit()
            db.session.close()
            flash('Deleted successfully', 'success')
            return redirect(f'/admin/products/view/{b}')
        elif 'manager' in session:
            flash('Requesting admin', 'success')
            return redirect(f"/admin/delete-request/product/{a}?by={session['name']}")
    else:
        flash('Authorization required','warning')
        return redirect(url_for('admin'))
@app.route('/admin/category/delete/<string:a>')
def delete_cat(a):
    if 'admin' in session or ('manager' in session and session['status']==1):
        if 'admin' in session:
            cat = Category.query.filter_by(name=a).first()
            data = Products.query.filter_by(category=a)
            Category.query.filter_by(name=a).delete()
            Products.query.filter_by(category=a).delete()
            Section.query.filter_by(category=a).delete()
            try:
                delete(cat.image)
                for da in data:
                    delete(da.image)
            except:
                pass
            db.session.commit()
            db.session.close()
            flash('Successfully deleted Category','success')
            return redirect(url_for('add_cate'))
        elif 'manager' in session:
            flash('Requesting admin', 'success')
            return redirect(f"/admin/delete-request/category/{a}?by={session['name']}")
    else:
        flash('Authorization required','warning')
        return redirect(url_for('admin'))
@app.route('/admin/section/delete/<string:sec>')
def delete_sec(sec):
    if 'admin' in session or ('manager' in session and session['status']==1):
        if 'admin' in session:
            section = Section.query.filter_by(section_name=sec).first()
            data = Products.query.filter_by(section_name=sec).all()
            try:
                if 'default' not in section.image:
                    delete(section.image)
                for da in data:
                    if 'default' not in da.image:
                        delete(da.image)
            except:
                pass
            Section.query.filter_by(section_name=sec).delete()
            Products.query.filter_by(section_name=sec).delete()
            db.session.commit()
            db.session.close()
            flash('Successfully deleted Section','success')
            return redirect(url_for('add_cate'))
        elif 'manager' in session:
            flash('Requesting admin', 'success')
            return redirect(f"/admin/delete-request/section/{sec}?by={session['name']}")
    else:
        flash('Authorization required','warning')
        return redirect(url_for('admin'))
#---------------------------------------------------------------------

#edit category admin or store manager
@app.route('/admin/category/edit/<string:a>',methods=['GET','POST'])
def edit_cat(a):
    if 'admin' in session or ('manager' in session and session['status']==1):
        data = Category.query.filter_by(name=a).first()
        if request.method == 'POST':
            name = request.form.get('name')
            details = request.form.get('details')
            try:
                img = request.files['image']
                try:
                    delete(data.image)
                except:
                    pass
                file_name = save_cat(img)
                Category.query.filter_by(name=a).update(dict(image=file_name))
            except:
                pass
            if name:
                Category.query.filter_by(name=a).update(dict(name=name))
            if details:
                Category.query.filter_by(name=a).update(dict(details=details))
            db.session.commit()
            db.session.close()
            flash('Successfully Edited', 'success')
            return redirect(url_for('add_cate'))
        return render_template('admin-category-edit.html', log=session, data=data)
    else:
        flash('Authorization required','warning')
        return redirect(url_for('admin'))
    
@app.route('/admin/search', methods=['GET', 'POST'])
def admin_search():
    if 'admin' in session or 'manager' in session:
        if request.method == 'POST':
            data = request.form.get('search')
            data = '%'+data+'%'
            try:
                query = Products.query.filter(or_(
                    Products.category.like(data),
                    Products.product_name.like(data),
                    Products.detail.like(data),
                    Products.expiry.like(data),
                    Products.section_name.like(data))).all()
                test = query[0].category
            except:
                query = [{'category':'Not Found'}]
            return render_template('admin-product-view.html', data=query, log=session)
        return redirect(url_for('admin'))
    return redirect(url_for('admin'))
#---------------------api-----------------------------------------------------------------------------------------
from werkzeug.exceptions import HTTPException
from tinydb import TinyDB, Query
User_api = Query()
tdb = TinyDB("api_user.json")

@auth.verify_password
def verify(username, password):
    user = tdb.get(User_api.username==username)
    if user and check_password_hash(user["password"], password):
        return user
@auth.get_user_roles
def get_user_roles(user):
    return user["role"]
@auth.error_handler
def auth_error(status):
    return "Access Denied", status

class MyDateFormat(fields.Raw):
    def format(self, value):
        return value.strftime('%Y-%m-%d')

#common errors
class NotFoundError(HTTPException):
    def __init__(self, status_code):
        self.response = make_response('', status_code)

class InternalServerError(HTTPException):
    def __init__(self, status_code):
        self.response = make_response('', status_code)

class ExistsError(HTTPException):
    def __init__(self, status_code):
        self.response = make_response('', status_code)

class NotExistsError(HTTPException):
    def __init__(self, status_code):
        self.response = make_response('', status_code)

class BuisnessValidationError(HTTPException):
    def __init__(self, status_code, error_code, error_message):
        message={"error_code": error_code, "error_message": error_message}
        self.response = make_response(json.dumps(message), status_code)

#productAPI

output_product = {
    "id" : fields.Integer,
    "product_name": fields.String,
    "category": fields.String,
    "detail": fields.String,
    "price": fields.Integer,
    "stock": fields.Integer,
    "unit": fields.String,
    "expiry": MyDateFormat,
    "section_name": fields.String,
    "image": fields.String
}

product_parser = reqparse.RequestParser()
product_parser.add_argument("product_name")
product_parser.add_argument("detail")
product_parser.add_argument("category")
product_parser.add_argument("price", type=int)
product_parser.add_argument("stock", type=int)
product_parser.add_argument("expiry", type=inputs.date)
product_parser.add_argument("unit")
product_parser.add_argument("section_name")
product_parser.add_argument("image")

class ProductAPI(Resource):
    #url: /api/product/<category>?sec=<section_name>
    @marshal_with(output_product)
    def get(self, category):
        try:
            sec = request.args.get('sec')
            if sec is None:
                product_obj = Products.query.filter_by(category=category).all()
            else:  
                product_obj = Products.query.filter(and_(Products.category == category,
                                                    Products.section_name == sec)).all()
            if product_obj:
                return  product_obj
            else:
                raise NotFoundError(status_code=404)
        except NotFoundError as nfe:
            raise nfe
        except Exception as e:
            raise InternalServerError(status_code=500)

#url: /api/product?id=<int>
    @marshal_with(output_product) 
    @auth.login_required(role=['admin', 'manager'])
    def put(self):
        try:
            id = request.args.get('id')
            args = product_parser.parse_args()
            product_name = args.get("product_name",None)
            category1 = args.get("category",None)
            detail = args.get("detail",None)
            price = args.get("price",None)
            stock = args.get("stock",None)
            expiry = args.get("expiry",None)
            unit = args.get("unit",None)
            section_name = args.get("section_name",None)
            image = args.get("image",None)
            if product_name is None:
                raise BuisnessValidationError(status_code=400, error_code="PROD404", error_message="Product name is required")
            if category1 is None:
                raise BuisnessValidationError(status_code=400, error_code="CATE404", error_message="Category is required")
            product_obj = Products.query.filter_by(id=id).first()
            if product_obj:
                product_obj.product_name= product_name
                product_obj.detail=detail
                product_obj.category=category1
                product_obj.price = price
                product_obj.image = image
                product_obj.stock = stock
                product_obj.expiry = expiry
                product_obj.unit = unit
                product_obj.section_name = section_name
                db.session.commit()
                updated_course = Products.query.filter_by(product_name=product_name).first()
                return updated_course, 200              
            else:
                raise NotExistsError(status_code=404)

        except BuisnessValidationError as bve:
            raise bve
        except NotExistsError as nee:
            raise nee
        except Exception as e:
            raise InternalServerError(status_code=500)

#url: /api/product        
    @marshal_with(output_product)
    @auth.login_required(role=['admin', 'manager'])
    def post(self):
        try:
            args = product_parser.parse_args()
            product_name = args.get("product_name",None)
            category1 = args.get("category",None)
            detail = args.get("detail",None)
            price = args.get("price",None)
            stock = args.get("stock",None)
            expiry = args.get("expiry",None)
            unit = args.get("unit",None)
            section_name = args.get("section_name",None)
            image = args.get("image",None)
            if product_name is None:
                raise BuisnessValidationError(status_code=400, error_code="PROD001", error_message="Product Name is required")
            if category1 is None:
                raise BuisnessValidationError(status_code=400, error_code="CATE001", error_message="Category is required")
            if price is None or stock is None:
                raise BuisnessValidationError(status_code=400, error_code="MISC001", error_message="price and stock is required")
            product_obj = Products.query.filter_by(product_name=product_name).first()
            if product_obj:
                raise ExistsError(status_code=409)
            else:
                new_product = Products(product_name=product_name, detail=detail, category=category1, price=price, image=image, stock=stock, expiry=expiry, unit=unit, section_name=section_name)
                db.session.add(new_product)
                db.session.commit()
                db.session.close()
                new_product = Products.query.filter_by(product_name=product_name).first()
                return new_product, 201
        except BuisnessValidationError as bve:
            raise bve
        except ExistsError as ee:
            raise ee
        except Exception as e:
            raise InternalServerError(status_code=500)

#url: /api/product?id=<int>        
    @auth.login_required(role='admin')
    def delete(self):
        try:
            id = request.args.get('id')
            product_obj = Products.query.get(int(id))
            if product_obj:
                db.session.delete(product_obj)
                db.session.commit()
                return "", 200
            else:
                raise NotFoundError(status_code=404)
        except NotFoundError as nfe:
            raise nfe
        except Exception as e:
            raise InternalServerError(status_code=500)
api.add_resource(ProductAPI, "/api/product", "/api/product/<category>")

#categoryAPI
output_category = {
    "id": fields.Integer,
    "name": fields.String,
    "details": fields.String
}

class categoryAPI(Resource):
    @marshal_with(output_category)
    def get(self):
        try:
            category_obj = Category.query.all()
            if category_obj:
                return category_obj
            else:
                raise NotFoundError(status_code=404)
        except NotFoundError as nfe:
                raise nfe
        except Exception as e:
                raise InternalServerError(status_code=500)
api.add_resource(categoryAPI, "/api/category")

#sectionAPI
output_section = {
    "id": fields.Integer,
    "category": fields.String,
    "section_name": fields.String,
    "image": fields.String
}

section_parser =reqparse.RequestParser()
section_parser.add_argument("category")
section_parser.add_argument("section_name")
section_parser.add_argument("image")

class sectionAPI(Resource):
    #url: /api/section/<string:category>
    @marshal_with(output_section)
    def get(self,category):
        try:
            section_obj = Section.query.filter_by(category=category).all()
            if section_obj:
                return  section_obj
            else:
                raise NotFoundError(status_code=404)
        except NotFoundError as nfe:
            raise nfe
        except Exception as e:
            raise InternalServerError(status_code=500)
        
    #url: /api/section?id=<int>    
    @marshal_with(output_section)
    @auth.login_required(role=['admin', 'manager'])
    def put(self):
        try:
            id = request.args.get('id')
            args = section_parser.parse_args()
            section_name = args.get("section_name",None)
            category = args.get("category",None)
            image = args.get("image",None)
            image_path = save_sec(image)
            if section_name is None:
                raise BuisnessValidationError(status_code=400, error_code="SECTION001", error_message="Section Name is required")
            if category is None:
                raise BuisnessValidationError(status_code=400, error_code="CATE002", error_message="Category is required")
            section_obj = Section.query.filter_by(id=id).first()
            if section_obj:
                section_obj.section_name=section_name
                section_obj.category=category
                section_obj.image=image_path
                db.session.commit()
                updated_section = Section.query.filter_by(id=id).first()
                return updated_section, 200              
            else:
                raise NotExistsError(status_code=404)

        except BuisnessValidationError as bve:
            raise bve
        except NotExistsError as nee:
            raise nee
        except Exception as e:
            raise InternalServerError(status_code=500)

    #url: /api/section
    @marshal_with(output_section)
    @auth.login_required(role=['admin', 'manager'])
    def post(self):
        try:
            args = section_parser.parse_args()
            section_name = args.get("section_name",None)
            category = args.get("category",None)
            image = args.get("image",None)
            if section_name is None:
                raise BuisnessValidationError(status_code=400, error_code="SECTION001", error_message="Secton Name is required")
            if category is None:
                raise BuisnessValidationError(status_code=400, error_code="CATE002", error_message="Category is required")
            section_obj = Section.query.filter_by(section_name=section_name).first()
            if section_obj:
                raise ExistsError(status_code=409)
            else:
                new_course = Section(section_name=section_name, category=category, image=image)
                db.session.add(new_course)
                db.session.commit()
                new_course = Section.query.filter_by(section_name=section_name).first()
                return new_course, 201
        except BuisnessValidationError as bve:
            raise bve
        except ExistsError as ee:
            raise ee
        except Exception as e:
            raise InternalServerError(status_code=500)
    
    #url: /api/section?id=<int>
    @auth.login_required(role='admin')
    def delete(self):
        try:
            id = request.args.get('id')
            section_obj = Section.query.filter_by(id=id).first()
            if section_obj:
                product_obj=Products.query.filter_by(section_name=section_obj.section_name).first()
                while product_obj:
                    db.session.delete(product_obj)
                    db.session.commit()
                    product_obj=Products.query.filter_by(section_name=section_obj.section_name).first()
                db.session.delete(section_obj)
                db.session.commit()
                return "", 200
            else:
                raise NotFoundError(status_code=404)
        except NotFoundError as nfe:
            raise nfe
        except Exception as e:
           raise InternalServerError(status_code=500)
api.add_resource(sectionAPI, "/api/section", "/api/section/<string:category>")