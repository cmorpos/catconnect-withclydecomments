from catconnect import app
from flask import render_template, redirect, url_for, flash, request
from catconnect.models import Item, User, Cats
from catconnect.forms import RegisterForm, LoginForm, CatAdoptForm, CancelAdoptForm
from catconnect import db
from flask_login import login_user, logout_user, login_required, current_user
import urllib.request
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'catconnect/static/uploads/'

app.secret_key = 'secret key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/adoptionpage', methods=['GET', 'POST'])
@login_required
def adoption_page():
    cat_adopt_form = CatAdoptForm()
    cancel_adopt_form = CancelAdoptForm()
    if request.method == "POST":
        #Cat Adoption Logic
        adopted_cats = request.form.get('adopted_cats')
        a_cats_object = Item.query.filter_by(name=adopted_cats).first()
        if a_cats_object:
            if  current_user.can_purchase(a_cats_object):
                a_cats_object.buy(current_user)
                flash(f"Congratulations! You adopted {a_cats_object.name}.", category='success')
            else:
                flash("Unfortunately, you reached the adoption limit.")
        #Cancel Adoption Logic
        returned_cats = request.form.get('returned_cats')
        r_cats_object = Item.query.filter_by(name=returned_cats).first()
        if r_cats_object:
            if current_user.can_sell(r_cats_object):
                r_cats_object.sell(current_user)
                flash(f"You returned {r_cats_object.name} back for adoption.", category='success')
            else:
                flash("Something went wrong with adoption", category='danger')

        return redirect(url_for('adoption_page'))

    if request.method == "GET":
        cats = Item.query.filter_by(owner=None)
        owned_cats = Item.query.filter_by(owner=current_user.id)
        return render_template('adoptionpage.html', cats=cats, cat_adopt_form=cat_adopt_form, owned_cats=owned_cats, cancel_adopt_form=cancel_adopt_form)

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_to_create = User(username=form.username.data,
                              email_address=form.email_address.data,
                              password=form.password1.data)
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        flash(f"Account created successfully! You are now logged in as {user_to_create.username}.", category='success')
        return redirect(url_for('adoption_page'))
    if form.errors != {}:
        for err_msg in form.errors.values():
            flash(f'There was an error in creating a user: {err_msg}', category='danger')

    return render_template('register.html',form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username= form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(
                attempted_password=form.password.data
        ):
            login_user(attempted_user)
            flash(f'Success! You are logged in as: {attempted_user.username}', category='success')
            return redirect(url_for('adoption_page'))
        else:
            flash('Username and password do not match! Please try again.', category='danger')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("home_page"))

@app.route("/addcat", methods=['GET', 'POST'])
def addcat():

    if request.method == 'POST':
        cat_name = request.form['cat_name']
        cat_breed = request.form['breed']
        cat_age = request.form['age']
        cat_desc = request.form['description']

        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No image selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # print('upload_image filename: ' + filename)
            flash('Image successfully uploaded and displayed below')
            # return render_template('index.html', filename=filename)
        else:
            flash('Allowed image types are - png, jpg, jpeg, gif')
            return redirect(request.url)

        cat = Cats(name=cat_name, breed=cat_breed, age=cat_age, description=cat_desc, image=filename)
        our_cats = Cats.query.order_by(Cats.date_added)
        
        db.session.add(cat)
        try:
            db.session.commit()
        except:
            # Add a message for unsuccessful addition of cat
            db.session.rollback()
        db.session.commit()

        return render_template('cat_list.html', cats=our_cats)

    else:
        return render_template('add_cat.html')

@app.route("/catlist")
def cat_list():
    our_cats = Cats.query.order_by(Cats.date_added)
    return render_template('cat_list.html', cats=our_cats)





