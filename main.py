import os
import json
from flask import Blueprint, render_template, flash, session, send_from_directory, request
from flask_login import login_required, current_user
from .logbook import FlightLog
from .models import LogBook
from . import db
import pandas as pd


main = Blueprint("main", __name__)

# Global variables
pilot = None
flightlog = None
logbook = None

def get_aero():
    """Retrieves flight log data from aerogest
    """
    global pilot, flightlog, logbook
    if not pilot:
        print("CALLING AEROGEST AGAIN")
        pilot = {"username": current_user.name, "password": current_user.password}
        flightlog = FlightLog(pilot)
        logbook = flightlog.logbook

@main.route('/')
@login_required
def index():
    return render_template('index.html')

@main.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(main.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@main.route('/profile')
@login_required
def profile():
    get_aero()
    return render_template('profile.html', name=current_user.name, dataframe=logbook.to_html(index=None))

@main.route('/stats')
@login_required
def stats():
    get_aero()
    flightstats = flightlog.log_agg()
    flightstats_html = [k.to_html(index=True) for k in flightstats]
    return render_template('stats.html', name=current_user.name, dataframes=flightstats_html)


from .planes import WeightBalance, PlanePerf
from .forms import PrepflightForm
@main.route("/prepflight", methods=['GET', 'POST'])
def prepflight():
    # form defaults
    form = PrepflightForm()
    
    if form.validate_on_submit():
        # WeightBalance accepts extra parameters - full dict is Ok
        p = WeightBalance(**form.data)
        # Split tkoff and ldng data for prediction
        tk_dict = {k: v for k, v in form.data.items() if k.startswith("tk")}
        ld_dict = {k: v for k, v in form.data.items() if k.startswith("ld")}
        tkoff = PlanePerf(p.planetype, p.auw, **tk_dict)
        ldng = PlanePerf(p.planetype, p.auw, **ld_dict)


    else:
        print("ERRORS")
        print(form.errors)
        for k, v in form.errors.items():
            print(k, v)

        #return

    return render_template('prepflight.html', form=form)