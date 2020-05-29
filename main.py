import os
import logging
import json
import pandas as pd
import urllib
from datetime import datetime, timezone
from flask import Blueprint, render_template, flash, session, send_from_directory, request
from flask_login import login_required, current_user
from .logbook import FlightLog
from .models import LogBook
from .planes import WeightBalance, PlanePerf
from .forms import PrepflightForm
from . import db


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
        logging.info("CALLING AEROGEST AGAIN")
        pilot = {"username": current_user.name, "password": current_user.password}
        flightlog = FlightLog(pilot)
        logbook = flightlog.logbook

# @main.route('/')
# @login_required
# def index():
#     return render_template('index.html')

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
    last_quarter = flightlog.last_quarter().to_html(index=True)
    flightstats_html = [k.to_html(index=True) for k in flightstats]
    return render_template('stats.html', name=current_user.name,
                        dataframes=flightstats_html, last_quarter=last_quarter)

@main.route("/", methods=['GET', 'POST'])
def prepflight():
    # form defaults
    form = PrepflightForm()
    
    if request.method == "POST":
        if form.validate_on_submit():
            # WeightBalance accepts extra parameters - full dict is Ok
            plane = WeightBalance(**form.data)

            tkoff = PlanePerf(plane.planetype, plane.auw, form.data["tkalt"], form.data["tktemp"], form.data["tkqnh"])
            ldng = PlanePerf(plane.planetype, plane.auw, form.data["ldalt"], form.data["ldtemp"], form.data["ldqnh"])
            
            # Get plot images
            balance_img = plane.plot_balance(encode=True)
            tkoff_data = tkoff.predict("takeoff").to_html()
            tkoff_img = tkoff.plot_performance("takeoff", encode=True)
            ldng_data = ldng.predict("landing").to_html()
            ldng_img = ldng.plot_performance("landing", encode=True)

            timestamp = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M %Z")

            return render_template('report.html', form=form, plane=plane,
                    timestamp = timestamp,
                    balance=urllib.parse.quote(balance_img),
                    takeoff_data=tkoff_data,
                    takeoff=urllib.parse.quote(tkoff_img),
                    landing_data=ldng_data,
                    landing=urllib.parse.quote(ldng_img))
            
        else:
            print("ERRORS")
            print(form.data)
            print(form.errors)
            for k, v in form.errors.items():
                print(k, v)
                print(form[k])

            #return

    return render_template('prepflight.html', form=form)