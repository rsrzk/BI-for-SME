from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    signup_date = db.Column(db.DateTime(timezone=True), default=func.now())
    authorization = db.Column(db.String(150))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    company = db.relationship('Company', backref=db.backref('users', lazy=True))
    notes = db.relationship('Note')
    

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150), unique=True)
    creation_date = db.Column(db.DateTime(timezone=True), default=func.now())
    pbi_source = db.Column(db.String(100000))
    drive_folder = db.Column(db.String(100000))

    def to_dict(self):
        return {'id': self.id, 'name': self.company_name}