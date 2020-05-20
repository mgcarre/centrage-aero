from flask_login import UserMixin, current_user
from datetime import datetime
from . import db


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)# primary keys are required by SQLAlchemy
    name = db.Column(db.String(1000), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    registered_on = db.Column(db.DateTime, nullable=True)


class LogBook(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pilot = db.Column(db.String(20), primary_key=False, nullable=False)
    date = db.Column(db.String(10), primary_key=False, nullable=False)
    departure = db.Column(db.String(8), primary_key = False, nullable=False)
    arrival = db.Column(db.String(8), nullable=False)
    model = db.Column(db.String(12), nullable=False)
    callsign = db.Column(db.String(8), nullable=False)
    flight = db.Column(db.String(8), nullable=False)
    dfield = db.Column(db.String(4), nullable=False)
    afield = db.Column(db.String(4), nullable=False)
    ftype = db.Column(db.String(10), nullable=False)
    fmode = db.Column(db.String(3), nullable=False)
    duration = db.Column(db.String(8), nullable=False)


