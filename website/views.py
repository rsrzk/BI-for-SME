from flask import Blueprint, render_template, flash, request, jsonify, session
from flask_login import login_required, current_user
from .models import Note, Company
from . import db
import json

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    if current_user.authorization == 'admin':
        companies = Company.query.all()
        selected_company_pbi = session.get('selected_company_pbi')
        selected_company_name = session.get('selected_company_name')

        # Convert companies to a list of dictionaries
        companies = [company.to_dict() for company in companies]

        return render_template("home.html", user=current_user, companies=companies, selected_company_pbi=selected_company_pbi, selected_company_name=selected_company_name)
    else:
        if current_user.company:
            return render_template("home.html", user=current_user)
        else:
            return render_template("home.html", user=current_user, no_company=True)

@views.route('/delete-note', methods=['POST'])
def delete_note():  
    note = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})

@views.route('/demo')
def demo():
    return render_template("demo.html", user=current_user)

@views.route('/faq')
def faq():
    return render_template('faq.html', user=current_user)