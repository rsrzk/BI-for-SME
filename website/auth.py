from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import User, Company
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')            


    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    new_user = None  # Declare the new_user variable with a default value
    if request.method == 'POST':
        # Validating and creating a new user
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 3:
            flash('Password must be at least 3 characters.', category='error')
        else:
            new_user = User(email=email, first_name=first_name, password=generate_password_hash(password1, method='sha256'), company_id=1)

            # Set default authorization based on user count
            if User.query.count() == 0:
                new_user.authorization = 'admin'
            else:
                new_user.authorization = 'member'
            
            # Save the new user to the database
            db.session.add(new_user)
            db.session.commit()
        
        # Check if the user was successfully created
        user_was_created_successfully = new_user is not None

        # Check if the user was created from the admin page
        if 'admin' in request.referrer:
            if user_was_created_successfully:
                flash('New member created successfully.', category='success')
                return redirect(url_for('auth.admin'))
            else:
                flash('Error occurred while creating new member.', category='error')
                return redirect(url_for('auth.admin'))

        else:
            # Remaining code for logging in the new user and redirecting to the home page
            if user_was_created_successfully:
                login_user(new_user, remember=True)
                flash('Account created!', category='success')
                return redirect(url_for('views.home'))
            else:
                flash('Error occurred while creating account.', category='error')
    return render_template("sign_up.html", user=current_user)



@auth.route('/admin')
@login_required
def admin():
    authorization = current_user.authorization
    if authorization == 'admin':
        users = User.query.all()
        companies = Company.query.all()
        return render_template("admin.html", user=current_user, users=users, companies=companies)
    else:
        flash('You must be an admin to access this page.', category='error')
        return redirect(url_for('views.home'))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user
    company_name = user.company.company_name if user.company else None
    user_to_update = User.query.get_or_404(user.id)
    if request.method == 'POST':
        user_to_update.first_name = request.form.get('firstName')
        user_to_update.password1 = request.form.get('password1')
        user_to_update.password2 = request.form.get('password2')

        if len(user_to_update.first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif user_to_update.password1 != user_to_update.password2:
            flash('Passwords don\'t match.', category='error')
        elif len(user_to_update.password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            try:
                update_user = User(id=id, first_name=user_to_update.first_name, password=generate_password_hash(user_to_update.password1, method='sha256'))
                db.session.commit()
                flash('Account updated!', category='success')
                return render_template("profile.html", user=current_user)
            except:
                flash('There was a problem updating your account.', category='error')
                return render_template("profile.html", user=current_user)
    return render_template("profile.html", user=current_user, company_name=company_name)

@auth.route('/admin/delete_user/<int:target_user_id>', methods=['POST'])
@login_required
def delete_user(target_user_id):
    if target_user_id == current_user.id:
        flash("You may not delete your own account.", category='error')
        return redirect(url_for('auth.admin'))

    if target_user_id == 1:
        flash("The admin account 1 cannot be deleted.", category='error')
        return redirect(url_for('auth.admin'))
    
    user = User.query.get(target_user_id)
    if not user:
        flash("User not found.", category='error')
    else:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully.", category='success')

    return redirect(url_for('auth.admin'))

@auth.route('/admin/update_authorization/<int:target_user_id>', methods=['POST'])
@login_required
def update_authorization(target_user_id):
    user = User.query.get(target_user_id)
    new_authorization = request.form['new_authorization']  # Use 'new_authorization' instead of 'authorization'
    user.authorization = new_authorization
    db.session.commit()
    flash("Authorization updated successfully.", category='success')
    return redirect(url_for('auth.admin'))

@auth.route('/assign_company/<int:target_user_id>', methods=['POST'])
def assign_company(target_user_id):
    company_id = int(request.form['company_id'])
    user = User.query.get(target_user_id)
    company = Company.query.get(company_id)

    if user and company:
        user.company = company
        db.session.commit()
        flash('Company assigned successfully!', 'success')
    else:
        flash('User or company not found!', 'error')
    return redirect(url_for('auth.admin'))

@auth.route('/select_company', methods=['POST'])
def select_company():
    company_id = request.form.get('company')
    selected_company = Company.query.get(company_id)

    if selected_company is not None:
        # Store the PBI Source of the selected company in the session
        session['selected_company_pbi'] = selected_company.pbi_source
        session['selected_company_name'] = selected_company.company_name
    else:
        flash('Invalid company selection!', category='error')

    return redirect(url_for('views.home'))

@auth.route('/admin/update_pbi/<int:target_company_id>', methods=['POST'])
@login_required
def update_pbi(target_company_id):
    company = Company.query.get(target_company_id)
    new_pbi = request.form['newPBI']
    company.pbi_source = new_pbi
    db.session.commit()
    flash("PBI source updated successfully.", category='success')
    return redirect(url_for('auth.admin'))

@auth.route('/admin/update_drive/<int:target_company_id>', methods=['POST'])
@login_required
def update_drive(target_company_id):
    company = Company.query.get(target_company_id)
    new_drive = request.form['newDrive']
    company.drive_folder = new_drive
    db.session.commit()
    flash("Google drive folder updated successfully.", category='success')
    return redirect(url_for('auth.admin'))

@auth.route('/create_company', methods=['POST'])
def create_company():
    new_company = None  # Declare the new_user variable with a default value
    if request.method == 'POST':
        # Validating and creating a new user
        company_name = request.form.get('companyName')
        pbi_source = request.form.get('pbiSource')
        drive_folder = request.form.get('driveFolder')

        company_exists = Company.query.filter_by(company_name=company_name).first()
        if company_exists:
            flash('Company already exists.', category='error')
        elif len(company_name) < 1:
            flash('Company name must be greater than 1 character.', category='error')
        else:
            new_company = Company(company_name=company_name, pbi_source=pbi_source, drive_folder=drive_folder)
            
            # Save the new company to the database
            db.session.add(new_company)
            db.session.commit()
        
        # Check if the company was successfully created
        company_was_created_successfully = new_company is not None

        if company_was_created_successfully:
            flash('New company created successfully.', category='success')
            return redirect(url_for('auth.admin'))
        else:
            flash('Error occurred while creating new member.', category='error')
            return redirect(url_for('auth.admin'))
    return render_template("admin.html", user=current_user)