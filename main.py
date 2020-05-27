import os
import json
from flask import Blueprint, render_template, flash, session, send_from_directory, request
from flask_login import login_required, current_user
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
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
    import urllib
    # form defaults
    form = PrepflightForm()
    
    if form.validate_on_submit():
        # WeightBalance accepts extra parameters - full dict is Ok
        plane = WeightBalance(**form.data)

        tkoff = PlanePerf(plane.planetype, plane.auw, form.data["tkalt"], form.data["tktemp"], form.data["tkqnh"])
        ldng = PlanePerf(plane.planetype, plane.auw, form.data["ldalt"], form.data["ldtemp"], form.data["ldqnh"])
        
        # Get plot images
        balance_img = plane.plot_balance(encode=True)
        tkoff_data = tkoff.predict("takeoff").to_html(classes="dataframe")
        tkoff_img = tkoff.plot_performance("takeoff", encode=True)
        ldng_data = ldng.predict("landing").to_html()
        ldng_img = ldng.plot_performance("landing", encode=True)

        return render_template('report.html', form=form, plane=plane,
                balance=urllib.parse.quote(balance_img),
                takeoff_data=tkoff_data,
                takeoff=urllib.parse.quote(tkoff_img),
                landing_data=ldng_data,
                landing=urllib.parse.quote(ldng_img))
        
    else:
        print("ERRORS")
        print(form.errors)
        for k, v in form.errors.items():
            print(k, v)

        #return

    return render_template('prepflight.html', form=form)