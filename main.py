import json
import re
from flask_mail import Mail
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import random
import pickle
from sklearn.neighbors import NearestNeighbors


local_server = True
if(local_server):
    with open('config.json', 'r') as c:
        params = json.load(c)["params"]
else:
    with open('/home/man787878787/mysite/config.json', 'r') as c:
        params = json.load(c)["params"]

app = Flask(__name__)
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)
mail = Mail(app)
app.secret_key = '12ka4'
if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']

db = SQLAlchemy(app)

class Product_details(db.Model):
    __tablename__ = 'product_details'
    Product_id = db.Column(db.BigInteger, primary_key=True)
    product_name = db.Column(db.Text)
    product_rating = db.Column(db.Float)
    product_prize = db.Column(db.BigInteger)
    image_link = db.Column(db.Text)
    product_link = db.Column(db.Text)
    product_category = db.Column(db.Text)
    product_features = db.Column(db.Text)
    slug = db.Column(db.Text)

class Register_info(db.Model):
    __tablename__ = 'register_info'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    password = db.Column(db.Text)
    email = db.Column(db.Text)
    phone_number = db.Column(db.Text)
    address = db.Column(db.Text)


class User_search(db.Model):
    __tablename__ = 'user_search'
    search_no = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer)
    query = db.Column(db.Text)
    product_id = db.Column(db.Integer)
    product_rating = db.Column(db.Float)

@app.route("/",methods=['GET'])

def home():
    products = Product_details.query.all()
    top = Product_details.query.filter_by(product_rating=5).order_by(db.func.random()).all()
    mobile = Product_details.query.filter_by(product_category='mobiles_and_assessories').order_by(db.func.random()).all()
    computers = Product_details.query.filter_by(product_category='computers').order_by(db.func.random()).all()
    audio = Product_details.query.filter_by(product_category='audio_video').order_by(db.func.random()).all()
    camera = Product_details.query.filter_by(product_category='camera_and_accesories').order_by(db.func.random()).all()
    home = Product_details.query.filter_by(product_category='home_entertainment').order_by(db.func.random()).all()

    return render_template('index.html',products=products,top=top,audio=audio,mobile=mobile,computers=computers,camera=camera,home=home)

@app.route("/<string:slug>",methods=['GET'])
def product(slug):
    print(slug)
    product = Product_details.query.filter_by(Product_id=slug).first()
    a=[]
    if product is not None:
        for i in eval(product.product_features):
            if(i[0]!='not found'):
                a.append(i)
    image_names = pickle.load(open('image_names.pkl', 'rb'))
    feature_list = pickle.load(open('feature_list.pkl', 'rb'))
    fname = pickle.load(open('fname.pkl', 'rb'))
    l = []
    for i in fname:
        # Split the URL by '/' and get the last element
        image_name = i.split('/')[-1]
        # Remove the query string parameter from the image name
        image_name = image_name.split('?')[0]
        # Append the image name to the list
        l.append(image_name)
    ida= product.Product_id
    iname = image_names[ida]
    findex=l.index(iname)
    neighbors = NearestNeighbors(n_neighbors=7, metric='cosine')
    neighbors.fit(feature_list)
    link_no = findex
    distances, indices = neighbors.kneighbors([feature_list[link_no]])
    indices = indices.flatten()
    ids_of_suggested_products=[]
    for i in indices[1:7]:
        ids_of_suggested_products.append(image_names.index(l[i]))
    home=[]
    for i in ids_of_suggested_products:
        home.append(Product_details.query.filter_by(Product_id=i).first())
    return render_template('product.html',product=product,a=a,home=home)

@app.route("/next")
def next():
    # get the current page number from the query string
    page_num = int(request.args.get('page', 1))
    # calculate the page number for the next page

    next_page_num = page_num + 1
    # redirect to the next page
    return redirect(url_for('search', page=next_page_num,query =request.args.get('query')))

@app.route("/prev")
def prev():
    # get the current page number from the query string
    page_num = int(request.args.get('page', 1))
    # calculate the page number for the previous page
    prev_page_num = page_num - 1
    # redirect to the previous page
    return redirect(url_for('search', page=prev_page_num,query=request.args.get('query')))

@app.route("/login",methods=['GET','POST'])
def login():
    msg=''
    if (request.method == 'POST' and  'password' in request.form and  'email' in request.form):
        email = request.form.get('email')
        password = request.form.get('password')
        existing_user = Register_info.query.filter_by(email=email, password=password).first()
        if existing_user:
            msg='You have succesfully login'
            session['authenticated'] = True  # Set a session variable to indicate that the user is authenticated
            session['user_id'] = existing_user.user_id
            session['name'] = existing_user.name   # Store the user ID in the session
            session.permanent = True  # Make the session permanent to avoid automatic logout
            return redirect(url_for('home'))
        elif Register_info.query.filter_by(email=email, password=password).first():
            msg='Enter valid password'
        else:
            msg = 'Enter valid credentials'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('login.html',msg=msg)
@app.route("/forget",methods=['GET','POST'])


def forget():
    msg=''
    kuchbhi = 1
    kaik = False
    if (request.method == 'POST' and 'email' in request.form):
        email = request.form.get('email')
        session['email'] = email
        existing_user = Register_info.query.filter_by(email=email).first()
        if existing_user == False:
            msg = '!Please sign up first'
            return render_template('forget.html', kuchbhi=kuchbhi, kaik=kaik, msg=msg)
        else:
            ot = random.randint(000000, 999999)
            ot = str(ot)
            session['ot'] = ot
            message = " your otp is" + ot + "\n"
            mail.send_message('For otp', sender=params['gmail-user'], recipients=[email],body=message)
            kuchbhi = 0
            return render_template('forget.html', kuchbhi=kuchbhi, kaik=kaik, msg=msg)
        return render_template('forget.html',kuchbhi=kuchbhi,kaik=kaik,msg=msg)
    if (request.method == 'POST' and 'otp' in request.form):
        otp = request.form.get('otp')
        print(otp,session['ot'])
        if otp == session['ot']:
            kuchbhi=2
            kaik=True
            return render_template('forget.html',kuchbhi=kuchbhi,kaik=kaik,msg=msg)
        else:
            msg = "Enter your otp was wrong"
            kuchbhi=1
            return render_template('forget.html',kuchbhi=kuchbhi,kaik=kaik,msg=msg)
    if (request.method == 'POST' and 'password' in request.form and 'cpassword' in request.form):
        password = request.form.get('password')
        cpassword = request.form.get('cpassword')
        if password == cpassword:
            Register_info.query.filter_by(email=session['email']).update(dict(password=request.form.get('password')))
            db.session.commit()
            return redirect(url_for('login'))
        else:
            msg='Enter right password'
            return render_template('forget.html', kuchbhi=kuchbhi, kaik=kaik, msg=msg)
    return render_template('forget.html',kuchbhi=kuchbhi,kaik = kaik,msg=msg)
@app.route("/register",methods=['GET','POST'])
def register():
    msg=''
    if(request.method=='POST' and 'name' in request.form and 'password' in request.form and 'address' in request.form and 'email' in request.form):
        name = request.form.get('name')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        password = request.form.get('password')
        address = request.form.get('address')
        existing_user = db.session.execute(text(f"SELECT * FROM register_info WHERE email='{email}' OR phone_number='{phone_number}'")).fetchone()
        if existing_user:
            msg='user already exist please login'
        elif len(phone_number)>10:
            msg='please enter valid phone number'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', name):
            msg = 'Username must contain only characters and numbers !'
        elif not name or not password or not email or not address:
            msg = 'Please fill out the form !'
        else:
            entry = Register_info(name=name, password=password, email=email, phone_number=phone_number, address=address)
            db.session.add(entry)
            db.session.commit()
            message = "Hi "+name+"\n Thank you for sign up into our application "+"\n Happy E shoping"
            mail.send_message('Welcome to eshop ', sender=params['gmail-user'], recipients=[email],
                              body=message + "\n")
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html',msg=msg)
@app.route("/contact",methods=['GET','POST'])
def contact():
    if (request.method == 'POST' and 'name' in request.form and 'phone_number' in request.form and 'email' in request.form):
        name = request.form.get('name')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        message = request.form.get('message')
        mail.send_message('New message from '+name ,sender = email,recipients = [params['gmail-user']],body = message + "\n" +phone_number)
    return render_template('contact.html',params=params)

@app.route("/profile",methods=['GET','POST'])
def profile():
    pro_d = db.session.execute(text(f"SELECT * FROM register_info WHERE user_id='{session['user_id']}'")).all()
    if len(pro_d)==0:
        session['authenticated'] = False
        return redirect(url_for('login'))
    if (request.method == 'POST'):
        session['authenticated'] = False
        return redirect(url_for('login'))
    return render_template('profile.html',pro_d=pro_d)
@app.route('/search', methods=['GET','POST'])
def search():
    page_num = int(request.args.get('page', 1))
    products = db.session.execute(text(f"SELECT * FROM product_details ;")).all()
    if page_num==1:
        query = request.args.get('query').lower()
        pro_do = []
        name = []
        pro_d = []
        for i in range(len(products)):
            name.append(products[i][1].lower())
        for i in range(len(name)):
            if query in products[i][6] or query in products[i][7] or query in name[i]:
                pro_do.append(products[i])
        # if len(pro_do)>10:
        #     for i in pro_do[:10]:
        #         entry = User_search(user_id=session['user_id'], product_id=i[0], query=query, product_rating = i[2])
        #         db.session.add(entry)
        #         db.session.commit()
        # elif len(pro_do)<=30:
        #     for i in pro_do:
        #         entry = User_search(user_id=session['user_id'], product_id=i[0], query=query, product_rating = i[2])
        #         db.session.add(entry)
        #         db.session.commit()
    else:
        query = request.args.get('query').lower()
        pro_do = []
        name = []
        pro_d = []
        for i in range(len(products)):
            name.append(products[i][1].lower())
        for i in range(len(name)):
            if query in products[i][6] or query in products[i][7] or query in name[i]:
                pro_do.append(products[i])
    page_num = int(request.args.get('page', 1))
    per_page = 12
    offset = (page_num - 1) * per_page
    total_products = len(pro_do)
    total_pages = int(total_products / per_page) + (total_products % per_page > 0)
    if page_num!=total_pages:
        if total_products>0:
            for i in range(offset,offset+per_page):
                pro_d.append(pro_do[i])
    else:
        if total_products>0:
            for i in range(offset,offset+(total_products-(per_page*(page_num-1)))):
                pro_d.append(pro_do[i])
    return render_template('search.html',pro_d=pro_d,query=query,page_num=page_num, total_pages=total_pages)
if local_server:
    app.run(debug=True)