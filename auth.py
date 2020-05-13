from flask import Blueprint, redirect, url_for, render_template, request, flash
#from flask import current_app as app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, LogBook
from . import db

auth = Blueprint("auth", __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash("Already logged in.")
        return redirect(url_for('main.profile'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()

        logbook = LogBook.query.filter_by(pilot=user.name).first()
        if logbook:
            db.session.delete(logbook)
            db.session.commit()

        # check if user actually exists
        # take the user supplied password, hash it, and compare it to the hashed password in database
        #if not user or not check_password_hash(user.password, password):
        if not user or user.password != password:
            flash('Please check your login details and try again.')
            return redirect(url_for('auth.login')) # if user doesn't exist or password is wrong, reload the page

        # if the above check passes, then we know the user has the right credentials
        login_user(user, remember=remember)
        return redirect(url_for('main.profile'))

    return render_template(('login.html'))

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        print('HERE', user)

        if user:
            flash('Email address already exists')
            return redirect(url_for('auth.signup'))

        #new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))
        new_user = User(email=email, name=name, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('User registered')
        return redirect(url_for('auth.login'))

    return render_template('signup.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
