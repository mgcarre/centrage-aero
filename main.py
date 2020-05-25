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
    form = PrepflightForm(tktemp=15, ldtemp=15, tkqnh=1013, ldqnh=1013)
    
    if request.method == 'POST':
        if form.is_submitted():
            print("FORM SUBMITTED")
            print(form.plane.data)
        if form.validate():
            print(form.data)
        else:
            print(form.errors)

    planes = json.dumps(WeightBalance._planes)
    callsigns = list(WeightBalance._planes.keys())
    plane = WeightBalance(callsigns[0])

    form.plane.choices = ["FXXXX"] + callsigns
    
    form.bew = plane.bew
    form.bearm = plane.cg
    form.bemoment = plane.moment

    # Front row
    pax_weight_range = range(0, 145, 5)
    pax_weight_range = [i for i in zip(pax_weight_range, pax_weight_range)]
    form.pax0.choices = pax_weight_range
    form.pax1.choices = pax_weight_range
    #form.frontweight = plane.frontweight
    form.frontarm = plane.arms["front"]
    form.frontmoment = plane.frontmoment
    # Rear row
    form.pax2.choices = pax_weight_range
    form.pax3.choices = pax_weight_range
    form.rearweight = plane.rearweight
    form.reararm = plane.arms["rear"]
    form.rearmoment = plane.rearmoment
    # Baggage
    baggage_weight_range = range(0, plane.bagmax + 1, 5)
    form.baggage.choices = [i for i in zip(baggage_weight_range, baggage_weight_range)]
    form.bagweight = plane.baggage
    form.bagarm = plane.arms["baggage"]
    form.bagmoment = plane.bagmoment
    # Fuel
    form.fuel = plane.fuel
    form.fuelmass = plane.fuel_mass
    fuel_gauge_range = [0, .5, 1, 1.5, 2, 2.5, 3, 3.5, 4]
    form.fuelgauge.choices = [i for i in zip(fuel_gauge_range, fuel_gauge_range)]
    form.fuelarm = plane.arms["fuel"]
    form.fuelmoment = plane.fuelmoment
    # Sth to do here about the max
    auxfuel_weight_range = range(0, plane.maxauxfuel + 41, 5)
    form.auxfuel.choices = [i for i in zip(auxfuel_weight_range, auxfuel_weight_range)]
    form.auxfuelmass = plane.auxfuel_mass
    form.auxfuelarm = plane.arms["auxfuel"]
    form.auxfuelmoment = plane.auxfuelmoment
    # Performances
    altitude_range = range(0, 8100, 100)
    altitude_choices = [i for i in zip(altitude_range, altitude_range)]
    form.tkalt.choices = altitude_choices
    form.ldalt.choices = altitude_choices
    temperature_range = range(-20, 51, 1)
    temperature_choices = [i for i in zip(temperature_range, temperature_range)]
    form.tktemp.choices = temperature_choices
    form.ldtemp.choices = temperature_choices
    qnh_range = range(950, 1051, 1)
    qnh_choices = [i for i in zip(qnh_range, qnh_range)]
    form.tkqnh.choices = qnh_choices
    form.ldqnh.choices = qnh_choices

    return render_template('prepflight.html', form=form, planes=planes)