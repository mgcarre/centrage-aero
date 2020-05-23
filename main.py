import os
import json
from flask import Blueprint, render_template, flash, session, send_from_directory
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
@main.route("/prepflight")
def prepflight():
    # form defaults
    form = PrepflightForm(tktemp=15, ldtemp=15, tkqnh=1013, ldqnh=1013)

    planes = json.dumps(WeightBalance._planes)
    callsigns = list(WeightBalance._planes.keys())
    plane = WeightBalance(callsigns[0])

    form.plane.choices = ["FXXXX"] + callsigns
    
    form.bew = plane.bew
    form.bearm = plane.cg
    form.bemoment = plane.moment

    # Front row
    weight_range = range(0, 145, 5)
    form.pax0.choices = weight_range
    form.pax1.choices = weight_range
    #form.frontweight = plane.frontweight
    form.frontarm = plane.arms["front"]
    form.frontmoment = plane.frontmoment
    # Rear row
    form.pax2.choices = weight_range
    form.pax3.choices = weight_range
    form.rearweight = plane.rearweight
    form.reararm = plane.arms["rear"]
    form.rearmoment = plane.rearmoment
    # Baggage
    form.baggage.choices = range(0, plane.bagmax + 1, 5)
    form.bagweight = plane.baggage
    form.bagarm = plane.arms["baggage"]
    form.bagmoment = plane.bagmoment
    # Fuel
    form.fuel = plane.fuel
    form.fuelmass = plane.fuel_mass
    form.fuelgauge.choices = [0, .5, 1, 1.5, 2, 2.5, 3, 3.5, 4]
    form.fuelarm = plane.arms["fuel"]
    form.fuelmoment = plane.fuelmoment
    form.auxfuel.choices = range(0, plane.maxauxfuel + 40, 5)
    form.auxfuelmass = plane.auxfuel_mass
    form.auxfuelarm = plane.arms["auxfuel"]
    form.auxfuelmoment = plane.auxfuelmoment
    # Performances
    form.tkalt.choices = range(0, 8100, 100)
    form.ldalt.choices = range(0, 8100, 100)
    form.tktemp.choices = range(-20, 51, 1)
    form.ldtemp.choices = range(-20, 50, 1)
    form.tkqnh.choices = range(950, 1051, 1)
    form.ldqnh.choices = range(950, 1050, 1)

    return render_template('prepflight.html', form=form, planes=planes)