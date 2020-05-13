from flask import Blueprint, render_template, flash, session
from flask_login import login_required, current_user
from .logbook import FlightLog
from .models import LogBook
from . import db
import pandas as pd


main = Blueprint("main", __name__)

def get_aero():
    """Retrieves flight log data from aerogest
    """
    print("HERE", session.keys())
    pilot = LogBook.query.filter_by(pilot=current_user.name).first()
    if not pilot:
        print("THERE")
        session['pilot'] = {"username": current_user.name, "password": current_user.password}
        flightlog = FlightLog(session['pilot'])
        logbook = flightlog.logbook
        logbook['pilot'] = current_user.name
        print(logbook)
        new_rows = []
        for _, row in flightlog.logbook.iterrows():
            new_row = LogBook(
                pilot = row['pilot'],
                date = row['Date'],
                departure = row['H.Départ'],
                arrival = row['H.Retour'],
                model = row['Type'],
                callsign = row['Immat'],
                flight = row['Vol'],
                dfield = row['Départ'],
                afield = row['Arrivée'],
                ftype = row['Type de vol'],
                fmode = row['Mode'],
                duration = row['Temps (hh:mm)']
            )
            new_rows.append(new_row)
        db.session.add_all(new_rows)
        db.session.flush()
        db.session.commit()           

@main.route('/')
@login_required
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    get_aero()
    logbook = db.session.query(LogBook).filter_by(pilot=current_user.name).all()
    print(logbook)
    logbook = pd.read_sql(LogBook, db.get_engine())
    print(logbook)
    return render_template('profile.html', name=current_user.name, dataframe=logbook)

@main.route('/stats')
@login_required
def stats():
    get_aero()
    flightstats = session['flightlog'].log_agg()
    flightstats_html = [k.to_html(index=True) for k in flightstats]
    return render_template('stats.html', name=current_user.name, dataframes=flightstats_html)
