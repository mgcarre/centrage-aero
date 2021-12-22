# *_* coding: utf-8 *_*

"""Flask views."""

import os
import logging
import urllib
from datetime import datetime, timezone
import jsonpickle
import pandas as pd

from flask import (
    abort,
    Blueprint,
    current_app,
    render_template,
    flash,
    session,
    redirect,
    request,
    url_for,
    send_from_directory,
)
from .ads import ADs
from .oils import Avgas
from .logbook import FlightLog
from .planes import WeightBalance, PlanePerf
from .forms import PrepflightForm


main = Blueprint("main", __name__)


def get_aerogest_data(current_data):
    """Retrieve flight log data from aerogest.

    It detects a change of aerogest user to refresh the data
    or returns the current data if no change.

    Stores a new dictionary in session variable aerogest_data:
    - pilot: dictionary of username/password
    - flightlog: serialized instance of FlightLog class

    Adds session variable is_logged from FlightLog is_logged attribute.
    """
    if not current_data:
        # Initializing a dict of aerogest data
        # (pilot and flightlog)
        current_data = {}
        session["aerogest_data"] = {}

    if current_data == {} or current_data["pilot"]["username"] != session["username"]:
        new_data = {}
        logging.info("Calling aerogest")
        new_data["pilot"] = {
            "username": session["username"],
            "password": session["password"],
        }
        flightlog = FlightLog(new_data["pilot"], log_format="json")
        # Serialize the instance of FlightLog
        new_data["flightlog"] = jsonpickle.encode(flightlog)

        session["aerogest_data"] = new_data
        session["is_logged"] = flightlog.is_logged


@main.route("/login", methods=["GET", "POST"])
def login():
    """Login to Aerogest Online web site."""
    if session.get("is_logged"):
        flash("Already logged in.")
        return redirect(url_for("main.profile"))
        # return redirect(request.referrer)

    if request.method == "POST":
        username = request.form.get("name")
        password = request.form.get("password")

        session["username"] = username
        session["password"] = password

        get_aerogest_data(session.get("aerogest_data"))

        if not session.get("is_logged"):
            flash("Wrong username or password")
            return redirect(url_for("main.login"))

        return redirect(url_for("main.profile"))

    return render_template(("login.html"))


@main.route("/logout")
def logout():
    """Logout from Aerogest Online."""
    if "username" in session.keys():
        session.clear()
    return redirect(url_for("main.prepflight"))


@main.route("/favicon.ico")
def favicon():
    """Define static path for site favicon."""
    return send_from_directory(
        os.path.join(main.root_path, current_app.config["STATIC_FOLDER"]),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@main.route("/profile")
def profile():
    """Display aerogest log book."""
    # Gets back to login page if first time or aerogest login failed
    if "username" not in session.keys() or not session.get("is_logged"):
        logging.warning("User %s not logged", session.get("username"))
        return redirect(url_for("main.login"))

    get_aerogest_data(session.get("aerogest_data"))

    # Otherwise display logbook
    flightlog = jsonpickle.decode(session.get("aerogest_data")["flightlog"])
    logbook = pd.read_json(flightlog.logbook, convert_dates=False)
    return render_template(
        "profile.html", name=session["username"], dataframe=logbook.to_html(index=None)
    )


@main.route("/fleet")
def fleet():
    """Display planes characteristics."""
    planes = WeightBalance.load_fleet_data()
    return render_template("fleet.html", data=planes)


@main.route("/stats")
def stats():
    """Aerogest log data aggregated."""
    if "username" not in session.keys():
        return redirect(url_for("main.login"))

    get_aerogest_data(session.get("aerogest_data"))

    # Deserialize the instance of FlightLog
    flightlog = jsonpickle.decode(session.get("aerogest_data")["flightlog"])

    flightstats = flightlog.log_agg()
    flightstats_html = [k.to_html(index=True) for k in flightstats]

    last_quarter_html = flightlog.last_quarter().to_html()

    return render_template(
        "stats.html",
        name=session["username"],
        dataframes=flightstats_html,
        last_quarter=last_quarter_html,
    )


@main.route("/", methods=["GET", "POST"])
def prepflight():
    """Form for flight preparation."""
    # form defaults
    form = PrepflightForm()

    if request.method == "POST":
        if form.validate_on_submit():
            # WeightBalance accepts extra parameters - full dict is Ok
            plane = WeightBalance(**form.data)

            if not plane.is_ready_to_fly:
                flash("Chargement invalide", "error")
                return render_template("prepflight.html", form=form, plane=plane)

            tkoff = PlanePerf(
                plane.planetype,
                plane.auw,
                form.data["tkalt"],
                form.data["tktemp"],
                form.data["tkqnh"],
            )
            ldng = PlanePerf(
                plane.planetype,
                plane.auw,
                form.data["ldalt"],
                form.data["ldtemp"],
                form.data["ldqnh"],
            )

            # Get plot images
            balance_img = plane.plot_balance(encode=True)
            tkoff_data = tkoff.predict("takeoff").to_html()
            tkoff_Zp = f"{tkoff.Zp:.0f}"
            tkoff_Zd = f"{tkoff.Zd:.0f}"
            tkoff_img = tkoff.plot_performance("takeoff", encode=True)
            ldng_data = ldng.predict("landing").to_html()
            ldng_Zp = f"{ldng.Zp:.0f}"
            ldng_Zd = f"{ldng.Zd:.0f}"
            ldng_img = ldng.plot_performance("landing", encode=True)

            timestamp = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M %Z")

            tkAD = ADs(form.data["tkaltinput"].upper())
            ldAD = ADs(form.data["ldaltinput"].upper())
            
            return render_template(
                "report.html",
                form=form,
                plane=plane,
                timestamp=timestamp,
                balance=urllib.parse.quote(balance_img),
                takeoff_data=tkoff_data,
                tkoff_Zp=tkoff_Zp,
                tkoff_Zd=tkoff_Zd,
                takeoff=urllib.parse.quote(tkoff_img),
                landing_data=ldng_data,
                ldng_Zp=ldng_Zp,
                ldng_Zd=ldng_Zd,
                landing=urllib.parse.quote(ldng_img),
                tkAD=tkAD,
                ldAD=ldAD,
            )

        logging.error(form.errors)

    return render_template("prepflight.html", form=form)

@main.route("/essence", methods=["GET"])
def essence():
    if not request.args:
        abort(404)
    oil = Avgas(request.args.get('type'))
    return {'density': oil.density, 'title':oil.title}

@main.route("/ad", methods=["GET"])
def aerodrome():
    if not request.args:
        abort(404)

    terrain = ADs(request.args.get('code').upper())
    return {
        'code': terrain.code,
        'var': terrain.var,
        'geo': terrain.point,
        'nom': terrain.nom, 
        'alt': terrain.alt, 
        'trafic': terrain.trafic,
        'statut': terrain.statut
        }