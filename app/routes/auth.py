import os
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models.user import User

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('interview.dashboard'))
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if current_user.is_authenticated:
        return redirect(url_for('interview.dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        error = None

        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif not role:
            error = 'Role selection is required.'
        elif User.query.filter_by(username=username).first() is not None:
            error = f"User {username} is already registered."
        elif User.query.filter_by(email=email).first() is not None:
            error = f"Email {email} is already registered."

        if error is None:
            new_user = User(username=username, email=email, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('auth.login'))

        flash(error, 'danger')

    # Available roles for registration
    roles = [
        {'id': 'software_engineer', 'name': 'Software Engineer'},
        {'id': 'data_scientist', 'name': 'Data Scientist'},
        {'id': 'product_manager', 'name': 'Product Manager'},
        {'id': 'hr', 'name': 'HR Professional'},
        {'id': 'marketing', 'name': 'Marketing Specialist'},
        {'id': 'sales', 'name': 'Sales Representative'},
        {'id': 'customer_support', 'name': 'Customer Support'},
        {'id': 'manager', 'name': 'Manager'}
    ]
    
    return render_template('register.html', roles=roles)


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if current_user.is_authenticated:
        return redirect(url_for('interview.dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form
        error = None

        user = User.query.filter_by(username=username).first()

        if user is None:
            error = 'Incorrect username.'
        elif not user.check_password(password):
            error = 'Incorrect password.'

        if error is None:
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('interview.dashboard')
            flash('Logged in successfully!', 'success')
            return redirect(next_page)
            
        flash(error, 'danger')

    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/profile', methods=('GET', 'POST'))
@login_required
def profile():
    if request.method == 'POST':
        email = request.form['email']
        role = request.form['role']
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        error = None

        # Check if email is already taken by another user
        if email != current_user.email:
            user_with_email = User.query.filter_by(email=email).first()
            if user_with_email and user_with_email.id != current_user.id:
                error = f"Email {email} is already registered by another user."

        # Verify current password if trying to change password
        if new_password and not current_user.check_password(current_password):
            error = "Current password is incorrect."

        if error is None:
            current_user.email = email
            current_user.role = role
            
            if new_password:
                current_user.set_password(new_password)
                
            db.session.commit()
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('auth.profile'))

        flash(error, 'danger')

    # Available roles for updating profile
    roles = [
        {'id': 'software_engineer', 'name': 'Software Engineer'},
        {'id': 'data_scientist', 'name': 'Data Scientist'},
        {'id': 'product_manager', 'name': 'Product Manager'},
        {'id': 'hr', 'name': 'HR Professional'},
        {'id': 'marketing', 'name': 'Marketing Specialist'},
        {'id': 'sales', 'name': 'Sales Representative'},
        {'id': 'customer_support', 'name': 'Customer Support'},
        {'id': 'manager', 'name': 'Manager'}
    ]
    
    return render_template('profile.html', user=current_user, roles=roles)
